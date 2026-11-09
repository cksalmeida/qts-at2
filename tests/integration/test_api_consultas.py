"""Testes de integração das rotas /api/... (RN01–RN06, formato e disponibilidade)."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from app.schemas import Especialidade
from app.services.agendamento import HORARIOS_ATENDIMENTO
from app.services.feriados import ServicoFeriadosIndisponivel
from tests.factories import ConsultaFactory, fake, proximo_dia_util, proximo_sabado

pytestmark = pytest.mark.integration

ID_INEXISTENTE = 999_999
ALVO_FERIADOS = "app.services.agendamento.buscar_feriados"


# ---------------------------------------------------------------- Fluxo principal


def test_post_valido_retorna_201_com_payload_e_id(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    consulta = ConsultaFactory.build()

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert isinstance(corpo["id"], int)
    esperado = consulta | {"id": corpo["id"], "horario": f"{consulta['horario']}:00"}
    assert corpo == esperado


def test_listagem_contem_consulta_criada(client: TestClient, consulta_criada: dict) -> None:
    # Arrange
    id_esperado = consulta_criada["id"]

    # Act
    resposta = client.get("/api/consultas")

    # Assert
    assert resposta.status_code == 200
    assert id_esperado in [consulta["id"] for consulta in resposta.json()]


def test_filtro_por_data_retorna_so_consultas_do_dia(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    dia_alvo = proximo_dia_util(1)
    outro_dia = proximo_dia_util((dia_alvo - date.today()).days + 1)
    client.post("/api/consultas", json=ConsultaFactory.build(data=dia_alvo.isoformat()))
    client.post("/api/consultas", json=ConsultaFactory.build(data=outro_dia.isoformat()))

    # Act
    resposta = client.get("/api/consultas", params={"data": dia_alvo.isoformat()})

    # Assert
    assert resposta.status_code == 200
    datas = [consulta["data"] for consulta in resposta.json()]
    assert datas == [dia_alvo.isoformat()]


def test_get_por_id_retorna_200(client: TestClient, consulta_criada: dict) -> None:
    # Arrange
    id_consulta = consulta_criada["id"]

    # Act
    resposta = client.get(f"/api/consultas/{id_consulta}")

    # Assert
    assert resposta.status_code == 200
    assert resposta.json() == consulta_criada


def test_get_por_id_inexistente_retorna_404(client: TestClient) -> None:
    # Arrange
    url = f"/api/consultas/{ID_INEXISTENTE}"

    # Act
    resposta = client.get(url)

    # Assert
    assert resposta.status_code == 404


def test_delete_retorna_204_e_consulta_some(client: TestClient, consulta_criada: dict) -> None:
    # Arrange
    url = f"/api/consultas/{consulta_criada['id']}"

    # Act
    resposta_delete = client.delete(url)
    resposta_get = client.get(url)

    # Assert
    assert resposta_delete.status_code == 204
    assert resposta_get.status_code == 404


def test_delete_inexistente_retorna_404(client: TestClient) -> None:
    # Arrange
    url = f"/api/consultas/{ID_INEXISTENTE}"

    # Act
    resposta = client.delete(url)

    # Assert
    assert resposta.status_code == 404


# --------------------------------------------------------------- Regras de negócio


def test_rn01_data_no_passado_retorna_422(client: TestClient, sem_feriados: MagicMock) -> None:
    # Arrange
    ontem = date.today() - timedelta(days=1)
    consulta = ConsultaFactory.build(data=ontem.isoformat())

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    assert "passado" in resposta.json()["detail"]


def test_rn02_sabado_retorna_422(client: TestClient, sem_feriados: MagicMock) -> None:
    # Arrange
    consulta = ConsultaFactory.build(data=proximo_sabado().isoformat())

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    assert "fim de semana" in resposta.json()["detail"]


def test_rn03_feriado_retorna_422_com_nome(client: TestClient, mocker: MockerFixture) -> None:
    # Arrange
    data_escolhida = proximo_dia_util()
    mocker.patch(ALVO_FERIADOS, return_value={data_escolhida: "Feriado de Teste"})
    consulta = ConsultaFactory.build(data=data_escolhida.isoformat())

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    assert "Feriado de Teste" in resposta.json()["detail"]


@pytest.mark.parametrize("horario", ["07:00", "09:15", "18:00"])
def test_rn04_horario_fora_do_atendimento_retorna_422(
    client: TestClient, sem_feriados: MagicMock, horario: str
) -> None:
    # Arrange
    consulta = ConsultaFactory.build(horario=horario)

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    assert horario in resposta.json()["detail"]


def test_rn05_mesma_especialidade_data_horario_retorna_409(
    client: TestClient, consulta_criada: dict
) -> None:
    # Arrange
    conflitante = ConsultaFactory.build(
        especialidade=consulta_criada["especialidade"],
        data=consulta_criada["data"],
        horario=consulta_criada["horario"],
    )

    # Act
    resposta = client.post("/api/consultas", json=conflitante)

    # Assert
    assert resposta.status_code == 409


def test_rn05_outra_especialidade_mesmo_horario_retorna_201(
    client: TestClient, consulta_criada: dict
) -> None:
    # Arrange
    outra = fake.random_element(
        [e.value for e in Especialidade if e.value != consulta_criada["especialidade"]]
    )
    consulta = ConsultaFactory.build(
        especialidade=outra, data=consulta_criada["data"], horario=consulta_criada["horario"]
    )

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 201


def test_rn06_api_feriados_indisponivel_retorna_503(
    client: TestClient, mocker: MockerFixture
) -> None:
    # Arrange
    mocker.patch(ALVO_FERIADOS, side_effect=ServicoFeriadosIndisponivel)
    consulta = ConsultaFactory.build()

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 503
    assert "indisponível" in resposta.json()["detail"]
    assert client.get("/api/consultas").json() == []


# ------------------------------------------------------- Validação de formato (Pydantic)


@pytest.mark.parametrize(
    "campo, valor_invalido",
    [
        ("paciente_email", "email-sem-arroba"),
        ("paciente_nome", "Ab"),
        ("especialidade", "ortopedia"),
    ],
    ids=["email_invalido", "nome_curto", "especialidade_inexistente"],
)
def test_formato_invalido_retorna_422(
    client: TestClient, sem_feriados: MagicMock, campo: str, valor_invalido: str
) -> None:
    # Arrange
    consulta = ConsultaFactory.build(**{campo: valor_invalido})

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    assert campo in str(resposta.json()["detail"])
    sem_feriados.assert_not_called()


# ------------------------------------------------------------------ Disponibilidade


def test_disponibilidade_dia_livre_tem_20_horarios(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    parametros = {
        "data": proximo_dia_util().isoformat(),
        "especialidade": ConsultaFactory.build()["especialidade"],
    }

    # Act
    resposta = client.get("/api/disponibilidade", params=parametros)

    # Assert
    assert resposta.status_code == 200
    assert len(resposta.json()["horarios_livres"]) == len(HORARIOS_ATENDIMENTO) == 20


def test_disponibilidade_exclui_horario_agendado(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    consulta = ConsultaFactory.build(horario="09:00")
    client.post("/api/consultas", json=consulta)
    parametros = {"data": consulta["data"], "especialidade": consulta["especialidade"]}

    # Act
    resposta = client.get("/api/disponibilidade", params=parametros)

    # Assert
    assert resposta.status_code == 200
    livres = resposta.json()["horarios_livres"]
    assert "09:00:00" not in livres
    assert len(livres) == 19


def test_disponibilidade_em_feriado_retorna_422(
    client: TestClient, mocker: MockerFixture
) -> None:
    # Arrange
    data_escolhida = proximo_dia_util()
    nome_feriado = fake.catch_phrase()
    mocker.patch(ALVO_FERIADOS, return_value={data_escolhida: nome_feriado})
    parametros = {"data": data_escolhida.isoformat(), "especialidade": "pediatria"}

    # Act
    resposta = client.get("/api/disponibilidade", params=parametros)

    # Assert
    assert resposta.status_code == 422
    assert nome_feriado in resposta.json()["detail"]


def test_disponibilidade_com_api_fora_retorna_503(
    client: TestClient, mocker: MockerFixture
) -> None:
    # Arrange
    mocker.patch(ALVO_FERIADOS, side_effect=ServicoFeriadosIndisponivel)
    parametros = {"data": proximo_dia_util().isoformat(), "especialidade": "pediatria"}

    # Act
    resposta = client.get("/api/disponibilidade", params=parametros)

    # Assert
    assert resposta.status_code == 503
    assert resposta.json()["detail"]


# ------------------------------------------------------------ Mock como evidência


def test_dia_util_consulta_feriados_do_ano_uma_vez(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    consulta = ConsultaFactory.build()
    ano = date.fromisoformat(consulta["data"]).year

    # Act
    client.post("/api/consultas", json=consulta)

    # Assert
    sem_feriados.assert_called_once_with(ano)


def test_sabado_nao_consulta_api_de_feriados(
    client: TestClient, sem_feriados: MagicMock
) -> None:
    # Arrange
    consulta = ConsultaFactory.build(data=proximo_sabado().isoformat())

    # Act
    resposta = client.post("/api/consultas", json=consulta)

    # Assert
    assert resposta.status_code == 422
    sem_feriados.assert_not_called()
