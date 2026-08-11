# Conselheiro Financeiro IA

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

LangGraph · FastAPI · Streamlit · Claude API · SQLAlchemy

## Status

🚧 Em desenvolvimento — projeto de portfólio.

## Como rodar (em breve)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Estrutura do projeto

```
src/
  agents/    # agentes especialistas e orquestrador
  api/       # endpoints FastAPI
  core/      # config, schemas, utilidades compartilhadas
  frontend/  # app Streamlit
tests/       # testes unitários e de integração
docs/        # documentação de arquitetura
```
