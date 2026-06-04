"""
Physician Review Node — Human-in-the-Loop
------------------------------------------
Ce nœud représente l'interruption humaine du workflow.
Le médecin traitant reçoit la synthèse clinique et la recommandation intermédiaire,
puis saisit sa conduite à tenir avant que le rapport final soit généré.

LangGraph interrompt le graphe ici grâce à l'interruption configurée dans graph.py.
La reprise se fait via l'API POST /consultation/resume avec le champ physician_treatment.
"""
from langchain_core.messages import AIMessage
from app.state import MedicalState


def physician_review_node(state: MedicalState) -> MedicalState:
    """
    Nœud PhysicianReview (Human-in-the-Loop).
    
    Ce nœud est configuré avec interrupt_before dans le graphe.
    Quand LangGraph atteint ce nœud, il suspend l'exécution et attend
    la reprise via l'API resume avec physician_treatment rempli.
    
    Si physician_treatment est déjà fourni (reprise), le nœud valide et continue.
    """
    messages = list(state.get("messages", []))
    physician_treatment = state.get("physician_treatment", "")

    if not physician_treatment:
        # L'exécution sera interrompue avant ce nœud (interrupt_before)
        # Ce bloc ne sera pas atteint lors de l'interruption initiale,
        # mais sert de garde-fou.
        messages.append(AIMessage(
            content="[INTERRUPTION] En attente de la revue du médecin traitant."
        ))
        return {**state, "messages": messages}

    # Le médecin a fourni sa conduite à tenir → validation et continuation
    messages.append(AIMessage(
        content=f"Revue médicale enregistrée. Conduite à tenir : {physician_treatment}"
    ))

    return {
        **state,
        "messages": messages,
        "physician_treatment": physician_treatment,
        "next": "report_agent"
    }
