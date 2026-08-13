# Classes base — estrutura e fluxo

## Estrutura (quem herda de quem, quem usa quem)

```mermaid
classDiagram
    class AgentRole {
        <<enum>>
        ORQUESTRADOR
        DIAGNOSTICO
        DIVIDAS
        INVESTIMENTOS
        PLANEJAMENTO
        GUARDRAILS
    }

    class AgentContext {
        +session_id: str
        +user_message: str
        +history: list
        +metadata: dict
    }

    class AgentResponse {
        +agent: AgentRole
        +content: str
        +requires_review: bool
        +metadata: dict
        +created_at: datetime
    }

    class BaseAgent {
        <<abstract>>
        +role: AgentRole
        +system_prompt: str
        -_llm: BaseChatModel
        +__init__(llm)
        +run(context)* AgentResponse
        #_build_messages(context) list
    }

    class AgenteInvestimentos {
        +role = INVESTIMENTOS
        +system_prompt = "Você é um educador..."
        +run(context) AgentResponse
    }

    BaseAgent <|-- AgenteInvestimentos : herda
    BaseAgent ..> AgentContext : recebe em run()
    BaseAgent ..> AgentResponse : devolve de run()
    AgentResponse --> AgentRole : usa
```

**Como ler:** `BaseAgent` é abstrata (nunca instanciada diretamente — o `*` em `run()`
indica método abstrato). `AgenteInvestimentos` herda dela e só precisa
sobrescrever `role`, `system_prompt` e `run()`. O `_llm` é injetado no
construtor, não criado pela classe.

## Fluxo de execução (o que acontece quando você chama `run()`)

```mermaid
sequenceDiagram
    participant Voce as Seu código
    participant Agente as AgenteInvestimentos
    participant Base as BaseAgent._build_messages
    participant LLM as LLM injetado

    Voce->>Agente: AgenteInvestimentos(llm=llm)
    Note over Agente: __init__ herdado do BaseAgent<br/>guarda self._llm = llm

    Voce->>Agente: agente.run(contexto)
    Agente->>Base: self._build_messages(contexto)
    Note over Base: monta a lista de mensagens:<br/>1. role=system, content=self.system_prompt<br/>2. histórico da conversa<br/>3. role=user, content=pergunta atual
    Base-->>Agente: messages (lista pronta)

    Agente->>LLM: self._llm.invoke(messages)
    Note over LLM: é AQUI que o system_prompt<br/>chega no LLM — dentro da lista messages
    LLM-->>Agente: result.content

    Agente-->>Voce: AgentResponse(agent, content, ...)
```

**O ponto-chave:** o `system_prompt` não é passado separadamente para o LLM.
Ele vira o primeiro item da lista `messages` (com `"role": "system"`), montada
por `_build_messages`. O "encontro" entre prompt e LLM acontece numa única
linha: `self._llm.invoke(messages)`.
