"""Agente especialista em educação sobre investimentos."""

from src.agents.base import BaseAgent
from src.core.schemas import AgentContext, AgentResponse, AgentRole


class AgenteInvestimentos(BaseAgent):
    """Explica conceitos de investimento sem recomendar ativos específicos.

    Herda de BaseAgent e só precisa definir `role`, `system_prompt`
    e implementar `run()` — todo o resto (injeção do LLM, montagem
    de mensagens) já vem pronto da classe base.
    """

    role = AgentRole.INVESTIMENTOS # definie que esse é o agente de investimentos, que é o que o orquestrador vai usar pra saber qual agente chamar
    system_prompt = (
        "Você é um educador financeiro. Sua função é explicar "
        "conceitos de investimento de forma didática e acessível: "
        "renda fixa, renda variável, perfil de risco, diversificação, "
        "tesouro direto, fundos imobiliários, etc.\n\n"
        "REGRA ABSOLUTA: nunca recomende um ativo, ticker, fundo, "
        "corretora ou instituição financeira específica. Seu papel é "
        "dar conhecimento para que a pessoa decida por conta própria, "
        "nunca decidir por ela."
    )

    def run(self, context: AgentContext) -> AgentResponse:
        messages = self._build_messages(context) #chama o método que já veio pronto da classe pai. O AgenteInvestimentos não precisou reescrever essa lógica.
        result = self._llm.invoke(messages) #usa o LLM que foi injetado lá no __init__ da classe base (self._llm foi guardado por BaseAgent.__init__, e AgenteInvestimentos nem precisou escrever seu próprio __init__ — herdou ele da classe base)
        return AgentResponse(agent=self.role, content=result.content) #Empacota o resultado no formato padronizado AgentResponse, preenchendo agent=self.role (que aponta pra AgentRole.INVESTIMENTOS) e content com o texto que o LLM devolveu.
