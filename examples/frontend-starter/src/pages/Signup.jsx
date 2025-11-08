import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useFormValidation } from '../hooks/useFormValidation';
import { validators } from '../utils/validation';
import { signUp, confirmSignUp, resendConfirmationCode } from '../utils/cognito';
import './Login.css';

function Signup() {
  const { success, error: showError } = useToast();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requiresVerification, setRequiresVerification] = useState(false);
  const [signupEmail, setSignupEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);

  const signupSchema = {
    email: [validators.required, validators.email],
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
    name: [], // Optional
  };

  const {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    validate,
  } = useFormValidation(
    { email: '', password: '', confirmPassword: '', name: '' },
    signupSchema
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

  const passwordRequirements = checkPasswordRequirements(values.password);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) {
      showError('Please fix the errors in the form');
      return;
    }

    setIsSubmitting(true);

    try {
      const attributes = {};
      if (values.name) {
        attributes.name = values.name;
      }

      const result = await signUp(values.email, values.password, attributes);
      
      setSignupEmail(values.email);
      
      if (result.userConfirmed) {
        // User is already confirmed (shouldn't happen normally, but handle it)
        success('Account created successfully! Please login.');
        navigate('/login');
      } else {
        // Email verification required
        setRequiresVerification(true);
        success('Account created! Please check your email for verification code.');
      }
    } catch (err) {
      console.error('[SIGNUP] Signup error:', err);
      
      // Handle specific Cognito errors
      let errorMessage = 'Signup failed';
      if (err.code === 'UsernameExistsException') {
        errorMessage = 'An account with this email already exists';
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

  const handleVerifyCode = async (e) => {
    e.preventDefault();
    
    if (!verificationCode.trim()) {
      showError('Please enter the verification code');
      return;
    }

    setIsVerifying(true);

    try {
      await confirmSignUp(signupEmail, verificationCode.trim());
      success('Email verified successfully! You can now log in.');
      navigate('/login');
    } catch (err) {
      console.error('[SIGNUP] Verification error:', err);
      
      let errorMessage = 'Verification failed';
      if (err.code === 'CodeMismatchException') {
        errorMessage = 'Invalid verification code. Please check and try again.';
      } else if (err.code === 'ExpiredCodeException') {
        errorMessage = 'Verification code has expired. Please request a new one.';
      } else if (err.code === 'NotAuthorizedException') {
        errorMessage = 'This account is already verified. Please log in.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      showError(errorMessage);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResendCode = async () => {
    setIsResending(true);

    try {
      await resendConfirmationCode(signupEmail);
      success('Verification code resent! Please check your email.');
    } catch (err) {
      console.error('[SIGNUP] Resend error:', err);
      
      let errorMessage = 'Failed to resend code';
      if (err.code === 'UserNotFoundException') {
        errorMessage = 'No account found with this email address';
      } else if (err.code === 'InvalidParameterException') {
        errorMessage = 'Invalid email address';
      } else if (err.code === 'LimitExceededException') {
        errorMessage = 'Too many attempts. Please try again later.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      showError(errorMessage);
    } finally {
      setIsResending(false);
    }
  };

  if (requiresVerification) {
    return (
      <div className="login">
        <div className="login-container">
          <img src="/elevare-logo.svg" alt="ElevareAI" style={{ width: '80px', height: '80px', marginBottom: '1rem' }} />
          <h1>Verify Your Email</h1>
          <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
            We've sent a verification code to <strong>{signupEmail}</strong>
          </p>
          <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Please check your email and enter the verification code below.
          </p>
          <form onSubmit={handleVerifyCode}>
            <div className="form-group">
              <input
                type="text"
                placeholder="Enter verification code"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
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
            </div>
            <button type="submit" disabled={isVerifying || !verificationCode.trim()}>
              {isVerifying ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>
          <p style={{ marginTop: '1rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Didn't receive the code?{' '}
            <button
              type="button"
              onClick={handleResendCode}
              disabled={isResending}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--primary)',
                textDecoration: 'none',
                cursor: isResending ? 'not-allowed' : 'pointer',
                padding: 0,
                fontSize: '0.9rem',
                opacity: isResending ? 0.6 : 1
              }}
            >
              {isResending ? 'Resending...' : 'Resend Code'}
            </button>
            {' or '}
            <Link 
              to="/login" 
              style={{ color: 'var(--primary)', textDecoration: 'none' }}
            >
              Go to Login
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
        <h1>ElevareAI</h1>
        <p className="tagline" style={{ marginBottom: '2rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
          Lift your learning, gently.
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <input
              type="email"
              placeholder="Email"
              value={values.email}
              onChange={(e) => handleChange('email', e.target.value)}
              onBlur={() => handleBlur('email')}
              required
              className={touched.email && errors.email ? 'error' : ''}
            />
            {touched.email && errors.email && (
              <span className="error-message">{errors.email}</span>
            )}
          </div>
          <div className="form-group">
            <input
              type="text"
              placeholder="Name (optional)"
              value={values.name}
              onChange={(e) => handleChange('name', e.target.value)}
              onBlur={() => handleBlur('name')}
              className={touched.name && errors.name ? 'error' : ''}
            />
            {touched.name && errors.name && (
              <span className="error-message">{errors.name}</span>
            )}
          </div>
          <div className="form-group">
            <input
              type="password"
              placeholder="Password"
              value={values.password}
              onChange={(e) => handleChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              required
              className={touched.password && errors.password ? 'error' : ''}
            />
            {touched.password && errors.password && (
              <span className="error-message">{errors.password}</span>
            )}
            {values.password && (
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
              placeholder="Confirm Password"
              value={values.confirmPassword}
              onChange={(e) => handleChange('confirmPassword', e.target.value)}
              onBlur={() => handleBlur('confirmPassword')}
              required
              className={touched.confirmPassword && errors.confirmPassword ? 'error' : ''}
            />
            {touched.confirmPassword && errors.confirmPassword && (
              <span className="error-message">{errors.confirmPassword}</span>
            )}
          </div>
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>
        <p style={{ marginTop: '1rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          Already have an account? <Link to="/login" style={{ color: 'var(--primary)', textDecoration: 'none' }}>Login</Link>
        </p>
      </div>
    </div>
  );
}

export default Signup;

