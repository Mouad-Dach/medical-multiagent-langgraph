"""
Supervisor Node
---------------
Orchestre le workflow et décide du prochain agent à invoquer.
Utilise un LLM pour analyser l'état courant et router vers le bon nœud.
"""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.state import MedicalState

# Prompt système du Supervisor
SUPERVISOR_SYSTEM = """Tu es le superviseur d'un système d'orientation clinique préliminaire.
Tu dois décider du prochain agent à invoquer selon l'état courant du workflow.

Règles de routage :
1. Si aucune synthèse clinique n'existe encore → router vers "diagnostic_agent"
2. Si la synthèse existe mais pas la conduite du médecin → router vers "physician_review"
3. Si la conduite du médecin existe mais pas le rapport final → router vers "report_agent"
4. Si le rapport final existe → router vers "FINISH"

Réponds UNIQUEMENT avec l'un de ces mots : diagnostic_agent, physician_review, report_agent, FINISH
"""


def supervisor_node(state: MedicalState) -> MedicalState:
    """
    Nœud Supervisor : analyse l'état et décide du prochain agent.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Construction du contexte pour le supervisor
    context_parts = []
    context_parts.append(f"Cas initial patient : {state.get('patient_initial_case', 'Non fourni')}")
    context_parts.append(f"Nombre de questions posées : {state.get('question_count', 0)}/5")
    context_parts.append(f"Synthèse clinique : {'Disponible' if state.get('diagnostic_summary') else 'Non disponible'}")
    context_parts.append(f"Recommandation intermédiaire : {'Disponible' if state.get('interim_care') else 'Non disponible'}")
    context_parts.append(f"Conduite médecin : {'Disponible' if state.get('physician_treatment') else 'Non disponible'}")
    context_parts.append(f"Rapport final : {'Disponible' if state.get('final_report') else 'Non disponible'}")

    context = "\n".join(context_parts)

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM),
        HumanMessage(content=f"État actuel du workflow :\n{context}\n\nQuel est le prochain agent ?")
    ]

    response = llm.invoke(messages)
    decision = response.content.strip()

    # Validation de la décision
    valid_decisions = ["diagnostic_agent", "physician_review", "report_agent", "FINISH"]
    if decision not in valid_decisions:
        # Fallback logique
        if not state.get("diagnostic_summary"):
            decision = "diagnostic_agent"
        elif not state.get("physician_treatment"):
            decision = "physician_review"
        elif not state.get("final_report"):
            decision = "report_agent"
        else:
            decision = "FINISH"

    return {**state, "next": decision}
