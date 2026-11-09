# SPEC-05 — Documentação e preparação da entrega

## Objetivo
Deixar o repositório pronto para avaliação: README com instruções via uv e métricas,
AI_USAGE.md completo e conferência de todos os itens exigidos pela AT2.

## Referências
- Página da AT2 (requisitos técnicos e itens de submissão).
- `PRD.md`, `CLAUDE.md`, `specs/`, `resultados/`.
- SPECs 01 a 04 concluídas.

## Tarefas

### 1. `README.md`
Seções, nesta ordem:
1. Nome e descrição curta da aplicação (o domínio e a verificação de feriados).
2. Stack.
3. Pré-requisitos: Python 3.12+ e uv.
4. Instalação: `uv sync` e `uv run playwright install chromium`.
5. Como rodar a aplicação: `uv run uvicorn app.main:app --reload` e endereços (`/`, `/agendar`, `/docs`).
6. Como rodar os testes: `uv run pytest -v` e por marcador (`-m integration`, `-m e2e`, `-m accessibility`); opção `--headed --slowmo 500`.
7. Teste de carga: comandos da SPEC-04 (Bash e PowerShell).
8. **Resultados do teste de carga**: tabela de métricas da SPEC-04, comparação com o RNF01 e ambiente do teste.
9. Estrutura de pastas comentada.
10. Documentação do projeto: links para `PRD.md`, `CLAUDE.md`, `AI_USAGE.md` e `specs/`.

### 2. `AI_USAGE.md`
- Completar a estrutura existente com o que o Claude Code gerou em cada SPEC.
- As colunas de auditoria e ajustes são preenchidas pelo **autor**; o Claude Code apenas deixa os campos indicados, sem inventar conteúdo de revisão.

### 3. Conferência final (checklist da AT2)
Gerar uma tabela "Requisito da AT2 → arquivo/teste que atende" e verificar cada linha:
- [ ] `PRD.md` com rotas, interface e RNFs
- [ ] Regras de contexto (`CLAUDE.md`)
- [ ] `AI_USAGE.md`
- [ ] `pyproject.toml` gerenciado com uv, Python 3.12+
- [ ] FastAPI + Pydantic + páginas HTML
- [ ] Testes `@pytest.mark.integration` com `TestClient`, status e payload, padrão AAA
- [ ] `@pytest.fixture` com `yield`
- [ ] `mocker.patch` com cenários de sucesso e falha
- [ ] Factory com `Faker("pt_BR")`
- [ ] Testes `@pytest.mark.e2e` com Playwright, POM e seletores semânticos
- [ ] `@pytest.mark.accessibility` com Axe-core (WCAG 2.1 AA) e `to_be_focused()`
- [ ] `locustfile.py` com `HttpUser` e `@task`
- [ ] Métricas (RPS, p95, falhas) no README

### 4. Verificação limpa
- Clonar o repositório em uma pasta nova e seguir **apenas** o README: `uv sync`, instalar o Chromium, `uv run pytest -v`. Tudo deve passar.

## Critérios de aceite
- [ ] Checklist da AT2 100% marcado.
- [ ] Verificação limpa concluída com sucesso.
- [ ] Repositório público no GitHub.

## Commit sugerido
`docs: README, AI_USAGE e conferência final (SPEC-05)`
