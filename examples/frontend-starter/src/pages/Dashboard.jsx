import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Dashboard.css';

function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: progress, isLoading: progressLoading, error: progressError } = useQuery({
    queryKey: ['progress', user?.id],
    queryFn: () => {
      console.log('[DASHBOARD] Fetching progress for user:', user.id);
      return api.getProgress(user.id).then(res => {
        console.log('[DASHBOARD] Progress response:', res.data);
        return res.data;
      });
    },
    enabled: !!user?.id,
    retry: false, // Don't retry on error in development
    onError: (error) => {
      console.error('[DASHBOARD] Progress API error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        userId: user?.id
      });
    }
  });

  const { data: nudgesData, isLoading: nudgesLoading } = useQuery({
    queryKey: ['nudges', user?.id],
    queryFn: () => {
      console.log('[DASHBOARD] Fetching nudges for user:', user.id);
      return api.getNudges(user.id).then(res => {
        console.log('[DASHBOARD] Nudges response:', res.data);
        return res.data;
      });
    },
    enabled: !!user?.id,
    retry: false,
    onError: (error) => {
      console.error('[DASHBOARD] Nudges API error:', error);
    }
  });

  if (progressLoading || nudgesLoading) {
    return (
      <div className="dashboard">
        <LoadingSpinner message="Loading dashboard..." />
      </div>
    );
  }

  const nudges = nudgesData?.data?.nudges || [];
  // Backend returns 'type' not 'nudge_type'
  const inactivityNudge = nudges.find(n => n.type === 'inactivity');
  const otherNudges = nudges.filter(n => n.type !== 'inactivity');

  return (
    <div className="dashboard">
      <h1>Welcome to AI Study Companion</h1>
      
      {progressError && (
        <div style={{ 
          background: '#fff3cd', 
          padding: '1rem', 
          marginBottom: '1rem', 
          borderRadius: '4px',
          border: '1px solid #ffc107'
        }}>
          <strong>Note:</strong> API calls are failing (expected in development with mock authentication). 
          The backend needs to be running and configured for API calls to work.
        </div>
      )}

      {/* Inactivity Nudge - Prominent Display */}
      {inactivityNudge && (
        <div className="nudge-card inactivity-nudge">
          <div className="nudge-header">
            <span className="nudge-icon">🔔</span>
            <h3>Important Notice</h3>
          </div>
          <p className="nudge-message">{inactivityNudge.message}</p>
          {inactivityNudge.suggestions && inactivityNudge.suggestions.length > 0 && (
            <div className="nudge-suggestions">
              <strong>Suggested Actions:</strong>
              <ul>
                {inactivityNudge.suggestions.map((suggestion, idx) => (
                  <li key={idx}>
                    {suggestion.includes('Schedule') || suggestion.includes('session') ? (
                      <button 
                        className="nudge-action-btn primary"
                        onClick={() => {
                          // Navigate to a booking page or show booking modal
                          // For now, just show an alert
                          alert('This would open the session booking page. In production, this would integrate with your booking system.');
                        }}
                      >
                        {suggestion}
                      </button>
                    ) : (
                      <span>{suggestion}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Other Nudges */}
      {otherNudges.length > 0 && (
        <div className="nudges-section">
          {otherNudges.map((nudge, idx) => (
            <div key={idx} className="nudge-card">
              <div className="nudge-header">
                <span className="nudge-icon">💡</span>
                <h3>{nudge.type === 'goal_completion' ? 'Goal Completed!' : 'Suggestion'}</h3>
              </div>
              <p className="nudge-message">{nudge.message}</p>
              {nudge.suggestions && nudge.suggestions.length > 0 && (
                <div className="nudge-suggestions">
                  <ul>
                    {nudge.suggestions.map((suggestion, sIdx) => (
                      <li key={sIdx}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      
      <div className="dashboard-grid">
        <div className="card">
          <h2>Progress Overview</h2>
          {progress?.data ? (
            <div>
              <p>Goals: {progress.data.goals?.length || 0}</p>
              <p>Sessions: {progress.data.recent_sessions?.length || 0}</p>
            </div>
          ) : (
            <div>
              <p>No data available</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>
                {progressError ? 'API error (backend may not be running)' : 'Loading...'}
              </p>
            </div>
          )}
        </div>

        <div className="card">
          <h2>Quick Actions</h2>
          <div className="actions">
            <Link to="/practice">Start Practice</Link>
            <Link to="/qa">Ask a Question</Link>
            <Link to="/progress">View Progress</Link>
            <Link to="/goals">Manage Goals</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

