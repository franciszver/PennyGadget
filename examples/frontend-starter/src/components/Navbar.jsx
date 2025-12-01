import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Notifications from './Notifications';
import './Navbar.css';

// Version info injected at build time
const APP_VERSION = typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : 'dev';
const BUILD_TIME = typeof __BUILD_TIME__ !== 'undefined' ? __BUILD_TIME__ : 'local';

function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Format build time for display
  const formatBuildTime = (isoString) => {
    if (!isoString || isoString === 'local') return 'local';
    try {
      const date = new Date(isoString);
      return date.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit'
      });
    } catch {
      return isoString.slice(0, 16);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/dashboard" className="navbar-brand">
          <img src="/elevare-logo.svg" alt="ElevareAI" className="navbar-logo" />
          <span className="navbar-brand-text">ElevareAI</span>
          <span className="navbar-version" title={`Build: ${formatBuildTime(BUILD_TIME)}`}>
            v{APP_VERSION}
          </span>
        </Link>
        <div className="navbar-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/practice">Practice</Link>
          <Link to="/qa">Q&A</Link>
          <Link to="/progress">Progress</Link>
          <Link to="/goals">Goals</Link>
          <Link to="/messaging">Messages</Link>
          <div className="navbar-user">
            <Notifications />
            <Link to="/settings" className="navbar-settings">Settings</Link>
            <span>{user?.email || 'User'}</span>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

