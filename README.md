# Agenda de Consultas com Verificação de Feriados

Aplicação web para agendar consultas médicas em uma clínica. Antes de confirmar um
agendamento, o sistema verifica se a data é um dia útil: recusa datas passadas, fins de semana
e **feriados nacionais**, consultados na [BrasilAPI](https://brasilapi.com.br/docs#tag/Feriados-Nacionais).
Também bloqueia horários fora do atendimento (08:00–17:30, de 30 em 30 minutos) e horários já
ocupados na mesma especialidade. Se a BrasilAPI estiver fora do ar, o agendamento é recusado
com 503, porque não se agenda sem confirmar o dia útil.

O projeto é o Sistema Sob Teste (SUT) da AT2 de Qualidade e Teste de Software: testes de
integração, E2E, acessibilidade e carga.

## Stack

| Camada | Ferramentas |
|---|---|
| Linguagem e projeto | Python 3.12+, [uv](https://docs.astral.sh/uv/) (`pyproject.toml`, `uv.lock`) |
| Aplicação | FastAPI, Pydantic v2, Jinja2 (páginas HTML), SQLite (`sqlite3`), httpx (BrasilAPI) |
| Testes de integração | pytest, `TestClient`, pytest-mock, Faker (`pt_BR`) |
| Testes E2E e acessibilidade | pytest-playwright (Chromium), Page Object Model, axe-playwright-python (Axe-core) |
| Teste de carga | Locust |

## Pré-requisitos

- Python 3.12 ou superior. Se não estiver instalado, o uv baixa a versão certa sozinho.
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado.

## Instalação

```bash
uv sync                                # cria o .venv e instala as dependências (inclusive as de teste)
uv run playwright install chromium     # navegador usado nos testes E2E e de acessibilidade
```

## Como rodar a aplicação

```bash
uv run uvicorn app.main:app --reload
```

| Endereço | O que é |
|---|---|
| http://127.0.0.1:8000/ | Listagem das consultas agendadas, com botão para cancelar |
| http://127.0.0.1:8000/agendar | Formulário de agendamento |
| http://127.0.0.1:8000/docs | Swagger da API JSON (`/api/consultas`, `/api/disponibilidade`) |

O banco SQLite fica em `agenda.db`. Para usar outro arquivo, defina a variável de ambiente
`AGENDA_DB_PATH`. A primeira consulta de feriados de cada ano precisa de internet; depois fica
em cache na memória.

## Como rodar os testes

```bash
uv run pytest -v                       # todas as suítes (41 testes)
uv run pytest -m integration -v        # integração da API e do serviço de feriados (31)
uv run pytest -m e2e -v                # fluxo no navegador com Playwright (4)
uv run pytest -m accessibility -v      # Axe-core WCAG 2.1 AA e navegação por teclado (6)
```

Para **ver o navegador** executando os testes (útil para demonstração):

```bash
uv run pytest -m e2e --headed --slowmo 500
```

Os testes **não dependem de internet**:
- nos de integração, `buscar_feriados` é substituída com `mocker.patch`;
- nos E2E e de acessibilidade, o servidor sobe numa thread do próprio pytest, com uma lista fixa de feriados.

Cada teste usa um banco SQLite temporário.

## Teste de carga

O servidor roda **sem** `--reload` e com banco separado, para não misturar os dados de carga
com os de desenvolvimento. A primeira consulta de feriados precisa de internet.

**1. Subir o servidor**

Bash (Linux/macOS/Git Bash):
```bash
AGENDA_DB_PATH=carga.db uv run uvicorn app.main:app --port 8000
```
PowerShell (Windows):
```powershell
$env:AGENDA_DB_PATH="carga.db"; uv run uvicorn app.main:app --port 8000
```

**2. Em outro terminal, rodar o Locust**

Com interface web (abrir http://localhost:8089, 50 usuários, taxa de 5/s):
```bash
uv run locust -f locustfile.py --host http://127.0.0.1:8000
```

Modo reproduzível (gera os CSVs em `resultados/`):
```bash
uv run locust -f locustfile.py --host http://127.0.0.1:8000 --users 50 --spawn-rate 5 --run-time 1m --headless --csv resultados/carga
```

## Resultados do teste de carga

**Meta (RNF01 do PRD):** com 50 usuários concorrentes, p95 ≤ 500 ms nas rotas de leitura e
taxa de falhas < 1%.

**Perfil simulado (`locustfile.py`):** cada usuário espera de 1 a 3 s entre as ações. Os pesos são
5 × listar consultas, 3 × ver disponibilidade, 2 × abrir a página inicial e 1 × agendar.
Parâmetros: 50 usuários, 5 novos por segundo, 1 minuto.

| Rota | Requisições | RPS | p95 (ms) | Falhas | Taxa de falhas | RNF01 |
|---|---:|---:|---:|---:|---:|---|
| `GET /` | 244 | 4,12 | 11 | 0 | 0,00% | atendido |
| `GET /api/consultas` | 624 | 10,55 | 11 | 0 | 0,00% | atendido |
| `GET /api/disponibilidade` | 421 | 7,12 | 5 | 0 | 0,00% | atendido |
| `POST /api/consultas` (escrita) | 92 | 1,56 | 9 | 0 | 0,00% | atendido (a meta de p95 vale só para leitura) |
| **Agregado** | **1381** | **23,34** | **10** | **0** | **0,00%** | **atendido** |

Fonte: [`resultados/carga_stats.csv`](resultados/carga_stats.csv), com o histórico em
[`carga_stats_history.csv`](resultados/carga_stats_history.csv).

**Conclusão: RNF01 atendido.** O p95 das rotas de leitura ficou entre 5 e 11 ms, cerca de 45 vezes
abaixo do limite, e não houve falhas.

**Como as falhas foram contadas.** Rejeições previstas pelas regras de negócio são respostas
corretas da aplicação e não contam como falha de desempenho:
- **409**: horário ocupado. Com 50 usuários disputando 20 horários, há colisões.
- **422 de feriado**: a data aleatória pode cair num feriado real.

Qualquer outro status fora de 2xx conta como falha. Nesta execução, o log do servidor registrou
1 × 409 e 31 × 422 de feriado (20/11, 25/12 e 01/01), todos classificados como sucesso.

**Ambiente do teste**

| Item | Valor |
|---|---|
| Data | 09/11/2026 |
| Máquina | MacBook Air, Apple M5 (10 núcleos), 16 GB de RAM |
| Sistema | macOS 26.6.2 |
| Python / Locust | 3.12.14 / 2.47.0 |
| Servidor | uvicorn, 1 processo, SQLite em arquivo |

> O servidor e o Locust rodaram **na mesma máquina**, disputando a mesma CPU e sem latência de
> rede real (`127.0.0.1`). Os tempos absolutos valem para comparar com a meta, não como medida de
> capacidade em produção.

## Estrutura de pastas

```
.
├── PRD.md                      # requisitos: modelo, regras RN01–RN06, rotas, RNFs, estratégia de testes
├── CLAUDE.md                   # regras de contexto seguidas pelo Claude Code
├── AI_USAGE.md                 # relatório de uso de IA e auditoria por SPEC
├── ENTREGA.md                  # checklist da AT2: requisito → arquivo/teste que atende
├── specs/                      # SPEC-01 a SPEC-05 (tarefas e critérios de aceite)
├── pyproject.toml              # dependências (uv) e configuração do pytest (marcadores)
├── uv.lock                     # versões exatas, para instalação reproduzível
├── locustfile.py               # teste de carga: Paciente(HttpUser) com tarefas ponderadas
├── resultados/                 # CSVs do Locust (evidência do RNF01)
├── app/
│   ├── main.py                 # cria o FastAPI, lifespan (cria o banco), handlers 409/422/503
│   ├── database.py             # conexão SQLite (lê AGENDA_DB_PATH) e criação da tabela
│   ├── schemas.py              # modelos Pydantic: validação de FORMATO
│   ├── repository.py           # todo o SQL fica aqui
│   ├── services/
│   │   ├── feriados.py         # ÚNICA chamada externa (BrasilAPI) + cache por ano
│   │   └── agendamento.py      # regras de negócio RN01–RN06
│   ├── routes/
│   │   ├── api.py              # rotas JSON /api/...
│   │   └── pages.py            # páginas HTML (reaproveitam o mesmo serviço)
│   └── templates/              # Jinja2: base, lista, agendar, mensagens (role=status/alert)
└── tests/
    ├── conftest.py             # fixtures: banco temporário, client, mocks, servidor em thread
    ├── factories.py            # ConsultaFactory com Faker("pt_BR") e datas relativas a hoje
    ├── integration/            # @integration: API e serviço de feriados (TestClient + mocks)
    ├── e2e/
    │   ├── pages/              # Page Objects (só seletores semânticos)
    │   └── test_fluxo_agendamento.py   # @e2e: agendar, feriado, conflito, cancelar
    └── accessibility/          # @accessibility: Axe-core WCAG 2.1 AA e ordem do Tab
```

## Documentação do projeto

- [`PRD.md`](PRD.md): requisitos do produto.
- [`CLAUDE.md`](CLAUDE.md): regras de contexto para o Claude Code.
- [`AI_USAGE.md`](AI_USAGE.md): como a IA foi usada e o que ela gerou em cada SPEC.
- [`specs/`](specs/): SPECs de implementação, da [01](specs/SPEC-01-estrutura-e-api.md) à [05](specs/SPEC-05-documentacao-entrega.md).
- [`ENTREGA.md`](ENTREGA.md): conferência dos requisitos da AT2.
