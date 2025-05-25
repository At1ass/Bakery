import React, { useState } from 'react';
import { login, register } from '../api';
import './Login.css';

export default function Login({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      if (isRegistering) {
        await register(email, password, role);
        // After registration, automatically log in
        const response = await login(email, password);
        onLogin(response.access_token);
      } else {
        const response = await login(email, password);
        onLogin(response.access_token);
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setError(error.response?.data?.detail || 'Authentication failed');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>Password:</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          
          {isRegistering && (
            <div className="form-group">
              <label>Role:</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="role-select"
              >
                <option value="user">Customer</option>
                <option value="seller">Seller</option>
              </select>
            </div>
          )}
          
          <button type="submit" className="submit-btn">
            {isRegistering ? 'Register' : 'Login'}
          </button>
        </form>
        
        <div className="toggle-form">
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            className="toggle-btn"
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
