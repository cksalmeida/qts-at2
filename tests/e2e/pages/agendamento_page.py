"""Page Object do formulário /agendar: só ações e localizadores, sem asserts."""

from playwright.sync_api import Locator, Page

from app.routes.pages import NOMES_ESPECIALIDADES


class AgendamentoPage:
    CAMINHO = "/agendar"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.nome = page.get_by_label("Nome")
        self.email = page.get_by_label("E-mail")
        self.especialidade = page.get_by_label("Especialidade")
        self.data = page.get_by_label("Data")
        self.horario = page.get_by_label("Horário")
        self.observacoes = page.get_by_label("Observações")
        self.botao_agendar = page.get_by_role("button", name="Agendar")

    def abrir(self) -> "AgendamentoPage":
        self.page.goto(self.CAMINHO)
        return self

    def preencher(self, dados: dict) -> None:
        """`dados` no formato da ConsultaFactory (data em AAAA-MM-DD, horário HH:MM)."""
        self.nome.fill(dados["paciente_nome"])
        self.email.fill(dados["paciente_email"])
        self.especialidade.select_option(label=NOMES_ESPECIALIDADES[dados["especialidade"]])
        self.data.fill(dados["data"])
        self.horario.select_option(label=dados["horario"])
        self.observacoes.fill(dados.get("observacoes") or "")

    def enviar(self) -> None:
        self.botao_agendar.click()

    def agendar(self, dados: dict) -> None:
        self.preencher(dados)
        self.enviar()

    @property
    def alerta(self) -> Locator:
        return self.page.get_by_role("alert")
