# SPEC-02 — Testes de integração com Fixtures, Mocks e Faker

## Objetivo
Cobrir a API e o serviço de feriados com testes de integração (`@pytest.mark.integration`)
usando `TestClient`, fixtures com setup/teardown via `yield`, mocks com `mocker.patch`
(cenários de sucesso e falha) e massa de dados gerada por Factory com `Faker("pt_BR")`.

## Referências
- `PRD.md`: seções 4 (regras), 6 (rotas) e 9 (estratégia de testes).
- `CLAUDE.md`: padrões de teste.
- SPEC-01 concluída.

## Escopo
**Dentro:** `tests/conftest.py`, `tests/factories.py`, `tests/integration/`.
**Fora:** E2E e acessibilidade (SPEC-03), carga (SPEC-04).

## Tarefas

### 1. Dependências
`uv add --dev pytest-mock faker`

### 2. Factory (`tests/factories.py`)
- `fake = Faker("pt_BR")`.
- `proximo_dia_util(a_partir_de_dias: int = 1) -> date`: primeira segunda a sexta a partir de hoje + N dias.
- `proximo_sabado() -> date`.
- `ConsultaFactory`:
  - `build(**sobrescritas) -> dict`: dicionário pronto para JSON (datas e horários em ISO), com nome, e-mail, especialidade e horário aleatórios válidos e data = dia útil aleatório nos próximos 60 dias.
  - `build_batch(quantidade, **sobrescritas) -> list[dict]`.
- Explicar no código por que a Factory existe: um único lugar sabe montar uma consulta válida; cada teste muda só o campo que quer provar.

### 3. Fixtures (`tests/conftest.py`)
| Fixture | Escopo | O que faz |
|---|---|---|
| `banco_temporario` | function | Define `AGENDA_DB_PATH` para um arquivo em `tmp_path` (via `monkeypatch`), inicializa o banco, `yield`, depois apaga o arquivo |
| `client` | function | Usa `banco_temporario`; abre `TestClient(app)` em `with` e faz `yield` |
| `limpar_cache_feriados` | function, `autouse=True` | Chama `limpar_cache()` antes e depois de cada teste |
| `sem_feriados` | function | `mocker.patch("app.services.agendamento.buscar_feriados", return_value={})` e devolve o mock |
| `consulta_criada` | function | Cria uma consulta via POST (com `sem_feriados`) e devolve o JSON da resposta |

### 4. Testes da API (`tests/integration/test_api_consultas.py`)
Todos com `@pytest.mark.integration` e AAA comentado.

**Fluxo principal**
- POST válido → 201; payload igual ao enviado e com `id`.
- GET `/api/consultas` contém a consulta criada; filtro `?data=` retorna só as do dia.
- GET por `id` → 200; `id` inexistente → 404.
- DELETE → 204 e GET seguinte → 404; DELETE de `id` inexistente → 404.

**Regras de negócio**
- RN01: data de ontem → 422.
- RN02: sábado → 422.
- RN03: mock retorna `{data_escolhida: "Feriado de Teste"}` → 422 e a mensagem contém "Feriado de Teste".
- RN04: `@pytest.mark.parametrize` com `07:00`, `09:15`, `18:00` → 422.
- RN05: mesma especialidade, data e horário → 409; mesma data e horário com outra especialidade → 201.
- RN06: mock com `side_effect=ServicoFeriadosIndisponivel` → 503 com mensagem.

**Validação de formato (Pydantic)**
- `parametrize` com e-mail inválido, nome com 2 caracteres e especialidade inexistente → 422.

**Disponibilidade**
- Dia útil sem consultas → 20 horários; após agendar 09:00, a lista não contém 09:00.
- Feriado (mock) → 422; API fora (mock) → 503.

**Uso do mock como evidência**
- Agendamento em dia útil: `mock.assert_called_once_with(ano_da_data)`.
- Agendamento em sábado: `mock.assert_not_called()` (prova que RN02 é verificada antes da chamada externa).

### 5. Testes do serviço de feriados (`tests/integration/test_servico_feriados.py`)
Mock em `app.services.feriados.httpx.get` (a dependência real é a rede).
- Resposta 200 com JSON no formato da BrasilAPI → dicionário `{date: nome}` correto.
- Resposta 500 → `ServicoFeriadosIndisponivel`.
- `side_effect=httpx.ConnectError(...)` → `ServicoFeriadosIndisponivel`.
- Duas chamadas para o mesmo ano → `httpx.get` chamado uma única vez (cache).
- Falha seguida de sucesso → a falha não fica no cache.

## Critérios de aceite
- [ ] `uv run pytest -m integration -v` com todos os testes passando.
- [ ] Os testes passam sem internet (desligar a rede e rodar de novo).
- [ ] Nenhuma data fixa no corpo dos testes.
- [ ] Toda fixture com recurso usa `yield` e faz limpeza depois.

## Explicações esperadas do Claude Code
- Ciclo de vida de uma fixture com `yield` e o que significa escopo `function`.
- Diferença entre `return_value` e `side_effect`.
- Por que o patch é em `app.services.agendamento.buscar_feriados` e não em `app.services.feriados.buscar_feriados`, e por que no teste do serviço o patch é em `httpx.get`.
- O que o `TestClient` faz por baixo dos panos e por que não precisa subir servidor.

## Commit sugerido
`test: testes de integração com fixtures, mocks e Faker (SPEC-02)`
