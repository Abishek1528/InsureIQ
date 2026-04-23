import React, { useState } from 'react';
import './App.css';
import InsuranceForm from './components/InsuranceForm';
import ResultsDisplay from './components/ResultsDisplay';
import ChatInterface from './components/ChatInterface';
import { getRecommendation } from './services/api';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const handleFormSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setSessionId(null);

    try {
      const data = await getRecommendation(formData);
      setResults(data);
      // The updated API returns both the data and the session_id
      setSessionId(data.session_id);
    } catch (err) {
      setError(err.message || 'Something went wrong while fetching recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>InsureIQ</h1>
        <p>AI-Powered Personalized Insurance Recommendations</p>
      </header>

      <main>
        <InsuranceForm onSubmit={handleFormSubmit} loading={loading} />

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {results && <ResultsDisplay data={results} />}
      </main>

      {/* Floating Chat Assistant */}
      {sessionId && <ChatInterface sessionId={sessionId} />}
    </div>
  );
}

export default App;
