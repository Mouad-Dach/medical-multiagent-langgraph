import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

export default function PhysicianReview({ diagnosticSummary, interimCare, onSubmit, loading }) {
  const [treatment, setTreatment] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (treatment.trim()) onSubmit(treatment.trim());
  };

  return (
    <div className="screen">
      <div className="card">
        <h2>👨‍⚕️ Revue du Médecin Traitant</h2>
        <p className="subtitle">
          Veuillez examiner la synthèse clinique et proposer votre conduite à tenir.
        </p>

        <div className="section">
          <h3>📋 Synthèse Clinique Préliminaire</h3>
          <div className="summary-box">
            <ReactMarkdown>{diagnosticSummary}</ReactMarkdown>
          </div>
        </div>

        <div className="section">
          <h3>💊 Recommandation Intermédiaire</h3>
          <div className="care-box">
            <p style={{ whiteSpace: 'pre-line' }}>{interimCare}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="treatment">Conduite à tenir / Traitement proposé</label>
          <textarea
            id="treatment"
            rows={5}
            placeholder="Décrivez votre diagnostic, le traitement prescrit et les recommandations au patient..."
            value={treatment}
            onChange={e => setTreatment(e.target.value)}
            required
          />
          <button type="submit" disabled={loading || !treatment.trim()} className="btn-primary">
            {loading ? 'Génération du rapport...' : 'Valider et générer le rapport →'}
          </button>
        </form>
      </div>
    </div>
  );
}
