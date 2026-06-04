"""
FastAPI Application — API d'orientation clinique multi-agents
-------------------------------------------------------------
Endpoints :
  POST /sessions/start              → Créer une nouvelle session
  POST /consultation/start          → Démarrer une consultation
  POST /consultation/resume         → Reprendre après Human-in-the-Loop
  GET  /consultation/{thread_id}    → État courant d'une consultation
  GET  /consultation/{thread_id}/report → Rapport final
"""
import uuid
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.graph import medical_graph
from app.state import MedicalState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Système Multi-Agents d'Orientation Clinique",
    description=(
        "API pour le workflow d'orientation clinique préliminaire basé sur LangGraph. "
        "Ce système ne remplace pas une consultation médicale."
    ),
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schémas Pydantic ──────────────────────────────────────────────────────────
class StartSessionResponse(BaseModel):
    session_id: str
    message: str


class StartConsultationRequest(BaseModel):
    session_id: Optional[str] = None
    patient_initial_case: str


class StartConsultationResponse(BaseModel):
    thread_id: str
    status: str
    next_question: Optional[str] = None
    question_number: Optional[int] = None
    message: str


class ResumeConsultationRequest(BaseModel):
    """
    Corps pour la reprise après interruption.
    - patient_answer : réponse du patient à la question courante
    - physician_treatment : conduite à tenir (uniquement pour l'étape médecin)
    """
    patient_answer: Optional[str] = None
    physician_treatment: Optional[str] = None


class ConsultationStateResponse(BaseModel):
    thread_id: str
    status: str
    question_count: int
    has_diagnostic_summary: bool
    has_interim_care: bool
    has_physician_treatment: bool
    has_final_report: bool
    current_question: Optional[str] = None
    interim_care: Optional[str] = None
    diagnostic_summary: Optional[str] = None


class FinalReportResponse(BaseModel):
    thread_id: str
    final_report: str
    disclaimer: str = "Ce système ne remplace pas une consultation médicale."


# ── Helpers ───────────────────────────────────────────────────────────────────
CLINICAL_QUESTIONS = [
    "Depuis combien de temps ressentez-vous ces symptômes ?",
    "Pouvez-vous décrire précisément la nature et la localisation de vos symptômes ?",
    "Avez-vous de la fièvre, des frissons ou d'autres signes généraux associés ?",
    "Avez-vous des antécédents médicaux importants ou prenez-vous des médicaments en cours ?",
    "Ces symptômes vous ont-ils déjà affecté(e) par le passé, et si oui, comment ont-ils évolué ?"
]


def get_graph_state(thread_id: str) -> MedicalState:
    """Récupère l'état courant du graphe pour un thread donné."""
    config = {"configurable": {"thread_id": thread_id}}
    state = medical_graph.get_state(config)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Session {thread_id} introuvable.")
    return state.values


def get_graph_status(state: MedicalState) -> str:
    """Détermine le statut lisible de la consultation."""
    if state.get("final_report"):
        return "completed"
    if state.get("physician_treatment"):
        return "generating_report"
    if state.get("diagnostic_summary"):
        return "awaiting_physician_review"
    question_count = state.get("question_count", 0)
    if question_count >= 5:
        return "analyzing"
    if question_count > 0:
        return "questioning"
    return "started"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Système Multi-Agents d'Orientation Clinique",
        "version": "1.0.0",
        "disclaimer": "Ce système ne remplace pas une consultation médicale.",
    }


@app.post("/sessions/start", response_model=StartSessionResponse, tags=["Sessions"])
def start_session():
    """Crée une nouvelle session (thread_id unique)."""
    session_id = str(uuid.uuid4())
    return StartSessionResponse(
        session_id=session_id,
        message=f"Session créée. Utilisez ce session_id pour démarrer une consultation."
    )


@app.post("/consultation/start", response_model=StartConsultationResponse, tags=["Consultation"])
def start_consultation(request: StartConsultationRequest):
    """
    Démarre une nouvelle consultation.
    Initialise l'état et déclenche le Supervisor → DiagnosticAgent → première question.
    """
    thread_id = request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: MedicalState = {
        "messages": [],
        "patient_initial_case": request.patient_initial_case,
        "patient_answers": [],
        "question_count": 0,
        "session_id": thread_id,
    }

    try:
        # Lancer le graphe — s'arrêtera à la 1ère question ou à physician_review
        for event in medical_graph.stream(initial_state, config, stream_mode="values"):
            pass  # On consomme le stream jusqu'à l'interruption

        state = get_graph_state(thread_id)
        question_count = state.get("question_count", 0)

        return StartConsultationResponse(
            thread_id=thread_id,
            status="questioning",
            next_question=CLINICAL_QUESTIONS[question_count] if question_count < 5 else None,
            question_number=question_count + 1 if question_count < 5 else None,
            message=f"Consultation démarrée. Question {question_count + 1}/5 posée."
        )
    except Exception as e:
        logger.error(f"Erreur démarrage consultation : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultation/resume", tags=["Consultation"])
