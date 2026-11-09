# Conferência final — checklist da AT2

Verificado em 09/11/2026 com `uv run pytest -v` (41 testes passando: 31 de integração,
4 E2E e 6 de acessibilidade) e com uma verificação limpa (cópia nova do repositório, seguindo
apenas o README).

| # | Requisito da AT2 | Arquivo / teste que atende | OK |
|---|---|---|:---:|
| 1 | `PRD.md` com rotas, interface e RNFs | [`PRD.md`](PRD.md): seções 6 (rotas API e HTML), 7 (interface) e 8 (RNF01–RNF05, ISO/IEC 25010) | ✅ |
| 2 | Regras de contexto | [`CLAUDE.md`](CLAUDE.md): stack, arquitetura, padrões de teste, acessibilidade e estilo | ✅ |
| 3 | `AI_USAGE.md` | [`AI_USAGE.md`](AI_USAGE.md): ferramentas, fluxo de trabalho e registro do que a IA gerou em cada SPEC | ✅ |
| 4 | `pyproject.toml` gerenciado com uv, Python 3.12+ | [`pyproject.toml`](pyproject.toml) (`requires-python = ">=3.12"`), [`uv.lock`](uv.lock), `.python-version` | ✅ |
| 5 | FastAPI + Pydantic + páginas HTML | `app/main.py`, `app/schemas.py`, `app/routes/api.py`, `app/routes/pages.py`, `app/templates/` | ✅ |
| 6 | `@pytest.mark.integration` com `TestClient`, status e payload, padrão AAA | `tests/integration/test_api_consultas.py` (25 testes) e `test_servico_feriados.py` (6); todos com `# Arrange / # Act / # Assert` | ✅ |
| 7 | `@pytest.fixture` com `yield` | `tests/conftest.py`: `banco_temporario`, `client`, `limpar_cache_feriados`, `servidor` (setup → `yield` → limpeza) | ✅ |
| 8 | `mocker.patch` com cenários de sucesso e falha | `sem_feriados` / `return_value` (sucesso e feriado) e `side_effect=ServicoFeriadosIndisponivel` (503) em `app.services.agendamento.buscar_feriados`; `httpx.get` com 200, 500, `ConnectError` e JSON inválido em `test_servico_feriados.py` | ✅ |
| 9 | Factory com `Faker("pt_BR")` | [`tests/factories.py`](tests/factories.py): `ConsultaFactory.build()` / `build_batch()`; datas sempre relativas a hoje | ✅ |
| 10 | `@pytest.mark.e2e` com Playwright, POM e seletores semânticos | `tests/e2e/test_fluxo_agendamento.py` + `tests/e2e/pages/` (`AgendamentoPage`, `ListaConsultasPage`); só `get_by_role` / `get_by_label` / `get_by_text` | ✅ |
| 11 | `@pytest.mark.accessibility` com Axe-core (WCAG 2.1 AA) e `to_be_focused()` | `tests/accessibility/test_acessibilidade.py`: Axe com tags `wcag2a/2aa/21a/21aa` em 4 estados de página (0 violações), ordem do Tab com `to_be_focused()` e agendamento só por teclado | ✅ |
| 12 | `locustfile.py` com `HttpUser` e `@task` | [`locustfile.py`](locustfile.py): `Paciente(HttpUser)`, 4 `@task` com pesos 5/3/2/1, `between(1, 3)` | ✅ |
| 13 | Métricas (RPS, p95, falhas) no README | [README → Resultados do teste de carga](README.md#resultados-do-teste-de-carga) + [`resultados/carga_stats.csv`](resultados/carga_stats.csv) | ✅ |

## Pendências do autor

- [ ] Commitar cada SPEC e publicar o repositório **público** no GitHub.
- [ ] Repetir a verificação limpa a partir do `git clone` do repositório publicado.
