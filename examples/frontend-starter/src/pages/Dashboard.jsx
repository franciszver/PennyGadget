import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Dashboard.css';

function Dashboard() {
  const { user } = useAuth();

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

  const { data: gamification, isLoading: gamificationLoading, error: gamificationError } = useQuery({
    queryKey: ['gamification', user?.id],
    queryFn: () => {
      console.log('[DASHBOARD] Fetching gamification for user:', user.id);
      return api.getGamification(user.id).then(res => {
        console.log('[DASHBOARD] Gamification response:', res.data);
        return res.data;
      });
    },
    enabled: !!user?.id,
    retry: false, // Don't retry on error in development
    onError: (error) => {
      console.error('[DASHBOARD] Gamification API error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        userId: user?.id
      });
    }
  });

  if (progressLoading || gamificationLoading) {
    return (
      <div className="dashboard">
        <LoadingSpinner message="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h1>Welcome to AI Study Companion</h1>
      
      {(progressError || gamificationError) && (
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
          <h2>Gamification</h2>
          {gamification?.data ? (
            <div>
              <p>Level: {gamification.data.level}</p>
              <p>XP: {gamification.data.xp}</p>
              <p>Streak: {gamification.data.current_streak} days</p>
            </div>
          ) : (
            <div>
              <p>No data available</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>
                {gamificationError ? 'API error (backend may not be running)' : 'Loading...'}
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