def resume_consultation(thread_id: str, request: ResumeConsultationRequest):
    """
    Reprend la consultation après une interruption (réponse patient ou revue médecin).
    
    - Si patient_answer est fourni : enregistre la réponse et pose la question suivante.
    - Si physician_treatment est fourni : reprend après la revue médecin.
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = get_graph_state(thread_id)
        question_count = state.get("question_count", 0)
        patient_answers = list(state.get("patient_answers", []))

        # ── Cas 1 : Réponse patient ───────────────────────────────────────────
        if request.patient_answer is not None:
            if question_count >= 5:
                raise HTTPException(
                    status_code=400,
                    detail="Toutes les questions ont déjà été répondues."
                )

            patient_answers.append(request.patient_answer)
            new_count = question_count + 1

            # Mettre à jour l'état et reprendre
            update = {
                "patient_answers": patient_answers,
                "question_count": new_count,
            }
            medical_graph.update_state(config, update)

            # Reprendre le graphe
            for event in medical_graph.stream(None, config, stream_mode="values"):
                pass

            updated_state = get_graph_state(thread_id)
            status = get_graph_status(updated_state)

            response = {
                "thread_id": thread_id,
                "status": status,
                "question_count": new_count,
                "message": f"Réponse {new_count}/5 enregistrée."
            }

            if new_count < 5:
                response["next_question"] = CLINICAL_QUESTIONS[new_count]
                response["question_number"] = new_count + 1
            elif status == "awaiting_physician_review":
                response["diagnostic_summary"] = updated_state.get("diagnostic_summary")
                response["interim_care"] = updated_state.get("interim_care")
                response["message"] = "Questions complètes. En attente de la revue du médecin."

            return response

        # ── Cas 2 : Revue médecin ─────────────────────────────────────────────
        elif request.physician_treatment is not None:
            if not state.get("diagnostic_summary"):
                raise HTTPException(
                    status_code=400,
                    detail="La synthèse clinique n'est pas encore disponible."
                )

            update = {"physician_treatment": request.physician_treatment}
            medical_graph.update_state(config, update, as_node="physician_review")

            # Reprendre après physician_review
            for event in medical_graph.stream(None, config, stream_mode="values"):
                pass

            updated_state = get_graph_state(thread_id)
            return {
                "thread_id": thread_id,
                "status": get_graph_status(updated_state),
                "message": "Revue médecin enregistrée. Rapport final en cours de génération.",
                "has_final_report": bool(updated_state.get("final_report"))
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Fournir patient_answer ou physician_treatment."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur reprise consultation {thread_id} : {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}", response_model=ConsultationStateResponse, tags=["Consultation"])
def get_consultation(thread_id: str):
    """Retourne l'état courant d'une consultation."""
    state = get_graph_state(thread_id)
    question_count = state.get("question_count", 0)

    return ConsultationStateResponse(
        thread_id=thread_id,
        status=get_graph_status(state),
        question_count=question_count,
        has_diagnostic_summary=bool(state.get("diagnostic_summary")),
        has_interim_care=bool(state.get("interim_care")),
        has_physician_treatment=bool(state.get("physician_treatment")),
        has_final_report=bool(state.get("final_report")),
        current_question=CLINICAL_QUESTIONS[question_count] if question_count < 5 else None,
        interim_care=state.get("interim_care"),
        diagnostic_summary=state.get("diagnostic_summary"),
    )


@app.get("/consultation/{thread_id}/report", response_model=FinalReportResponse, tags=["Consultation"])
def get_report(thread_id: str):
    """Retourne le rapport final d'une consultation terminée."""
    state = get_graph_state(thread_id)
    final_report = state.get("final_report")

    if not final_report:
        raise HTTPException(
            status_code=404,
            detail="Le rapport final n'est pas encore disponible."
        )

    return FinalReportResponse(
        thread_id=thread_id,
        final_report=final_report,
    )
