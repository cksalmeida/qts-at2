"""Factory de massa de dados de teste.

Por que existe: um único lugar sabe montar uma consulta VÁLIDA. Cada teste chama
ConsultaFactory.build() e sobrescreve apenas o campo que quer provar (ex.: horario="07:00"),
deixando explícito no teste o que importa e escondendo o que é só "preenchimento".
Se o modelo mudar (um campo novo obrigatório, por exemplo), só esta classe é ajustada.

As datas nunca são fixas: são calculadas a partir de hoje, para os testes não
quebrarem com o passar do tempo.
"""

from datetime import date, timedelta

from faker import Faker

from app.schemas import Especialidade
from app.services.agendamento import HORARIOS_ATENDIMENTO

fake = Faker("pt_BR")

DIAS_A_FRENTE = 60


def proximo_dia_util(a_partir_de_dias: int = 1) -> date:
    """Primeira data de segunda a sexta a partir de hoje + N dias."""
    dia = date.today() + timedelta(days=a_partir_de_dias)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


def proximo_sabado() -> date:
    hoje = date.today()
    dias_ate_sabado = (5 - hoje.weekday()) % 7 or 7
    return hoje + timedelta(days=dias_ate_sabado)


def dia_util_aleatorio() -> date:
    return proximo_dia_util(fake.random_int(min=1, max=DIAS_A_FRENTE))


class ConsultaFactory:
    @staticmethod
    def build(**sobrescritas: object) -> dict:
        """Dicionário pronto para JSON (data e horário em ISO)."""
        consulta = {
            "paciente_nome": fake.name(),
            "paciente_email": fake.email(),
            "especialidade": fake.random_element(list(Especialidade)).value,
            "data": dia_util_aleatorio().isoformat(),
            "horario": fake.random_element(HORARIOS_ATENDIMENTO).strftime("%H:%M"),
            "observacoes": fake.sentence(nb_words=8),
        }
        consulta.update(sobrescritas)
        return consulta

    @classmethod
    def build_batch(cls, quantidade: int, **sobrescritas: object) -> list[dict]:
        """Gera `quantidade` consultas sem repetir (especialidade, data, horario),
        para que um lote nunca provoque um 409 por acaso."""
        lote: list[dict] = []
        chaves: set[tuple] = set()
        while len(lote) < quantidade:
            consulta = cls.build(**sobrescritas)
            chave = (consulta["especialidade"], consulta["data"], consulta["horario"])
            if chave not in chaves:
                chaves.add(chave)
                lote.append(consulta)
        return lote
