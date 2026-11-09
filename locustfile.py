"""Teste de carga (RNF01): 50 pacientes usando a agenda ao mesmo tempo.

Este arquivo é um CLIENTE EXTERNO, como um navegador ou app de celular: fala com a
aplicação apenas por HTTP e não importa nada de `app/`.

Execução reproduzível (servidor em outro terminal, sem --reload):
    AGENDA_DB_PATH=carga.db uv run uvicorn app.main:app --port 8000
    uv run locust -f locustfile.py --host http://127.0.0.1:8000 --users 50 \\
        --spawn-rate 5 --run-time 1m --headless --csv resultados/carga
"""

from datetime import date, timedelta

from faker import Faker
from locust import HttpUser, between, task
from locust.clients import ResponseContextManager

fake = Faker("pt_BR")

ESPECIALIDADES = ["clinico_geral", "cardiologia", "dermatologia", "pediatria"]
HORARIOS = [f"{hora:02d}:{minuto:02d}" for hora in range(8, 18) for minuto in (0, 30)]
DIAS_A_FRENTE = 60
MARCA_DIA_SEM_ATENDIMENTO = "Não há atendimento"
MARCA_FIM_DE_SEMANA = "fim de semana"


def dia_util_aleatorio() -> str:
    """Segunda a sexta nos próximos 60 dias (pode cair em feriado real; ver abaixo)."""
    dia = date.today() + timedelta(days=fake.random_int(min=1, max=DIAS_A_FRENTE))
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia.isoformat()


def _detalhe(resposta: ResponseContextManager) -> str:
    try:
        return str(resposta.json().get("detail", ""))
    except ValueError:
        return ""


def _e_feriado(resposta: ResponseContextManager) -> bool:
    """Como só geramos dias úteis futuros, um 422 "Não há atendimento em ..." que não
    seja de fim de semana só pode ser feriado nacional (RN03)."""
    detalhe = _detalhe(resposta)
    return MARCA_DIA_SEM_ATENDIMENTO in detalhe and MARCA_FIM_DE_SEMANA not in detalhe


def classificar(resposta: ResponseContextManager, aceitar_conflito: bool = False) -> None:
    """Decide o que é FALHA DE DESEMPENHO.

    Rejeições previstas pelas regras de negócio são respostas corretas e rápidas da
    aplicação, não erros. Contá-las como falha distorceria a métrica do RNF01:
    - 409: horário ocupado. Com 50 usuários escolhendo entre 20 horários, colisões
      são esperadas (e provam que RN05 resiste à concorrência).
    - 422 de feriado: a data aleatória pode cair num feriado real (ex.: 25/12).
    Qualquer outro status fora de 2xx (500, 503, 422 inesperado, timeout) é falha.
    """
    if resposta.ok:
        resposta.success()
    elif aceitar_conflito and resposta.status_code == 409:
        resposta.success()
    elif resposta.status_code == 422 and _e_feriado(resposta):
        resposta.success()
    else:
        resposta.failure(f"HTTP {resposta.status_code}: {_detalhe(resposta)[:120]}")


class Paciente(HttpUser):
    # Pausa de 1 a 3 s entre ações, como uma pessoa lendo a tela antes de clicar.
    wait_time = between(1, 3)

    @task(5)
    def listar_consultas(self) -> None:
        self.client.get("/api/consultas", name="/api/consultas")

    @task(3)
    def ver_disponibilidade(self) -> None:
        parametros = {"data": dia_util_aleatorio(), "especialidade": fake.random_element(ESPECIALIDADES)}
        with self.client.get(
            "/api/disponibilidade", params=parametros,
            name="/api/disponibilidade", catch_response=True,
        ) as resposta:
            classificar(resposta)

    @task(2)
    def abrir_pagina_inicial(self) -> None:
        self.client.get("/", name="/")

    @task(1)
    def agendar_consulta(self) -> None:
        consulta = {
            "paciente_nome": fake.name(),
            "paciente_email": fake.email(),
            "especialidade": fake.random_element(ESPECIALIDADES),
            "data": dia_util_aleatorio(),
            "horario": fake.random_element(HORARIOS),
            "observacoes": fake.sentence(nb_words=6),
        }
        with self.client.post(
            "/api/consultas", json=consulta, name="/api/consultas", catch_response=True
        ) as resposta:
            classificar(resposta, aceitar_conflito=True)
