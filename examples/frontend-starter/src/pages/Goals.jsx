import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  const [showCreateForm, setShowCreateForm] = useState(false);
  
  const goalSchema = {
    title: [validators.required, validators.minLength(3), validators.maxLength(100)],
    description: [validators.maxLength(500)],
    goal_type: [validators.required],
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
    onSuccess: () => {
      success('Goal created successfully!');
      queryClient.invalidateQueries(['goals', user?.id]);
      setShowCreateForm(false);
      setNewGoal({ title: '', description: '', goal_type: 'Standard', target_completion_date: '' });
    },
    onError: (err) => {
      console.error('[GOALS] Create error:', err);
      showError('Failed to create goal. Backend may not be running.');
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
            <div key={goal.id} className="goal-card">
              <div className="goal-header">
                <h3>{goal.title}</h3>
                <span className={`goal-status goal-status-${goal.status}`}>
                  {goal.status}
                </span>
              </div>
              {goal.description && (
                <p className="goal-description">{goal.description}</p>
              )}
              <div className="goal-meta">
                <span className="goal-type">{goal.goal_type}</span>
                {goal.target_completion_date && (
                  <span className="goal-date">
                    Target: {new Date(goal.target_completion_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              {goal.completion_percentage !== undefined && (
                <div className="goal-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${goal.completion_percentage}%` }}
                    />
                  </div>
                  <span className="progress-text">{goal.completion_percentage}% complete</span>
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

