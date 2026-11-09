"""Page Object da listagem /: só ações e localizadores, sem asserts."""

from playwright.sync_api import Locator, Page


class ListaConsultasPage:
    CAMINHO = "/"

    def __init__(self, page: Page) -> None:
        self.page = page

    def abrir(self) -> "ListaConsultasPage":
        self.page.goto(self.CAMINHO)
        return self

    def linha_do_paciente(self, nome: str) -> Locator:
        return self.page.get_by_role("row", name=nome)

    def cancelar(self, nome: str) -> None:
        self.page.get_by_role("button", name=f"Cancelar consulta de {nome}").click()

    @property
    def status(self) -> Locator:
        return self.page.get_by_role("status")

    @property
    def mensagem_vazia(self) -> Locator:
        return self.page.get_by_text("Nenhuma consulta agendada.")
