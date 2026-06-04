"""
Care Tools
----------
Outils LangChain pour générer des recommandations de soins intermédiaires.
Ces tools sont intégrés via MCP et utilisés par le DiagnosticAgent.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


class InterimCareInput(BaseModel):
    symptoms_summary: str = Field(description="Résumé des symptômes du patient")
    red_flags: Optional[list[str]] = Field(
        default=None,
        description="Liste des signaux d'alarme détectés (red flags)"
    )
    urgency_level: str = Field(
        default="modere",
        description="Niveau d'urgence : faible, modere, eleve"
    )


@tool("recommend_interim_care", args_schema=InterimCareInput)
def recommend_interim_care_tool(
    symptoms_summary: str,
    red_flags: Optional[list[str]] = None,
    urgency_level: str = "modere"
) -> str:
    """
    Génère des recommandations de soins intermédiaires prudentes pour le patient
    en attendant la consultation du médecin traitant.
    
    Les recommandations sont toujours prudentes et non-médicales :
    repos, hydratation, surveillance, consultation rapide si aggravation.
    """
    base_recommendations = [
        "Reposez-vous suffisamment et évitez les efforts physiques intenses.",
        "Maintenez une hydratation adéquate (eau, tisanes légères).",
        "Surveillez l'évolution de vos symptômes attentivement.",
        "Consultez rapidement un médecin en cas d'aggravation.",
    ]

    if red_flags:
        urgent_recs = [
            "⚠️ Des signes d'alarme ont été détectés. Consultez un médecin sans délai.",
            "En cas de difficultés respiratoires sévères, appelez le 15 (SAMU).",
        ]
        recommendations = urgent_recs + base_recommendations
    elif urgency_level == "eleve":
        recommendations = [
            "Une consultation médicale rapide est recommandée.",
        ] + base_recommendations
    else:
        recommendations = base_recommendations

    recommendations.append(
        "⚕️ Ces recommandations sont préliminaires et ne remplacent pas l'avis d'un médecin."
    )

    return "\n".join(f"• {r}" for r in recommendations)


class SymptomCheckInput(BaseModel):
    symptoms: list[str] = Field(description="Liste des symptômes rapportés")


@tool("check_red_flags", args_schema=SymptomCheckInput)
def check_red_flags_tool(symptoms: list[str]) -> str:
    """
    Vérifie la présence de signaux d'alarme (red flags) dans les symptômes rapportés.
    Retourne une liste de red flags détectés.
    """
    # Mots-clés indicatifs de red flags (liste non exhaustive et non diagnostique)
    red_flag_keywords = {
        "douleur thoracique": "Douleur thoracique — consultation urgente recommandée",
        "difficulté à respirer": "Détresse respiratoire potentielle",
        "difficultés respiratoires": "Détresse respiratoire potentielle",
        "perte de conscience": "Syncope — évaluation urgente nécessaire",
        "paralysie": "Déficit neurologique — urgence médicale",
        "sang dans": "Saignement anormal — évaluation nécessaire",
        "forte fièvre": "Hyperthermie — surveillance étroite",
        "confusion": "Altération de la conscience — urgence",
        "vomissements répétés": "Déshydratation potentielle",
    }

    symptoms_lower = " ".join(symptoms).lower()
    detected = [
        msg for keyword, msg in red_flag_keywords.items()
        if keyword in symptoms_lower
    ]

    if detected:
        return "RED_FLAGS_DETECTES|" + "|".join(detected)
    return "AUCUN_RED_FLAG_DETECTE"
