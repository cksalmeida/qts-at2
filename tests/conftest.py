"""Fixtures compartilhadas pelos testes."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app.database import inicializar_banco
from app.main import app
from app.services.feriados import limpar_cache
from tests.factories import ConsultaFactory


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

