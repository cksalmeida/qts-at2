"""Único módulo que faz requisição HTTP externa (BrasilAPI — feriados nacionais)."""

from datetime import date

import httpx

URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"
TIMEOUT_SEGUNDOS = 5

_cache: dict[int, dict[date, str]] = {}


class ServicoFeriadosIndisponivel(Exception):
    """A BrasilAPI não respondeu corretamente; não é possível confirmar o dia útil."""


def _consultar_api(ano: int) -> list[dict]:
    try:
        resposta = httpx.get(URL.format(ano=ano), timeout=TIMEOUT_SEGUNDOS)
    except httpx.HTTPError as erro:
        raise ServicoFeriadosIndisponivel(
            "Serviço de feriados indisponível. Tente novamente mais tarde."
        ) from erro
    if resposta.status_code != 200:
        raise ServicoFeriadosIndisponivel(
            f"Serviço de feriados indisponível (status {resposta.status_code})."
            " Tente novamente mais tarde."
        )
    try:
        return resposta.json()
    except ValueError as erro:
        raise ServicoFeriadosIndisponivel(
            "Serviço de feriados retornou uma resposta inválida."
        ) from erro


def _converter(itens: list[dict]) -> dict[date, str]:
    try:
        return {date.fromisoformat(item["date"]): item["name"] for item in itens}
    except (TypeError, KeyError, ValueError) as erro:
        raise ServicoFeriadosIndisponivel(
            "Serviço de feriados retornou uma resposta inválida."
        ) from erro


def buscar_feriados(ano: int) -> dict[date, str]:
    """Retorna {data: nome_do_feriado} do ano, usando cache em memória."""
    if ano in _cache:
        return _cache[ano]
    feriados = _converter(_consultar_api(ano))
    _cache[ano] = feriados
    return feriados


def limpar_cache() -> None:
    _cache.clear()
