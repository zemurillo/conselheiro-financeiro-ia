# Arquitetura

## Visão geral

O sistema é dividido em três camadas desacopladas: **frontend** (Streamlit),
**API** (FastAPI) e **núcleo de agentes** (LangGraph). O frontend nunca fala
diretamente com os agentes — toda a comunicação passa pela API, o que permite
trocar a interface (web, mobile, WhatsApp) sem tocar na lógica de negócio.

```mermaid
flowchart TD
    U([Usuário]) --> S[Streamlit - UI]
    S -->|POST /chat| A[API - FastAPI]
    A --> O[Agente Orquestrador]

    O --> D[Agente de Diagnóstico]
    O --> V[Agente de Dívidas]
    O --> I[Agente de Investimentos]
    O --> P[Agente de Planejamento]

    D --> G[Agente de Guardrails]
    V --> G
    I --> G
    P --> G

    G -->|resposta validada| A
    A -->|JSON| S
    S --> U
```

## Papel de cada agente

| Agente | Responsabilidade | Nunca faz |
|---|---|---|
| Orquestrador | Interpreta a intenção do usuário e roteia para o(s) especialista(s) certo(s) | Responder diretamente perguntas de domínio |
| Diagnóstico | Organiza a situação financeira relatada (renda, gastos, dívidas) | Dar conselhos de investimento |
| Dívidas | Explica estratégias de quitação (bola de neve, avalanche, renegociação) | Indicar credor ou instituição específica |
| Investimentos | Educa sobre conceitos (renda fixa/variável, perfil de risco, tesouro direto, FIIs) | Recomendar ativo/ticker específico |
| Planejamento | Ajuda a estruturar metas e reserva de emergência | Prometer retorno ou prazo de resultado |
| Guardrails | Audita a resposta de qualquer agente antes de liberar ao usuário | Deixar passar recomendação específica de investimento |

## Fluxo de uma requisição

1. Usuário envia mensagem no Streamlit
2. Streamlit faz `POST /chat` na API com a mensagem e o `session_id`
3. FastAPI valida o payload (Pydantic) e invoca o grafo LangGraph
4. O orquestrador decide qual(is) especialista(s) acionar
5. O(s) especialista(s) geram a resposta
6. O agente de guardrails audita a resposta (bloqueia recomendações específicas)
7. A API devolve a resposta em JSON
8. O Streamlit renderiza no chat

## Decisões de design

- **API como camada intermediária**: desacopla frontend de lógica de negócio,
  permite escalar/deployar cada camada separadamente.
- **Guardrails como agente dedicado**: em vez de confiar só no prompt de cada
  especialista, existe uma camada de auditoria explícita — decisão de
  governança, não só de engenharia.
- **Sem recomendação de ativo específico**: restrição de produto, reforçada em
  prompt E em guardrail (defesa em profundidade).

## Stack

- **Orquestração**: LangGraph
- **LLM**: Claude (via API)
- **API**: FastAPI + Pydantic
- **Frontend**: Streamlit
- **Persistência**: SQLite (dev) / Postgres (produção)
- **Deploy**: API em Render/AWS · Frontend em Streamlit Community Cloud
