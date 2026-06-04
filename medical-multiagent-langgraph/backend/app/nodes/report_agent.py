"""
Report Agent Node
-----------------
Génère le rapport final structuré en intégrant :
- Le cas initial du patient
- Les réponses aux 5 questions
- La synthèse clinique préliminaire
- La recommandation intermédiaire
- La conduite à tenir du médecin traitant
"""
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.state import MedicalState

REPORT_SYSTEM = """Tu es un agent de génération de rapports médicaux structurés.
Tu dois produire un rapport d'orientation clinique complet et professionnel.

Le rapport DOIT obligatoirement mentionner en conclusion :
"Ce système ne remplace pas une consultation médicale."

Structure du rapport :
1. En-tête (date, référence)
2. Informations patient (cas initial + réponses)
3. Synthèse clinique préliminaire
4. Recommandation intermédiaire
5. Conduite à tenir recommandée par le médecin traitant
6. Conclusion avec avertissement légal

Rédige le rapport en français, de manière professionnelle et structurée.
Utilise le format Markdown pour la mise en forme.
"""


def report_agent_node(state: MedicalState) -> MedicalState:
    """
    Nœud ReportAgent : génère le rapport final structuré.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

    patient_case = state.get("patient_initial_case", "Non renseigné")
    patient_answers = state.get("patient_answers", [])
    diagnostic_summary = state.get("diagnostic_summary", "Non disponible")
    interim_care = state.get("interim_care", "Non disponible")
    physician_treatment = state.get("physician_treatment", "Non renseigné")

    # Construction des réponses formatées
    from app.nodes.diagnostic_agent import CLINICAL_QUESTIONS
    answers_formatted = "\n".join([
        f"- **Q{i+1}** : {CLINICAL_QUESTIONS[i] if i < len(CLINICAL_QUESTIONS) else 'Question'}\n  **Réponse** : {ans}"
        for i, ans in enumerate(patient_answers[:5])
    ]) or "Aucune réponse enregistrée"

    now = datetime.now().strftime("%d/%m/%Y à %H:%M")
    session_id = state.get("session_id", "N/A")

    report_messages = [
        SystemMessage(content=REPORT_SYSTEM),
        HumanMessage(content=f"""
Génère le rapport final avec les données suivantes :

**Date** : {now}
**Référence session** : {session_id}

**Cas initial décrit par le patient** :
{patient_case}

**Réponses du patient aux questions cliniques** :
{answers_formatted}

**Synthèse clinique préliminaire** :
{diagnostic_summary}

**Recommandation intermédiaire générée** :
{interim_care}

**Conduite à tenir recommandée par le médecin traitant** :
{physician_treatment}
""")
    ]

    response = llm.invoke(report_messages)
    final_report = response.content.strip()

    messages = list(state.get("messages", []))
    messages.append(AIMessage(content="Rapport final généré avec succès."))

    return {
        **state,
        "messages": messages,
        "final_report": final_report,
        "next": "FINISH"
    }
