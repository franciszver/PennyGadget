import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Gamification.css';

function Gamification() {
  const { user } = useAuth();

  const { data: gamification, isLoading: gamificationLoading } = useQuery({
    queryKey: ['gamification', user?.id],
    queryFn: () => api.getGamification(user.id).then(res => res.data),
    enabled: !!user?.id,
    retry: false,
    onError: (err) => {
      console.log('[GAMIFICATION] API error (expected in dev):', err);
    }
  });

  const { data: leaderboard, isLoading: leaderboardLoading } = useQuery({
    queryKey: ['leaderboard'],
    queryFn: () => api.getLeaderboard({ limit: 10 }).then(res => res.data),
    retry: false,
    onError: (err) => {
      console.log('[LEADERBOARD] API error (expected in dev):', err);
    }
  });

  if (gamificationLoading || leaderboardLoading) {
    return (
      <div className="gamification">
        <LoadingSpinner message="Loading gamification data..." />
      </div>
    );
  }

  const gamificationData = gamification?.data || {};
  const leaderboardData = leaderboard?.data || [];

  // Calculate XP needed for next level
  const currentLevel = gamificationData.level || 1;
  const xpForNextLevel = currentLevel * 100;
  const currentXP = gamificationData.xp || 0;
  const xpProgress = (currentXP % 100) / 100 * 100;

  return (
    <div className="gamification">
      <h1>Gamification</h1>

      <div className="gamification-grid">
        <div className="gamification-card main-stats">
          <h2>Your Progress</h2>
          <div className="level-display">
            <div className="level-badge">Level {currentLevel}</div>
            <div className="xp-display">
              <div className="xp-bar">
                <div 
                  className="xp-fill" 
                  style={{ width: `${xpProgress}%` }}
                />
              </div>
              <span className="xp-text">
                {currentXP} / {xpForNextLevel} XP
              </span>
            </div>
          </div>

          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{gamificationData.current_streak || 0}</div>
              <div className="stat-label">Day Streak</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{gamificationData.total_xp || 0}</div>
              <div className="stat-label">Total XP</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{gamificationData.badges?.length || 0}</div>
              <div className="stat-label">Badges</div>
            </div>
          </div>
        </div>

        <div className="gamification-card badges">
          <h2>Badges</h2>
          {gamificationData.badges && gamificationData.badges.length > 0 ? (
            <div className="badges-list">
              {gamificationData.badges.map((badge, idx) => (
                <div key={idx} className="badge-item">
                  <div className="badge-icon">🏆</div>
                  <div className="badge-info">
                    <strong>{badge.name}</strong>
                    <span className="badge-description">{badge.description}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-badges">
              <p>No badges yet. Keep practicing to earn badges!</p>
            </div>
          )}
        </div>

        <div className="gamification-card leaderboard">
          <h2>Leaderboard</h2>
          {leaderboardData.length > 0 ? (
            <div className="leaderboard-list">
              {leaderboardData.map((entry, idx) => (
                <div 
                  key={entry.user_id} 
                  className={`leaderboard-entry ${entry.user_id === user?.id ? 'current-user' : ''}`}
                >
                  <span className="rank">#{idx + 1}</span>
                  <span className="username">{entry.username || `User ${entry.user_id.substring(0, 8)}`}</span>
                  <span className="score">{entry.xp || 0} XP</span>
                  <span className="level">Lv {entry.level || 1}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-leaderboard">
              <p>No leaderboard data available.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Gamification;

