# AI_USAGE — Relatório de uso de Inteligência Artificial

## Ferramentas utilizadas
| Ferramenta | Uso |
|---|---|
| Claude (chat, claude.ai — modelo Claude Opus 5.5) | Entendimento da atividade, redação do `PRD.md`, do `CLAUDE.md` e das SPECs |
| Claude Code (modelo: Claude Opus 5.5 — `claude-opus-5-5`) | Implementação do código e dos testes a partir das SPECs |

## Fluxo de trabalho
1. **Entendimento:** leitura da atividade com apoio do Claude no chat.
2. **Especificação:** `PRD.md` escrito com o Claude e revisado/aprovado pelo autor.
3. **Regras de contexto:** `CLAUDE.md` define stack, arquitetura, padrões de teste e acessibilidade que o Claude Code deve seguir.
4. **Divisão em SPECs:** o desenvolvimento foi dividido em 5 SPECs (`specs/`), cada uma com objetivo, tarefas e critérios de aceite verificáveis.
5. **Implementação:** cada SPEC foi enviada ao Claude Code, que implementou e explicou o código.
6. **Reflexão e construção conjunta:** ao longo de todo o projeto, o autor foi refletindo sobre as decisões e construindo a solução junto com o Claude no chat: discutindo o que o Claude Code entregava em cada SPEC, entendendo as explicações e decidindo os próximos passos.

## Registro por SPEC
| SPEC | O que a IA gerou |
|---|---|
| [SPEC-01](specs/SPEC-01-estrutura-e-api.md) — Estrutura e API | Projeto uv (`pyproject.toml`, `uv.lock`) e `app/`: schemas Pydantic, SQLite com `UNIQUE(especialidade, data, horario)`, repositório, `feriados.py` (BrasilAPI + cache), `agendamento.py` (RN01–RN06), rotas `/api/...` e handlers 409/422/503. **Desvio:** o uv 0.12.5 gerava layout de pacote (`src/`); refeito com `uv init --app --no-package` para obter o `main.py` previsto. |
| [SPEC-02](specs/SPEC-02-testes-integracao.md) — Testes de integração | `tests/factories.py` (`ConsultaFactory`, Faker pt_BR, datas relativas), fixtures com `yield` em `tests/conftest.py`, 31 testes `integration` (API e serviço de feriados) com `mocker.patch`. **Alteração em código da SPEC-01:** mensagem padrão em `ServicoFeriadosIndisponivel`, para o 503 nunca sair com `detail` vazio. `build_batch` sem repetir especialidade/data/horário. |
| [SPEC-03](specs/SPEC-03-interface-e2e-acessibilidade.md) — Interface, E2E e acessibilidade | Templates Jinja2 acessíveis, `app/routes/pages.py` (POST → 303 → GET), servidor de teste em thread com `session_mocker`, Page Objects, 4 testes `e2e` e 6 `accessibility` (Axe: 0 violações; ordem do Tab; agendamento só por teclado). **Alteração em código da SPEC-01:** mensagem de conflito passa a começar com "Horário ocupado". Ajustes no teste de teclado: paradas de Tab internas do `<input type="date">`, `--lang=pt-BR` no Chromium e busca por prefixo no `<select>`. |
| [SPEC-04](specs/SPEC-04-testes-carga.md) — Carga | `locustfile.py` (`Paciente(HttpUser)`, pesos 5/3/2/1, `between(1, 3)`, 409 e 422 de feriado tratados como sucesso), execução headless de 1 min com 50 usuários e CSVs em `resultados/` (RNF01 atendido: p95 ≤ 11 ms, 0% de falhas). |
| [SPEC-05](specs/SPEC-05-documentacao-entrega.md) — Documentação | `README.md` (instalação, execução, testes, carga, métricas, estrutura), `ENTREGA.md` (checklist da AT2), preenchimento deste registro e descrição do `pyproject.toml`. Verificação limpa feita numa cópia dos arquivos versionáveis, pois o repositório ainda não tinha commits. |

## Ajustes feitos na fase de especificação
- Na revisão das SPECs, identificou-se que formulários HTML não enviam `DELETE`; foi incluída no PRD a rota `POST /consultas/{id}/cancelar` para o botão "Cancelar" da listagem.

## Responsabilidade
Todo o código foi revisado e executado pelo autor antes de ser versionado. A IA foi usada como
ferramenta de apoio; as decisões finais e a validação dos resultados são do autor.
