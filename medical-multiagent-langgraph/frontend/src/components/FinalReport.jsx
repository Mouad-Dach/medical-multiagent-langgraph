import React from 'react';
import ReactMarkdown from 'react-markdown';

export default function FinalReport({ report, threadId, onNewConsultation }) {
  const handlePrint = () => window.print();

  return (
    <div className="screen">
      <div className="card">
        <div className="report-header">
          <h2>📄 Rapport Final d'Orientation Clinique</h2>
          <p className="session-id">Session : {threadId}</p>
        </div>

        <div className="report-body">
          <ReactMarkdown>{report}</ReactMarkdown>
        </div>

        <div className="disclaimer final">
          ⚕️ <strong>Ce système ne remplace pas une consultation médicale.</strong>
        </div>

        <div className="btn-group">
          <button onClick={handlePrint} className="btn-secondary">🖨️ Imprimer</button>
          <button onClick={onNewConsultation} className="btn-primary">+ Nouvelle consultation</button>
        </div>
      </div>
    </div>
  );
}
