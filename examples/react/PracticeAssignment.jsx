/**
 * Practice Assignment Component Example
 * Request and complete practice items
 */

import React, { useState } from 'react';
import apiClient from '../api-client/apiClient';

function PracticeAssignment({ studentId }) {
  const [subject, setSubject] = useState('');
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState(null);
  const [error, setError] = useState(null);

  const handleRequest = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setItems(null);

    try {
      const result = await apiClient.assignPractice(studentId, subject, {
        num_items: 5,
      });

      setItems(result.data.items);
      
      if (result.data.adaptive_metadata?.all_ai_generated) {
        // Show message about AI-generated items
        console.log('All items are AI-generated and flagged for review');
      }
    } catch (err) {
      setError(err.message || 'Failed to assign practice');
      console.error('Practice Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (itemId, assignmentId, isCorrect, timeTaken, hintsUsed) => {
    try {
      const result = await apiClient.completePractice(assignmentId, itemId, {
        student_answer: 'user answer',
        correct: isCorrect,
        time_taken_seconds: timeTaken,
        hints_used: hintsUsed,
      });

      // Update UI with performance feedback
      console.log('Performance Score:', result.data.performance_score);
      console.log('Rating Change:', result.data.student_rating_after - result.data.student_rating_before);
    } catch (err) {
      console.error('Complete Practice Error:', err);
    }
  };

  return (
    <div className="practice-assignment">
      <h2>Practice Assignment</h2>

      <form onSubmit={handleRequest}>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Subject (e.g., Algebra)"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !subject.trim()}>
          {loading ? 'Loading...' : 'Get Practice Items'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {items && (
        <div className="practice-items">
          {items.map((item) => (
            <div key={item.item_id} className="practice-item">
              <div className="item-header">
                <span className="source-badge">{item.source}</span>
                {item.flagged && <span className="flagged-badge">Flagged for Review</span>}
                <span className="difficulty">Difficulty: {item.difficulty}</span>
              </div>

              <div className="question">
                <h4>Question:</h4>
                <p>{item.question}</p>
              </div>

              <div className="answer-section">
                <button onClick={() => {/* Show answer */}}>Show Answer</button>
                <div className="answer" style={{ display: 'none' }}>
                  <h4>Answer:</h4>
                  <p>{item.answer}</p>
                  {item.explanation && (
                    <div className="explanation">
                      <h4>Explanation:</h4>
                      <p>{item.explanation}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="completion">
                <button
                  onClick={() =>
                    handleComplete(item.item_id, item.item_id, true, 60, 0)
                  }
                >
                  Mark Correct
                </button>
                <button
                  onClick={() =>
                    handleComplete(item.item_id, item.item_id, false, 120, 2)
                  }
                >
                  Mark Incorrect
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PracticeAssignment;

