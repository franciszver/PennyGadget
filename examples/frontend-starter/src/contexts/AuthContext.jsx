import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('[AUTH] Initializing auth context...');
    
    // Check for existing auth token
    const token = localStorage.getItem('auth_token');
    const userId = localStorage.getItem('user_id');
    const userRole = localStorage.getItem('user_role');
    
    console.log('[AUTH] Found in localStorage:', { 
      hasToken: !!token, 
      hasUserId: !!userId, 
      userRole 
    });
    
    if (token && userId) {
      console.log('[AUTH] Restoring authenticated state');
      // Validate token and set user
      // In production, this would verify with Cognito
      setIsAuthenticated(true);
      setUser({ id: userId, role: userRole || 'student' });
      console.log('[AUTH] Auth state restored - isAuthenticated: true');
    } else {
      console.log('[AUTH] No existing auth found, user not authenticated');
    }
    setLoading(false);
    console.log('[AUTH] Auth context initialized, loading: false');
  }, []);

  const login = async (email, password) => {
    try {
      console.log('[AUTH] Login called with email:', email);
      
      // Demo account UUIDs mapping
      const demoAccountIds = {
        'demo_goal_complete@demo.com': '180bcad6-380e-4a2f-809b-032677fcc721',
        'demo_sat_complete@demo.com': '0281a3c5-e9aa-4d65-ad33-f49a80a77a23',
        'demo_chemistry@demo.com': '063009da-20a4-4f53-8f67-f06573f7195e',
        'demo_low_sessions@demo.com': 'e8bf67c3-57e6-405b-a1b5-80ac75aaf034',
        'demo_multi_goal@demo.com': 'c02cb7f8-e63c-4945-9406-320e1d9046f3'
      };
      
      // In production, this would use AWS Cognito
      // For now, mock authentication
      const token = 'mock-token-' + Date.now();
      // Use actual UUID for demo accounts, otherwise generate a fake one
      const userId = demoAccountIds[email] || 'user-' + email.replace('@', '-').replace('.', '-');
      
      console.log('[AUTH] Generated token and userId:', { token: token.substring(0, 20) + '...', userId });
      
      // Store token and user info
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_id', userId);
      localStorage.setItem('user_role', 'student');
      
      console.log('[AUTH] Stored in localStorage');
      console.log('[AUTH] Verifying storage:', {
        token: localStorage.getItem('auth_token') ? 'exists' : 'missing',
        userId: localStorage.getItem('user_id'),
        role: localStorage.getItem('user_role')
      });
      
      // Update state synchronously
      setIsAuthenticated(true);
      setUser({ id: userId, role: 'student', email: email });
      
      console.log('[AUTH] State updated - isAuthenticated: true, user:', { id: userId, role: 'student' });
      
      // Return success - navigation will happen in Login component
      return { success: true };
    } catch (error) {
      console.error('[AUTH] Login error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_role');
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

