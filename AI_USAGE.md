# AI_USAGE — Relatório de uso de Inteligência Artificial

## Ferramentas utilizadas
| Ferramenta | Uso |
|---|---|
| Claude (chat, claude.ai — modelo Claude Opus 5.5) | Entendimento da atividade, redação do `PRD.md`, do `CLAUDE.md` e das SPECs |
| Claude Code (modelo: _preencher_) | Implementação do código e dos testes a partir das SPECs |

## Fluxo de trabalho
1. **Entendimento:** leitura da atividade com apoio do Claude no chat.
2. **Especificação:** `PRD.md` escrito com o Claude e revisado/aprovado pelo autor.
3. **Regras de contexto:** `CLAUDE.md` define stack, arquitetura, padrões de teste e acessibilidade que o Claude Code deve seguir.
4. **Divisão em SPECs:** o desenvolvimento foi dividido em 5 SPECs (`specs/`), cada uma com objetivo, tarefas e critérios de aceite verificáveis.
5. **Implementação:** cada SPEC foi enviada ao Claude Code, que implementou e explicou o código.
6. **Auditoria:** antes de cada commit, o autor revisou o código, executou os critérios de aceite e registrou abaixo o que conferiu e o que precisou ser ajustado.

## Registro por SPEC
| SPEC | O que a IA gerou | Como foi auditado | Ajustes feitos pelo autor |
|---|---|---|---|
| [SPEC-01](specs/SPEC-01-estrutura-e-api.md) — Estrutura e API | _preencher_ | _preencher_ | _preencher_ |
| [SPEC-02](specs/SPEC-02-testes-integracao.md) — Testes de integração | _preencher_ | _preencher_ | _preencher_ |
| [SPEC-03](specs/SPEC-03-interface-e2e-acessibilidade.md) — Interface, E2E e acessibilidade | _preencher_ | _preencher_ | _preencher_ |
| [SPEC-04](specs/SPEC-04-testes-carga.md) — Carga | _preencher_ | _preencher_ | _preencher_ |
| [SPEC-05](specs/SPEC-05-documentacao-entrega.md) — Documentação | _preencher_ | _preencher_ | _preencher_ |

## Ajustes feitos na fase de especificação
- Na revisão das SPECs, identificou-se que formulários HTML não enviam `DELETE`; foi incluída no PRD a rota `POST /consultas/{id}/cancelar` para o botão "Cancelar" da listagem.

## Responsabilidade
Todo o código foi revisado e executado pelo autor antes de ser versionado. A IA foi usada como
ferramenta de apoio; as decisões finais e a validação dos resultados são do autor.
