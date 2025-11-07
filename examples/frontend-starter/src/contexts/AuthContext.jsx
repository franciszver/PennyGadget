import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('[AUTH] Initializing auth context...');
    
    // Demo account UUIDs mapping (must match login function)
    const demoAccountIds = {
      'demo_goal_complete@demo.com': '180bcad6-380e-4a2f-809b-032677fcc721',
      'demo_sat_complete@demo.com': '0281a3c5-e9aa-4d65-ad33-f49a80a77a23',
      'demo_chemistry@demo.com': '063009da-20a4-4f53-8f67-f06573f7195e',
      'demo_low_sessions@demo.com': 'e8bf67c3-57e6-405b-a1b5-80ac75aaf034',
      'demo_multi_goal@demo.com': 'c02cb7f8-e63c-4945-9406-320e1d9046f3',
      'demo_qa@demo.com': 'c0227285-166a-4a90-b7fd-d4d7e7ff4e39'
    };
    
    // Check for existing auth token
    const token = localStorage.getItem('auth_token');
    let userId = localStorage.getItem('user_id');
    const userRole = localStorage.getItem('user_role');
    const userEmail = localStorage.getItem('user_email'); // Store email for validation
    
    console.log('[AUTH] Found in localStorage:', { 
      hasToken: !!token, 
      hasUserId: !!userId, 
      userRole,
      userEmail
    });
    
    // Validate userId format - if it's a fake ID (starts with 'user-'), try to fix it
    if (userId && userId.startsWith('user-')) {
      console.log('[AUTH] Detected fake user ID, attempting to fix...');
      
      // Try to get email from localStorage or infer from fake ID
      let emailToCheck = userEmail;
      if (!emailToCheck && userId.startsWith('user-')) {
        // Infer email from fake ID format: user-demo_qa-demo-com -> demo_qa@demo.com
        // The fake ID format is: user-{email_prefix}-{domain_part1}-{domain_part2}
        // Where email_prefix has underscores converted to hyphens
        // Example: demo_low_sessions@demo.com -> user-demo_low_sessions-demo-com
        // But the conversion might lose the 's', so we need to check all possible variations
        
        // Remove 'user-' prefix
        const idWithoutPrefix = userId.replace('user-', '');
        
        // Try to match against known demo accounts by checking if any email
        // when converted to fake ID format matches this ID
        // Handle variations where underscores might be converted to hyphens inconsistently
        for (const [email, uuid] of Object.entries(demoAccountIds)) {
          // Convert email to fake ID format: demo_low_sessions@demo.com -> demo_low_sessions-demo-com
          const fakeIdFromEmail = 'user-' + email.replace('@', '-').replace(/\./g, '-');
          
          // Also try with underscores converted to hyphens
          const emailPrefix = email.split('@')[0];
          const emailDomain = email.split('@')[1];
          const fakeIdWithHyphens = 'user-' + emailPrefix.replace(/_/g, '-') + '-' + emailDomain.replace(/\./g, '-');
          
          // Check for exact match or if the fake ID contains the email prefix (with variations)
          // Handle cases where underscores/hyphens are mixed and plural/singular variations
          const emailPrefixHyphenated = emailPrefix.replace(/_/g, '-');
          const emailPrefixWithUnderscores = emailPrefix; // Keep original with underscores
          
          // Create variations to match against
          const variations = [
            emailPrefixHyphenated, // demo-low-sessions
            emailPrefixHyphenated + 's', // demo-low-sessionss (in case 's' was dropped)
            emailPrefixHyphenated.replace(/s$/, ''), // demo-low-session (remove trailing 's')
            emailPrefixWithUnderscores, // demo_low_sessions
            emailPrefixWithUnderscores + 's', // demo_low_sessionss
            emailPrefixWithUnderscores.replace(/s$/, ''), // demo_low_session
          ];
          
          // Check if any variation matches the fake ID
          const matches = fakeIdFromEmail === userId || 
              fakeIdWithHyphens === userId ||
              variations.some(variation => {
                // Check if fake ID starts with or contains the variation
                return idWithoutPrefix.startsWith(variation) || 
                       idWithoutPrefix.includes(variation) ||
                       variation.includes(idWithoutPrefix.split('-')[0]); // Partial match on first part
              });
          
          if (matches) {
            emailToCheck = email;
            console.log('[AUTH] Matched fake ID to email:', email, '(checked variations:', variations.length, ')');
            break;
          }
        }
        
        // If no match found, try the old inference method
        if (!emailToCheck) {
          const parts = idWithoutPrefix.split('-');
          if (parts.length >= 3) {
            // Last two parts are domain parts, rest is the email prefix
            // But we need to be careful - underscores in email become hyphens
            // So we need to check all possible combinations
            const domainPart = parts.slice(-2).join('.');
            const possiblePrefixes = [parts.slice(0, -2).join('_')]; // Try with underscores
            
            // Also try variations if the last part of prefix might have been split
            for (const prefix of possiblePrefixes) {
              const testEmail = `${prefix}@${domainPart}`;
              if (demoAccountIds[testEmail]) {
                emailToCheck = testEmail;
                break;
              }
            }
          }
        }
        
        console.log('[AUTH] Inferred email from fake ID:', emailToCheck);
      }
      
      if (emailToCheck) {
        const correctId = demoAccountIds[emailToCheck];
        if (correctId) {
          console.log('[AUTH] Found correct UUID, updating localStorage');
          userId = correctId;
          localStorage.setItem('user_id', correctId);
          if (!userEmail) {
            localStorage.setItem('user_email', emailToCheck);
          }
        } else {
          console.log('[AUTH] No UUID mapping found for', emailToCheck, ', clearing invalid auth');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user_id');
          localStorage.removeItem('user_role');
          localStorage.removeItem('user_email');
          userId = null;
        }
      } else {
        console.log('[AUTH] Cannot infer email, clearing invalid auth');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_role');
        localStorage.removeItem('user_email');
        userId = null;
      }
    }
    
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
      // Note: These will be generated when create_demo_users.py is run
      // The script will output the actual UUIDs - update this mapping after running the script
      const demoAccountIds = {
        'demo_goal_complete@demo.com': '180bcad6-380e-4a2f-809b-032677fcc721',
        'demo_sat_complete@demo.com': '0281a3c5-e9aa-4d65-ad33-f49a80a77a23',
        'demo_chemistry@demo.com': '063009da-20a4-4f53-8f67-f06573f7195e',
        'demo_low_sessions@demo.com': 'e8bf67c3-57e6-405b-a1b5-80ac75aaf034',
        'demo_multi_goal@demo.com': 'c02cb7f8-e63c-4945-9406-320e1d9046f3',
        'demo_qa@demo.com': 'c0227285-166a-4a90-b7fd-d4d7e7ff4e39'
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
      localStorage.setItem('user_email', email); // Store email for validation
      
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
    localStorage.removeItem('user_email');
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

