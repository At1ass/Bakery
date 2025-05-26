import React, { useState } from 'react';
import { login, register } from '../api';
import './Login.css';

export default function Login({ onLogin }) {
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
      setError('Это поле обязательно');
      return false;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Пожалуйста, введите действительный адрес электронной почты');
      return false;
    }

    if (isRegistering) {
      if (password !== confirmPassword) {
        setError('Пароли не совпадают.');
        return false;
      }

      if (password.length < 12) {
        setError('Пароль должен содержать не менее 12 символов');
        return false;
      }

      if (!(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$/.test(password))) {
        setError('Пароль должен содержать хотя бы одну заглавную букву, одну строчную букву, одну цифру и один специальный символ (@$!%*?&).');
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
        setError('Ошибка входа. Проверьте ваши данные.');
      } else if (error.response?.status === 422) {
        setError('Ошибка валидации. Проверьте ваши данные.');
      } else if (error.response?.status === 409 && isRegistering) {
        setError('Этот email уже зарегистрирован. Попробуйте войти.');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        setError('Ошибка сети. Проверьте подключение к интернету.');
      } else {
        setError(error.response?.data?.detail || error.message || 'Произошла неизвестная ошибка.');
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
      <form onSubmit={handleSubmit} className="login-form">
        <h2>{isRegistering ? 'Регистрация' : 'Вход'}</h2>
        
        {error && <div className="error-message" role="alert">{error}</div>}
        
        <div className="form-group">
          <label htmlFor="email">Электронная почта:</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Электронная почта"
            autoComplete="email"
            disabled={loading}
            aria-label="Электронная почта"
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Пароль:</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={handlePasswordChange}
            required
            placeholder="Пароль"
            autoComplete={isRegistering ? "new-password" : "current-password"}
            minLength={isRegistering ? "12" : undefined}
            disabled={loading}
            aria-label="Пароль"
          />
          {isRegistering && passwordStrength && (
            <div className={`password-strength ${getPasswordStrengthClass()}`}>
              Сила пароля: {passwordStrength}
              {passwordStrength !== 'strong' && (
                <div className="password-requirements">
                  Пароль должен содержать не менее 12 символов
                </div>
              )}
            </div>
          )}
        </div>
        
        {isRegistering && (
          <>
            <div className="form-group">
              <label htmlFor="confirmPassword">Подтвердите пароль:</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Подтвердите пароль"
                autoComplete="new-password"
                minLength="12"
                disabled={loading}
                aria-label="Подтвердите пароль"
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="role">Роль:</label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                required
                disabled={loading}
                aria-label="Роль"
              >
                <option value="Customer">Покупатель</option>
                <option value="Seller">Продавец</option>
              </select>
            </div>
          </>
        )}
        
        <button 
          type="submit" 
          className="submit-btn"
          disabled={loading}
          aria-label={isRegistering ? 'Зарегистрироваться' : 'Войти'}
        >
          {loading ? 'Загрузка...' : (isRegistering ? 'Зарегистрироваться' : 'Войти')}
        </button>
        
        <div className="auth-switch">
          <p>
            {isRegistering ? 'Уже есть аккаунт?' : 'Нет аккаунта?'}
            <button
              type="button"
              className="switch-btn"
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError('');
                setPassword('');
                setConfirmPassword('');
                setPasswordStrength('');
              }}
              disabled={loading}
            >
              {isRegistering ? 'Войти здесь' : 'Зарегистрироваться здесь'}
            </button>
          </p>
        </div>
      </form>
    </div>
  );
}
