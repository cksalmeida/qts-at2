"""Testes do serviço de feriados. A dependência real é a rede, então o mock é em httpx.get."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import httpx
import pytest
from pytest_mock import MockerFixture

from app.services.feriados import ServicoFeriadosIndisponivel, buscar_feriados
from tests.factories import fake, proximo_dia_util

pytestmark = pytest.mark.integration

ALVO_HTTP = "app.services.feriados.httpx.get"


def _resposta(mocker: MockerFixture, status_code: int, corpo: object = None) -> MagicMock:
    resposta = mocker.Mock(status_code=status_code)
    resposta.json.return_value = corpo
    return resposta


def _feriados_brasilapi(ano: int, quantidade: int = 3) -> list[dict]:
    """Lista no formato da BrasilAPI com datas e nomes aleatórios do ano informado."""
    inicio = date(ano, 1, 1)
    datas = sorted({inicio + timedelta(days=fake.random_int(0, 364)) for _ in range(quantidade)})
    return [
        {"date": dia.isoformat(), "name": fake.catch_phrase(), "type": "national"}
        for dia in datas
    ]


def test_resposta_200_vira_dicionario_data_nome(mocker: MockerFixture) -> None:
    # Arrange
    ano = proximo_dia_util().year
    corpo = _feriados_brasilapi(ano)
    mocker.patch(ALVO_HTTP, return_value=_resposta(mocker, 200, corpo))

    # Act
    feriados = buscar_feriados(ano)

    # Assert
    assert feriados == {date.fromisoformat(item["date"]): item["name"] for item in corpo}


def test_resposta_500_lanca_servico_indisponivel(mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch(ALVO_HTTP, return_value=_resposta(mocker, 500))

    # Act
    with pytest.raises(ServicoFeriadosIndisponivel) as erro:
        buscar_feriados(proximo_dia_util().year)

    # Assert
    assert "status 500" in str(erro.value)


def test_erro_de_conexao_lanca_servico_indisponivel(mocker: MockerFixture) -> None:
    # Arrange
    mocker.patch(ALVO_HTTP, side_effect=httpx.ConnectError("sem conexão"))

    # Act
    with pytest.raises(ServicoFeriadosIndisponivel) as erro:
        buscar_feriados(proximo_dia_util().year)

    # Assert
    assert "indisponível" in str(erro.value)


def test_json_invalido_lanca_servico_indisponivel(mocker: MockerFixture) -> None:
    # Arrange
    resposta = _resposta(mocker, 200)
    resposta.json.side_effect = ValueError("JSON inválido")
    mocker.patch(ALVO_HTTP, return_value=resposta)

    # Act
    with pytest.raises(ServicoFeriadosIndisponivel) as erro:
        buscar_feriados(proximo_dia_util().year)

    # Assert
    assert "resposta inválida" in str(erro.value)


def test_cache_evita_segunda_chamada_http(mocker: MockerFixture) -> None:
    # Arrange
    ano = proximo_dia_util().year
    mock_get = mocker.patch(
        ALVO_HTTP, return_value=_resposta(mocker, 200, _feriados_brasilapi(ano))
    )

    # Act
    primeira = buscar_feriados(ano)
    segunda = buscar_feriados(ano)

    # Assert
    mock_get.assert_called_once()
    assert primeira == segunda


def test_falha_nao_fica_no_cache(mocker: MockerFixture) -> None:
    # Arrange
    ano = proximo_dia_util().year
    corpo = _feriados_brasilapi(ano)
    mock_get = mocker.patch(
        ALVO_HTTP,
        side_effect=[httpx.ConnectError("sem conexão"), _resposta(mocker, 200, corpo)],
    )
    with pytest.raises(ServicoFeriadosIndisponivel):
        buscar_feriados(ano)

    # Act
    feriados = buscar_feriados(ano)

    # Assert
    assert mock_get.call_count == 2
    assert len(feriados) == len(corpo)
