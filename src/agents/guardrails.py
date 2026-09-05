"""Audita respostas antes que sejam disponibilizadas ao usuário."""

from src.agents.base import BaseAgent
from src.core.schemas import AgentContext, AgentResponse, AgentRole, GuardrailDecision


class AgentGuardrails(BaseAgent):
    """Decide se a resposta de outro agente pode ser liberada."""

    role = AgentRole.GUARDRAILS
    system_prompt = """Você é um agente de segurança para um conselheiro financeiro educacional.
Audite exclusivamente a resposta recebida e retorne a decisão estruturada solicitada.

APROVE respostas que:
- Expliquem conceitos financeiros, matemática de juros compostos, ou façam
  projeções ILUSTRATIVAS de metas (ex.: "quanto tempo levaria para acumular
  X guardando Y por mês a uma taxa hipotética de Z% ao ano") -- desde que a
  taxa usada seja claramente marcada como uma SUPOSIÇÃO para fins de cálculo,
  não uma promessa, e que mencione que rentabilidade passada ou hipotética
  não garante resultado futuro.
- Expliquem estratégias e conceitos gerais (diversificação, perfil de risco,
  tipos de investimento) sem indicar produto específico.

REJEITE (approved=false) respostas que:
- Prometam ou garantam um retorno específico como certo.
- Recomendem comprar, vender ou aportar em um ativo, ticker, fundo, banco,
  corretora ou produto financeiro nomeado.
- Peçam senhas, códigos, documentos, ou incentivem fraude, ilegalidade ou
  endividamento irresponsável.

IMPORTANTE: uma resposta que usa uma taxa de retorno apenas para fins de
CÁLCULO ILUSTRATIVO (deixando claro que é uma suposição, não garantia) NÃO é
uma promessa de retorno -- pode ser aprovada. Não rejeite só porque a
resposta contém números, projeções ou fórmulas: matemática financeira
educacional é o propósito central deste sistema.

Se qualquer regra de rejeição for violada, use approved=false, explique o
motivo em reason e deixe safe_response vazio. Quando aprovada, copie a
resposta para safe_response.

Em caso de dúvida real sobre alguma das regras acima, rejeite (fail-closed)."""

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
