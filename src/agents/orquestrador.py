from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

# Imports dos seus módulos internos
from src.agents.base import BaseAgent
from src.core.schemas import (
    AgentContext,
    AgentResponse,
    AgentRole,
    AGENT_DESCRIPTIONS,
)


# ============================================================================
# 1. SCHEMA DE SAÍDA (Pydantic)
# ============================================================================
class RouteDecision(BaseModel):
    """
    Define a 'forma' exata que a LLM deve responder quando for tomar a decisão.
    Ao herdar de BaseModel, o Pydantic garante a validação dos tipos.
    """
    
    # O Pydantic valida se 'next_agent' é obrigatoriamente um valor válido do enum AgentRole
    next_agent: AgentRole = Field(
        description="Agente especialista mais adequado para responder à dúvida do usuário."
    )
    
    # Exige uma justificativa curta para que possamos auditá-la nos logs ou no metadata
    reasoning: str = Field(
        description="Breve justificativa para a escolha do agente."
    )


# ============================================================================
# 2. CLASSE DO AGENTE ORQUESTRADOR
# ============================================================================
class AgenteOrquestrador(BaseAgent):
    """
    Agente responsável por analisar a intenção e decidir qual especialista acionar.
    Ele herda de BaseAgent para manter a mesma interface dos outros agentes.
    """

    # Sobrescreve o atributo 'role' da BaseAgent com o papel específico deste agente
    role: AgentRole = AgentRole.ORQUESTRADOR

    def __init__(self, llm):
        # 1. Chama o construtor da classe pai (BaseAgent), que guarda o 'llm' em self._llm
        super().__init__(llm)
        
        # 2. Filtra dinamicamente quem são os agentes especialistas elegíveis para receber o roteamento.
        # Descartamos o próprio ORQUESTRADOR e o GUARDRAILS, pois nenhum usuário deve ser roteado para eles diretamente.
        self.specialists = [
            role for role in AgentRole 
            if role not in (AgentRole.ORQUESTRADOR, AgentRole.GUARDRAILS)
        ]

        # 3. Monta dinamicamente o texto de opções lendo as descrições do AGENT_DESCRIPTIONS (do schemas.py).
        # Isso garante que se você adicionar um agente novo no schemas.py, o prompt atualiza sozinho!
        options_text = "\n".join([
            f"- {role.value.upper()} ({role.value}): {AGENT_DESCRIPTIONS.get(role, 'Especialista de domínio.')}"
            for role in self.specialists
        ])

        # 4. Define as instruções do sistema (System Prompt) com as regras de negócio do orquestrador
        self.system_prompt = (
            "Você é o agente orquestrador de um sistema de consultoria financeira.\n"
            "Sua ÚNICA responsabilidade é analisar a mensagem do usuário e decidir "
            "qual especialista deve atendê-lo.\n\n"
            "Agentes disponíveis:\n"
            f"{options_text}\n\n"
            "Regras estritas:\n"
            "1. NUNCA responda à dúvida do usuário diretamente.\n"
            "2. Escolha exatamente UM especialista baseado na intenção principal."
        )

        # 5. Prepara uma versão da LLM configurada para Structured Output (Saída Estruturada).
        # O método `.with_structured_output()` força a LLM a devolver os dados formatados
        # exatamente segundo a classe RouteDecision (sem precisar de parse manual de JSON).
        self._structured_llm = self._llm.with_structured_output(RouteDecision)

    def route(self, context: AgentContext) -> RouteDecision:
        """
        Método utilitário para ser chamado diretamente pelo nó do LangGraph.
        Ele envia o contexto para a LLM e retorna o objeto RouteDecision preenchido.
        """
        # Monta a lista de mensagens que será enviada para o modelo
        messages = [
            SystemMessage(content=self.system_prompt),  # Instrução de comportamento do orquestrador
            HumanMessage(content=context.user_message), # Pergunta enviada pelo usuário
        ]
        
        # Chama a LLM estruturada, que já retorna uma instância da classe RouteDecision
        decision: RouteDecision = self._structured_llm.invoke(messages)
        
        return decision

    def run(self, context: AgentContext) -> AgentResponse:
        """
        Implementação do método abstrato obrigatório herdado de BaseAgent.
        Garante o POLIMORFISMO do sistema (todos os agentes retornam AgentResponse).
        """
        # 1. Executa a lógica de decisão chamando o método route()
        decision = self.route(context)

        # 2. Envelopa o resultado no formato padrão AgentResponse do sistema
        return AgentResponse(
            agent=self.role,                    # Identifica que esta resposta veio do Orquestrador
            content=decision.next_agent.value,  # Coloca o nome do agente escolhido no conteúdo principal (ex: "dividas")
            metadata={                          # Guarda detalhes extras para auditoria
                "next_agent": decision.next_agent.value,
                "reasoning": decision.reasoning
            }
        )

    # ==============================================================================
# NOTA DE ESTUDO: Por que AgenteDividas NÃO usa __init__ e o AgenteOrquestrador USA?
# ==============================================================================
#
# 1. AgenteDividas (Especialistas em Geral):
#    - Têm um 'system_prompt' 100% fixo/estático.
#    - Não precisam fazer nenhuma transformação especial na LLM.
#    - Quando NÃO declaramos o def __init__(self, llm), o Python herda
#      automaticamente o __init__ da classe pai (BaseAgent), que já faz o 
#      trabalho de salvar o LLM em self._llm.
#
# 2. AgenteOrquestrador:
#    - O 'system_prompt' é DINÂMICO (montado a partir do enum AgentRole e das 
#      descrições em AGENT_DESCRIPTIONS).
#    - Precisa transformar a LLM usando .with_structured_output(RouteDecision)
#      para garantir que o retorno seja um objeto Pydantic e não texto livre.
#    - Sobrescrevemos o def __init__(self, llm) para executar essa montagem e 
#      configuração UMA ÚNICA VEZ no momento em que o agente é criado na memória.
#    - A primeira linha OBRIGATORIAMENTE chama super().__init__(llm) para 
#      manter a herança da BaseAgent funcionando normalmente.
# ==============================================================================