import React, { useState, useEffect, useCallback } from 'react';
import { login, fetchProducts, createOrder, getCurrentUser } from './api.js';
import Login from './components/Login.jsx';
import ProductList from './components/ProductList.jsx';
import OrderForm from './components/OrderForm.jsx';
import SellerDashboard from './components/SellerDashboard.jsx';
import './App.css';

const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  const [products, setProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [sessionTimeout, setSessionTimeout] = useState(null);

  const resetSession = useCallback(() => {
    if (sessionTimeout) {
      clearTimeout(sessionTimeout);
    }
    const timeout = setTimeout(() => {
      handleLogout();
      setError('Your session has expired. Please log in again.');
    }, SESSION_TIMEOUT);
    setSessionTimeout(timeout);
  }, [sessionTimeout]);

  const handleUserActivity = useCallback(() => {
    resetSession();
  }, [resetSession]);

  useEffect(() => {
    // Add event listeners for user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach(event => {
      window.addEventListener(event, handleUserActivity);
    });

    return () => {
      events.forEach(event => {
        window.removeEventListener(event, handleUserActivity);
      });
      if (sessionTimeout) {
        clearTimeout(sessionTimeout);
      }
    };
  }, [handleUserActivity, sessionTimeout]);

  useEffect(() => {
    const initializeApp = async () => {
      if (token) {
        try {
          localStorage.setItem('token', token);
          resetSession();

          const [userResponse, productsResponse] = await Promise.all([
            getCurrentUser(token),
            fetchProducts(token)
          ]);

          setUser(userResponse.data);
          setProducts(productsResponse.data);
        } catch (error) {
          console.error('Failed to initialize:', error);
          
          if (error.response?.status === 401) {
            setError('Your session has expired. Please log in again.');
          } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
            setError('Unable to connect to the server. Please check your connection and try again.');
          } else {
            setError('Failed to load user data. Please log in again.');
          }
          
          handleLogout();
        } finally {
          setLoading(false);
        }
      } else {
        handleLogout();
        setLoading(false);
      }
    };

    initializeApp();
  }, [token, resetSession]);

  const handleLogin = (newToken) => {
    setError('');
    setToken(newToken);
    resetSession();
  };

  const handleLogout = () => {
    setToken('');
    localStorage.removeItem('token');
    setUser(null);
    setOrderItems([]);
    setError('');
    setSuccessMessage('');
    if (sessionTimeout) {
      clearTimeout(sessionTimeout);
    }
  };

  const handleOrder = async () => {
    setError('');
    setSuccessMessage('');
    
    if (!orderItems.length) {
      setError('Please add items to your order');
      setTimeout(() => setError(''), 5000);
      return;
    }

    try {
      await createOrder(token, { items: orderItems });
      setOrderItems([]);
      setSuccessMessage('Order placed successfully!');
      setTimeout(() => setSuccessMessage(''), 5000);
      
      // Refresh products to update availability
      const productsResponse = await fetchProducts(token);
      setProducts(productsResponse.data);
      resetSession();
    } catch (error) {
      console.error('Failed to place order:', error);
      if (error.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
        handleLogout();
      } else {
        setError(error.response?.data?.detail || 'Failed to place order. Please try again.');
      }
      setTimeout(() => setError(''), 5000);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="container">
      <header>
        <h1>Confectionery Store</h1>
        <div className="user-info">
          <span>Welcome, {user?.email}</span>
          <button onClick={handleLogout} className="logout-btn">
            Logout
          </button>
        </div>
      </header>

      {error && <div className="error-message" role="alert">{error}</div>}
      {successMessage && <div className="success-message" role="status">{successMessage}</div>}

      {user?.role === 'seller' ? (
        <SellerDashboard
          products={products}
          token={token}
          onProductsChange={setProducts}
          onError={(error) => {
            if (error.response?.status === 401) {
              handleLogout();
              setError('Your session has expired. Please log in again.');
            }
          }}
        />
      ) : (
        <div className="user-view">
          <ProductList
            products={products}
            onSelect={(items) => {
              setError('');
              setOrderItems([...orderItems, ...items]);
            }}
          />
          {orderItems.length > 0 && (
            <OrderForm
              items={orderItems}
              products={products}
              onSubmit={handleOrder}
              onClear={() => {
                setError('');
                setOrderItems([]);
              }}
            />
          )}
        </div>
      )}
    </div>
  );
}
