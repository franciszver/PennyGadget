import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Notifications from './Notifications';
import './Navbar.css';

function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/dashboard" className="navbar-brand">
          AI Study Companion
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

