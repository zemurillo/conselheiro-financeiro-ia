from typing import Dict, Any
from langgraph.graph import StateGraph, END

from src.core.schemas import GraphState, AgentContext, AgentResponse, AgentRole
from src.agents import (
    AgenteOrquestrador,
    AgentDiagnostico,
    AgenteDividas,
    AgenteInvestimentos,
    AgentePlanejamento,
    AgentGuardrails,
)


def create_app_graph(llm):
    """
    Instancia todos os agentes e compila o fluxo do LangGraph.
    """
    # Instanciação dos agentes
    orquestrador = AgenteOrquestrador(llm)
    
    agentes = {
        AgentRole.DIAGNOSTICO: AgentDiagnostico(llm),
        AgentRole.DIVIDAS: AgenteDividas(llm),
        AgentRole.INVESTIMENTOS: AgenteInvestimentos(llm),
        AgentRole.PLANEJAMENTO: AgentePlanejamento(llm),
        AgentRole.GUARDRAILS: AgentGuardrails(llm),
    }

    # ------------------------------------------------------------------------
    # Definição dos Nós (Nodes)
    # ------------------------------------------------------------------------
    def node_orquestrador(state: GraphState) -> Dict[str, Any]:
        context = AgentContext(
            session_id=state["session_id"],
            user_message=state["user_message"],
            history=state.get("history", []),
            metadata=state.get("metadata", {}),
        )
        decision = orquestrador.route(context)
        return {"next_agent": decision.next_agent.value}

    def _run_specialist(role: AgentRole, state: GraphState) -> Dict[str, Any]:
        context = AgentContext(
            session_id=state["session_id"],
            user_message=state["user_message"],
            history=state.get("history", []),
            metadata=state.get("metadata", {})
        )
        response: AgentResponse = agentes[role].run(context)
        return {"current_response": response.content}

    # Nó para cada especialista
    def node_diagnostico(state: GraphState) -> Dict[str, Any]:
        return _run_specialist(AgentRole.DIAGNOSTICO, state)

    def node_dividas(state: GraphState) -> Dict[str, Any]:
        return _run_specialist(AgentRole.DIVIDAS, state)

    def node_investimentos(state: GraphState) -> Dict[str, Any]:
        return _run_specialist(AgentRole.INVESTIMENTOS, state)

    def node_planejamento(state: GraphState) -> Dict[str, Any]:
        return _run_specialist(AgentRole.PLANEJAMENTO, state)

    # Nó de Guardrails (auditoria)
    def node_guardrails(state: GraphState) -> Dict[str, Any]:
        context = AgentContext(
            session_id=state["session_id"],
            user_message=state["current_response"],
            history=[],
            metadata=state.get("metadata", {})
        )
        response: AgentResponse = agentes[AgentRole.GUARDRAILS].run(context)
        if not response.approved:
            return {
                "final_response": None,
                "guardrail_blocked": True,
                "guardrail_reason": response.metadata.get(
                    "reason", "Resposta rejeitada"
                ),
            }
        return {"final_response": response.content, "guardrail_blocked": False}

    # ------------------------------------------------------------------------
    # Construção do Grafo
    # ------------------------------------------------------------------------
    workflow = StateGraph(GraphState)

    # Registro de nós
    workflow.add_node("orquestrador", node_orquestrador)
    workflow.add_node(AgentRole.DIAGNOSTICO.value, node_diagnostico)
    workflow.add_node(AgentRole.DIVIDAS.value, node_dividas)
    workflow.add_node(AgentRole.INVESTIMENTOS.value, node_investimentos)
    workflow.add_node(AgentRole.PLANEJAMENTO.value, node_planejamento)
    workflow.add_node(AgentRole.GUARDRAILS.value, node_guardrails)

    # Ponto de entrada
    workflow.set_entry_point("orquestrador")

    # Aresta Condicional (Roteamento)
    def route_decision(state: GraphState) -> str:
        return state["next_agent"]

    workflow.add_conditional_edges(
        "orquestrador",
        route_decision,
        {
            AgentRole.DIAGNOSTICO.value: AgentRole.DIAGNOSTICO.value,
            AgentRole.DIVIDAS.value: AgentRole.DIVIDAS.value,
            AgentRole.INVESTIMENTOS.value: AgentRole.INVESTIMENTOS.value,
            AgentRole.PLANEJAMENTO.value: AgentRole.PLANEJAMENTO.value,
        }
    )

    # Fluxo contínuo para Guardrails -> Fim
    workflow.add_edge(AgentRole.DIAGNOSTICO.value, AgentRole.GUARDRAILS.value)
    workflow.add_edge(AgentRole.DIVIDAS.value, AgentRole.GUARDRAILS.value)
    workflow.add_edge(AgentRole.INVESTIMENTOS.value, AgentRole.GUARDRAILS.value)
    workflow.add_edge(AgentRole.PLANEJAMENTO.value, AgentRole.GUARDRAILS.value)
    workflow.add_edge(AgentRole.GUARDRAILS.value, END)

    return workflow.compile()