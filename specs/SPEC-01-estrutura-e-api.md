# SPEC-01 — Estrutura do projeto e API de agendamento (SUT)

## Objetivo
Criar o projeto com uv e implementar a API JSON de agendamento de consultas, com todas as
regras de negócio (RN01–RN06) e a integração com a BrasilAPI de feriados. Ao final, a API
deve funcionar manualmente pelo Swagger (`/docs`). Páginas HTML ficam para a SPEC-03.

## Referências
- `PRD.md`: seções 3 (modelo), 4 (regras), 5 (dependência externa) e 6 (rotas da API).
- `CLAUDE.md`: arquitetura e estilo.

## Escopo
**Dentro:** `pyproject.toml`, aplicação FastAPI, schemas, banco SQLite, serviço de feriados, serviço de agendamento, rotas `/api/...`, configuração do pytest.
**Fora:** testes (SPEC-02), páginas HTML (SPEC-03), Locust (SPEC-04), README (SPEC-05).

## Tarefas

### 1. Projeto e dependências
O repositório já contém `PRD.md`, `CLAUDE.md`, `AI_USAGE.md` e `specs/`. Esses arquivos **não devem ser alterados** nesta SPEC.

- Na raiz do repositório: `uv init --app --python ">=3.12"`.
  - O comando mantém os arquivos existentes e cria `pyproject.toml`, `.python-version`, `README.md`, `.gitignore` e `main.py` (e `.git`, se a pasta ainda não for um repositório).
  - **Apagar o `main.py` da raiz**: o ponto de entrada da aplicação é `app/main.py`.
  - O `README.md` gerado fica como está; será escrito na SPEC-05.
- `uv add fastapi "uvicorn[standard]" "pydantic[email]" httpx jinja2 python-multipart`
- `uv add --dev pytest`
- No `pyproject.toml`, configurar o pytest:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["."]
  markers = [
      "integration: testes de integração da API com TestClient",
      "e2e: testes ponta a ponta com Playwright",
      "accessibility: auditoria WCAG 2.1 AA e navegação por teclado",
  ]
  ```
- **Complementar** o `.gitignore` gerado pelo uv com `*.db` e `.pytest_cache/`.

### 2. Estrutura de arquivos
Estrutura ao final desta SPEC (`*` = criado nesta SPEC; o restante já existe ou é gerado pelo uv):
```
agenda-consultas/
├── PRD.md                   # requisitos (não alterar)
├── CLAUDE.md                # regras de contexto (não alterar)
├── AI_USAGE.md              # relatório de uso de IA (não alterar)
├── specs/                   # SPEC-01 a SPEC-05 (não alterar)
├── README.md                # gerado pelo uv; escrito na SPEC-05
├── pyproject.toml           # gerado pelo uv + dependências e config do pytest
├── uv.lock                  # gerado pelo uv add
├── .python-version
├── .gitignore               # gerado pelo uv + complementos
└── app/                   *
    ├── __init__.py
    ├── main.py              # cria o FastAPI, lifespan, handlers de exceção, inclui rotas
    ├── database.py          # conectar() lendo AGENDA_DB_PATH; inicializar_banco()
    ├── schemas.py           # modelos Pydantic
    ├── repository.py        # operações no SQLite
    ├── services/
    │   ├── __init__.py
    │   ├── feriados.py      # única chamada externa (BrasilAPI) + cache
    │   └── agendamento.py   # regras de negócio RN01–RN06
    └── routes/
        ├── __init__.py
        └── api.py           # rotas /api/...
