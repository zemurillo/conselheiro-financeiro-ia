"Agente epecialista em educação sobre dívidas"

from src.agents.base import BaseAgent
from src.core.schemas import AgentContext, AgentResponse, AgentRole

class AgenteDividas(BaseAgent): #herdo o BAseAgent e só preciso definir role, system_prompt e implementar run() — todo o resto (injeção do LLM, montagem de mensagens) já vem pronto da classe base.
    """ Explica conceitos de dívidas e finanças pessoais sem recomendar produtos específicos."""

    role = AgentRole.DIVIDAS #definie que esse é o agente de dívidas, que é o que o orquestrador vai usar pra saber qual agente chamar
    system_prompt = ("""Você é um educador financeiro. Sua função é explicar conceitos de investimentos relacionados a dívidas de forma didática e acessível para ajudar pessoas endividas a saírem dessa situação
e conseguirem começar a guardar dinheiro para reserva de emergência, investimentos e sonhos.\n
REGRA ABSOLUTA: nunca recomende um ativo, ticker, fundo, correta ou instituição financeira específica. 
Seu papel é dar conhecimento para que a pessoa decida por conta própria, nunca decidir por ela
""")

    def run(self,context: AgentContext)-> AgentResponse: #self serve para acessar os atributos da classe, como self.role e self.system_prompt durante a instanciação do objeto. O self é passado automaticamente pelo Python quando chamamos o método em uma instância da classe, então não precisamos passar manualmente.
        messages = self._build_messages(context)
        result = self._llm.invoke(messages)
        return AgentResponse(agent=self.role,content=result.content) #chama o método que já veio pronto da classe pai. O AgenteDividas não precisou reescrever essa lógica.

#self.role aponta para AgentRole.DIVIDAS, que é o que o orquestrador vai usar pra saber qual agente chamar. content recebe o texto que o LLM devolveu, e empacota tudo no formato padronizado AgentResponse.

