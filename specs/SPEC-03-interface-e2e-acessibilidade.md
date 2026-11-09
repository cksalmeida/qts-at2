# SPEC-03 — Interface web, testes E2E com Playwright e acessibilidade

## Objetivo
Criar as páginas HTML de listagem e agendamento e testá-las como um usuário real:
testes E2E (`@pytest.mark.e2e`) com Playwright e Page Object Model, auditoria WCAG 2.1 AA
com Axe-core e verificação de navegação por teclado (`@pytest.mark.accessibility`).

## Referências
- `PRD.md`: seções 6 (rotas de páginas), 7 (interface), 8 (RNF02 e RNF03) e 9.
- `CLAUDE.md`: acessibilidade e padrões de teste.
- SPECs 01 e 02 concluídas.

## Escopo
**Dentro:** templates, `app/routes/pages.py`, `tests/e2e/`, `tests/accessibility/`, fixtures de servidor.
**Fora:** carga (SPEC-04), README (SPEC-05).

## Parte A — Interface

### 1. Templates (`app/templates/`)
- `base.html`: `<html lang="pt-BR">`, `<title>` por página, `<header>` com navegação ("Consultas" e "Agendar consulta"), `<main>`, área de mensagens. CSS embutido simples, com contraste AA e `outline` de foco visível.
- `lista.html`: `<h1>Consultas agendadas</h1>`; tabela com `<caption>` e `<th scope="col">` (Paciente, Especialidade, Data, Horário, Ações); em cada linha, um `<form method="post" action="/consultas/{id}/cancelar">` com botão "Cancelar consulta de {nome}" (texto acessível único por linha). Sem consultas: parágrafo "Nenhuma consulta agendada."
- `agendar.html`: `<h1>Agendar consulta</h1>`; campos com `<label for>`, nesta ordem: Nome, E-mail, Especialidade (select com nomes legíveis, ex.: "Cardiologia"), Data (`type="date"`), Horário (select de 08:00 a 17:30), Observações (textarea); botão "Agendar". Em erro, reexibir os valores digitados.
- Mensagens: sucesso em `<div role="status">`, erro em `<div role="alert">`.
- Datas exibidas no formato `dd/mm/aaaa`.

### 2. Rotas de página (`app/routes/pages.py`)
- `GET /` → lista; lê `?msg=` para exibir mensagem de sucesso.
- `GET /agendar` → formulário.
- `POST /agendar` → recebe `Form(...)`, monta `ConsultaEntrada` e chama o **mesmo** `agendar()` do serviço. Sucesso: `RedirectResponse("/?msg=...", status_code=303)`. Erro de validação, regra, conflito ou API fora: reexibe o formulário com a mensagem em `role="alert"` e o status HTTP correspondente (422, 409 ou 503).
- `POST /consultas/{id}/cancelar` → exclui e redireciona com 303 e mensagem.
- Configurar `Jinja2Templates` e incluir o router em `main.py`.

## Parte B — Infraestrutura de testes de interface

### 3. Dependências
- `uv add --dev pytest-playwright axe-playwright-python`
- `uv run playwright install chromium`

### 4. Fixtures (`tests/conftest.py`, adicionar)
| Fixture | Escopo | O que faz |
|---|---|---|
| `feriado_de_teste` | session | Devolve uma data = `proximo_dia_util(a_partir_de_dias=10)` |
| `servidor` | session | Cria banco em `tmp_path_factory`, define `AGENDA_DB_PATH`, aplica `session_mocker.patch("app.services.agendamento.buscar_feriados", return_value={feriado_de_teste: "Feriado de Teste"})`, sobe o uvicorn em uma *thread* (`uvicorn.Server` + `threading.Thread`, porta 8765), aguarda `server.started`, `yield "http://127.0.0.1:8765"`; no teardown, `server.should_exit = True`, `join()` da thread e restaura a variável de ambiente |
| `base_url` | session | Sobrescreve a fixture do pytest-playwright devolvendo o endereço do `servidor`, para usar `page.goto("/agendar")` com caminho relativo |
| `banco_limpo` | function | Para testes de interface: chama `repository.limpar()` antes de cada teste |

