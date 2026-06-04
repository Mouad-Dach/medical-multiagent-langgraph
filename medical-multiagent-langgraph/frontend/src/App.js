import React, { useState } from 'react';
import PatientForm from './components/PatientForm';
import QuestionnaireScreen from './components/QuestionnaireScreen';
import PhysicianReview from './components/PhysicianReview';
import FinalReport from './components/FinalReport';
import {
  startConsultation,
  resumeWithAnswer,
  resumeWithPhysician,
  getConsultation,
  getReport,
} from './services/api';
import './App.css';

const STEPS = {
  FORM: 'form',
  QUESTIONS: 'questions',
  PHYSICIAN: 'physician',
  REPORT: 'report',
};

export default function App() {
  const [step, setStep] = useState(STEPS.FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [threadId, setThreadId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [questionNumber, setQuestionNumber] = useState(1);
  const [diagnosticSummary, setDiagnosticSummary] = useState('');
  const [interimCare, setInterimCare] = useState('');
  const [finalReport, setFinalReport] = useState('');

  const handleError = (err) => {
    const msg = err.response?.data?.detail || err.message || 'Erreur inconnue';
    setError(msg);
    setLoading(false);
  };

  // Écran 1 → Démarrage consultation
  const handleStartConsultation = async (patientCase) => {
    setLoading(true);
    setError(null);
    try {
      const res = await startConsultation(patientCase);
      const { thread_id, next_question, question_number } = res.data;
      setThreadId(thread_id);
      setCurrentQuestion(next_question);
      setQuestionNumber(question_number);
      setStep(STEPS.QUESTIONS);
    } catch (err) { handleError(err); }
    finally { setLoading(false); }
  };

  // Écran 2 → Réponse patient
  const handlePatientAnswer = async (answer) => {
    setLoading(true);
    setError(null);
    try {
      const res = await resumeWithAnswer(threadId, answer);
      const data = res.data;

      if (data.status === 'awaiting_physician_review') {
        setDiagnosticSummary(data.diagnostic_summary || '');
        setInterimCare(data.interim_care || '');
        setStep(STEPS.PHYSICIAN);
      } else if (data.next_question) {
        setCurrentQuestion(data.next_question);
        setQuestionNumber(data.question_number);
      }
    } catch (err) { handleError(err); }
    finally { setLoading(false); }
  };

  // Écran 3 → Revue médecin
  const handlePhysicianReview = async (treatment) => {
    setLoading(true);
    setError(null);
    try {
      await resumeWithPhysician(threadId, treatment);
      // Récupérer le rapport final
      const reportRes = await getReport(threadId);
      setFinalReport(reportRes.data.final_report);
      setStep(STEPS.REPORT);
    } catch (err) { handleError(err); }
    finally { setLoading(false); }
  };

  const handleNewConsultation = () => {
    setStep(STEPS.FORM);
    setThreadId(null);
    setCurrentQuestion('');
    setQuestionNumber(1);
    setDiagnosticSummary('');
    setInterimCare('');
    setFinalReport('');
    setError(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏥 Système d'Orientation Clinique Préliminaire</h1>
        <div className="step-indicator">
          {['Cas patient', 'Questions', 'Médecin', 'Rapport'].map((label, i) => {
            const stepKeys = [STEPS.FORM, STEPS.QUESTIONS, STEPS.PHYSICIAN, STEPS.REPORT];
            const active = step === stepKeys[i];
            const done = stepKeys.indexOf(step) > i;
            return (
              <div key={label} className={`step ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
                <span>{i + 1}</span> {label}
              </div>
            );
          })}
        </div>
      </header>

      {error && (
        <div className="error-banner">
          ❌ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      <main>
        {step === STEPS.FORM && (
          <PatientForm onSubmit={handleStartConsultation} loading={loading} />
        )}
        {step === STEPS.QUESTIONS && (
          <QuestionnaireScreen
            currentQuestion={currentQuestion}
            questionNumber={questionNumber}
            onAnswer={handlePatientAnswer}
            loading={loading}
          />
        )}
        {step === STEPS.PHYSICIAN && (
          <PhysicianReview
            diagnosticSummary={diagnosticSummary}
            interimCare={interimCare}
            onSubmit={handlePhysicianReview}
            loading={loading}
          />
        )}
        {step === STEPS.REPORT && (
          <FinalReport
            report={finalReport}
            threadId={threadId}
            onNewConsultation={handleNewConsultation}
          />
        )}
      </main>

      <footer>
        <p>⚕️ Ce système est un exercice académique et ne remplace pas une consultation médicale.</p>
      </footer>
    </div>
  );
}
