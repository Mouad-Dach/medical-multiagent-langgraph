"""
Graph Definition — Système Multi-Agents Médical
-----------------------------------------------
Définit le graphe LangGraph avec :
- Supervisor (orchestration)
- DiagnosticAgent (questions patient + synthèse clinique)
- PhysicianReview (Human-in-the-Loop)
- ReportAgent (rapport final)

Persistance : MemorySaver (peut être remplacé par SqliteSaver pour la production)
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.state import MedicalState
from app.nodes.supervisor import supervisor_node
from app.nodes.diagnostic_agent import diagnostic_agent_node
from app.nodes.physician_review import physician_review_node
from app.nodes.report_agent import report_agent_node


def route_supervisor(state: MedicalState) -> str:
    """
    Fonction de routage basée sur le champ 'next' défini par le Supervisor.
    Retourne le nom du prochain nœud.
    """
    next_node = state.get("next", "diagnostic_agent")
    if next_node == "FINISH":
        return END
    return next_node


def should_continue_diagnostic(state: MedicalState) -> str:
    """
    Détermine si le DiagnosticAgent doit continuer à poser des questions
    ou passer au Supervisor pour continuer le workflow.
    """
    question_count = state.get("question_count", 0)
    if question_count < 5:
        return "diagnostic_agent"  # Continuer les questions
    return "supervisor"            # Toutes les questions posées → Supervisor


def build_graph() -> StateGraph:
    """
    Construit et compile le graphe LangGraph.
    Retourne le graphe compilé avec checkpointer.
    """
    # ── Création du graphe ────────────────────────────────────────────────────
    builder = StateGraph(MedicalState)

    # ── Ajout des nœuds ───────────────────────────────────────────────────────
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("diagnostic_agent", diagnostic_agent_node)
    builder.add_node("physician_review", physician_review_node)
    builder.add_node("report_agent", report_agent_node)

    # ── Point d'entrée ────────────────────────────────────────────────────────
    builder.set_entry_point("supervisor")

    # ── Arêtes conditionnelles depuis le Supervisor ───────────────────────────
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "diagnostic_agent": "diagnostic_agent",
            "physician_review": "physician_review",
            "report_agent": "report_agent",
            END: END,
        }
    )

    # ── Arêtes depuis les agents métiers vers le Supervisor ───────────────────
    # DiagnosticAgent : peut boucler ou revenir au Supervisor
    builder.add_conditional_edges(
        "diagnostic_agent",
        should_continue_diagnostic,
        {
            "diagnostic_agent": "diagnostic_agent",  # Boucle questions
            "supervisor": "supervisor",              # Suite du workflow
        }
    )

    # PhysicianReview → Supervisor après validation du médecin
    builder.add_edge("physician_review", "supervisor")

    # ReportAgent → Supervisor pour terminer
    builder.add_edge("report_agent", "supervisor")

    # ── Compilation avec checkpointer et interruption Human-in-the-Loop ───────
    checkpointer = MemorySaver()
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["physician_review"],  # Interruption avant la revue médecin
    )

    return graph


# Instance globale du graphe
medical_graph = build_graph()
