from typing import Annotated, Optional
from typing_extensions import TypedDict, Literal
from langgraph.graph.message import add_messages


class MedicalState(TypedDict, total=False):
    """
    État partagé entre tous les agents du graphe médical.
    Chaque champ est optionnel (total=False) car il est rempli progressivement.
    """
    messages: Annotated[list, add_messages]

    # Champ de routage du Supervisor
    next: Literal[
        "diagnostic_agent",
        "physician_review",
        "report_agent",
        "FINISH"
    ]

    # Données patient
    patient_initial_case: str          # Cas initial saisi par le patient
    patient_answers: list[str]         # Réponses aux 5 questions
    question_count: int                # Nombre de questions posées (0-5)

    # Synthèse et recommandations
    diagnostic_summary: str            # Synthèse clinique préliminaire
    interim_care: str                  # Recommandation intermédiaire

    # Intervention du médecin
    physician_treatment: str           # Conduite à tenir proposée par le médecin

    # Rapport final
    final_report: str                  # Rapport structuré final

    # Métadonnées
    session_id: Optional[str]
    error: Optional[str]
