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
      success('Goal reset! You can now work on lifting your confidence score.');
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
        <h1>Your Learning Journey</h1>
        {completedGoals.length > 0 && (
          <button
            onClick={() => setHideCompleted(!hideCompleted)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: hideCompleted ? 'var(--primary-color)' : 'var(--text-secondary)',
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
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>{goal.title}</strong>
                      </div>
                      <span style={{ 
                        padding: '0.25rem 0.5rem', 
                        borderRadius: '4px',
                        fontSize: '0.875rem',
                        backgroundColor: goal.status === 'completed' ? '#d4edda' : '#d1ecf1',
                        color: goal.status === 'completed' ? '#155724' : '#0c5460',
                        textTransform: 'capitalize'
                      }}>
                        {goal.status === 'completed' && '✓ '}
                        {goal.status}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexShrink: 0 }}>
                      {goal.elo_rating !== undefined && goal.elo_rating !== null && (
                        <span style={{ 
                          fontWeight: 'bold', 
                          color: goal.elo_rating >= 1500 ? 'var(--secondary-color)' : goal.elo_rating >= 1200 ? 'var(--primary-color)' : goal.elo_rating >= 800 ? 'var(--warning-color)' : 'var(--accent-color)',
                          fontSize: '1rem'
                        }}>
                          Elo: {goal.elo_rating}
                        </span>
                      )}
                      {goal.completion_percentage !== undefined && (
                        <span style={{ fontWeight: 'bold', color: goal.status === 'completed' ? 'var(--secondary-color)' : 'var(--primary-color)' }}>
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
                          backgroundColor: goal.status === 'completed' ? 'var(--secondary-color)' : 'var(--primary-color)'
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
                      backgroundColor: 'var(--bg-accent)', 
                      border: '1px solid var(--primary-light)',
                      borderRadius: '4px',
                      fontSize: '0.875rem'
                    }}>
                      <p style={{ margin: '0 0 0.5rem 0', color: 'var(--text-secondary)', fontWeight: '400' }}>
                        💡 Your confidence score is {goal.elo_rating < 800 ? 'Novice' : 'Beginner'} ({goal.elo_rating}). 
                        Want to lift it higher? Consider resetting this goal to practice more.
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Reset "${goal.title}"? This will give you a fresh start to lift your confidence score.`)) {
                            resetGoalMutation.mutate(goal.goal_id);
                          }
                        }}
                        disabled={resetGoalMutation.isPending}
                        style={{
                          padding: '0.5rem 1rem',
                          backgroundColor: 'var(--accent-color)',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: resetGoalMutation.isPending ? 'not-allowed' : 'pointer',
                          fontWeight: 'bold',
                          fontSize: '0.875rem',
                          opacity: resetGoalMutation.isPending ? 0.6 : 1
                        }}
                      >
                        {resetGoalMutation.isPending ? 'Resetting...' : 'Reset Goal & Lift Confidence'}
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>No goals yet. <span className="inspirational">Let's create one to begin your learning journey!</span></p>
          )}
        </div>

        {progressData.suggestions && progressData.suggestions.length > 0 && (
          <div className="progress-section">
            <h2>Suggestions</h2>
            {progressData.suggestions.map((suggestion, idx) => (
              <div key={idx}               style={{ 
                marginBottom: '1rem', 
                padding: '1.25rem', 
                backgroundColor: 'var(--bg-accent)', 
                borderRadius: 'var(--border-radius)',
                border: '1px solid var(--primary-light)',
                boxShadow: 'var(--shadow-soft)',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow)';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'var(--shadow-soft)';
                e.currentTarget.style.transform = 'translateY(0)';
              }}>
                <p style={{ marginBottom: '0.5rem', fontWeight: '400', fontSize: '1.05rem' }}>
                  {suggestion.message}
                </p>
                {suggestion.subjects && suggestion.subjects.length > 0 && (
                  <div>
                    <strong style={{ color: 'var(--primary-color)' }}>Curious about these subjects?</strong>
                    <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                      {suggestion.subjects.map((subject, subIdx) => (
                        <li 
                          key={subIdx}
                          style={{ 
                            cursor: 'pointer', 
                            color: 'var(--primary-color)',
                            textDecoration: 'none',
                            marginBottom: '0.5rem',
                            padding: '0.5rem',
                            borderRadius: 'var(--border-radius-sm)',
                            transition: 'all 0.2s ease',
                            display: 'inline-block'
                          }}
                          onClick={() => handleSuggestionClick(subject)}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = 'var(--primary-light)';
                            e.currentTarget.style.textDecoration = 'underline';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = 'transparent';
                            e.currentTarget.style.textDecoration = 'none';
                          }}
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

