import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import './Settings.css';

function Settings() {
  const { user, logout } = useAuth();
  const { success } = useToast();
  const [preferences, setPreferences] = useState({
    nudge_frequency_cap: 2,
    email_notifications: true,
    push_notifications: false,
  });

  const handleSave = (e) => {
    e.preventDefault();
    // In production, this would save to backend
    success('Settings saved!');
  };

  const handleLogout = () => {
    logout();
    success('Logged out successfully');
  };

  return (
    <div className="settings">
      <h1>Settings</h1>

      <div className="settings-sections">
        <div className="settings-section">
          <h2>Profile</h2>
          <div className="settings-card">
            <div className="setting-item">
              <label>Email</label>
              <input type="email" value={user?.email || ''} disabled />
            </div>
            <div className="setting-item">
              <label>User ID</label>
              <input type="text" value={user?.id || ''} disabled />
            </div>
            <div className="setting-item">
              <label>Role</label>
              <input type="text" value={user?.role || ''} disabled />
            </div>
          </div>
        </div>

        <div className="settings-section">
          <h2>Notifications</h2>
          <form onSubmit={handleSave} className="settings-card">
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={preferences.email_notifications}
                  onChange={(e) => setPreferences({ ...preferences, email_notifications: e.target.checked })}
                />
                Email Notifications
              </label>
            </div>
            <div className="setting-item">
              <label>
                <input
                  type="checkbox"
                  checked={preferences.push_notifications}
                  onChange={(e) => setPreferences({ ...preferences, push_notifications: e.target.checked })}
                />
                Push Notifications
              </label>
            </div>
            <div className="setting-item">
              <label>
                Nudge Frequency Cap
                <select
                  value={preferences.nudge_frequency_cap}
                  onChange={(e) => setPreferences({ ...preferences, nudge_frequency_cap: parseInt(e.target.value) })}
                >
                  <option value={1}>1 per day</option>
                  <option value={2}>2 per day</option>
                  <option value={3}>3 per day</option>
                  <option value={5}>5 per day</option>
                </select>
              </label>
            </div>
            <button type="submit" className="btn-primary">Save Preferences</button>
          </form>
        </div>

        <div className="settings-section">
          <h2>Account</h2>
          <div className="settings-card">
            <button onClick={handleLogout} className="btn-danger">
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;

