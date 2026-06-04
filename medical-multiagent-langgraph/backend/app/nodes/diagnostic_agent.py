"""
Diagnostic Agent Node
---------------------
Pose 5 questions successives au patient via le tool ask_patient,
puis produit une synthèse clinique préliminaire et une recommandation intermédiaire.
"""
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.state import MedicalState
from app.tools.patient_tools import ask_patient_tool
from app.tools.care_tools import recommend_interim_care_tool

# Les 5 questions cliniques standard
CLINICAL_QUESTIONS = [
    "Depuis combien de temps ressentez-vous ces symptômes ?",
    "Pouvez-vous décrire précisément la nature et la localisation de vos symptômes ?",
    "Avez-vous de la fièvre, des frissons ou d'autres signes généraux associés ?",
    "Avez-vous des antécédents médicaux importants ou prenez-vous des médicaments en cours ?",
    "Ces symptômes vous ont-ils déjà affecté(e) par le passé, et si oui, comment ont-ils évolué ?"
]

DIAGNOSTIC_SYSTEM = """Tu es un agent d'orientation clinique préliminaire. 
Tu dois analyser les informations fournies par le patient et produire une synthèse clinique.

IMPORTANT : Tu ne poses PAS de diagnostic médical définitif.
Tu produis uniquement une synthèse clinique préliminaire pour aider le médecin traitant.

Format de ta synthèse (JSON strict) :
{
  "resume_symptomes": "...",
  "elements_notables": ["...", "..."],
  "red_flags": ["..." ou []],
  "synthese_clinique": "...",
  "orientation_proposee": "..."
}
"""

INTERIM_CARE_SYSTEM = """Tu es un agent de recommandation de soins intermédiaires prudents.
Propose des mesures générales non-médicales adaptées en attendant la consultation du médecin.
Ces recommandations doivent être prudentes : repos, hydratation, surveillance des symptômes, 
consultation rapide en cas d'aggravation.
Ne propose JAMAIS de médicaments spécifiques ni de traitements médicaux.
Réponds en français de manière claire et rassurante.
"""


def diagnostic_agent_node(state: MedicalState) -> MedicalState:
    """
    Nœud DiagnosticAgent :
    1. Pose les 5 questions au patient (via tool ask_patient)
    2. Génère la synthèse clinique préliminaire
    3. Génère la recommandation intermédiaire (via tool recommend_interim_care)
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    llm_with_tools = llm.bind_tools([ask_patient_tool, recommend_interim_care_tool])

    patient_case = state.get("patient_initial_case", "")
    patient_answers = state.get("patient_answers", [])
    question_count = state.get("question_count", 0)
    messages = list(state.get("messages", []))

    # ── Étape 1 : Poser les questions manquantes ──────────────────────────────
    new_answers = list(patient_answers)
    new_count = question_count

    # Si on n'a pas encore posé toutes les questions, on retourne la prochaine question
    # (l'état sera mis à jour par l'API lors de la réponse du patient)
    if new_count < 5:
        next_question = CLINICAL_QUESTIONS[new_count]
        messages.append(AIMessage(content=f"Question {new_count + 1}/5 : {next_question}"))
        return {
            **state,
            "messages": messages,
            "question_count": new_count,
            "patient_answers": new_answers,
            # On reste dans diagnostic_agent jusqu'à 5 questions complètes
            "next": "diagnostic_agent"
        }

    # ── Étape 2 : Synthèse clinique (toutes les questions répondues) ──────────
    answers_text = "\n".join([
        f"Q{i+1}: {CLINICAL_QUESTIONS[i]}\nR{i+1}: {ans}"
        for i, ans in enumerate(new_answers[:5])
    ])

    synthesis_messages = [
        SystemMessage(content=DIAGNOSTIC_SYSTEM),
        HumanMessage(content=f"""
Cas initial : {patient_case}

Réponses du patient :
{answers_text}

Génère la synthèse clinique préliminaire en JSON.
""")
    ]
    synthesis_response = llm.invoke(synthesis_messages)
    diagnostic_summary = synthesis_response.content.strip()

    # ── Étape 3 : Recommandation intermédiaire ────────────────────────────────
    care_messages = [
        SystemMessage(content=INTERIM_CARE_SYSTEM),
        HumanMessage(content=f"""
Synthèse clinique : {diagnostic_summary}

Propose des recommandations intermédiaires prudentes pour ce patient.
""")
    ]
    care_response = llm.invoke(care_messages)
    interim_care = care_response.content.strip()

    messages.append(AIMessage(content=f"Synthèse clinique générée. Recommandation intermédiaire prête."))

    return {
        **state,
        "messages": messages,
        "diagnostic_summary": diagnostic_summary,
        "interim_care": interim_care,
        "next": "physician_review"
    }
