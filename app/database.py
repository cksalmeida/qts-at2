"""Conexão com o SQLite e criação do esquema."""

import os
import sqlite3
from contextlib import closing

CAMINHO_PADRAO = "agenda.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS consultas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_nome TEXT NOT NULL,
    paciente_email TEXT NOT NULL,
    especialidade TEXT NOT NULL,
    data TEXT NOT NULL,
    horario TEXT NOT NULL,
    observacoes TEXT,
    UNIQUE (especialidade, data, horario)
)
"""


def caminho_banco() -> str:
    """Lê AGENDA_DB_PATH a cada chamada, para os testes poderem trocar o banco."""
    return os.environ.get("AGENDA_DB_PATH", CAMINHO_PADRAO)


def conectar() -> sqlite3.Connection:
    conexao = sqlite3.connect(caminho_banco(), timeout=10)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco() -> None:
    with closing(conectar()) as conexao, conexao:
        conexao.execute(ESQUEMA)