```
As pastas `tests/` (SPEC-02), `app/templates/` e `app/routes/pages.py` (SPEC-03), `locustfile.py` e `resultados/` (SPEC-04) virão depois.

### 3. Schemas (`app/schemas.py`)
- `Especialidade(str, Enum)`: `clinico_geral`, `cardiologia`, `dermatologia`, `pediatria`.
- `ConsultaEntrada`: `paciente_nome` (3–100 caracteres), `paciente_email` (`EmailStr`), `especialidade`, `data` (`date`), `horario` (`time`), `observacoes` (opcional, até 500).
- `ConsultaSaida(ConsultaEntrada)`: acrescenta `id: int`.
- `Disponibilidade`: `data`, `especialidade`, `horarios_livres: list[time]`.
- Os schemas validam **formato**; as regras RN01–RN06 ficam no serviço.

### 4. Banco (`app/database.py` e `app/repository.py`)
- Tabela `consultas` com as colunas do modelo; `data` e `horario` gravados como texto ISO.
- Restrição `UNIQUE(especialidade, data, horario)`, como segunda barreira contra conflito sob concorrência (importante para o teste de carga).
- `conectar()` lê `AGENDA_DB_PATH` a cada chamada (padrão `agenda.db`).
- Funções do repositório: `inserir`, `listar(data=None)`, `obter(id)`, `excluir(id) -> bool`, `horarios_ocupados(data, especialidade) -> set[time]`, `limpar()`.
- `inicializar_banco()` é chamada no lifespan da aplicação.

### 5. Serviço de feriados (`app/services/feriados.py`)
- `URL = "https://brasilapi.com.br/api/feriados/v1/{ano}"`.
- Exceção `ServicoFeriadosIndisponivel`.
- `buscar_feriados(ano: int) -> dict[date, str]`: retorna `{data: nome_do_feriado}`.
  - `httpx.get` com timeout de 5 segundos.
  - Erro de rede, status diferente de 200 ou JSON inválido → `ServicoFeriadosIndisponivel`.
  - Cache em memória por ano (`_cache: dict[int, dict[date, str]]`). Só respostas bem-sucedidas entram no cache.
- `limpar_cache() -> None` (usada pelos testes).

### 6. Serviço de agendamento (`app/services/agendamento.py`)
- Importar com `from app.services.feriados import buscar_feriados, ServicoFeriadosIndisponivel`.
- Exceções: `RegraNegocioViolada` (→ 422) e `HorarioOcupado` (→ 409).
- `HORARIOS_ATENDIMENTO`: de 08:00 a 17:30, a cada 30 minutos.
- `validar_dia(data)`: aplica, **nesta ordem**, RN01 (passado), RN02 (fim de semana) e RN03 (feriado). A consulta externa (RN03) vem por último para não gastar chamada quando a data já é inválida por regras locais.
- `agendar(entrada) -> ConsultaSaida`: valida RN04 (horário), chama `validar_dia`, verifica RN05 (conflito) e insere. Um `IntegrityError` do SQLite também vira `HorarioOcupado`.
- `horarios_disponiveis(data, especialidade) -> list[time]`: chama `validar_dia` e devolve os horários de atendimento menos os ocupados.
- `ServicoFeriadosIndisponivel` não é tratada aqui: sobe até o handler (RN06).
- Mensagens de erro claras em português; no caso de feriado, incluir o nome (ex.: "Não há atendimento em 20/11/2026: Dia da consciência negra").

### 7. Rotas e handlers
- Rotas da tabela "API (JSON)" do PRD, com `response_model` e `status_code` corretos.
- Em `main.py`, handlers de exceção: `RegraNegocioViolada` → 422, `HorarioOcupado` → 409, `ServicoFeriadosIndisponivel` → 503, todos no formato `{"detail": "mensagem"}`.

## Critérios de aceite
- [ ] `uv sync` executa sem erros.
- [ ] Não existe `main.py` na raiz, e `PRD.md`, `CLAUDE.md`, `AI_USAGE.md` e `specs/` estão inalterados (`git status` não os mostra como modificados).
- [ ] `uv run uvicorn app.main:app --reload` sobe a aplicação e `/docs` lista as 5 rotas da API.
- [ ] Pelo `/docs`:
  - [ ] POST em um próximo dia útil, às 09:00 → **201** com `id`.
  - [ ] POST em `2026-11-20` → **422** com "Dia da consciência negra" na mensagem.
  - [ ] POST em um sábado → **422**.
  - [ ] POST às 07:00 ou às 09:15 → **422**.
  - [ ] Repetir o primeiro POST (mesma especialidade, data e horário) → **409**.
  - [ ] GET `/api/disponibilidade` no mesmo dia e especialidade → lista sem 09:00.
  - [ ] DELETE da consulta → **204**; DELETE de novo → **404**.
- [ ] O cenário 503 será verificado com mock na SPEC-02.

## Explicações esperadas do Claude Code
- Diferença entre validação de formato (Pydantic) e regra de negócio (serviço).
- Por que a ordem das validações em `validar_dia` importa.
- Como funcionam o cache e o lifespan.
- Por que o `UNIQUE` no banco complementa a verificação de conflito feita no código.

## Commit sugerido
`feat: estrutura do projeto e API de agendamento (SPEC-01)`
