# PROPOSTA DE SERVICOS

## Plataforma FinOps Docker -- Metricas de Custo AWS

---

| | |
|---|---|
| **Cliente** | Amauri -- Projeto FinOps |
| **Prestador** | Pedro Hedro -- Engenheiro DevOps |
| **Empresa** | WebStation . [webstation.com.br](https://webstation.com.br) |
| **Data** | Marco de 2026 |
| **Versao** | 2.0 (Revisada -- Tremor + ECS Fargate) |

---

## 1. Objetivo

Criar uma plataforma FinOps containerizada para coleta, armazenamento, previsao e visualizacao de custos AWS. A plataforma utiliza um **dashboard customizado com Tremor (React)** integrado ao Next.js, substituindo o Grafana para uma experiencia mais moderna e personalizavel.

**Modelo de deploy:** Single Docker Image (monolito operacional) rodando em **AWS ECS Fargate**, com ClickHouse como banco de dados externo.

---

## 2. Arquitetura

### 2.1 Visao Geral (Producao -- ECS Fargate)

```
                        Internet
                            |
                    [ ALB (porta 443) ]        <-- PENDENTE: configurar
                            |
                +-----------+-----------+
                |   ECS Fargate Task    |
                |   (Single Container)  |
                |                       |
                |  +-- supervisord --+  |
                |  |                 |  |
                |  | [Dashboard]     |  |  Next.js 16 + Tremor (porta 3000)
                |  | [API]           |  |  FastAPI + Uvicorn (porta 8080)
                |  | [Collector]     |  |  Python + boto3 (background worker)
                |  |                 |  |
                |  +-----------------+  |
                +-----------+-----------+
                            |
                    [ ClickHouse ]             <-- Externo (ClickHouse Cloud ou container separado)
                            |
                    [ AWS Cost Explorer API ]   <-- Fonte de dados
```

### 2.2 Visao Local (Docker Compose -- Desenvolvimento)

```
+--------------------------------------------------------------+
|                     Docker Compose                            |
|                                                               |
|  +----------+    +------------+    +--------------+           |
|  | Collector |-->| ClickHouse |<---| Normalizer   |           |
|  | (Python)  |   |  (Banco)   |    |  (Python)    |           |
|  +----------+    +------+-----+    +--------------+           |
|       |                 |                                     |
|       |                 v                                     |
|  AWS Cost        +------------+                               |
|  Explorer API    |  Forecast  |                               |
|                  | (Prophet)  |                               |
|                  +------------+                               |
|                                                               |
|  +----------+    +-------------------------------------------+|
|  |   API    |--->|      Dashboard (Next.js + Tremor)         ||
|  | (FastAPI)|    |  Custo Total | Por Servico | Tendencia    ||
|  +----------+    |  Por Equipe  | Por Ambiente | Forecast    ||
|                  +-------------------------------------------+|
+--------------------------------------------------------------+
```

### 2.3 Componentes

| Componente | Stack | Funcao | Porta |
|-----------|-------|--------|:-----:|
| **dashboard** | Next.js 16 + Tremor + Tailwind | Dashboard interativo com graficos modernos | 3000 |
| **api** | FastAPI + Uvicorn | API REST com fallback para mock data | 8080 |
| **collector** | Python 3.11 + boto3 | Coleta custos via AWS Cost Explorer API (loop 24h) | -- |
| **clickhouse** | ClickHouse Server | Armazena dados de custo (columnar, rapido) | 8123/9000 |
| **normalizer** | Python 3.11 | Enriquece dados (equipe, ambiente, tags) | -- |
| **forecast** | Python 3.11 + Prophet | Previsao de custos 30 dias | -- |

> **Mudanca vs v1.0:** Grafana + Prometheus + Exporter foram **substituidos** pelo dashboard Next.js com Tremor.
> Isso eliminou 3 containers (exporter, prometheus, grafana) e deu total controle sobre a UI/UX.

---

## 3. Escopo -- O que foi entregue

### Base do Amauri (scripts originais)
- Collector -> ClickHouse com AWS Cost Explorer
- Normalizer para enriquecer dados
- Forecast com Prophet (previsao 30 dias)

### Melhorias implementadas

| # | Melhoria | Status |
|---|----------|--------|
| 1 | **Dashboard customizado** com Next.js + Tremor (substituiu Grafana) | DONE |
| 2 | **API REST** com FastAPI + modo demo (mock data) | DONE |
| 3 | **Single Docker Image** com Supervisord (multi-stage build) | DONE |
| 4 | **Deploy ECS Fargate** com task definition ARM64 (Graviton) | DONE |
| 5 | **ECR** para armazenar a imagem Docker | DONE |
| 6 | **Health checks** no ClickHouse (docker-compose) | DONE |
| 7 | **Variaveis de ambiente** via `.env` | DONE |
| 8 | **Scheduler** no collector (loop 24h) | DONE |
| 9 | **Volumes persistentes** para ClickHouse | DONE |
| 10 | **Tratamento de erros** e logging nos scripts Python | DONE |
| 11 | **Script build_and_push.sh** para CI/CD manual | DONE |
| 12 | **Task definition** JSON para ECS Fargate | DONE |

### Problemas identificados no deploy atual (ECS)

| # | Problema | Impacto | Correcao |
|---|----------|---------|----------|
| 1 | **Collector sem boto3** -- `ModuleNotFoundError: No module named 'boto3'` | Collector em FATAL (supervisord desistiu) | Instalar dependencias do collector no Dockerfile.prod |
| 2 | **Sem ClickHouse externo** -- container nao tem banco | API rodando em modo mock/demo | Provisionar ClickHouse (Cloud ou EC2) |
| 3 | **Sem ALB** -- acesso direto pela ENI com IP publico | Sem HTTPS, sem DNS amigavel | Criar ALB + ACM + Route53 |
| 4 | **Sem health check** no ECS | healthStatus: UNKNOWN | Adicionar healthCheck na task definition apontando para /api/health |
| 5 | **ExecuteCommand desabilitado** | Nao da para fazer exec/debug no container | Habilitar enableExecuteCommand |
| 6 | **Security Group aberto** | Verificar regras de ingress | Restringir para ALB only |

---

## 4. Estrutura do Projeto (Atual)

```
finops-platform/
|-- docker-compose.yml          <-- Dev local (multi-container)
|-- Dockerfile.prod             <-- Producao (single image, multi-stage)
|-- supervisord.conf            <-- Orquestrador de processos no container
|-- entrypoint.sh               <-- Script de inicializacao
|-- build_and_push.sh           <-- Build + push para ECR
|-- task-def.json               <-- ECS Fargate task definition
|-- .env / .env.example         <-- Variaveis de ambiente
|-- Makefile                    <-- Comandos utilitarios
|
|-- api/
|   |-- Dockerfile              <-- Dev
|   |-- main.py                 <-- FastAPI (endpoints: health, summary, services, daily, breakdown, teams, details)
|   |-- requirements.txt
|   +-- test_main.py
|
|-- collector/
|   |-- Dockerfile              <-- Dev
|   |-- collector.py            <-- Coleta AWS Cost Explorer (+ mock data fallback)
|   +-- requirements.txt        <-- boto3, clickhouse-driver
|
|-- dashboard/
|   |-- src/app/                <-- Next.js 16 pages + Tremor components
|   |-- package.json
|   +-- tailwind.config.ts
|
|-- normalizer/
|   |-- Dockerfile
|   +-- normalizer.py
|
|-- forecast/
|   |-- Dockerfile
|   +-- forecast.py
|
+-- clickhouse_init/
    +-- 01_init.sql             <-- Schema inicial (tabela costs)
```

---

## 5. Detalhamento das Tarefas (Revisado)

| # | Tarefa | Horas | Status |
|---|--------|:---:|--------|
| 1 | Setup inicial (repo, .env, .gitignore, Makefile) | 1h | DONE |
| 2 | Docker Compose com health checks, volumes, networking | 2h | DONE |
| 3 | Collector com scheduler, retry e error handling | 3h | DONE |
| 4 | Normalizer com enriquecimento por tags AWS | 1.5h | DONE |
| 5 | Forecast com Prophet | 2h | DONE |
| 6 | **Dashboard Next.js + Tremor** (substituiu Grafana) | 4h | DONE |
| 7 | **API FastAPI** com fallback mock data | 3h | DONE |
| 8 | **Dockerfile.prod** multi-stage (single image) | 2h | DONE |
| 9 | **Deploy ECS Fargate** (task-def, ECR, service) | 2h | DONE (com bugs) |
| 10 | Correcao do Dockerfile.prod (dependencias collector) | 0.5h | PENDENTE |
| 11 | ALB + HTTPS + DNS | 2h | PENDENTE |
| 12 | Health check ECS + ExecuteCommand | 0.5h | PENDENTE |
| 13 | ClickHouse externo (Cloud ou EC2) | 2h | PENDENTE |
| 14 | Testes E2E + validacao final | 2h | PENDENTE |
| | **TOTAL** | **~27.5h** | |

---

## 6. Investimento

| Valor/h | **Custo Total** |
|:---:|:---:|
| R$ 90/h | **R$ 2.475** |
| R$ 100/h | **R$ 2.750** |
| R$ 110/h | **R$ 3.025** |
| R$ 120/h | **R$ 3.300** |

> **Nota:** O escopo cresceu vs proposta original (+7.5h) devido a substituicao do Grafana pelo dashboard customizado e o deploy em ECS (que era exclusao na v1.0).

---

## 7. Dashboard -- Tremor (Substituiu Grafana)

### Endpoints da API disponibilizados

| Endpoint | Funcao |
|----------|--------|
| `GET /api/health` | Status da plataforma (production vs demo/mock) |
| `GET /api/summary?days=30` | Custo total atual vs periodo anterior |
| `GET /api/services?days=30&limit=5` | Top servicos AWS por custo |
| `GET /api/daily?days=30` | Tendencia diaria (actual + forecast) |
| `GET /api/breakdown?days=30` | Custo por environment (prod/staging/dev) |
| `GET /api/teams?days=30` | Custo por equipe |
| `GET /api/details?days=7&limit=100` | Dados detalhados (drill-down) |

### Paineis do Dashboard

**Visao Executiva:**
- Card de custo total do periodo com variacao percentual
- Grafico de barras -- Top servicos mais caros
- Grafico de linha -- Tendencia diaria com forecast
- Tabela ranqueada -- Top 5 servicos

**Drill-Down:**
- Custo por environment (prod/staging/dev)
- Custo por equipe (baseado em tags)
- Tabela detalhada com filtros

---

## 8. Pre-requisitos

| Requisito | Detalhe |
|-----------|---------|
| **Docker + Docker Compose** | Para desenvolvimento local |
| **Credenciais AWS** | Access Key com permissao `ce:GetCostAndUsage` |
| **Conta AWS (ECS)** | Para deploy em producao (Fargate + ECR) |
| **ClickHouse** | Local (docker-compose) ou externo (ClickHouse Cloud) |

> [!NOTE]
> **Custo AWS do Cost Explorer API:** ~$0.01 por request. Com coleta diaria, o custo mensal da API e desprezivel (~$0.30/mes).
> **Custo ECS Fargate (ARM64):** ~$15-25/mes para 1 vCPU + 2GB RAM rodando 24/7.

---

## 9. Premissas e Exclusoes

### Incluso

- Dashboard customizado Next.js + Tremor (substituiu Grafana)
- API FastAPI com modo demo (mock data)
- Single Docker Image com Supervisord
- Deploy ECS Fargate com ECR
- Docker Compose para desenvolvimento local
- Scripts de build e push
- Health checks e logging

### Exclusoes

- Multi-cloud (GCP, Azure) -- apenas AWS
- Autenticacao de usuarios -- MVP sem auth
- CI/CD automatizado (GitHub Actions) -- build manual via script
- ClickHouse gerenciado -- provisionamento a parte
- Integracao Slack/Teams -- add-on futuro
- Multi-conta AWS (Organizations) -- ver PLAN-finops-improvements.md

---

## 10. Proximos Passos Imediatos

1. **Corrigir Dockerfile.prod** -- instalar dependencias do collector (`pip install -r /app/collector/requirements.txt`)
2. **Rebuild + push** da imagem para ECR
3. **Provisionar ClickHouse** externo (ClickHouse Cloud free tier ou EC2)
4. **Criar ALB** com certificado HTTPS (ACM) + DNS
5. **Habilitar health check** na task definition + ExecuteCommand
6. **Validar** dashboard acessivel via HTTPS

---

**WebStation . [webstation.com.br](https://webstation.com.br)**
**Proposta Confidencial -- Marco de 2026**
