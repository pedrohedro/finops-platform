# Agente FinOps — F1 (copiloto somente leitura)

Responde perguntas sobre custos em linguagem natural usando Claude com tool use.

```
Dashboard (chat) ──POST /api/agent/chat──▶ API FinOps ──▶ agente (127.0.0.1:8090)
                                             ▲                     │
                                             └── GET /api/* ◀──────┘  (tools)
```

## Decisões de segurança

- **Somente leitura**: as ferramentas são uma lista fechada de rotas `GET` da API
  (`/api/summary`, `/api/services`, `/api/daily`, `/api/breakdown`, `/api/teams`,
  `/api/details`). A entrada de cada ferramenta é validada no schema estrito e de novo
  no servidor antes da chamada.
- **Menor privilégio**: o agente não recebe credenciais do ClickHouse nem da AWS; só
  fala com a API.
- **Sem exposição direta**: escuta apenas em loopback (supervisord) ou na rede privada
  do Compose; o navegador só fala com a API, que valida o histórico (máx. 20 turnos,
  4.000 caracteres, papéis alternados, sem `system`).
- **Teto de custo**: orçamento diário de tokens (`AGENT_DAILY_TOKEN_BUDGET`),
  concorrência máxima (`AGENT_MAX_CONCURRENCY`) e no máximo `AGENT_MAX_ITERATIONS`
  chamadas ao modelo por pergunta.
- **Auditoria**: cada chamada de ferramenta gera um log JSON (`agent_tool_call`) com
  `request_id`, ferramenta, entrada, status e duração. O texto das perguntas não é logado.
- **Recusas**: `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`) reencaminha
  recusas de classificador para um modelo de fallback; uma recusa final vira uma
  mensagem neutra.

## Configuração

| Variável | Padrão | |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Sem ela o agente fica desligado (503). Em produção, injete via Secrets Manager. |
| `AGENT_MODEL` | `claude-opus-5-5` | |
| `AGENT_EFFORT` | `medium` | `low` corta custo/latência em perguntas simples. |
| `AGENT_DAILY_TOKEN_BUDGET` | `2000000` | Por processo, zera à meia-noite UTC. |
| `AGENT_MAX_CONCURRENCY` | `4` | Acima disso responde 429. |
| `AGENT_MAX_ITERATIONS` | `6` | |
| `FINOPS_API_URL` | `http://127.0.0.1:8080` | |

## Métricas

`/metrics`: `finops_agent_chat_requests_total{outcome}`, `finops_agent_tokens_total{direction}`,
`finops_agent_tool_calls_total{tool,status}`.

## Testes

```bash
python -m pytest agent -q
```
