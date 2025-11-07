import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import './Notifications.css';

function Notifications() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const popupRef = useRef(null);
  const queryClient = useQueryClient();

  const createGoalMutation = useMutation({
    mutationFn: (data) => api.createGoal(data),
    onSuccess: () => {
      success('Goal created successfully!');
      queryClient.invalidateQueries(['progress', user?.id]);
      queryClient.invalidateQueries(['goals', user?.id]);
      queryClient.invalidateQueries(['nudges', user?.id]);
    },
    onError: (err) => {
      console.error('[NOTIFICATIONS] Create goal error:', err);
      showError('Failed to create goal. Please try again.');
    },
  });

  const handleSuggestionClick = (suggestion) => {
    if (!suggestion || !user?.id) return;
    
    createGoalMutation.mutate({
      student_id: user.id,
      title: `Learn ${suggestion}`,
      description: `Goal created from suggestion: ${suggestion}`,
      goal_type: 'Standard',
      subject_name: suggestion,
    });
  };

  // Fetch nudges
  const { data: nudgesData, isLoading } = useQuery({
    queryKey: ['nudges', user?.id],
    queryFn: () => api.getNudges(user.id).then(res => res.data),
    enabled: !!user?.id,
    retry: false,
    refetchInterval: 30000, // Refetch every 30 seconds
    onError: (error) => {
      console.error('[NOTIFICATIONS] API error:', error);
    }
  });

  const markAsReadMutation = useMutation({
    mutationFn: (nudgeId) => api.engageNudge(nudgeId, 'opened'),
    onSuccess: () => {
      queryClient.invalidateQueries(['nudges', user?.id]);
    }
  });

  const nudges = nudgesData?.data?.nudges || [];
  const unreadCount = nudges.length;

  // Close popup when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Mark all as read when popup opens (but don't block if it fails)
  useEffect(() => {
    if (isOpen && nudges.length > 0) {
      nudges.forEach(nudge => {
        markAsReadMutation.mutate(nudge.nudge_id, {
          onError: (err) => {
            console.error('[NOTIFICATIONS] Failed to mark nudge as read:', err);
          }
        });
      });
    }
  }, [isOpen, nudges.length]);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div className="notifications-container" ref={popupRef}>
      <button 
        className="notifications-bell" 
        onClick={handleToggle}
        aria-label="Notifications"
      >
        <svg 
          width="24" 
          height="24" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="notifications-badge">{unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notifications-popup">
          <div className="notifications-header">
            <h3>Notifications</h3>
            {unreadCount > 0 && (
              <span className="notifications-count">{unreadCount} new</span>
            )}
          </div>

          <div className="notifications-content">
            {isLoading ? (
              <div className="notifications-loading">Loading notifications...</div>
            ) : nudges.length > 0 ? (
              <ul className="notifications-list">
                {nudges.map((nudge, idx) => (
                  <li key={idx} className="notification-item">
                    <div className="notification-icon">
                      {nudge.type === 'inactivity' && '⚠️'}
                      {nudge.type === 'goal_completion' && '🎉'}
                      {nudge.type === 'login' && '👋'}
                      {!['inactivity', 'goal_completion', 'login'].includes(nudge.type) && '💡'}
                    </div>
                    <div className="notification-content">
                      <p className="notification-message">{nudge.message}</p>
                      {nudge.suggestions && nudge.suggestions.length > 0 && (
                        <div className="notification-suggestions">
                          <strong>Suggestions:</strong>
                          <ul>
                            {nudge.suggestions.map((suggestion, sIdx) => (
                              <li 
                                key={sIdx}
                                style={{ 
                                  cursor: 'pointer', 
                                  color: 'var(--primary-color)',
                                  textDecoration: 'underline'
                                }}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleSuggestionClick(suggestion);
                                }}
                                title="Click to create a goal for this suggestion"
                              >
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {nudge.trigger_reason && (
                        <div className="notification-reason">
                          {nudge.trigger_reason}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="notifications-empty">
                <p>No new notifications</p>
                <p className="notifications-empty-subtitle">You're all caught up!</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Notifications;

