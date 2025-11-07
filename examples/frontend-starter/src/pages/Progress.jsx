import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Progress.css';

function Progress() {
  const { user } = useAuth();

  const { data: progress, isLoading } = useQuery({
    queryKey: ['progress', user?.id],
    queryFn: () => api.getProgress(user.id).then(res => res.data),
    enabled: !!user?.id,
  });

  if (isLoading) {
    return (
      <div className="progress">
        <LoadingSpinner message="Loading progress..." />
      </div>
    );
  }

  const progressData = progress?.data || {};

  return (
    <div className="progress">
      <h1>Your Progress</h1>
      
      <div className="progress-sections">
        <div className="progress-section">
          <h2>Goals</h2>
          {progressData.goals?.length > 0 ? (
            <ul>
              {progressData.goals.map((goal, idx) => (
                <li key={idx}>
                  <strong>{goal.title}</strong> - {goal.status}
                  {goal.completion_percentage && (
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${goal.completion_percentage}%` }}
                      />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>No goals yet. Create one to get started!</p>
          )}
        </div>

        <div className="progress-section">
          <h2>Recent Sessions</h2>
          {progressData.recent_sessions?.length > 0 ? (
            <ul>
              {progressData.recent_sessions.map((session, idx) => (
                <li key={idx}>
                  <strong>{session.subject}</strong> - {session.session_date}
                  <br />
                  Duration: {session.duration_minutes} minutes
                </li>
              ))}
            </ul>
          ) : (
            <p>No sessions yet.</p>
          )}
        </div>

        <div className="progress-section">
          <h2>Practice Statistics</h2>
          <div className="stats">
            <div className="stat">
              <strong>Completed:</strong> {progressData.practice_stats?.completed || 0}
            </div>
            <div className="stat">
              <strong>Average Score:</strong> {progressData.practice_stats?.average_score || 'N/A'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Progress;

