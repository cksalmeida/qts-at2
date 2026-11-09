"""Páginas HTML. Reaproveitam o MESMO serviço da API: nenhuma regra de negócio aqui."""

from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import repository
from app.schemas import ConsultaEntrada
from app.services import agendamento
from app.services.feriados import ServicoFeriadosIndisponivel

router = APIRouter(include_in_schema=False)

templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")

NOMES_ESPECIALIDADES = {
    "clinico_geral": "Clínico geral",
    "cardiologia": "Cardiologia",
    "dermatologia": "Dermatologia",
    "pediatria": "Pediatria",
}

ROTULOS_CAMPOS = {
    "paciente_nome": "Nome (3 a 100 caracteres)",
    "paciente_email": "E-mail",
    "especialidade": "Especialidade",
    "data": "Data",
    "horario": "Horário",
    "observacoes": "Observações (até 500 caracteres)",
}


def data_br(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


templates.env.filters["data_br"] = data_br
templates.env.globals["especialidades"] = NOMES_ESPECIALIDADES


def _redirecionar(**parametros: str) -> RedirectResponse:
    """POST → 303 → GET: o navegador troca o POST por um GET em `/`."""
    return RedirectResponse(f"/?{urlencode(parametros)}", status_code=status.HTTP_303_SEE_OTHER)


def _mensagem_validacao(erro: ValidationError) -> str:
    campos = dict.fromkeys(ROTULOS_CAMPOS[str(e["loc"][0])] for e in erro.errors())
    return "Verifique os campos: " + ", ".join(campos) + "."


def _formulario(request: Request, valores: dict, erro: str, status_code: int) -> HTMLResponse:
    contexto = {
        "valores": valores,
        "erro": erro,
        "horarios": [h.strftime("%H:%M") for h in agendamento.HORARIOS_ATENDIMENTO],
    }
    return templates.TemplateResponse(request, "agendar.html", contexto, status_code=status_code)


@router.get("/", response_class=HTMLResponse)
def pagina_lista(request: Request, msg: str | None = None, erro: str | None = None) -> HTMLResponse:
    contexto = {"consultas": repository.listar(), "sucesso": msg, "erro": erro}
    return templates.TemplateResponse(request, "lista.html", contexto)


@router.get("/agendar", response_class=HTMLResponse)
def pagina_agendar(request: Request) -> HTMLResponse:
    return _formulario(request, valores={}, erro="", status_code=status.HTTP_200_OK)


@router.post("/agendar", response_class=HTMLResponse, response_model=None)
def enviar_agendamento(
    request: Request,
    paciente_nome: str = Form(""),
    paciente_email: str = Form(""),
    especialidade: str = Form(""),
    data: str = Form(""),
    horario: str = Form(""),
    observacoes: str = Form(""),
) -> HTMLResponse | RedirectResponse:
    valores = {
        "paciente_nome": paciente_nome,
        "paciente_email": paciente_email,
        "especialidade": especialidade,
        "data": data,
        "horario": horario,
        "observacoes": observacoes,
    }
    try:
        entrada = ConsultaEntrada(**(valores | {"observacoes": observacoes or None}))
        consulta = agendamento.agendar(entrada)
    except ValidationError as erro:
        return _formulario(request, valores, _mensagem_validacao(erro), 422)
    except agendamento.RegraNegocioViolada as erro:
        return _formulario(request, valores, str(erro), 422)
    except agendamento.HorarioOcupado as erro:
        return _formulario(request, valores, str(erro), 409)
    except ServicoFeriadosIndisponivel as erro:
        return _formulario(request, valores, str(erro), 503)
    return _redirecionar(
        msg=f"Consulta de {consulta.paciente_nome} agendada para "
        f"{data_br(consulta.data)} às {consulta.horario.strftime('%H:%M')}."
    )


@router.post("/consultas/{id}/cancelar")
def cancelar_consulta(id: int) -> RedirectResponse:
    consulta = repository.obter(id)
    if consulta is None or not repository.excluir(id):
        return _redirecionar(erro="Consulta não encontrada.")
    return _redirecionar(msg=f"Consulta de {consulta.paciente_nome} cancelada.")
