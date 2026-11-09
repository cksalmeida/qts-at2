"""Modelos Pydantic: validam apenas o FORMATO dos dados.

As regras de negócio (RN01–RN06) ficam em app/services/agendamento.py.
"""

from datetime import date, time
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Especialidade(str, Enum):
    clinico_geral = "clinico_geral"
    cardiologia = "cardiologia"
    dermatologia = "dermatologia"
    pediatria = "pediatria"


class ConsultaEntrada(BaseModel):
    paciente_nome: str = Field(min_length=3, max_length=100)
    paciente_email: EmailStr
    especialidade: Especialidade
    data: date
    horario: time
    observacoes: str | None = Field(default=None, max_length=500)


class ConsultaSaida(ConsultaEntrada):
    id: int


class Disponibilidade(BaseModel):
    data: date
    especialidade: Especialidade
    horarios_livres: list[time]
