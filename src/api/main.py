"""Ponto de entrada da API. Expõe o sistema multiagentes via HTTP.

Rodar localmente:
    uvicorn src.api.main:app --reload --port 8000
"""

from dotenv import load_dotenv

load_dotenv()  # precisa vir ANTES de qualquer código que leia variáveis do .env

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from src.core.database import get_db, init_db
from src.core.graph import create_app_graph
from src.core.llm_factory import get_llm
from src.core.repository import obter_historico, salvar_mensagem
from src.api.api_schemas import ChatRequest, ChatResponse

app = FastAPI(title="Conselheiro Financeiro IA")

# --- Instanciação ÚNICA, na subida da API ---
_llm = get_llm()
_grafo = create_app_graph(_llm)


@app.on_event("startup")
def on_startup() -> None:
    """Roda uma única vez, quando a API sobe -- garante que as tabelas
    do banco existem antes da primeira requisição chegar. Sem isso, a
    primeira chamada ao `/chat` falharia tentando gravar numa tabela
    que ainda não foi criada.
    """
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Recebe uma mensagem do usuário, roda o grafo, devolve a resposta.

    `db: Session = Depends(get_db)` é a injeção de dependência do
    FastAPI -- o mesmo princípio da injeção de LLM nos agentes, só que
    aplicada pelo próprio framework: ele chama `get_db()` (definido em
    src/core/database.py) antes deste endpoint rodar, entrega a sessão
    de banco já pronta, e garante que ela é fechada no final -- mesmo
    se o código abaixo lançar uma exceção no meio do caminho.
    """
    # Antes: `historico = _historicos.setdefault(request.session_id, [])`
    # Agora: lê do banco -- sobrevive a reinícios da API.
    historico = obter_historico(db, request.session_id)

    estado_inicial = {
        "session_id": request.session_id,
        "user_message": request.message,
        "history": historico,
        "metadata": {},
    }

    estado_final = _grafo.invoke(estado_inicial)

    # Trata o caso em que o Guardrails bloqueou a resposta -- lembra do
    # TODO que você resolveu no main.py anterior? Se você já
    # implementou algo diferente aqui, mantenha a sua versão; o
    # importante é que `resposta_final` nunca fique None antes de
    # salvar no banco (a coluna `content` é `nullable=False`).
    if estado_final.get("guardrail_blocked"):
        resposta_final = "Não posso ajudar com isso da forma como foi pedido."
        bloqueado = True
    else:
        resposta_final = estado_final["final_response"]
        bloqueado = False

    agente_que_respondeu = estado_final["next_agent"]

    # Persiste a troca no banco -- substitui o antigo
    # `historico.append(...)` em memória. Cada mensagem vira uma linha
    # na tabela `mensagens`, associada a esta sessão.
    salvar_mensagem(db, request.session_id, role="user", content=request.message)
    salvar_mensagem(
        db,
        request.session_id,
        role="assistant",
        content=resposta_final,
        agent=agente_que_respondeu,
    )

    return ChatResponse(
        session_id=request.session_id,
        agent=agente_que_respondeu,
        content=resposta_final,
        blocked=bloqueado,
    )