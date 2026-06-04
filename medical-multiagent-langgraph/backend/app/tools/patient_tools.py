"""
Patient Tools
-------------
Outils LangChain utilisés par le DiagnosticAgent pour interagir avec le patient.
Ces tools sont également exposés via MCP (voir mcp_client.py).
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class AskPatientInput(BaseModel):
    question: str = Field(description="La question clinique à poser au patient")
    question_number: int = Field(description="Le numéro de la question (1 à 5)", ge=1, le=5)


@tool("ask_patient", args_schema=AskPatientInput)
def ask_patient_tool(question: str, question_number: int) -> str:
    """
    Outil pour poser une question clinique au patient.
    Retourne un marqueur indiquant que la question a été enregistrée
    et qu'une réponse est attendue via l'interface utilisateur.
    
    Dans le workflow LangGraph, cet outil déclenche une interruption
    pour recueillir la réponse du patient via l'API.
    """
    return (
        f"QUESTION_POSEE|{question_number}|{question}|"
        f"En attente de la réponse du patient pour la question {question_number}/5."
    )


class RecordAnswerInput(BaseModel):
    question_number: int = Field(description="Numéro de la question (1-5)", ge=1, le=5)
    answer: str = Field(description="Réponse fournie par le patient")


@tool("record_patient_answer", args_schema=RecordAnswerInput)
def record_patient_answer_tool(question_number: int, answer: str) -> str:
    """
    Outil pour enregistrer la réponse d'un patient à une question clinique.
    """
    return f"REPONSE_ENREGISTREE|{question_number}|{answer}"
