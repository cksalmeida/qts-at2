# CLAUDE.md — Regras de contexto para o Claude Code

Este arquivo orienta o Claude Code em todo o desenvolvimento deste projeto.
A fonte de verdade dos requisitos é o `PRD.md`. As tarefas estão divididas em SPECs na pasta `specs/`.
Em caso de dúvida ou ambiguidade, pergunte em vez de supor.

## Forma de trabalho
- Implemente **somente a SPEC indicada** no pedido. Não adiante itens de SPECs seguintes.
- Este é um projeto de aprendizado: ao terminar cada arquivo, explique em detalhes o que cada trecho faz e por que foi escrito assim.
- Ao final da SPEC, rode os comandos dos critérios de aceite, mostre o resultado e liste o que foi criado ou alterado.
- Se algo da SPEC conflitar com o `PRD.md` ou com este arquivo, pare e pergunte.
- Não faça commits: o autor revisa e commita cada SPEC.

## Stack obrigatória
- Python 3.12+, projeto gerenciado com **uv** (`pyproject.toml`). Comandos sempre via `uv run`.
- Dependências adicionadas com `uv add` (produção) e `uv add --dev` (testes e carga).
- FastAPI para rotas, Pydantic v2 para validação, Jinja2 para páginas HTML, SQLite (módulo `sqlite3`), httpx para a API externa.
- Não adicionar dependências fora das previstas nas SPECs sem justificar.

## Arquitetura
- `app/services/feriados.py` é o **único** módulo que faz requisição HTTP externa.
- Regras de negócio (RN01–RN06 do PRD) ficam em `app/services/agendamento.py`, nunca dentro das rotas.
- Acesso ao banco fica em `app/repository.py`.
- Rotas JSON em `app/routes/api.py`; páginas HTML em `app/routes/pages.py`.
- Códigos de status HTTP seguem a tabela de rotas do `PRD.md`.
- O caminho do banco SQLite vem da variável de ambiente `AGENDA_DB_PATH` (padrão `agenda.db`), lida no momento da conexão, para que os testes possam usar um banco temporário.

## Padrões de teste
- Todo teste segue **AAA** (Arrange, Act, Assert), com os três blocos separados por linha em branco e comentados (`# Arrange`, `# Act`, `# Assert`).
- Todo teste tem um marcador: `integration`, `e2e` ou `accessibility`.
- Dados de teste vêm das Factories em `tests/factories.py` (`Faker("pt_BR")`); não usar dados fixos no corpo do teste, exceto o valor que o teste quer provar.
- Datas de teste nunca são fixas: são calculadas a partir de hoje (ex.: próximo dia útil), para os testes não quebrarem com o passar do tempo.
- Mocks com `mocker.patch` apontam para onde a função é **usada** (ex.: `app.services.agendamento.buscar_feriados`), não onde foi definida.
- Para cada regra que depende da API externa, testar sucesso **e** falha.
- Testes E2E usam **Page Object Model** (`tests/e2e/pages/`) e apenas seletores semânticos: `get_by_role`, `get_by_label`, `get_by_text`. Proibido usar seletores CSS ou XPath.
- Nenhum teste pode depender de internet.

## Acessibilidade (HTML)
- `<html lang="pt-BR">`, estrutura com `<header>`, `<main>` e um único `<h1>` por página.
- Todo campo de formulário tem `<label for>` associado.
- Mensagens de erro usam `role="alert"`; de sucesso, `role="status"`.
- Não remover o contorno de foco (`outline`) dos elementos.
- Contraste mínimo compatível com WCAG 2.1 AA.

## Estilo
- Nomes de variáveis, funções e mensagens em português.
- Type hints em todas as funções.
- Funções pequenas, com uma responsabilidade.