Explicar por que o servidor roda em *thread* no mesmo processo: assim o `session_mocker` vale também para as requisições que o navegador faz, e os testes não dependem da internet.

### 5. Page Objects (`tests/e2e/pages/`)
- `agendamento_page.py` — `AgendamentoPage(page)`:
  `abrir()`, `preencher(dados: dict)`, `enviar()`, `agendar(dados)` (preenche e envia), `alerta` (propriedade: `page.get_by_role("alert")`).
  Seleções: `get_by_label("Nome")`, `get_by_label("Especialidade").select_option(label=...)`, `get_by_role("button", name="Agendar")` etc.
- `lista_page.py` — `ListaConsultasPage(page)`:
  `abrir()`, `linha_do_paciente(nome)` (`get_by_role("row", name=...)`), `cancelar(nome)`, `status` (propriedade: `get_by_role("status")`), `mensagem_vazia` (`get_by_text("Nenhuma consulta agendada.")`).
- Page Objects não fazem `assert`: só ações e localizadores. Os `expect` ficam nos testes.

## Parte C — Testes

### 6. E2E (`tests/e2e/test_fluxo_agendamento.py`, `@pytest.mark.e2e`)
- Agendar com dados da Factory → redireciona para a lista, `status` com mensagem de sucesso e linha do paciente visível.
- Agendar no `feriado_de_teste` → permanece no formulário e `alerta` contém "Feriado de Teste".
- Agendar duas vezes o mesmo horário e especialidade → segundo envio mostra `alerta` de horário ocupado.
- Cancelar uma consulta existente → linha some e `status` confirma o cancelamento.
- Nos cenários de sucesso, garantir que a data gerada pela Factory seja diferente de `feriado_de_teste` (senão o teste falharia aleatoriamente).
- `fill` em campo `type="date"` usa o formato `AAAA-MM-DD`.
- Usar `expect(...)` do `playwright.sync_api` (espera automática), nunca `time.sleep`.

### 7. Acessibilidade (`tests/accessibility/test_acessibilidade.py`, `@pytest.mark.accessibility`)
- Axe-core (`from axe_playwright_python.sync_playwright import Axe`) restrito às tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, nas páginas:
  - `/` vazia e com consultas;
  - `/agendar` limpa e após um erro (com `role="alert"` visível).
  - Assert: zero violações; em caso de falha, a mensagem do assert mostra o relatório do Axe.
  - Confirmar na documentação do pacote a forma exata de passar as tags e ler as violações.
- Teclado (`/agendar`):
  - Focar "Nome" e, a cada `page.keyboard.press("Tab")`, verificar com `expect(...).to_be_focused()` a ordem: E-mail → Especialidade → Data → Horário → Observações → botão Agendar.
  - Preencher o formulário só com teclado e enviar com `Enter` → consulta agendada.
- Se o Axe apontar violação, **corrigir o HTML**, não o teste, e explicar a violação encontrada.

## Critérios de aceite
- [ ] `uv run uvicorn app.main:app --reload`: páginas navegáveis e funcionando no navegador.
- [ ] `uv run pytest -m e2e -v` passando.
- [ ] `uv run pytest -m accessibility -v` passando, com zero violações.
- [ ] `uv run pytest -m e2e --headed --slowmo 500` mostra o navegador executando o fluxo (útil para o vídeo).
- [ ] `uv run pytest -v` roda as três suítes juntas sem interferência.
- [ ] Nenhum seletor CSS ou XPath nos testes.

## Explicações esperadas do Claude Code
- O que é o Page Object Model e o que se ganha com ele.
- Por que seletores semânticos também são um teste indireto de acessibilidade.
- Como funcionam as esperas automáticas do `expect`.
- O padrão POST → redirect 303 → GET e por que ele evita reenvio do formulário.
- Cada regra do Axe que eventualmente falhar e como foi corrigida.

## Commit sugerido
`feat: interface web, testes E2E e de acessibilidade (SPEC-03)`
