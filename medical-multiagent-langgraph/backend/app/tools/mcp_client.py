"""
MCP Client
----------
Client pour l'intégration des outils via le protocole MCP (Model Context Protocol).
Permet au DiagnosticAgent d'utiliser les outils exposés par le serveur MCP local.
"""
import asyncio
import json
import logging
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MCP_SERVER_URL = "http://localhost:8001"


class MCPPatientQueryInput(BaseModel):
    patient_id: str = Field(description="Identifiant de session patient")
    query_type: str = Field(
        description="Type de requête : antecedents, medicaments, allergies"
    )


@tool("mcp_patient_history", args_schema=MCPPatientQueryInput)
async def mcp_patient_history_tool(patient_id: str, query_type: str) -> str:
    """
    Outil MCP : consulte l'historique patient via le serveur MCP.
    Retourne les antécédents, médicaments ou allergies selon le type de requête.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/patient_history",
                json={"patient_id": patient_id, "query_type": query_type}
            )
            if response.status_code == 200:
                data = response.json()
                return json.dumps(data, ensure_ascii=False)
            else:
                return f"Erreur MCP : {response.status_code}"
    except Exception as e:
        logger.warning(f"MCP server indisponible : {e}")
        return "Données historique non disponibles (serveur MCP hors ligne)."


class MCPDrugCheckInput(BaseModel):
    medications: list[str] = Field(description="Liste des médicaments à vérifier")
    symptoms: list[str] = Field(description="Symptômes rapportés")


@tool("mcp_drug_interaction_check", args_schema=MCPDrugCheckInput)
async def mcp_drug_interaction_tool(medications: list[str], symptoms: list[str]) -> str:
    """
    Outil MCP : vérifie les interactions médicamenteuses potentielles.
    Utilise la base de données du serveur MCP.
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/tools/drug_interactions",
                json={"medications": medications, "symptoms": symptoms}
            )
            if response.status_code == 200:
                return response.json().get("result", "Aucune interaction détectée.")
            return "Vérification indisponible."
    except Exception as e:
        logger.warning(f"MCP drug check indisponible : {e}")
        return "Vérification des interactions non disponible (serveur MCP hors ligne)."


def get_mcp_tools():
    """Retourne la liste des outils MCP disponibles."""
    return [mcp_patient_history_tool, mcp_drug_interaction_tool]
