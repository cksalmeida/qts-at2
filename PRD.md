# PRD — Agenda de Consultas com Verificação de Feriados

## 1. Visão geral

Aplicação web para agendar consultas médicas em uma clínica. Antes de confirmar um
agendamento, o sistema verifica se a data é um dia útil, consultando uma API pública
de feriados nacionais (BrasilAPI). O objetivo acadêmico é servir de Sistema Sob Teste
(SUT) para testes de integração, E2E, acessibilidade e carga (AT2 de QTS).

**Stack:** Python 3.12+, uv, FastAPI, Pydantic, Jinja2 (páginas HTML), SQLite.

## 2. Escopo

**Dentro do escopo**
- Agendar, listar, consultar e cancelar consultas.
- Bloquear agendamentos em fins de semana, feriados nacionais, datas passadas,
  fora do horário de atendimento e em horários já ocupados.
- Interface web com listagem e formulário de agendamento.

**Fora do escopo**
- Autenticação de usuários.
- Feriados estaduais e municipais (a BrasilAPI retorna apenas feriados nacionais).
- Envio de e-mail ou notificações.

## 3. Modelo de dados

### Consulta
| Campo | Tipo | Regras |
|---|---|---|
| `id` | int | Gerado pelo sistema |
| `paciente_nome` | str | Obrigatório, 3 a 100 caracteres |
| `paciente_email` | e-mail | Obrigatório, formato válido |
| `especialidade` | enum | `clinico_geral`, `cardiologia`, `dermatologia`, `pediatria` |
| `data` | date | Ver regras de negócio |
| `horario` | time | Ver regras de negócio |
| `observacoes` | str \| null | Opcional, até 500 caracteres |

## 4. Regras de negócio

| ID | Regra | Resposta da API |
|---|---|---|
| RN01 | A data não pode estar no passado | 422 |
| RN02 | A data não pode cair em sábado ou domingo | 422 |
| RN03 | A data não pode ser feriado nacional (consulta à BrasilAPI) | 422, com o nome do feriado na mensagem |
| RN04 | Horário entre 08:00 e 17:30, em intervalos de 30 minutos | 422 |
| RN05 | Não pode existir outra consulta da mesma especialidade na mesma data e horário | 409 |
| RN06 | Se a API de feriados estiver indisponível, o agendamento é recusado (não se agenda sem confirmar o dia útil) | 503 |

## 5. Dependência externa

- **Serviço:** BrasilAPI — Feriados Nacionais
- **Endpoint:** `GET https://brasilapi.com.br/api/feriados/v1/{ano}`
- **Resposta:** lista de objetos `{"date": "AAAA-MM-DD", "name": "...", "type": "national", ...}`
- **Isolamento:** toda chamada externa fica em `app/services/feriados.py`, na função
  `buscar_feriados(ano)`. Nenhum outro módulo faz requisição HTTP externa. Isso permite
  substituir a dependência por mocks nos testes.
- **Cache:** os feriados de cada ano são guardados em memória após a primeira consulta,
  para não sobrecarregar a API externa nem distorcer o teste de carga.

## 6. Rotas

### API (JSON)
| Método | Rota | Descrição | Respostas |
|---|---|---|---|
| GET | `/api/consultas` | Lista consultas (filtro opcional `?data=AAAA-MM-DD`) | 200 |
| GET | `/api/consultas/{id}` | Detalha uma consulta | 200, 404 |
| POST | `/api/consultas` | Agenda uma consulta | 201, 409, 422, 503 |
| DELETE | `/api/consultas/{id}` | Cancela uma consulta | 204, 404 |
| GET | `/api/disponibilidade?data=AAAA-MM-DD&especialidade=...` | Horários livres no dia, ou motivo de indisponibilidade | 200, 422, 503 |

### Páginas (HTML)
| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Listagem das consultas agendadas, com opção de cancelar |
| GET | `/agendar` | Formulário de agendamento |
| POST | `/agendar` | Processa o formulário; em sucesso redireciona para `/` com mensagem; em erro reexibe o formulário com a mensagem |
| POST | `/consultas/{id}/cancelar` | Cancela a consulta a partir do botão da listagem (formulários HTML não enviam DELETE) e redireciona para `/` com mensagem |

## 7. Interface web

- **Listagem (`/`):** tabela com cabeçalhos (`<th scope="col">`) contendo paciente,
  especialidade, data, horário e botão "Cancelar".
- **Formulário (`/agendar`):** campos Nome, E-mail, Especialidade (select), Data
  (`type="date"`), Horário (select), Observações (textarea) e botão "Agendar".
- **Mensagens:** sucesso e erro exibidas em região com `role="status"` (sucesso) ou
  `role="alert"` (erro), para serem anunciadas por leitores de tela.
- Todo campo tem `<label for="...">` associado; a ordem do Tab segue a ordem visual.

## 8. Requisitos não funcionais (ISO/IEC 25010)

| ID | Característica | Requisito | Como é verificado |
|---|---|---|---|
| RNF01 | Eficiência de desempenho | Com 50 usuários concorrentes, p95 ≤ 500 ms nas rotas de leitura e taxa de falhas < 1% | Locust (`locustfile.py`), métricas no README |
| RNF02 | Usabilidade (acessibilidade) | Páginas sem violações WCAG 2.1 níveis A e AA | Axe-core via `axe-playwright-python` |
| RNF03 | Usabilidade (acessibilidade) | Formulário operável só pelo teclado, com foco em ordem lógica | Playwright: `Tab` + `to_be_focused()` |
| RNF04 | Confiabilidade (tolerância a falhas) | Falha da API de feriados não derruba a aplicação; retorna 503 com mensagem clara | Teste de integração com mock simulando falha |
| RNF05 | Manutenibilidade (testabilidade) | Dependência externa isolada em um único módulo | Revisão de código + uso de `mocker.patch` |

## 9. Estratégia de testes

| Nível | Marcador | Ferramentas | Foco |
|---|---|---|---|
| Integração | `@pytest.mark.integration` | TestClient, fixtures, pytest-mock, Faker | Rotas, status HTTP, payloads, RN01–RN06 |
| E2E | `@pytest.mark.e2e` | pytest-playwright, Page Object Model | Fluxo de agendar, ver na lista e cancelar |
| Acessibilidade | `@pytest.mark.accessibility` | axe-playwright-python, Playwright | RNF02 e RNF03 |
| Carga | — | Locust | RNF01 |

- Dados de teste gerados por Factory com `Faker("pt_BR")`.
- Cada teste usa banco SQLite temporário, criado e removido por fixture (`yield`).
- Nos testes de integração, `buscar_feriados` é substituída com `mocker.patch`.
- Nos testes E2E, o servidor sobe em segundo plano durante a sessão de testes e a
  consulta de feriados usa uma lista fixa, para não depender da internet.
