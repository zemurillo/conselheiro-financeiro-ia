"""Schemas de entrada/saída da API -- o "contrato HTTP" com o frontend.

Por que não reaproveitar AgentContext/AgentResponse (de src/core/schemas.py)
direto aqui?

Porque o contrato da API é uma coisa, e o modelo de domínio dos agentes
é outra -- eles têm motivos diferentes para mudar. O frontend não
precisa saber, por exemplo, a metadata interna que o Guardrails anexou
pra auditoria, ou os detalhes de `history` no formato exato que o
LangGraph espera. Ele só quer: "manda uma mensagem, recebe um texto de
volta, com uma flag dizendo se foi bloqueado". Separar os dois schemas
significa que você pode reorganizar o AgentContext internamente (Semana
3 pra frente) sem quebrar ninguém que já consome a API -- e vice-versa.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """O que o frontend envia em POST /chat."""

    session_id: str
    message: str


class ChatResponse(BaseModel):
    """O que a API devolve para o frontend."""

    session_id: str
    agent: str  # qual agente respondeu -- ex.: "investimentos"
    content: str
    blocked: bool = False  # True quando o Guardrails rejeitou a resposta
