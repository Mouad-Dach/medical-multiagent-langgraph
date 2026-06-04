"""
Serveur MCP (Model Context Protocol)
--------------------------------------
Expose des outils médicaux via le protocole MCP pour être utilisés
par les agents LangGraph.

Lancer avec : python server.py
Port par défaut : 8001
"""
import json
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Medical Tools Server",
    description="Serveur MCP exposant des outils médicaux pour le système multi-agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Chargement des données de référence ───────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"

def load_json(filename: str) -> dict:
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}

DRUG_INTERACTIONS_DB = load_json("drug_interactions.json")
SYMPTOM_PROTOCOLS_DB = load_json("symptom_protocols.json")


# ── Schémas ───────────────────────────────────────────────────────────────────
class PatientHistoryRequest(BaseModel):
    patient_id: str
    query_type: str  # antecedents | medicaments | allergies


class DrugInteractionRequest(BaseModel):
    medications: list[str]
    symptoms: list[str]


class SymptomProtocolRequest(BaseModel):
    symptoms: list[str]
    age_range: Optional[str] = "adulte"


# ── Endpoints MCP ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"service": "MCP Medical Tools Server", "version": "1.0.0"}


@app.get("/tools", tags=["MCP"])
def list_tools():
    """Liste les outils disponibles sur ce serveur MCP."""
    return {
        "tools": [
            {
                "name": "patient_history",
                "description": "Consulte l'historique médical d'un patient",
                "endpoint": "/tools/patient_history"
            },
            {
                "name": "drug_interactions",
                "description": "Vérifie les interactions médicamenteuses",
                "endpoint": "/tools/drug_interactions"
            },
            {
                "name": "symptom_protocol",
                "description": "Retourne le protocole de prise en charge pour des symptômes",
                "endpoint": "/tools/symptom_protocol"
            }
        ]
    }


@app.post("/tools/patient_history", tags=["MCP Tools"])
def get_patient_history(request: PatientHistoryRequest):
    """
    Outil MCP : retourne l'historique médical simulé d'un patient.
    Dans un système réel, ceci interrogerait un DPI (Dossier Patient Informatisé).
    """
    # Données simulées pour le projet académique
    mock_data = {
        "antecedents": {
            "result": "Antécédents : Hypertension artérielle (2018), Allergie à la pénicilline",
            "source": "DPI simulé"
        },
        "medicaments": {
            "result": "Médicaments en cours : Amlodipine 5mg/j",
            "source": "DPI simulé"
        },
        "allergies": {
            "result": "Allergies connues : Pénicilline (urticaire), Aspirine (intolérance)",
            "source": "DPI simulé"
        }
    }
    
    query_type = request.query_type.lower()
    if query_type in mock_data:
        return mock_data[query_type]
    return {"result": "Information non disponible", "source": "DPI simulé"}


@app.post("/tools/drug_interactions", tags=["MCP Tools"])
def check_drug_interactions(request: DrugInteractionRequest):
    """
    Outil MCP : vérifie les interactions médicamenteuses potentielles.
    """
    medications_lower = [m.lower() for m in request.medications]
    
    # Vérification simple basée sur la base de données locale
    interactions = []
    for med in medications_lower:
        if med in DRUG_INTERACTIONS_DB:
            interactions.append(DRUG_INTERACTIONS_DB[med])
    
    if interactions:
        return {
            "result": f"Interactions potentielles détectées : {'; '.join(interactions)}",
            "warning": True
        }
    return {
        "result": "Aucune interaction médicamenteuse majeure détectée dans notre base.",
        "warning": False
    }


@app.post("/tools/symptom_protocol", tags=["MCP Tools"])
def get_symptom_protocol(request: SymptomProtocolRequest):
    """
    Outil MCP : retourne le protocole de prise en charge pour des symptômes donnés.
    """
    symptoms_lower = [s.lower() for s in request.symptoms]
    
    protocols = []
    for symptom in symptoms_lower:
        for key, protocol in SYMPTOM_PROTOCOLS_DB.items():
            if key in symptom:
                protocols.append(protocol)
    
    if protocols:
        return {
            "result": " | ".join(set(protocols)),
            "source": "Protocoles cliniques simulés"
        }
    return {
        "result": "Protocole standard : surveillance clinique, repos, hydratation. Consulter si aggravation.",
        "source": "Protocole par défaut"
    }


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)
