"""Operações no banco SQLite (única camada que escreve SQL)."""

import sqlite3
from contextlib import closing
from datetime import date, time

from app.database import conectar
from app.schemas import ConsultaEntrada, ConsultaSaida

COLUNAS = "id, paciente_nome, paciente_email, especialidade, data, horario, observacoes"


def _para_consulta(linha: sqlite3.Row) -> ConsultaSaida:
    return ConsultaSaida(
        id=linha["id"],
        paciente_nome=linha["paciente_nome"],
        paciente_email=linha["paciente_email"],
        especialidade=linha["especialidade"],
        data=date.fromisoformat(linha["data"]),
        horario=time.fromisoformat(linha["horario"]),
        observacoes=linha["observacoes"],
    )


def inserir(entrada: ConsultaEntrada) -> ConsultaSaida:
    """Insere a consulta. Propaga sqlite3.IntegrityError se violar o UNIQUE."""
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute(
            "INSERT INTO consultas (paciente_nome, paciente_email, especialidade,"
            " data, horario, observacoes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                entrada.paciente_nome,
                entrada.paciente_email,
                entrada.especialidade.value,
                entrada.data.isoformat(),
                entrada.horario.strftime("%H:%M"),
                entrada.observacoes,
            ),
        )
        novo_id = cursor.lastrowid
    return ConsultaSaida(id=novo_id, **entrada.model_dump())


def listar(data: date | None = None) -> list[ConsultaSaida]:
    sql = f"SELECT {COLUNAS} FROM consultas"
    parametros: tuple[str, ...] = ()
    if data is not None:
        sql += " WHERE data = ?"
        parametros = (data.isoformat(),)
    sql += " ORDER BY data, horario, especialidade"
    with closing(conectar()) as conexao:
        linhas = conexao.execute(sql, parametros).fetchall()
    return [_para_consulta(linha) for linha in linhas]


def obter(id: int) -> ConsultaSaida | None:
    with closing(conectar()) as conexao:
        linha = conexao.execute(
            f"SELECT {COLUNAS} FROM consultas WHERE id = ?", (id,)
        ).fetchone()
    return _para_consulta(linha) if linha else None


def excluir(id: int) -> bool:
    with closing(conectar()) as conexao, conexao:
        cursor = conexao.execute("DELETE FROM consultas WHERE id = ?", (id,))
    return cursor.rowcount > 0


def horarios_ocupados(data: date, especialidade: str) -> set[time]:
    with closing(conectar()) as conexao:
        linhas = conexao.execute(
            "SELECT horario FROM consultas WHERE data = ? AND especialidade = ?",
            (data.isoformat(), especialidade),
        ).fetchall()
    return {time.fromisoformat(linha["horario"]) for linha in linhas}


def limpar() -> None:
    with closing(conectar()) as conexao, conexao:
        conexao.execute("DELETE FROM consultas")
