"""Audita respostas antes que sejam disponibilizadas ao usuário."""

from src.agents.base import BaseAgent
from src.core.schemas import AgentContext, AgentResponse, AgentRole, GuardrailDecision


class AgentGuardrails(BaseAgent):
    """Decide se a resposta de outro agente pode ser liberada."""

    role = AgentRole.GUARDRAILS
    system_prompt = """Você é um agente de segurança para um conselheiro financeiro educacional.
Audite exclusivamente a resposta recebida e retorne a decisão estruturada solicitada.

A resposta só pode ser aprovada se for educativa, clara e prudente, sem promessas de
retorno, recomendação de compra ou venda de ativo, ticker, fundo, banco, corretora ou
produto financeiro específico. Também não pode pedir senhas, códigos ou documentos,
nem incentivar fraude, ilegalidade ou endividamento irresponsável.

Se qualquer regra for violada, use approved=false, explique o motivo em reason e
 deixe safe_response vazio. Quando aprovada, copie a resposta para safe_response.
Em caso de dúvida, rejeite (fail-closed)."""

    def __init__(self, llm):
        super().__init__(llm)
        self._structured_llm = llm.with_structured_output(GuardrailDecision)

    def run(self, context: AgentContext) -> AgentResponse:
        messages = self._build_messages(context)
        decision: GuardrailDecision = self._structured_llm.invoke(messages)
        approved = decision.approved and bool(decision.safe_response.strip())
        return AgentResponse(
            agent=self.role,
            content=decision.safe_response if approved else "",
            approved=approved,
            requires_review=not approved,
            metadata={"reason": decision.reason, "approved": approved},
        )
