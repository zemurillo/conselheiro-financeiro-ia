"""Schemas base compartilhados por todos os agentes do sistema."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class GraphState(TypedDict, total=False):
    """Estado compartilhado pelos nós do fluxo de atendimento."""

    session_id: str
    user_message: str
    history: list[dict[str, str]]
    metadata: dict[str, Any]
    next_agent: str
    current_response: str
    final_response: str | None
    guardrail_blocked: bool
    guardrail_reason: str


class AgentRole(str, Enum): #Herda as classes str e Enum para que seja possível comparar diretamente com strings e serializar
    """Identifica cada agente do sistema por um nome estável.

    Um Enum evita erros de digitação espalhados pelo código (ex:
    "orquestrador" vs "Orquestrador" vs "orq") e dá autocomplete na
    IDE. Herdar de `str` além de `Enum` permite comparar direto com
    strings e serializar em JSON sem conversão manual.
    """

    ORQUESTRADOR = "orquestrador"
    DIAGNOSTICO = "diagnostico"
    DIVIDAS = "dividas"
    INVESTIMENTOS = "investimentos"
    PLANEJAMENTO = "planejamento"
    GUARDRAILS = "guardrails"


# Fora da classe: dicionário que mapeia o enum para a descrição
AGENT_DESCRIPTIONS = {
    AgentRole.DIAGNOSTICO: "organização financeira, renda, gastos e raio-x orçamentário.",
    AgentRole.DIVIDAS: "estratégias de quitação (bola de neve, avalanche) e renegociação.",
    AgentRole.INVESTIMENTOS: "educação financeira, conceitos de renda fixa/variável e perfil de risco.",
    AgentRole.PLANEJAMENTO: "metas financeiras, reserva de emergência e planos de longo prazo.",
}

class AgentContext(BaseModel):
    """Tudo que um agente precisa saber para responder.

    Todos os agentes recebem o MESMO tipo de contexto — cada um usa
    só o que precisa. Isso mantém a assinatura de `BaseAgent.run()`
    estável mesmo quando agentes diferentes lidam com dados
    diferentes, e é o que permite ao orquestrador chamar qualquer
    agente da mesma forma, sem saber os detalhes internos dele.
    """

    session_id: str # identifica de qual conversa isso faz parte
    user_message: str #as mensagens anteriores da conversa (cada item é algo como {"role": "user", "content": "..."})
    history: list[dict[str, str]] = Field(default_factory=list) #se você escrever history: list = [] como valor padrão, todas as instâncias da classe compartilhariam a mesma lista na memória — adicionar um item no histórico de uma conversa vazaria pra outra. default_factory=list diz "toda vez que criar um objeto novo sem passar history, chame list() de novo, criando uma lista nova e isolada". Pydantic já resolve isso pra você, mas é importante saber o porquê.
    metadata: dict[str, Any] = Field(default_factory=dict) #— um espaço genérico pra qualquer coisa extra que você queira anexar no futuro sem precisar mudar a classe (ex: o perfil de risco que o usuário informou, timestamp, canal de origem). Any porque o conteúdo pode ser string, número, lista — não dá pra travar o tipo aqui sem saber ainda o que você vai guardar.


class GuardrailDecision(BaseModel):
    """Decisão estruturada do agente que audita respostas."""

    approved: bool = False
    reason: str = ""
    safe_response: str = ""

#Por que é um objeto e não 4 parâmetros soltos na função?
#Imagina def run(session_id, user_message, history, metadata). Se amanhã você precisar adicionar um 5º dado (digamos, o idioma do usuário), você teria que mudar a assinatura de todo agente que existe. Com um objeto, você adiciona o campo em um lugar só (AgentContext) e todo agente que já usa context.algum_campo continua funcionando — os que não usam o campo novo simplesmente ignoram.

class AgentResponse(BaseModel):
    """Saída padronizada de qualquer agente do sistema.

    Padronizar a resposta é o que permite ao orquestrador e ao
    guardrail tratarem qualquer agente de forma genérica — eles não
    precisam saber se a resposta veio do agente de Dívidas ou do de
    Investimentos, só que ela segue esse formato (polimorfismo).

    `requires_review` sinaliza pro guardrail que essa resposta
    precisa de atenção extra antes de ir pro usuário (ex: o agente
    identificou um tema sensível mas respondeu mesmo assim).
    """

    agent: AgentRole #qual agente gerou a resposta (ex: "dividas")
    content: str #o texto da resposta 
    approved: bool = True
    requires_review: bool = False # se True, o guardrail vai sinalizar pro usuário que a resposta precisa de revisão antes de ser enviada
    metadata: dict[str, Any] = Field(default_factory=dict) # um espaço genérico pra qualquer coisa extra que você queira anexar no futuro sem precisar mudar a classe (ex: o perfil de risco que o usuário informou, timestamp, canal de origem). Any porque o conteúdo pode ser string, número, lista — não dá pra travar o tipo aqui sem saber ainda o que você vai guardar.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # timestamp de quando a resposta foi criada, em UTC. Pydantic vai chamar a função lambda toda vez que criar um objeto novo sem passar created_at, garantindo que cada resposta tenha o timestamp correto.


# Por que isso é o coração do design "polimórfico":
# O orquestrador, ao final, faz algo como:

# python
# resposta: AgentResponse = agente_escolhido.run(context)

# Ele não precisa saber se agente_escolhido é o de Dívidas, Investimentos ou Planejamento — só precisa saber que qualquer um deles devolve um AgentResponse. Isso é o que te permite adicionar um agente novo no futuro (ex: "Agente de Aposentadoria") sem mexer em uma linha sequer do orquestrador ou do guardrail — eles continuam funcionando porque o "formato do envelope" não mudou.