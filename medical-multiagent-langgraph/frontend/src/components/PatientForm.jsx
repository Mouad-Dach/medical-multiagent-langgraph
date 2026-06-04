import React, { useState } from 'react';

export default function PatientForm({ onSubmit, loading }) {
  const [patientCase, setPatientCase] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (patientCase.trim()) onSubmit(patientCase.trim());
  };

  return (
    <div className="screen">
      <div className="card">
        <h2>🏥 Orientation Clinique Préliminaire</h2>
        <p className="subtitle">
          Décrivez votre situation médicale initiale. Un agent clinique vous posera
          ensuite 5 questions pour affiner l'orientation.
        </p>
        <div className="disclaimer">
          ⚕️ Ce système ne remplace pas une consultation médicale.
        </div>
        <form onSubmit={handleSubmit}>
          <label htmlFor="case">Description de votre cas</label>
          <textarea
            id="case"
            rows={5}
            placeholder="Ex: Je ressens des douleurs thoraciques depuis ce matin accompagnées d'une légère fièvre..."
            value={patientCase}
            onChange={e => setPatientCase(e.target.value)}
            required
          />
          <button type="submit" disabled={loading || !patientCase.trim()} className="btn-primary">
            {loading ? 'Démarrage...' : 'Démarrer la consultation →'}
          </button>
        </form>
      </div>
    </div>
  );
}
