# SPEC-04 — Testes de carga e performance com Locust

## Objetivo
Criar o `locustfile.py` que simula usuários concorrentes usando a aplicação, executar o teste
com parâmetros reproduzíveis e registrar RPS, tempo de resposta p95 e taxa de falhas,
comparando com a meta do RNF01.

## Referências
- `PRD.md`: seção 8 (RNF01: 50 usuários, p95 ≤ 500 ms nas leituras, falhas < 1%).
- SPECs 01 a 03 concluídas.

## Escopo
**Dentro:** `locustfile.py`, pasta `resultados/` com os CSVs, rascunho da seção de métricas para o README.
**Fora:** otimizações de desempenho (só se a meta não for atingida, e após discutir com o autor).

## Tarefas

### 1. Dependência
`uv add --dev locust`

### 2. `locustfile.py` (na raiz do projeto)
- Classe `Paciente(HttpUser)` com `wait_time = between(1, 3)`.
- Tarefas com pesos que imitam o uso real (mais leitura que escrita):
  | Peso | Tarefa | Requisição |
  |---|---|---|
  | 5 | `listar_consultas` | `GET /api/consultas` |
  | 3 | `ver_disponibilidade` | `GET /api/disponibilidade` com dia útil e especialidade aleatórios |
  | 2 | `abrir_pagina_inicial` | `GET /` |
  | 1 | `agendar_consulta` | `POST /api/consultas` com dados do Faker (pt_BR) |
- Usar `name=` nas requisições com parâmetros (ex.: `name="/api/disponibilidade"`), para o Locust agrupar as métricas por rota em vez de uma linha por URL.
- Rejeições **esperadas** pela regra de negócio não são falhas de desempenho. Com `catch_response=True`, marcar como sucesso:
  - 409 (horário ocupado, natural com 50 usuários agendando ao mesmo tempo);
  - 422 cuja mensagem indica feriado (a data aleatória pode cair em um feriado real).
  Qualquer outro status diferente de 2xx continua sendo falha. Comentar no código essa decisão.
- O `locustfile.py` não importa nada de `app/`: ele é um cliente externo, como um usuário real.

### 3. Execução
O servidor roda **sem** `--reload` e com banco separado, para não misturar dados de carga com os de desenvolvimento.
A primeira consulta de feriados precisa de internet (depois fica em cache).

Bash (Linux/macOS/Git Bash):
```bash
AGENDA_DB_PATH=carga.db uv run uvicorn app.main:app --port 8000
```
PowerShell (Windows):
```powershell
$env:AGENDA_DB_PATH="carga.db"; uv run uvicorn app.main:app --port 8000
```

Em outro terminal:
- **Modo com interface (para o vídeo):** `uv run locust -f locustfile.py --host http://127.0.0.1:8000` e abrir `http://localhost:8089` (50 usuários, taxa de 5/s).
- **Modo reproduzível (para o README):**
  ```bash
  uv run locust -f locustfile.py --host http://127.0.0.1:8000 --users 50 --spawn-rate 5 --run-time 1m --headless --csv resultados/carga
  ```

### 4. Registro das métricas
- A partir de `resultados/carga_stats.csv`, montar uma tabela para o README com, por rota e no agregado: requisições, RPS (`Requests/s`), p95 (`95%`), taxa de falhas (`Failure Count / Request Count`).
- Comparar com o RNF01 e indicar "atendido" ou "não atendido".
- Registrar o ambiente do teste (máquina, sistema operacional, data) e a observação de que servidor e Locust rodaram na mesma máquina, o que influencia os números.
- Os CSVs de `resultados/` são versionados como evidência.

## Critérios de aceite
- [ ] `uv run locust` com interface funcionando e exibindo RPS, tempos e falhas.
- [ ] Execução headless gera `resultados/carga_stats.csv`.
- [ ] Taxa de falhas reflete apenas erros reais (não 409 nem feriados).
- [ ] Rascunho da tabela de métricas pronto para entrar no README.
- [ ] `uv run pytest -v` continua passando (o `locustfile.py` não é coletado como teste).

## Explicações esperadas do Claude Code
- O que é um `HttpUser`, o que `@task` e os pesos fazem e para que serve o `wait_time`.
- Diferença entre usuários concorrentes e RPS.
- O que é o p95 e por que ele é mais informativo que a média.
- Por que o cache de feriados é essencial para a validade do teste de carga.

## Commit sugerido
`test: teste de carga com Locust e métricas (SPEC-04)`
