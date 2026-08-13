"""Schemas base compartilhados por todos os agentes do sistema."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    requires_review: bool = False # se True, o guardrail vai sinalizar pro usuário que a resposta precisa de revisão antes de ser enviada
    metadata: dict[str, Any] = Field(default_factory=dict) # um espaço genérico pra qualquer coisa extra que você queira anexar no futuro sem precisar mudar a classe (ex: o perfil de risco que o usuário informou, timestamp, canal de origem). Any porque o conteúdo pode ser string, número, lista — não dá pra travar o tipo aqui sem saber ainda o que você vai guardar.
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # timestamp de quando a resposta foi criada, em UTC. Pydantic vai chamar a função lambda toda vez que criar um objeto novo sem passar created_at, garantindo que cada resposta tenha o timestamp correto.
