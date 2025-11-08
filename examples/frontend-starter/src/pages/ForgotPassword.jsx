import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useFormValidation } from '../hooks/useFormValidation';
import { validators } from '../utils/validation';
import { forgotPassword, confirmPassword } from '../utils/cognito';
import './Login.css';

function ForgotPassword() {
  const { success, error: showError } = useToast();
  const navigate = useNavigate();
  const [step, setStep] = useState('request'); // 'request' or 'reset'
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const requestSchema = {
    email: [validators.required, validators.email],
  };

  const resetSchema = {
    code: [validators.required],
    password: [validators.required, validators.passwordPolicy],
    confirmPassword: [
      validators.required,
      (value, allValues) => {
        if (value !== allValues.password) {
          return 'Passwords do not match';
        }
        return null;
      },
    ],
  };

  const {
    values: requestValues,
    errors: requestErrors,
    touched: requestTouched,
    handleChange: handleRequestChange,
    handleBlur: handleRequestBlur,
    validate: validateRequest,
  } = useFormValidation({ email: '' }, requestSchema);

  const {
    values: resetValues,
    errors: resetErrors,
    touched: resetTouched,
    handleChange: handleResetChange,
    handleBlur: handleResetBlur,
    validate: validateReset,
  } = useFormValidation(
    { code: '', password: '', confirmPassword: '' },
    resetSchema
  );

  // Helper function to check password requirements
  const checkPasswordRequirements = (password) => {
    return {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSymbol: /[^A-Za-z0-9]/.test(password),
    };
  };

  const passwordRequirements = checkPasswordRequirements(resetValues.password);

  const handleRequestCode = async (e) => {
    e.preventDefault();
    
    if (!validateRequest()) {
      showError('Please fix the errors in the form');
      return;
    }

    setIsSubmitting(true);

    try {
      await forgotPassword(requestValues.email);
      setEmail(requestValues.email);
      setStep('reset');
      success('Password reset code sent! Please check your email.');
    } catch (err) {
      console.error('[FORGOT PASSWORD] Request error:', err);
      
      let errorMessage = 'Failed to send reset code';
      if (err.code === 'UserNotFoundException') {
        errorMessage = 'No account found with this email address';
      } else if (err.code === 'InvalidParameterException') {
        errorMessage = 'Invalid email address';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      showError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (!validateReset()) {
      showError('Please fix the errors in the form');
      return;
    }

    setIsSubmitting(true);

    try {
      await confirmPassword(email, resetValues.code.trim(), resetValues.password);
      success('Password reset successfully! You can now log in.');
      navigate('/login');
    } catch (err) {
      console.error('[FORGOT PASSWORD] Reset error:', err);
      
      let errorMessage = 'Password reset failed';
      if (err.code === 'CodeMismatchException') {
        errorMessage = 'Invalid verification code. Please check and try again.';
      } else if (err.code === 'ExpiredCodeException') {
        errorMessage = 'Verification code has expired. Please request a new one.';
      } else if (err.code === 'InvalidPasswordException') {
        errorMessage = 'Password does not meet requirements';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      showError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === 'reset') {
    return (
      <div className="login">
        <div className="login-container">
          <img src="/elevare-logo.svg" alt="ElevareAI" style={{ width: '80px', height: '80px', marginBottom: '1rem' }} />
          <h1>Reset Password</h1>
          <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
            We've sent a verification code to <strong>{email}</strong>
          </p>
          <form onSubmit={handleResetPassword}>
            <div className="form-group">
              <input
                type="text"
                placeholder="Enter verification code"
                value={resetValues.code}
                onChange={(e) => handleResetChange('code', e.target.value)}
                onBlur={() => handleResetBlur('code')}
                required
                maxLength={6}
                style={{ 
                  textAlign: 'center',
                  fontSize: '1.2rem',
                  letterSpacing: '0.5rem',
                  fontWeight: '600'
                }}
                autoFocus
              />
              {resetTouched.code && resetErrors.code && (
                <span className="error-message">{resetErrors.code}</span>
              )}
            </div>
            <div className="form-group">
              <input
                type="password"
                placeholder="New Password"
                value={resetValues.password}
                onChange={(e) => handleResetChange('password', e.target.value)}
                onBlur={() => handleResetBlur('password')}
                required
                className={resetTouched.password && resetErrors.password ? 'error' : ''}
              />
              {resetTouched.password && resetErrors.password && (
                <span className="error-message">{resetErrors.password}</span>
              )}
              {resetValues.password && (
                <div style={{ 
                  marginTop: '0.5rem', 
                  fontSize: '0.85rem', 
                  color: 'var(--text-secondary)',
                  padding: '0.75rem',
                  background: 'var(--background-secondary, #f5f5f5)',
                  borderRadius: 'var(--border-radius-sm, 4px)',
                  border: '1px solid var(--border-color, #ddd)'
                }}>
                  <div style={{ marginBottom: '0.5rem', fontWeight: '500' }}>Password must contain:</div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', listStyle: 'none' }}>
                    <li style={{ 
                      color: passwordRequirements.minLength ? 'var(--success, #28a745)' : 'var(--text-secondary)',
                      marginBottom: '0.25rem'
                    }}>
                      {passwordRequirements.minLength ? '✓' : '○'} At least 8 characters
                    </li>
                    <li style={{ 
                      color: passwordRequirements.hasUppercase ? 'var(--success, #28a745)' : 'var(--text-secondary)',
                      marginBottom: '0.25rem'
                    }}>
                      {passwordRequirements.hasUppercase ? '✓' : '○'} One uppercase letter (A-Z)
                    </li>
                    <li style={{ 
                      color: passwordRequirements.hasLowercase ? 'var(--success, #28a745)' : 'var(--text-secondary)',
                      marginBottom: '0.25rem'
                    }}>
                      {passwordRequirements.hasLowercase ? '✓' : '○'} One lowercase letter (a-z)
                    </li>
                    <li style={{ 
                      color: passwordRequirements.hasNumber ? 'var(--success, #28a745)' : 'var(--text-secondary)',
                      marginBottom: '0.25rem'
                    }}>
                      {passwordRequirements.hasNumber ? '✓' : '○'} One number (0-9)
                    </li>
                    <li style={{ 
                      color: passwordRequirements.hasSymbol ? 'var(--success, #28a745)' : 'var(--text-secondary)',
                      marginBottom: '0.25rem'
                    }}>
                      {passwordRequirements.hasSymbol ? '✓' : '○'} One symbol (!@#$%^&*...)
                    </li>
                  </ul>
                </div>
              )}
            </div>
            <div className="form-group">
              <input
                type="password"
                placeholder="Confirm New Password"
                value={resetValues.confirmPassword}
                onChange={(e) => handleResetChange('confirmPassword', e.target.value)}
                onBlur={() => handleResetBlur('confirmPassword')}
                required
                className={resetTouched.confirmPassword && resetErrors.confirmPassword ? 'error' : ''}
              />
              {resetTouched.confirmPassword && resetErrors.confirmPassword && (
                <span className="error-message">{resetErrors.confirmPassword}</span>
              )}
            </div>
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Resetting Password...' : 'Reset Password'}
            </button>
          </form>
          <p style={{ marginTop: '1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <Link 
              to="/login" 
              style={{ color: 'var(--primary)', textDecoration: 'none' }}
            >
              Back to Login
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="login">
      <div className="login-container">
        <img src="/elevare-logo.svg" alt="ElevareAI" style={{ width: '80px', height: '80px', marginBottom: '1rem' }} />
        <h1>Forgot Password</h1>
        <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
          Enter your email address and we'll send you a code to reset your password.
        </p>
        <form onSubmit={handleRequestCode}>
          <div className="form-group">
            <input
              type="email"
              placeholder="Email"
              value={requestValues.email}
              onChange={(e) => handleRequestChange('email', e.target.value)}
              onBlur={() => handleRequestBlur('email')}
              required
              className={requestTouched.email && requestErrors.email ? 'error' : ''}
              autoFocus
            />
            {requestTouched.email && requestErrors.email && (
              <span className="error-message">{requestErrors.email}</span>
            )}
          </div>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Sending...' : 'Send Reset Code'}
          </button>
        </form>
        <p style={{ marginTop: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Remember your password? <Link to="/login" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Login</Link>
        </p>
      </div>
    </div>
  );
}

export default ForgotPassword;

