"""RNF02 (WCAG 2.1 A/AA com Axe-core) e RNF03 (operação só pelo teclado)."""

from datetime import date

import pytest
from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import Locator, Page, expect

from app.routes.pages import NOMES_ESPECIALIDADES
from tests.e2e.pages import AgendamentoPage, ListaConsultasPage

pytestmark = [pytest.mark.accessibility, pytest.mark.usefixtures("banco_limpo")]

OPCOES_AXE = {
    "runOnly": {"type": "tag", "values": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]},
    "resultTypes": ["violations"],
}


MAXIMO_PARADAS_NO_CAMPO = 6


def _tab_ate_sair(page: Page, campo: Locator) -> None:
    """O Chromium põe paradas de Tab DENTRO do <input type="date"> (dia, mês, ano e o
    botão do calendário). Isso é comportamento nativo e acessível do navegador, não do
    nosso HTML; por isso avançamos até o foco sair do campo, sem fixar a contagem."""
    for _ in range(MAXIMO_PARADAS_NO_CAMPO):
        page.keyboard.press("Tab")
        if not campo.evaluate("elemento => elemento === document.activeElement"):
            return
    raise AssertionError("O foco ficou preso no campo de data.")


def _prefixo_unico(nome: str, opcoes: list[str]) -> str:
    """Menor início de `nome` que nenhuma outra opção compartilha (ex.: "Cl" para
    "Clínico geral"). A busca por digitação do <select> só precisa disso, e assim
    evitamos acentos e espaços (o espaço abre a lista de opções)."""
    for tamanho in range(1, len(nome) + 1):
        prefixo = nome[:tamanho].lower()
        if not any(o.lower().startswith(prefixo) for o in opcoes if o != nome):
            return nome[:tamanho]
    return nome


def _auditar(page: Page) -> tuple[int, str]:
    resultado = Axe().run(page, options=OPCOES_AXE)
    return resultado.violations_count, resultado.generate_report()


# ------------------------------------------------------------------- Axe-core


def test_lista_vazia_sem_violacoes(page: Page) -> None:
    # Arrange
    lista = ListaConsultasPage(page).abrir()
    expect(lista.mensagem_vazia).to_be_visible()

    # Act
    violacoes, relatorio = _auditar(page)

    # Assert
    assert violacoes == 0, relatorio


def test_lista_com_consultas_sem_violacoes(page: Page, dados_consulta: dict) -> None:
    # Arrange
    AgendamentoPage(page).abrir().agendar(dados_consulta)
    lista = ListaConsultasPage(page)
    expect(lista.linha_do_paciente(dados_consulta["paciente_nome"])).to_be_visible()

    # Act
    violacoes, relatorio = _auditar(page)

    # Assert
    assert violacoes == 0, relatorio


def test_formulario_limpo_sem_violacoes(page: Page) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    expect(formulario.botao_agendar).to_be_visible()

    # Act
    violacoes, relatorio = _auditar(page)

    # Assert
    assert violacoes == 0, relatorio


def test_formulario_com_erro_sem_violacoes(
    page: Page, dados_consulta: dict, feriado_de_teste: date
) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    formulario.agendar(dados_consulta | {"data": feriado_de_teste.isoformat()})
    expect(formulario.alerta).to_be_visible()

    # Act
    violacoes, relatorio = _auditar(page)

    # Assert
    assert violacoes == 0, relatorio


# -------------------------------------------------------------------- Teclado


def test_ordem_do_tab_segue_a_ordem_visual(page: Page) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    formulario.nome.focus()
    ordem_esperada = [
        formulario.email,
        formulario.especialidade,
        formulario.data,
        formulario.horario,
        formulario.observacoes,
        formulario.botao_agendar,
    ]

    for anterior, proximo in zip([formulario.nome, *ordem_esperada], ordem_esperada):
        # Act
        if anterior == formulario.data:
            _tab_ate_sair(page, formulario.data)
        else:
            page.keyboard.press("Tab")

        # Assert
        expect(proximo).to_be_focused()


def test_agendar_usando_apenas_teclado(page: Page, dados_consulta: dict) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    lista = ListaConsultasPage(page)
    ano, mes, dia = dados_consulta["data"].split("-")
    especialidade = NOMES_ESPECIALIDADES[dados_consulta["especialidade"]]
    formulario.nome.focus()

    # Act
    page.keyboard.type(dados_consulta["paciente_nome"])
    page.keyboard.press("Tab")
    page.keyboard.type(dados_consulta["paciente_email"])
    page.keyboard.press("Tab")
    page.keyboard.type(_prefixo_unico(especialidade, list(NOMES_ESPECIALIDADES.values())))
    page.keyboard.press("Tab")
    page.keyboard.type(f"{dia}{mes}{ano}")  # campo de data em pt-BR: dd/mm/aaaa
    _tab_ate_sair(page, formulario.data)
    page.keyboard.type(dados_consulta["horario"])
    page.keyboard.press("Tab")
    page.keyboard.type(dados_consulta["observacoes"])
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")

    # Assert
    expect(lista.status).to_contain_text("agendada")
    expect(lista.linha_do_paciente(dados_consulta["paciente_nome"])).to_be_visible()
