import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';
import { useFormValidation } from '../hooks/useFormValidation';
import { validators } from '../utils/validation';
import { signUp } from '../utils/cognito';
import './Login.css';

function Signup() {
  const { success, error: showError } = useToast();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [requiresVerification, setRequiresVerification] = useState(false);
  const [signupEmail, setSignupEmail] = useState('');

  const signupSchema = {
    email: [validators.required, validators.email],
    password: [validators.required, validators.minLength(8)],
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

  if (requiresVerification) {
    return (
      <div className="login">
        <div className="login-container">
          <img src="/elevare-logo.svg" alt="ElevareAI" style={{ width: '80px', height: '80px', marginBottom: '1rem' }} />
          <h1>Check Your Email</h1>
          <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)' }}>
            We've sent a verification code to <strong>{signupEmail}</strong>
          </p>
          <p style={{ marginBottom: '2rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Please check your email and click the verification link, or enter the verification code when you log in.
          </p>
          <Link 
            to="/login" 
            style={{ 
              display: 'inline-block',
              padding: '0.75rem 1.5rem',
              background: 'var(--primary-color)',
              color: 'white',
              textDecoration: 'none',
              borderRadius: 'var(--border-radius-sm)',
              marginTop: '1rem'
            }}
          >
            Go to Login
          </Link>
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
              placeholder="Password (min 8 characters)"
              value={values.password}
              onChange={(e) => handleChange('password', e.target.value)}
              onBlur={() => handleBlur('password')}
              required
              className={touched.password && errors.password ? 'error' : ''}
            />
            {touched.password && errors.password && (
              <span className="error-message">{errors.password}</span>
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

