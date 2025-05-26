import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { login, register } from '../api';
import './Login.css';

export default function Login({ onLogin }) {
  const { t } = useTranslation();
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Customer');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState('');

  const validatePassword = (password) => {
    const hasMinLength = password.length >= 12;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[@$!%*?&]/.test(password);

    if (hasMinLength && hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar) {
      return 'strong';
    } else if (hasMinLength && ((hasUpperCase && hasLowerCase) || (hasNumbers && hasSpecialChar))) {
      return 'medium';
    }
    return 'weak';
  };

  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    setPasswordStrength(validatePassword(newPassword));
  };

  const validateForm = () => {
    if (!email || !password) {
      setError(t('validation.required'));
      return false;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(t('validation.email'));
      return false;
    }

    if (isRegistering) {
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return false;
      }

      if (password.length < 12) {
        setError(t('auth.passwordMinLength'));
        return false;
      }

      if (!(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$/.test(password))) {
        setError('Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character (@$!%*?&).');
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    
    try {
      let loginResponse;
      if (isRegistering) {
        await register(email, password, role);
        // After registration, automatically log in
        loginResponse = await login(email, password);
      } else {
        loginResponse = await login(email, password);
      }

      if (loginResponse && loginResponse.access_token) {
        // Pass the full response with both tokens to the parent component
        onLogin(loginResponse);
      } else {
        console.error('Invalid login response:', loginResponse);
        throw new Error('No access token received');
      }
    } catch (error) {
      console.error('Authentication error:', error);
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        setError(t('auth.loginError'));
      } else if (error.response?.status === 422) {
        setError(t('error.validationError'));
      } else if (error.response?.status === 409 && isRegistering) {
        setError('This email is already registered. Please try logging in instead.');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        setError(t('error.networkError'));
      } else {
        setError(error.response?.data?.detail || error.message || t('error.unknownError'));
      }
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrengthClass = () => {
    switch (passwordStrength) {
      case 'strong':
        return 'password-strong';
      case 'medium':
        return 'password-medium';
      case 'weak':
        return 'password-weak';
      default:
        return '';
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>{isRegistering ? t('auth.register') : t('auth.login')}</h2>
        
        {error && <div className="error-message" role="alert">{error}</div>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">{t('auth.email')}:</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder={t('auth.email')}
              autoComplete="email"
              disabled={loading}
              aria-label={t('auth.email')}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">{t('auth.password')}:</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              required
              placeholder={t('auth.password')}
              autoComplete={isRegistering ? "new-password" : "current-password"}
              minLength={isRegistering ? "12" : undefined}
              disabled={loading}
              aria-label={t('auth.password')}
            />
            {isRegistering && passwordStrength && (
              <div className={`password-strength ${getPasswordStrengthClass()}`}>
                Password strength: {passwordStrength}
                {passwordStrength !== 'strong' && (
                  <div className="password-requirements">
                    {t('auth.passwordMinLength')}
                  </div>
                )}
              </div>
            )}
          </div>
          
          {isRegistering && (
            <>
              <div className="form-group">
                <label htmlFor="confirmPassword">{t('auth.confirmPassword')}:</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder={t('auth.confirmPassword')}
                  autoComplete="new-password"
                  minLength="12"
                  disabled={loading}
                  aria-label={t('auth.confirmPassword')}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="role">{t('auth.role')}:</label>
                <select
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="role-select"
                  disabled={loading}
                  aria-label={t('auth.role')}
                >
                  <option value="Customer">{t('auth.customer')}</option>
                  <option value="Seller">{t('auth.seller')}</option>
                </select>
              </div>
            </>
          )}
          
          <button 
            type="submit" 
            className={`submit-btn ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? (
              <span className="loading-spinner" aria-hidden="true"></span>
            ) : (
              isRegistering ? t('auth.registerButton') : t('auth.loginButton')
            )}
          </button>
        </form>
        
        <div className="toggle-form">
          <button
            onClick={() => {
              setIsRegistering(!isRegistering);
              setError('');
              setPassword('');
              setConfirmPassword('');
              setPasswordStrength('');
            }}
            className="toggle-btn"
            disabled={loading}
          >
            {isRegistering
              ? `${t('auth.alreadyHaveAccount')} ${t('auth.switchToLogin')}`
              : `${t('auth.dontHaveAccount')} ${t('auth.switchToRegister')}`}
          </button>
        </div>
      </div>
    </div>
  );
}
