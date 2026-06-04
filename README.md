# 🏥 Système Multi-Agents d'Orientation Clinique Préliminaire

> Projet académique — Pr. Mohamed YOUSSFI  
> **Ce système ne remplace pas une consultation médicale.**

Système multi-agents basé sur **LangGraph** simulant un workflow d'orientation clinique préliminaire. Le système recueille les informations patient via 5 questions cliniques, produit une synthèse préliminaire, intègre la validation d'un médecin traitant (Human-in-the-Loop), et génère un rapport final structuré.

---

## 📁 Structure du projet

```
medical-multiagent-langgraph/
├── backend/
│   ├── app/
│   │   ├── graph.py              # Graphe LangGraph principal
│   │   ├── state.py              # État partagé MedicalState
│   │   ├── api.py                # Application FastAPI
│   │   ├── nodes/
│   │   │   ├── supervisor.py     # Agent Supervisor
│   │   │   ├── diagnostic_agent.py  # Agent Diagnostic
│   │   │   ├── physician_review.py  # Human-in-the-Loop
│   │   │   └── report_agent.py   # Agent Rapport
│   │   └── tools/
│   │       ├── patient_tools.py  # Outils interaction patient
│   │       ├── care_tools.py     # Outils recommandations soins
│   │       └── mcp_client.py     # Client MCP
│   ├── main.py                   # Point d'entrée FastAPI
│   ├── langgraph.json            # Config LangGraph Studio
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── mcp_server/
│   ├── server.py                 # Serveur MCP
│   └── data/
│       ├── drug_interactions.json
│       └── symptom_protocols.json
├── frontend/
│   ├── src/
│   │   ├── App.js                # Application principale
│   │   ├── App.css
│   │   ├── components/
│   │   │   ├── PatientForm.jsx       # Écran 1 : Cas initial
│   │   │   ├── QuestionnaireScreen.jsx  # Écran 2 : Questions
│   │   │   ├── PhysicianReview.jsx   # Écran 3 : Revue médecin
│   │   │   └── FinalReport.jsx       # Écran 4 : Rapport final
│   │   └── services/api.js       # Appels API
│   ├── public/index.html
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Installation et démarrage

### Prérequis
- Python 3.11+
- Node.js 20+
- Clé API OpenAI
- (Optionnel) Docker & Docker Compose

---

### 1. Cloner le dépôt

```bash
git clone https://github.com/VOTRE_USERNAME/medical-multiagent-langgraph.git
cd medical-multiagent-langgraph
```

---

### 2. Backend

```bash
cd backend

# Créer et activer l'environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/macOS
# ou : venv\Scripts\activate    # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env et renseigner OPENAI_API_KEY=sk-...

# Lancer le backend
uvicorn main:app --reload --port 8000
```

L'API sera disponible sur : http://localhost:8000  
Documentation Swagger : http://localhost:8000/docs

---

### 3. Serveur MCP

Dans un nouveau terminal :

```bash
cd mcp_server
pip install fastapi uvicorn httpx
python server.py
```

Le serveur MCP sera disponible sur : http://localhost:8001

---

### 4. Frontend React

Dans un nouveau terminal :

```bash
cd frontend
npm install
npm start
```

L'interface sera disponible sur : http://localhost:3000

---

### 5. Démarrage avec Docker Compose (optionnel)

```bash
# À la racine du projet
cp backend/.env.example .env
# Éditer .env avec votre OPENAI_API_KEY

docker-compose up --build
```

---

## 🧪 Test dans LangGraph Studio

1. Installer LangGraph Studio (https://github.com/langchain-ai/langgraph-studio)
2. Ouvrir le dossier `backend/` dans LangGraph Studio
3. LangGraph Studio lira automatiquement `langgraph.json`
4. Le graphe `medical_graph` sera visualisé avec les nœuds :
   - `supervisor` → `diagnostic_agent` → `physician_review` → `report_agent`
5. Tester l'interruption Human-in-the-Loop sur le nœud `physician_review`

---

## 🔌 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/sessions/start` | Créer une nouvelle session |
| POST | `/consultation/start` | Démarrer une consultation |
| POST | `/consultation/resume?thread_id={id}` | Reprendre (réponse patient ou médecin) |
| GET | `/consultation/{thread_id}` | État courant |
| GET | `/consultation/{thread_id}/report` | Rapport final |

### Exemple de flux complet

```bash
# 1. Démarrer une consultation
curl -X POST http://localhost:8000/consultation/start \
  -H "Content-Type: application/json" \
  -d '{"patient_initial_case": "J'ai de la fièvre depuis 2 jours et une toux sèche."}'

# 2. Répondre aux questions (répéter 5 fois)
curl -X POST "http://localhost:8000/consultation/resume?thread_id=THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"patient_answer": "Depuis hier soir, environ 38.5°C"}'

# 3. Revue médecin
curl -X POST "http://localhost:8000/consultation/resume?thread_id=THREAD_ID" \
  -H "Content-Type: application/json" \
  -d '{"physician_treatment": "Repos, paracétamol 1g/8h, contrôle dans 48h si pas d amelioration."}'

# 4. Récupérer le rapport
curl http://localhost:8000/consultation/THREAD_ID/report
```

---

## 🧩 Workflow du graphe

```
START
  │
  ▼
Supervisor ──────────────────────────────────┐
  │                                           │
  ▼                                           │
DiagnosticAgent                               │
  │  ├─ Tool: ask_patient (boucle ×5)         │
  │  └─ Tool: recommend_interim_care          │
  │                                           │
  ▼ (retour Supervisor)                       │
Supervisor                                    │
  │                                           │
  ▼                                           │
PhysicianReview ← [INTERRUPTION HiTL]         │
  │                                           │
  ▼ (retour Supervisor)                       │
Supervisor                                    │
  │                                           │
  ▼                                           │
ReportAgent                                   │
  │                                           │
  ▼ (retour Supervisor)                       │
END ◄────────────────────────────────────────┘
```

---

## 🧪 Jeux de tests

### Cas 1 — Syndrome respiratoire simple
- Cas initial : *"Toux et légère fièvre depuis 3 jours"*
- Réponses : symptômes légers, pas d'antécédents majeurs
- Résultat attendu : recommandation repos + hydratation

### Cas 2 — Cas avec red flags
- Cas initial : *"Douleur thoracique intense avec difficultés respiratoires"*
- Résultat attendu : red flags détectés, orientation urgente

### Cas 3 — Cas bénin
- Cas initial : *"Légères courbatures et fatigue depuis hier soir"*
- Résultat attendu : recommandation repos, surveillance

---

## 📊 Critères d'évaluation couverts

| Critère | Couvert |
|---------|---------|
| Architecture LangGraph | ✅ Supervisor + 3 agents |
| Agents & Tools | ✅ ask_patient, recommend_interim_care, MCP |
| Human-in-the-Loop | ✅ interrupt_before physician_review |
| FastAPI | ✅ 5 endpoints requis |
| Frontend React | ✅ 4 écrans requis |
| MCP | ✅ Serveur MCP + client intégré |
| LangGraph Studio | ✅ langgraph.json configuré |
| Docker | ✅ docker-compose.yml |

---

## ⚠️ Avertissement éthique

Ce projet est un **exercice académique**. Il ne constitue pas un dispositif médical. Il ne fournit pas de diagnostic définitif. Tout rapport généré mentionne explicitement : **"Ce système ne remplace pas une consultation médicale."**

---

## 👤 Auteur

Mouad Dach
