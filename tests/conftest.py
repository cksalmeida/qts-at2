"""Fixtures compartilhadas pelos testes."""

import os
import threading
import time
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import uvicorn
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app import repository
from app.database import inicializar_banco
from app.main import app
from app.services.feriados import limpar_cache
from tests.factories import ConsultaFactory, proximo_dia_util

HOST = "127.0.0.1"
PORTA = 8765
TEMPO_MAXIMO_SUBIDA = 10


@pytest.fixture
def banco_temporario(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Cada teste ganha um SQLite próprio, criado antes e apagado depois."""
    caminho = tmp_path / "agenda_teste.db"
    monkeypatch.setenv("AGENDA_DB_PATH", str(caminho))
    inicializar_banco()

    yield caminho

    caminho.unlink(missing_ok=True)


@pytest.fixture
def client(banco_temporario: Path) -> Iterator[TestClient]:
    """O `with` dispara o lifespan da aplicação (startup/shutdown)."""
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture(autouse=True)
def limpar_cache_feriados() -> Iterator[None]:
    """Garante que nenhum teste herde feriados em cache de outro teste."""
    limpar_cache()
    yield
    limpar_cache()


@pytest.fixture
def sem_feriados(mocker: MockerFixture) -> MagicMock:
    """Substitui a consulta à BrasilAPI onde ela é USADA: nenhum dia é feriado."""
    return mocker.patch("app.services.agendamento.buscar_feriados", return_value={})


@pytest.fixture
def consulta_criada(client: TestClient, sem_feriados: MagicMock) -> dict:
    resposta = client.post("/api/consultas", json=ConsultaFactory.build())
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


# ------------------------------------------------- Interface (E2E e acessibilidade)


@pytest.fixture(scope="session")
def feriado_de_teste() -> date:
    return proximo_dia_util(a_partir_de_dias=10)


def _aguardar_subida(servidor: uvicorn.Server, thread: threading.Thread) -> None:
    limite = time.monotonic() + TEMPO_MAXIMO_SUBIDA
    while not servidor.started:
        if not thread.is_alive() or time.monotonic() > limite:
            raise RuntimeError(f"O servidor de testes não subiu em {HOST}:{PORTA}.")
        time.sleep(0.05)


@pytest.fixture(scope="session")
def servidor(
    tmp_path_factory: pytest.TempPathFactory,
    session_mocker: MockerFixture,
    feriado_de_teste: date,
) -> Iterator[str]:
    """Sobe a aplicação real numa thread DESTE processo, para que o mock de feriados
    valha também para as requisições feitas pelo navegador (e nada dependa da internet)."""
    caminho_original = os.environ.get("AGENDA_DB_PATH")
    os.environ["AGENDA_DB_PATH"] = str(tmp_path_factory.mktemp("e2e") / "agenda_e2e.db")
    session_mocker.patch(
        "app.services.agendamento.buscar_feriados",
        return_value={feriado_de_teste: "Feriado de Teste"},
    )
    config = uvicorn.Config(app, host=HOST, port=PORTA, log_level="warning")
    servidor_uvicorn = uvicorn.Server(config)
    thread = threading.Thread(target=servidor_uvicorn.run, daemon=True)
    thread.start()
    _aguardar_subida(servidor_uvicorn, thread)

    yield f"http://{HOST}:{PORTA}"

    servidor_uvicorn.should_exit = True
    thread.join(timeout=TEMPO_MAXIMO_SUBIDA)
    if caminho_original is None:
        os.environ.pop("AGENDA_DB_PATH", None)
    else:
        os.environ["AGENDA_DB_PATH"] = caminho_original


@pytest.fixture(scope="session")
def base_url(servidor: str) -> str:
    """Sobrescreve a fixture do pytest-playwright: permite page.goto("/agendar")."""
    return servidor


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Contexto em português (Accept-Language, formatação de números e datas no JS)."""
    return {**browser_context_args, "locale": "pt-BR"}


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict) -> dict:
    """O formato do <input type="date"> segue o IDIOMA DO NAVEGADOR (--lang), não o
    locale do contexto. Com pt-BR, os segmentos ficam dd/mm/aaaa em qualquer máquina."""
    argumentos = [*browser_type_launch_args.get("args", []), "--lang=pt-BR"]
    return {**browser_type_launch_args, "args": argumentos}


@pytest.fixture
def banco_limpo(servidor: str) -> None:
    """Cada teste de interface começa com a agenda vazia."""
    repository.limpar()


@pytest.fixture
def dados_consulta(feriado_de_teste: date) -> dict:
    """Consulta válida da Factory cuja data NUNCA cai no feriado simulado
    (senão um cenário de sucesso falharia aleatoriamente)."""
    dados = ConsultaFactory.build()
    while dados["data"] == feriado_de_teste.isoformat():
        dados = ConsultaFactory.build()
    return dados
