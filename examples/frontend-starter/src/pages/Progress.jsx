import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import { useLocalStorage } from '../hooks/useLocalStorage';
import './Progress.css';

function Progress() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [hideCompleted, setHideCompleted] = useLocalStorage('hideCompletedGoals', false);

  const { data: progress, isLoading } = useQuery({
    queryKey: ['progress', user?.id],
    queryFn: () => api.getProgress(user.id).then(res => res.data),
    enabled: !!user?.id,
  });

  const createGoalMutation = useMutation({
    mutationFn: (data) => api.createGoal(data),
    onSuccess: () => {
      success('Goal created successfully!');
      queryClient.invalidateQueries(['progress', user?.id]);
      queryClient.invalidateQueries(['goals', user?.id]);
    },
    onError: (err) => {
      console.error('[PROGRESS] Create goal error:', err);
      showError('Failed to create goal. Please try again.');
    },
  });

  const resetGoalMutation = useMutation({
    mutationFn: (goalId) => api.resetGoal(goalId),
    onSuccess: () => {
      success('Goal reset successfully! You can now work on improving your Elo rating.');
      queryClient.invalidateQueries(['progress', user?.id]);
      queryClient.invalidateQueries(['goals', user?.id]);
    },
    onError: (err) => {
      console.error('[PROGRESS] Reset goal error:', err);
      showError('Failed to reset goal. Please try again.');
    },
  });

  const handleSuggestionClick = (subjectName) => {
    if (!subjectName) return;
    
    createGoalMutation.mutate({
      student_id: user.id,
      title: `Learn ${subjectName}`,
      description: `Goal created from suggestion: ${subjectName}`,
      goal_type: 'Standard',
      subject_name: subjectName,
    });
  };

  const handleGoalClick = (goal) => {
    // goal.subject comes from the progress API response
    const subjectName = goal.subject || 'this goal';
    if (window.confirm(`Would you like to practice ${subjectName}?`)) {
      const subject = goal.subject || 'Math';
      navigate(`/practice?subject=${encodeURIComponent(subject)}`);
    }
  };

  if (isLoading) {
    return (
      <div className="progress">
        <LoadingSpinner message="Loading progress..." />
      </div>
    );
  }

  const progressData = progress?.data || {};
  
  // Filter goals based on hideCompleted setting
  const allGoals = progressData.goals || [];
  const activeGoals = allGoals.filter(g => g.status !== 'completed');
  const completedGoals = allGoals.filter(g => g.status === 'completed');
  const displayedGoals = hideCompleted ? activeGoals : allGoals;

  return (
    <div className="progress">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1>Your Progress</h1>
        {completedGoals.length > 0 && (
          <button
            onClick={() => setHideCompleted(!hideCompleted)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: hideCompleted ? '#007bff' : '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            {hideCompleted ? `Show Completed (${completedGoals.length})` : `Hide Completed (${completedGoals.length})`}
          </button>
        )}
      </div>
      
      <div className="progress-sections">
        <div className="progress-section">
          <h2>Goals</h2>
          {displayedGoals.length > 0 ? (
            <ul>
              {displayedGoals.map((goal, idx) => (
                <li 
                  key={idx}
                  style={{ cursor: 'pointer', padding: '0.5rem', borderRadius: '4px', transition: 'background-color 0.2s' }}
                  onClick={() => handleGoalClick(goal)}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f0f0f0'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  title="Click to practice this goal"
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div>
                      <strong>{goal.title}</strong> 
                      <span style={{ 
                        marginLeft: '0.5rem', 
                        padding: '0.25rem 0.5rem', 
                        borderRadius: '4px',
                        fontSize: '0.875rem',
                        backgroundColor: goal.status === 'completed' ? '#d4edda' : '#d1ecf1',
                        color: goal.status === 'completed' ? '#155724' : '#0c5460'
                      }}>
                        {goal.status === 'completed' ? '✓ Completed' : goal.status}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                      {goal.elo_rating !== undefined && goal.elo_rating !== null && (
                        <div style={{ 
                          display: 'flex', 
                          flexDirection: 'column', 
                          alignItems: 'flex-end',
                          fontSize: '0.875rem'
                        }}>
                          <span style={{ 
                            fontWeight: 'bold', 
                            color: goal.elo_rating >= 1500 ? '#28a745' : goal.elo_rating >= 1200 ? '#007bff' : goal.elo_rating >= 800 ? '#ffc107' : '#dc3545',
                            fontSize: '1rem'
                          }}>
                            Elo: {goal.elo_rating}
                          </span>
                          <span style={{ 
                            fontSize: '0.75rem', 
                            color: '#666',
                            marginTop: '0.25rem'
                          }}>
                            {goal.elo_rating >= 1500 ? 'Advanced' : goal.elo_rating >= 1200 ? 'Intermediate' : goal.elo_rating >= 800 ? 'Beginner' : 'Novice'}
                          </span>
                        </div>
                      )}
                      {goal.completion_percentage !== undefined && (
                        <span style={{ fontWeight: 'bold', color: goal.status === 'completed' ? '#28a745' : '#007bff' }}>
                          {goal.completion_percentage}%
                        </span>
                      )}
                    </div>
                  </div>
                  {goal.completion_percentage !== undefined && (
                    <div className="progress-bar" style={{ marginTop: '0.5rem' }}>
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${goal.completion_percentage}%`,
                          backgroundColor: goal.status === 'completed' ? '#28a745' : '#007bff'
                        }}
                      />
                    </div>
                  )}
                  {goal.completed_at && (
                    <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>
                      Completed: {new Date(goal.completed_at).toLocaleDateString()}
                    </div>
                  )}
                  {/* Show reset button if goal is completed but Elo is low */}
                  {goal.status === 'completed' && goal.elo_rating !== undefined && goal.elo_rating !== null && goal.elo_rating < 1200 && (
                    <div style={{ 
                      marginTop: '0.75rem', 
                      padding: '0.75rem', 
                      backgroundColor: '#fff3cd', 
                      border: '1px solid #ffc107',
                      borderRadius: '4px',
                      fontSize: '0.875rem'
                    }}>
                      <p style={{ margin: '0 0 0.5rem 0', color: '#856404', fontWeight: '500' }}>
                        ⚠️ Your Elo rating is {goal.elo_rating < 800 ? 'Novice' : 'Beginner'} ({goal.elo_rating}). 
                        Consider resetting this goal to practice more and improve your rating!
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Reset "${goal.title}"? This will allow you to practice more and improve your Elo rating.`)) {
                            resetGoalMutation.mutate(goal.goal_id);
                          }
                        }}
                        disabled={resetGoalMutation.isPending}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: '#ffc107',
                          color: '#856404',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: resetGoalMutation.isPending ? 'not-allowed' : 'pointer',
                          fontWeight: 'bold',
                          fontSize: '0.875rem',
                          opacity: resetGoalMutation.isPending ? 0.6 : 1
                        }}
                      >
                        {resetGoalMutation.isPending ? 'Resetting...' : 'Reset Goal & Improve Elo'}
                      </button>
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

        {progressData.suggestions && progressData.suggestions.length > 0 && (
          <div className="progress-section">
            <h2>Suggestions</h2>
            {progressData.suggestions.map((suggestion, idx) => (
              <div key={idx} style={{ 
                marginBottom: '1rem', 
                padding: '1rem', 
                backgroundColor: '#e7f3ff', 
                borderRadius: '8px',
                border: '1px solid #b3d9ff'
              }}>
                <p style={{ marginBottom: '0.5rem', fontWeight: '500' }}>
                  {suggestion.message}
                </p>
                {suggestion.subjects && suggestion.subjects.length > 0 && (
                  <div>
                    <strong>Suggested Subjects:</strong>
                    <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                      {suggestion.subjects.map((subject, subIdx) => (
                        <li 
                          key={subIdx}
                          style={{ 
                            cursor: 'pointer', 
                            color: '#007bff',
                            textDecoration: 'underline',
                            marginBottom: '0.25rem'
                          }}
                          onClick={() => handleSuggestionClick(subject)}
                          title="Click to create a goal for this subject"
                        >
                          {subject}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {suggestion.triggered_by && (
                  <div style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                    Based on: {suggestion.triggered_by.goal_name} ({suggestion.triggered_by.subject})
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Progress;

