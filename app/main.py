"""Ponto de entrada: cria o FastAPI, inicializa o banco e mapeia exceções → HTTP."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import inicializar_banco
from app.routes import api, pages
from app.services.agendamento import HorarioOcupado, RegraNegocioViolada
from app.services.feriados import ServicoFeriadosIndisponivel


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    inicializar_banco()  # roda uma vez, antes da primeira requisição
    yield


app = FastAPI(
    title="Agenda de Consultas",
    description="Agendamento de consultas com verificação de feriados nacionais (BrasilAPI).",
    lifespan=lifespan,
)


def _erro(status_code: int, erro: Exception) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": str(erro)})


@app.exception_handler(RegraNegocioViolada)
async def tratar_regra_violada(request: Request, erro: RegraNegocioViolada) -> JSONResponse:
    return _erro(status.HTTP_422_UNPROCESSABLE_CONTENT, erro)


@app.exception_handler(HorarioOcupado)
async def tratar_horario_ocupado(request: Request, erro: HorarioOcupado) -> JSONResponse:
    return _erro(status.HTTP_409_CONFLICT, erro)


@app.exception_handler(ServicoFeriadosIndisponivel)
async def tratar_feriados_indisponivel(
    request: Request, erro: ServicoFeriadosIndisponivel
) -> JSONResponse:
    return _erro(status.HTTP_503_SERVICE_UNAVAILABLE, erro)


app.include_router(api.router)
app.include_router(pages.router)
