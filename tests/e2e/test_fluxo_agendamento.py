"""Fluxo de agendar, ver na lista e cancelar, como um usuário real no navegador."""

import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages import AgendamentoPage, ListaConsultasPage

pytestmark = [pytest.mark.e2e, pytest.mark.usefixtures("banco_limpo")]


def test_agendar_redireciona_para_lista_com_sucesso(page: Page, dados_consulta: dict) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    lista = ListaConsultasPage(page)

    # Act
    formulario.agendar(dados_consulta)

    # Assert
    expect(page).to_have_url(re.compile(r"/\?msg="))
    expect(lista.status).to_contain_text("agendada")
    expect(lista.linha_do_paciente(dados_consulta["paciente_nome"])).to_be_visible()


def test_agendar_em_feriado_mostra_alerta(
    page: Page, dados_consulta: dict, feriado_de_teste: date
) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    dados = dados_consulta | {"data": feriado_de_teste.isoformat()}

    # Act
    formulario.agendar(dados)

    # Assert
    expect(formulario.alerta).to_contain_text("Feriado de Teste")
    expect(page).to_have_url("/agendar")
    expect(formulario.nome).to_have_value(dados["paciente_nome"])


def test_agendar_horario_ocupado_mostra_alerta(page: Page, dados_consulta: dict) -> None:
    # Arrange
    formulario = AgendamentoPage(page).abrir()
    formulario.agendar(dados_consulta)
    expect(ListaConsultasPage(page).status).to_be_visible()
    formulario.abrir()

    # Act
    formulario.agendar(dados_consulta)

    # Assert
    expect(formulario.alerta).to_contain_text("Horário ocupado")


def test_cancelar_remove_linha_e_confirma(page: Page, dados_consulta: dict) -> None:
    # Arrange
    nome = dados_consulta["paciente_nome"]
    AgendamentoPage(page).abrir().agendar(dados_consulta)
    lista = ListaConsultasPage(page)
    expect(lista.linha_do_paciente(nome)).to_be_visible()

    # Act
    lista.cancelar(nome)

    # Assert
    expect(lista.status).to_contain_text("cancelada")
    expect(lista.linha_do_paciente(nome)).to_have_count(0)
    expect(lista.mensagem_vazia).to_be_visible()
