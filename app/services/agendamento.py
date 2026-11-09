"""Regras de negócio RN01–RN06 do agendamento de consultas."""

import sqlite3
from datetime import date, time

from app import repository
from app.schemas import ConsultaEntrada, ConsultaSaida, Especialidade
from app.services.feriados import ServicoFeriadosIndisponivel, buscar_feriados

__all__ = [
    "HORARIOS_ATENDIMENTO",
    "HorarioOcupado",
    "RegraNegocioViolada",
    "ServicoFeriadosIndisponivel",
    "agendar",
    "horarios_disponiveis",
    "validar_dia",
]

HORARIOS_ATENDIMENTO: list[time] = [
    time(hora, minuto) for hora in range(8, 18) for minuto in (0, 30)
]  # 08:00, 08:30, ..., 17:30


class RegraNegocioViolada(Exception):
    """Violação de RN01–RN04 (→ 422)."""


class HorarioOcupado(Exception):
    """Violação de RN05 (→ 409)."""


def _formatar(data: date) -> str:
    return data.strftime("%d/%m/%Y")


def _validar_passado(data: date) -> None:  # RN01
    if data < date.today():
        raise RegraNegocioViolada(
            f"A data {_formatar(data)} está no passado. Escolha uma data a partir de hoje."
        )


def _validar_fim_de_semana(data: date) -> None:  # RN02
    if data.weekday() >= 5:
        raise RegraNegocioViolada(
            f"Não há atendimento em {_formatar(data)}: a data cai em fim de semana."
        )


def _validar_feriado(data: date) -> None:  # RN03 (pode lançar ServicoFeriadosIndisponivel → RN06)
    nome_feriado = buscar_feriados(data.year).get(data)
    if nome_feriado:
        raise RegraNegocioViolada(
            f"Não há atendimento em {_formatar(data)}: {nome_feriado}"
        )


def _validar_horario(horario: time) -> None:  # RN04
    if horario not in HORARIOS_ATENDIMENTO:
        raise RegraNegocioViolada(
            f"Horário {horario.strftime('%H:%M')} inválido. O atendimento é das 08:00"
            " às 17:30, em intervalos de 30 minutos."
        )


def validar_dia(data: date) -> None:
    """RN01 → RN02 → RN03. A consulta externa vem por último, de propósito."""
    _validar_passado(data)
    _validar_fim_de_semana(data)
    _validar_feriado(data)


def _mensagem_ocupado(entrada: ConsultaEntrada) -> str:
    return (
        f"Já existe consulta de {entrada.especialidade.value} em"
        f" {_formatar(entrada.data)} às {entrada.horario.strftime('%H:%M')}."
    )


def agendar(entrada: ConsultaEntrada) -> ConsultaSaida:
    _validar_horario(entrada.horario)
    validar_dia(entrada.data)
    ocupados = repository.horarios_ocupados(entrada.data, entrada.especialidade.value)
    if entrada.horario in ocupados:  # RN05
        raise HorarioOcupado(_mensagem_ocupado(entrada))
    try:
        return repository.inserir(entrada)
    except sqlite3.IntegrityError as erro:  # RN05 sob concorrência
        raise HorarioOcupado(_mensagem_ocupado(entrada)) from erro


def horarios_disponiveis(data: date, especialidade: Especialidade) -> list[time]:
    validar_dia(data)
    ocupados = repository.horarios_ocupados(data, especialidade.value)
    return [horario for horario in HORARIOS_ATENDIMENTO if horario not in ocupados]
