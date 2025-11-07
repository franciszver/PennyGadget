/**
 * Progress Dashboard Component Example
 * Display student goals and progress
 */

import React, { useState, useEffect } from 'react';
import apiClient from '../api-client/apiClient';

function ProgressDashboard({ userId }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProgress();
  }, [userId]);

  const loadProgress = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiClient.getProgress(userId, true);
      setData(result.data);
    } catch (err) {
      setError(err.message || 'Failed to load progress');
      console.error('Progress Error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div>Loading progress...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!data) {
    return null;
  }

  // Handle empty state
  if (data.empty_state) {
    return (
      <div className="progress-dashboard empty-state">
        <h2>Welcome!</h2>
        <p>{data.suggestions[0]?.message}</p>
        {data.suggestions[0]?.suggested_subjects && (
          <div>
            <p>Suggested subjects to get started:</p>
            <ul>
              {data.suggestions[0].suggested_subjects.map((subject, idx) => (
                <li key={idx}>{subject}</li>
              ))}
            </ul>
          </div>
        )}
        {data.disclaimer_required && data.disclaimer && (
          <div className="disclaimer">
            <p>{data.disclaimer.message}</p>
            <button onClick={() => {/* Acknowledge disclaimer */}}>
              I Understand
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="progress-dashboard">
      <h2>Your Progress</h2>

      {/* Insights */}
      {data.insights && data.insights.length > 0 && (
        <div className="insights">
          {data.insights.map((insight, idx) => (
            <div key={idx} className="insight">{insight}</div>
          ))}
        </div>
      )}

      {/* Goals */}
      <div className="goals">
        <h3>Active Goals</h3>
        {data.goals.map((goal) => (
          <div key={goal.goal_id} className="goal-card">
            <h4>{goal.title}</h4>
            <p>{goal.subject}</p>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${goal.completion_percentage}%` }}
              />
            </div>
            <p>{goal.completion_percentage}% Complete</p>
            <p>Streak: {goal.current_streak} days</p>
            <p>XP: {goal.xp_earned}</p>
          </div>
        ))}
      </div>

      {/* Suggestions */}
      {data.suggestions && data.suggestions.length > 0 && (
        <div className="suggestions">
          <h3>Suggestions</h3>
          {data.suggestions.map((suggestion, idx) => (
            <div key={idx} className="suggestion-card">
              <p>{suggestion.message}</p>
              {suggestion.subjects && (
                <ul>
                  {suggestion.subjects.map((subject, subIdx) => (
                    <li key={subIdx}>{subject}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      {data.stats && (
        <div className="stats">
          <p>Total Goals: {data.stats.total_goals}</p>
          <p>Completed: {data.stats.completed_goals}</p>
          <p>Average Completion: {data.stats.average_completion.toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}

export default ProgressDashboard;

