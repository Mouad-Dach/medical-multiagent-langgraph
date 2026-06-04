import React, { useState } from 'react';

export default function QuestionnaireScreen({ currentQuestion, questionNumber, onAnswer, loading }) {
  const [answer, setAnswer] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (answer.trim()) {
      onAnswer(answer.trim());
      setAnswer('');
    }
  };

  return (
    <div className="screen">
      <div className="card">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${(questionNumber / 5) * 100}%` }} />
        </div>
        <p className="progress-label">Question {questionNumber} / 5</p>

        <h2>🩺 Questions cliniques</h2>
        <div className="question-box">
          <p>{currentQuestion}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <label htmlFor="answer">Votre réponse</label>
          <textarea
            id="answer"
            rows={4}
            placeholder="Décrivez précisément..."
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            required
          />
          <button type="submit" disabled={loading || !answer.trim()} className="btn-primary">
            {loading ? 'Enregistrement...' : questionNumber < 5 ? 'Suivant →' : 'Terminer les questions →'}
          </button>
        </form>
      </div>
    </div>
  );
}
