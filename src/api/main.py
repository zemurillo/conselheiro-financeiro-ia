"""Ponto de entrada da API. Expõe o sistema multiagentes via HTTP.

Rodar localmente:
    uvicorn src.api.main:app --reload --port 8000

Depois disso, a API responde em http://localhost:8000 -- e você pode
conferir a documentação interativa (gerada automaticamente pelo
FastAPI a partir dos schemas Pydantic) em http://localhost:8000/docs.
"""

from fastapi import FastAPI
from dotenv import load_dotenv

# Ajuste este import conforme o caminho real onde você colocou
# `create_app_graph` -- pelo seu código, parece estar em
# `src/agents/graph.py` (é de lá que ele importa os agentes). Se você
# moveu para `src/core/graph.py`, troque a linha abaixo de acordo.

from src.core.graph import create_app_graph
from src.api.api_schemas import ChatRequest, ChatResponse
from src.core.llm_factory import get_llm



load_dotenv()  # lê o .env e injeta as variáveis no ambiente -- precisa vir ANTES de get_llm()


app = FastAPI(title="Conselheiro Financeiro IA")

# --- Instanciação ÚNICA, na subida da API ---
# Criar o LLM e montar o grafo (que por dentro instancia todos os
# agentes) tem um custo. Fazer isso UMA VEZ, quando a API sobe, e
# reaproveitar a mesma instância em toda requisição é bem mais barato
# que recriar tudo a cada `POST /chat` -- e também é o padrão esperado:
# o grafo em si não guarda estado de conversa nenhum (quem guarda é o
# `history` que você passa a cada chamada), então reusar a mesma
# instância entre requisições diferentes é seguro.
_llm = get_llm()
_grafo = create_app_graph(_llm)

# --- "Banco de dados" em memória, só para o histórico de conversas ---
# ATENÇÃO: isto é um placeholder simples para você já ter algo
# funcionando ponta a ponta. Ele tem duas limitações sérias, de
# propósito deixadas para depois:
#   1. Se a API reiniciar, todo histórico se perde (fica só na RAM).
#   2. Se você rodar mais de uma instância da API (comum em produção,
#      pra escalar), cada uma teria sua PRÓPRIA cópia deste dicionário
#      -- uma pessoa poderia "perder" o histórico dependendo de qual
#      instância atendesse a próxima requisição dela.
# Resolver isso de verdade é a Semana 8 do seu cronograma (persistência
# com SQLite/Postgres). Por ora, serve para validar o fluxo completo.
_historicos: dict[str, list[dict[str, str]]] = {}


@app.get("/health")
def health() -> dict:
    """Endpoint simples para checar se a API está no ar.

    Útil para scripts de monitoramento, e para a plataforma de deploy
    (Semana 9) confirmar que a aplicação subiu corretamente antes de
    direcionar tráfego pra ela.
    """
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Recebe uma mensagem do usuário, roda o grafo, devolve a resposta.

    Este é o ÚNICO ponto de entrada que o Streamlit vai chamar -- tudo
    que existe atrás dele (orquestrador, agentes especialistas,
    guardrail) fica escondido atrás deste contrato simples. É
    exatamente esse o benefício de ter uma API no meio: o frontend
    nunca soube, e nunca vai precisar saber, como o roteamento
    funciona por dentro.
    """
    # Recupera (ou cria, se for a primeira mensagem dessa sessão) o
    # histórico de conversa desta pessoa.
    historico = _historicos.setdefault(request.session_id, [])

    # Monta o estado inicial no formato que o grafo espera (bate com o
    # seu GraphState em src/core/schemas.py).
    estado_inicial = {
        "session_id": request.session_id,
        "user_message": request.message,
        "history": historico,
        "metadata": {},
    }

    estado_final = _grafo.invoke(estado_inicial)

    # TODO (seu turno): trate o caso em que o Guardrails bloqueou a
    # resposta. Dica: confira `estado_final["guardrail_blocked"]` --
    # quando for True, `estado_final["final_response"]` vem None (veja
    # o node_guardrails que você escreveu). Sugestão de implementação:
    #
    #   if estado_final.get("guardrail_blocked"):
    #       return ChatResponse(
    #           session_id=request.session_id,
    #           agent=estado_final["next_agent"],
    #           content="Não posso ajudar com isso da forma como foi pedido.",
    #           blocked=True,
    #       )
    #
    # Coloque esse bloco ANTES da linha abaixo que lê
    # `estado_final["final_response"]`, já que ela quebraria com um
    # valor None.

    resposta_final = estado_final["final_response"]

    # Atualiza o histórico em memória com esta troca, para que a
    # PRÓXIMA mensagem dessa mesma sessão já chegue com contexto.
    historico.append({"role": "user", "content": request.message})
    historico.append({"role": "assistant", "content": resposta_final})

    return ChatResponse(
        session_id=request.session_id,
        agent=estado_final["next_agent"],
        content=resposta_final,
    )
