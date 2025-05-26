import React, { useState } from 'react';
import { login, register } from '../api';
import './Login.css';

export default function Login({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState('');

  const validatePassword = (password) => {
    const hasMinLength = password.length >= 8;
    const hasUpperCase = /[A-Z]/.test(password);
    const hasLowerCase = /[a-z]/.test(password);
    const hasNumbers = /\d/.test(password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    if (hasMinLength && hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar) {
      return 'strong';
    } else if (hasMinLength && (hasUpperCase || hasLowerCase) && (hasNumbers || hasSpecialChar)) {
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
      setError('Please fill in all required fields.');
      return false;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address.');
      return false;
    }

    if (isRegistering) {
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return false;
      }

      if (password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return false;
      }

      if (passwordStrength === 'weak') {
        setError('Password is too weak. Please include uppercase, lowercase, numbers, and special characters.');
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
        onLogin(loginResponse.access_token);
      } else {
        console.error('Invalid login response:', loginResponse);
        throw new Error('No access token received');
      }
    } catch (error) {
      console.error('Authentication error:', error);
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        setError('Invalid email or password. Please try again.');
      } else if (error.response?.status === 422) {
        setError('Invalid input format. Please check your email and password.');
      } else if (error.response?.status === 409 && isRegistering) {
        setError('This email is already registered. Please try logging in instead.');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        setError('Unable to connect to the authentication service. Please try again later.');
      } else {
        setError(error.response?.data?.detail || error.message || 'Authentication failed. Please try again.');
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
        <h2>{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>
        
        {error && <div className="error-message" role="alert">{error}</div>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email:</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
              autoComplete="email"
              disabled={loading}
              aria-label="Email address"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={handlePasswordChange}
              required
              placeholder="Enter your password"
              autoComplete={isRegistering ? "new-password" : "current-password"}
              minLength="8"
              disabled={loading}
              aria-label="Password"
            />
            {isRegistering && passwordStrength && (
              <div className={`password-strength ${getPasswordStrengthClass()}`}>
                Password strength: {passwordStrength}
              </div>
            )}
          </div>
          
          {isRegistering && (
            <>
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password:</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Confirm your password"
                  autoComplete="new-password"
                  minLength="8"
                  disabled={loading}
                  aria-label="Confirm password"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="role">Role:</label>
                <select
                  id="role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="role-select"
                  disabled={loading}
                  aria-label="Select role"
                >
                  <option value="user">Customer</option>
                  <option value="seller">Seller</option>
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
              isRegistering ? 'Register' : 'Login'
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
              ? 'Already have an account? Login'
              : 'Need an account? Register'}
          </button>
        </div>
      </div>
    </div>
  );
}
