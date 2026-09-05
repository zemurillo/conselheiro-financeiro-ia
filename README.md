# Conselheiro Financeiro IA

> 🇬🇧 *An English version of this README is available [below](#conselheiro-financeiro-ia-en).*

🔗 **App no ar:** https://conselheiro-financeiro-ia-xsf2z9eyridysrktsihuez.streamlit.app/

Sistema multiagentes de educação financeira: ajuda pessoas a entender como
lidar com dívidas, organizar orçamento e aprender sobre investimentos —
**sem nunca recomendar um ativo específico**. O foco é dar conhecimento para
que a pessoa decida por conta própria.

> ⚠️ Este projeto tem fins educacionais. Nenhuma resposta do sistema deve ser
> interpretada como recomendação de investimento.

## Arquitetura

Veja [docs/arquitetura.md](docs/arquitetura.md) para o diagrama completo e as
decisões de design.

## Stack

LangGraph · FastAPI · Streamlit · OpenAI (com suporte a Anthropic/Groq via
factory de provedor) · SQLAlchemy · PostgreSQL (produção) / SQLite (dev)

## Status

✅ MVP em produção — API na Render, frontend no Streamlit Community Cloud,
banco de dados no Supabase (Postgres).

## Como rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # preencha sua OPENAI_API_KEY
```

Suba a API e o frontend em terminais separados:

```bash
# Terminal 1
uvicorn src.api.main:app --reload --port 8000

# Terminal 2
streamlit run src/frontend/app.py
```

Rodar os testes automatizados:

```bash
pytest tests/ -v
```

## Deploy

| Camada | Serviço |
|---|---|
| Frontend (Streamlit) | Streamlit Community Cloud |
| API (FastAPI) | Render (free tier) |
| Banco de dados | Supabase (Postgres, via connection pooler) |

Variáveis de ambiente (chaves de API, `DATABASE_URL`) são configuradas
diretamente nos painéis de cada plataforma — nunca commitadas no repositório.

## Estrutura do projeto

```
src/
  agents/    # agentes especialistas, orquestrador e guardrails
  api/       # endpoints FastAPI e schemas de request/response
  core/      # schemas de domínio, grafo (LangGraph), banco de dados, factory de LLM
  frontend/  # app Streamlit
tests/       # testes unitários e de integração
docs/        # documentação de arquitetura
```

---

<a name="conselheiro-financeiro-ia-en"></a>
# Conselheiro Financeiro IA (EN)

> 🇧🇷 *A versão em português está [acima](#conselheiro-financeiro-ia).*

🔗 **Live app:** https://conselheiro-financeiro-ia-xsf2z9eyridysrktsihuez.streamlit.app/

A multi-agent financial education system: helps people understand how to
handle debt, organize a budget, and learn about investing — **without ever
recommending a specific asset**. The goal is to give people the knowledge to
decide for themselves.

> ⚠️ This project is for educational purposes only. No response from the
> system should be interpreted as investment advice.

## Architecture

See [docs/arquitetura.md](docs/arquitetura.md) for the full diagram and
design decisions (in Portuguese, with an architecture diagram readable in
any language).

## Stack

LangGraph · FastAPI · Streamlit · OpenAI (with Anthropic/Groq support via a
provider factory) · SQLAlchemy · PostgreSQL (production) / SQLite (dev)

## Status

✅ MVP in production — API on Render, frontend on Streamlit Community Cloud,
database on Supabase (Postgres).

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # fill in your OPENAI_API_KEY
```

Run the API and frontend in separate terminals:

```bash
# Terminal 1
uvicorn src.api.main:app --reload --port 8000

# Terminal 2
streamlit run src/frontend/app.py
```

Run the automated tests:

```bash
pytest tests/ -v
```

## Deployment

| Layer | Service |
|---|---|
| Frontend (Streamlit) | Streamlit Community Cloud |
| API (FastAPI) | Render (free tier) |
| Database | Supabase (Postgres, via connection pooler) |

Environment variables (API keys, `DATABASE_URL`) are configured directly in
each platform's dashboard — never committed to the repository.

## Project structure

```
src/
  agents/    # specialist agents, orchestrator, and guardrails
  api/       # FastAPI endpoints and request/response schemas
  core/      # domain schemas, graph (LangGraph), database, LLM factory
  frontend/  # Streamlit app
tests/       # unit and integration tests
docs/        # architecture documentation
```