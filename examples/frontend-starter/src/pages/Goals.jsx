import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import { useFormValidation } from '../hooks/useFormValidation';
import { validators } from '../utils/validation';
import './Goals.css';

function Goals() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const handleGoalClick = (goal, e) => {
    // Don't trigger practice navigation if clicking the delete button
    if (e && (e.target.closest('.goal-delete-btn') || e.target.closest('button'))) {
      return;
    }
    
    if (window.confirm(`Would you like to practice ${goal.subject || 'this goal'}?`)) {
      const subject = goal.subject || 'Math';
      navigate(`/practice?subject=${encodeURIComponent(subject)}`);
    }
  };

  const handleDeleteGoal = (goal, e) => {
    e.stopPropagation(); // Prevent triggering goal click
    
    const confirmMessage = `Are you sure you want to delete "${goal.title}"?\n\nThis will permanently remove:\n- The goal and all its progress\n- All practice assignments linked to this goal\n\nThis action cannot be undone.`;
    
    if (window.confirm(confirmMessage)) {
      deleteMutation.mutate(goal.id);
    }
  };
  
  const goalSchema = {
    title: [validators.required, validators.minLength(3), validators.maxLength(100)],
    description: [validators.maxLength(500)],
    goal_type: [validators.required],
    subject_name: [validators.required, validators.minLength(2), validators.maxLength(100)],
    target_completion_date: [validators.futureDate],
  };

  const {
    values: newGoal,
    errors,
    touched,
    handleChange,
    handleBlur,
    validate,
    reset,
  } = useFormValidation(
    {
      title: '',
      description: '',
      goal_type: 'Standard',
      subject_name: '',
      target_completion_date: '',
    },
    goalSchema
  );

  const { data: goals, isLoading } = useQuery({
    queryKey: ['goals', user?.id],
    queryFn: () => api.getGoals(user.id).then(res => res.data),
    enabled: !!user?.id,
    retry: false,
    onError: (err) => {
      console.log('[GOALS] API error (expected in dev):', err);
    }
  });

  const createMutation = useMutation({
    mutationFn: (data) => api.createGoal(data),
    onSuccess: (response) => {
      // Check if response indicates success
      if (response?.data?.success !== false) {
      success('Goal created successfully!');
      queryClient.invalidateQueries(['goals', user?.id]);
      queryClient.invalidateQueries(['progress', user?.id]);
      setShowCreateForm(false);
      reset();
      // Reset form values explicitly
      handleChange('title', '');
      handleChange('description', '');
      handleChange('goal_type', 'Standard');
      handleChange('subject_name', '');
      handleChange('target_completion_date', '');
      } else {
        // Response indicates failure
        const errorMsg = response?.data?.error || response?.data?.detail || 'Failed to create goal';
        showError(errorMsg);
      }
    },
    onError: (err) => {
      console.error('[GOALS] Create error:', err);
      // Only show error if it's a real error (not a timeout that might have succeeded)
      // Check if we got a response - if not, it might be a network issue
      if (err.response) {
        // We got a response, so it's a real error
        const errorMsg = err.response?.data?.detail || err.response?.data?.error || 'Failed to create goal. Please try again.';
        showError(errorMsg);
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        // Timeout - check if goal was actually created by refreshing the list
        queryClient.invalidateQueries(['goals', user?.id]);
        showError('Request timed out. Checking if goal was created...');
        // After a delay, check if goal appears
        setTimeout(() => {
          queryClient.invalidateQueries(['goals', user?.id]);
        }, 1000);
      } else {
        // Network error or other issue
        showError('Failed to create goal. Backend may not be running.');
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (goalId) => api.deleteGoal(goalId),
    onSuccess: (response) => {
      const data = response.data?.data || {};
      const deletedCount = data.practice_assignments_deleted || 0;
      const message = deletedCount > 0 
        ? `Goal deleted successfully. ${deletedCount} practice assignment(s) were also removed.`
        : 'Goal deleted successfully.';
      success(message);
      queryClient.invalidateQueries(['goals', user?.id]);
      queryClient.invalidateQueries(['progress', user?.id]);
    },
    onError: (err) => {
      console.error('[GOALS] Delete error:', err);
      showError('Failed to delete goal. Please try again.');
    },
  });

  const resetGoalMutation = useMutation({
    mutationFn: (goalId) => api.resetGoal(goalId),
    onSuccess: () => {
      success('Goal reset successfully! You can now work on improving your Elo rating.');
      queryClient.invalidateQueries(['goals', user?.id]);
      queryClient.invalidateQueries(['progress', user?.id]);
    },
    onError: (err) => {
      console.error('[GOALS] Reset goal error:', err);
      showError('Failed to reset goal. Please try again.');
    },
  });

  const handleCreateGoal = (e) => {
    e.preventDefault();
    
    if (!validate()) {
      showError('Please fix the errors in the form');
      return;
    }
    
    createMutation.mutate({
      student_id: user.id,
      ...newGoal,
    });
  };

  const handleCancel = () => {
    reset();
    setShowCreateForm(false);
  };

  if (isLoading) {
    return (
      <div className="goals">
        <LoadingSpinner message="Loading goals..." />
      </div>
    );
  }

  const goalsList = goals?.data || [];

  return (
    <div className="goals">
      <div className="goals-header">
        <h1>My Goals</h1>
        <button 
          onClick={() => {
            if (showCreateForm) {
              handleCancel();
            } else {
              setShowCreateForm(true);
            }
          }}
          className="btn-primary"
        >
          {showCreateForm ? 'Cancel' : '+ New Goal'}
        </button>
      </div>

      {showCreateForm && (
        <div className="goal-form-card">
          <h2>Create New Goal</h2>
          <form onSubmit={handleCreateGoal}>
            <div className="form-group">
              <label>Title *</label>
              <input
                type="text"
                value={newGoal.title}
                onChange={(e) => handleChange('title', e.target.value)}
                onBlur={() => handleBlur('title')}
                required
                placeholder="e.g., Improve Math scores"
                className={touched.title && errors.title ? 'error' : ''}
              />
              {touched.title && errors.title && (
                <span className="error-message">{errors.title}</span>
              )}
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newGoal.description}
                onChange={(e) => handleChange('description', e.target.value)}
                onBlur={() => handleBlur('description')}
                placeholder="Optional description..."
                rows={3}
                className={touched.description && errors.description ? 'error' : ''}
              />
              {touched.description && errors.description && (
                <span className="error-message">{errors.description}</span>
              )}
            </div>
            <div className="form-group">
              <label>Subject *</label>
              <input
                type="text"
                value={newGoal.subject_name}
                onChange={(e) => handleChange('subject_name', e.target.value)}
                onBlur={() => handleBlur('subject_name')}
                required
                placeholder="e.g., Math, History of Ballet, Chemistry"
                className={touched.subject_name && errors.subject_name ? 'error' : ''}
              />
              {touched.subject_name && errors.subject_name && (
                <span className="error-message">{errors.subject_name}</span>
              )}
              <small style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'block' }}>
                This subject will appear in your Practice dropdown
              </small>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Goal Type</label>
                <select
                  value={newGoal.goal_type}
                  onChange={(e) => handleChange('goal_type', e.target.value)}
                  onBlur={() => handleBlur('goal_type')}
                  className={touched.goal_type && errors.goal_type ? 'error' : ''}
                >
                  <option value="Standard">Standard</option>
                  <option value="SAT">SAT</option>
                  <option value="AP">AP</option>
                </select>
                {touched.goal_type && errors.goal_type && (
                  <span className="error-message">{errors.goal_type}</span>
                )}
              </div>
              <div className="form-group">
                <label>Target Date</label>
                <input
                  type="date"
                  value={newGoal.target_completion_date}
                  onChange={(e) => handleChange('target_completion_date', e.target.value)}
                  onBlur={() => handleBlur('target_completion_date')}
                  className={touched.target_completion_date && errors.target_completion_date ? 'error' : ''}
                />
                {touched.target_completion_date && errors.target_completion_date && (
                  <span className="error-message">{errors.target_completion_date}</span>
                )}
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" disabled={createMutation.isPending} className="btn-primary">
                {createMutation.isPending ? 'Creating...' : 'Create Goal'}
              </button>
              <button 
                type="button" 
                onClick={handleCancel}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="goals-list">
        {goalsList.length === 0 ? (
          <div className="empty-state">
            <p>No goals yet. Create your first goal to get started!</p>
            <button 
              onClick={() => setShowCreateForm(true)}
              className="btn-primary"
            >
              Create Goal
            </button>
          </div>
        ) : (
          goalsList.map((goal) => (
            <div 
              key={goal.id} 
              className="goal-card"
              style={{ cursor: 'pointer', position: 'relative' }}
              onClick={(e) => handleGoalClick(goal, e)}
              title="Click to practice this goal"
            >
              <div className="goal-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <div style={{ flex: 1, paddingRight: '1rem' }}>
                  <h3 style={{ margin: 0, marginBottom: '0.5rem' }}>{goal.title}</h3>
                  {goal.status === 'completed' && (
                    <div style={{ marginBottom: '0.5rem' }}>
                      <span style={{ 
                        color: 'var(--secondary-color)', 
                        fontSize: '1.25rem',
                        lineHeight: '1',
                        display: 'inline-flex',
                        alignItems: 'center'
                      }}>
                        ✓
                      </span>
                    </div>
                  )}
                  <span className={`goal-status goal-status-${goal.status}`} style={{ textTransform: 'capitalize' }}>
                    {goal.status}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem', flexShrink: 0 }}>
                  <button
                    className="goal-delete-btn"
                    onClick={(e) => handleDeleteGoal(goal, e)}
                    style={{
                      background: 'var(--accent-color)',
                      color: 'white',
                      border: 'none',
                      borderRadius: 'var(--border-radius-sm)',
                      padding: '0.25rem 0.5rem',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      transition: 'all 0.2s',
                      lineHeight: '1',
                      minWidth: '24px',
                      height: '24px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}
                    onMouseEnter={(e) => {
                      if (!deleteMutation.isPending) {
                        e.currentTarget.style.background = 'var(--accent-hover)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!deleteMutation.isPending) {
                        e.currentTarget.style.background = 'var(--accent-color)';
                      }
                    }}
                    title="Delete this goal"
                    disabled={deleteMutation.isPending}
                  >
                    ×
                  </button>
                  {goal.elo_rating !== undefined && goal.elo_rating !== null && (
                    <div style={{ 
                      padding: '0.375rem 0.75rem',
                      borderRadius: '4px',
                      fontSize: '0.875rem',
                      fontWeight: 'bold',
                      color: goal.elo_rating >= 1500 ? 'var(--secondary-color)' : goal.elo_rating >= 1200 ? 'var(--primary-color)' : goal.elo_rating >= 800 ? 'var(--warning-color)' : 'var(--accent-color)',
                      backgroundColor: goal.elo_rating >= 1500 ? '#E8F5E9' : goal.elo_rating >= 1200 ? 'var(--primary-light)' : goal.elo_rating >= 800 ? 'var(--bg-accent)' : '#FFEBEE',
                      textAlign: 'right',
                      whiteSpace: 'nowrap'
                    }}>
                      Elo: {goal.elo_rating}
                    </div>
                  )}
                </div>
              </div>
              {goal.description && (
                <p className="goal-description" style={{ marginBottom: '0.75rem' }}>{goal.description}</p>
              )}
              <div className="goal-meta" style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                <span className="goal-type">{goal.goal_type}</span>
                {goal.target_completion_date && (
                  <span className="goal-date">
                    Target: {new Date(goal.target_completion_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              {goal.completion_percentage !== undefined && (
                <div className="goal-progress" style={{ marginBottom: '0.75rem' }}>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${goal.completion_percentage}%` }}
                    />
                  </div>
                  <span className="progress-text">{goal.completion_percentage}% complete</span>
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
                        resetGoalMutation.mutate(goal.id);
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
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Goals;

