/**
 * Q&A Component Example
 * Submit queries and display AI responses
 */

import React, { useState } from 'react';
import apiClient from '../api-client/apiClient';

function QAComponent({ studentId }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await apiClient.submitQuery({
        student_id: studentId,
        query: query,
        context: {
          recent_sessions: ['Algebra', 'Chemistry'],
        },
      });

      setResponse(result.data);
    } catch (err) {
      setError(err.message || 'An error occurred');
      console.error('Q&A Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qa-component">
      <h2>Ask a Question</h2>
      
      <form onSubmit={handleSubmit}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="What would you like help with?"
          rows={4}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Asking...' : 'Ask Question'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {response && (
        <div className="qa-response">
          <div className="confidence-badge">
            Confidence: <span className={response.confidence.toLowerCase()}>
              {response.confidence}
            </span>
          </div>
          
          {response.clarification_requested && (
            <div className="clarification">
              <p>{response.answer}</p>
              {response.suggestions && (
                <ul>
                  {response.suggestions.map((suggestion, idx) => (
                    <li key={idx}>{suggestion}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {!response.clarification_requested && (
            <div className="answer">
              <p>{response.answer}</p>
            </div>
          )}

          {response.tutor_escalation_suggested && (
            <div className="escalation-notice">
              <strong>Note:</strong> Consider asking your tutor for help with this topic.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default QAComponent;

