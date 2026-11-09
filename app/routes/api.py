"""Rotas JSON /api/... — apenas traduzem HTTP ↔ serviço, sem regras de negócio."""

from datetime import date

from fastapi import APIRouter, HTTPException, Response, status

from app import repository
from app.schemas import ConsultaEntrada, ConsultaSaida, Disponibilidade, Especialidade
from app.services import agendamento

router = APIRouter(prefix="/api", tags=["API"])

CONSULTA_NAO_ENCONTRADA = "Consulta não encontrada."


@router.get("/consultas", response_model=list[ConsultaSaida])
def listar_consultas(data: date | None = None) -> list[ConsultaSaida]:
    return repository.listar(data)


@router.get(
    "/consultas/{id}",
    response_model=ConsultaSaida,
    responses={404: {"description": CONSULTA_NAO_ENCONTRADA}},
)
def obter_consulta(id: int) -> ConsultaSaida:
    consulta = repository.obter(id)
    if consulta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, CONSULTA_NAO_ENCONTRADA)
    return consulta


@router.post(
    "/consultas",
    response_model=ConsultaSaida,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": "Horário já ocupado (RN05)."},
        422: {"description": "Dados inválidos ou regra RN01–RN04 violada."},
        503: {"description": "Serviço de feriados indisponível (RN06)."},
    },
)
def criar_consulta(entrada: ConsultaEntrada) -> ConsultaSaida:
    return agendamento.agendar(entrada)


@router.delete(
    "/consultas/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": CONSULTA_NAO_ENCONTRADA}},
)
def cancelar_consulta(id: int) -> Response:
    if not repository.excluir(id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, CONSULTA_NAO_ENCONTRADA)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/disponibilidade",
    response_model=Disponibilidade,
    responses={
        422: {"description": "Dia sem atendimento (RN01–RN03)."},
        503: {"description": "Serviço de feriados indisponível (RN06)."},
    },
)
def consultar_disponibilidade(data: date, especialidade: Especialidade) -> Disponibilidade:
    livres = agendamento.horarios_disponiveis(data, especialidade)
    return Disponibilidade(data=data, especialidade=especialidade, horarios_livres=livres)
