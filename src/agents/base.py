"""Classe base abstrata para todos os agentes do sistema."""

from abc import ABC, abstractmethod # classes abstratas que não podem ser instanciadas diretamente, só herdadas (um molde de contrato que obriga a subclasse a implementar certos métodos)

from langchain_core.language_models import BaseChatModel # qualquer modelo de chat do langchain, seja Claude, ChatGPT, Groq, etc. — a ideia é que o agente não se importe com o provedor, só com a interface do modelo de chat

from src.core.schemas import AgentContext, AgentResponse, AgentRole


class BaseAgent(ABC):
    """Contrato que todo agente especialista deve seguir.

    Por que uma classe ABSTRATA (ABC) e não só uma convenção?
    Porque queremos que o Python IMPEÇA a criação de um agente que
    esqueceu de implementar `run()`. Sem isso, o erro só apareceria
    em produção, na hora que alguém chamasse o método. Com ABC, o
    erro acontece na hora de instanciar a classe — muito mais cedo
    e muito mais barato de corrigir.

    Por que o LLM é INJETADO no construtor (em vez de cada agente
    criar seu próprio client)?
    1. Troca de provedor sem tocar no código do agente: hoje é
       Claude, amanhã pode ser Groq — só muda quem instancia o
       agente, não a classe em si.
    2. Testabilidade: nos testes, dá pra injetar um LLM falso (mock)
       que devolve respostas fixas, sem gastar tokens de verdade
       nem depender de internet.
    3. Cada agente pode, inclusive, usar um modelo DIFERENTE (ex:
       um modelo mais barato para o Diagnóstico, mais caro para
       Investimentos) sem mudar a estrutura da classe.
    """

    role: AgentRole # qual agente é (ex: "dividas") — cada subclasse vai definir isso como uma constante, e o orquestrador vai usar pra saber qual agente chamar.
    system_prompt: str # o prompt do sistema que vai ser injetado no LLM antes da conversa com o usuário — cada subclasse vai definir isso como uma constante, e o orquestrador vai usar pra saber qual agente chamar.

    #Não estão preenchidos, mas toda classe terá que ter um

    # cosntrutor de 1 parâmetro (o LLM) 
    # toda vez que eu chamar a classe tenho que passar o LLM que quero usar, e ele vai ser armazenado no atributo self._llm

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm


    @abstractmethod
    def run(self, context: AgentContext) -> AgentResponse:
        """Processa o contexto e devolve uma resposta padronizada.

        Este é o único método que cada subclasse É OBRIGADA a
        implementar — é aqui que mora a lógica específica de cada
        agente (polimorfismo: o orquestrador chama `agente.run()`
        sem saber, nem precisar saber, qual agente é).
        """
        raise NotImplementedError

    # é um método completo, não abstrato, porque a lógica de montar as mensagens é igual para todos os agentes — não faz sentido cada subclasse reimplementar o mesmo "junte o system prompt com o histórico e a mensagem do usuário". Fica pronto pra reuso, mas qualquer agente pode sobrescrever se precisar de algo diferente (ex: injetar um contexto extra).
    def _build_messages(self, context: AgentContext) -> list[dict[str, str]]:
        """Monta a lista de mensagens no formato esperado pelo LLM.

        Método CONCRETO (não abstrato) porque essa lógica é igual
        para todos os agentes — não faz sentido cada subclasse
        reimplementar o mesmo "junte o system prompt com o
        histórico e a mensagem do usuário". Fica pronto pra reuso,
        mas qualquer agente pode sobrescrever se precisar de algo
        diferente (ex: injetar um contexto extra).
        """
        messages = [{"role": "system", "content": self.system_prompt}]  # 1. instrução de comportamento que cada agente irá implementar
        messages.extend(context.history) # 2. histórico da conversa (cada item é algo como {"role": "user", "content": "..."})
        messages.append({"role": "user", "content": context.user_message}) # 3. mensagem do usuário (o que ele acabou de digitar)
        return messages
