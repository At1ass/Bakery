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
  const [isInitialized, setIsInitialized] = useState(false);

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
    if (token && user) {
      resetSession();
    }
  }, [resetSession, token, user]);

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

  // Single useEffect for user initialization
  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 2000;

    const initializeUser = async () => {
      // Skip if already initialized or no token
      if (isInitialized || !token) {
        setLoading(false);
        return;
      }

      try {
        const response = await getCurrentUser(token);
        if (!isMounted) return;

        setUser(response.data);
        resetSession();
        setLoading(false);
        setIsInitialized(true);
        setError('');
      } catch (error) {
        if (!isMounted) return;

        console.error('Failed to fetch user:', error);
        
        if (error.response?.status === 401 || retryCount >= MAX_RETRIES) {
          handleLogout();
          setError('Session expired or invalid. Please log in again.');
          setLoading(false);
          setIsInitialized(true);
        } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          retryCount++;
          setError(`Unable to connect to the server. Retry ${retryCount}/${MAX_RETRIES}...`);
          setTimeout(initializeUser, RETRY_DELAY);
        } else {
          handleLogout();
          setError('Failed to load user data. Please try logging in again.');
          setLoading(false);
          setIsInitialized(true);
        }
      }
    };

    initializeUser();

    return () => {
      isMounted = false;
    };
  }, [token, resetSession]);

  // Products fetch effect
  useEffect(() => {
    let isMounted = true;

    const loadProducts = async () => {
      if (!token || !user) return;

      try {
        console.log('Fetching products with token:', token);
        const response = await fetchProducts(token);
        console.log('Raw products response:', response);
        
        if (isMounted) {
          if (Array.isArray(response.data)) {
            console.log('Setting products state with:', response.data);
            setProducts(response.data);
          } else {
            console.error('Invalid products data format:', response.data);
            setError('Failed to load products: Invalid data format');
          }
        }
      } catch (error) {
        console.error('Failed to fetch products:', error);
        if (isMounted && error.response?.status === 401) {
          handleLogout();
          setError('Session expired. Please log in again.');
        } else if (isMounted) {
          setError('Failed to load products. Please refresh the page.');
        }
      }
    };

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, [token, user]);

  const handleLogin = useCallback((newToken) => {
    setError('');
    setToken(newToken);
    localStorage.setItem('token', newToken);
    setIsInitialized(false);
  }, []);

  const handleLogout = useCallback(() => {
    setToken('');
    localStorage.removeItem('token');
    setUser(null);
    setOrderItems([]);
    setError('');
    setSuccessMessage('');
    setIsInitialized(true);
    if (sessionTimeout) {
      clearTimeout(sessionTimeout);
    }
  }, [sessionTimeout]);

  const handleAddToOrder = (product) => {
    setOrderItems([...orderItems, product]);
    setSuccessMessage('Product added to order');
    setTimeout(() => setSuccessMessage(''), 3000);
  };

  const handlePlaceOrder = async (orderData) => {
    setError('');
    setSuccessMessage('');
    
    if (!orderItems.length) {
      setError('Please add items to your order');
      setTimeout(() => setError(''), 5000);
      return;
    }

    try {
      await createOrder(token, orderData);
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

  const handleProductsChange = useCallback((newProducts) => {
    setProducts(newProducts);
  }, []);

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="app" onClick={handleUserActivity}>
      <header>
        <h1>Confectionery Store</h1>
        {user && (
          <div className="user-info">
            Welcome, {user.email}
            <button onClick={handleLogout} className="logout-btn">Logout</button>
          </div>
        )}
      </header>

      {error && <div className="error-message" role="alert">{error}</div>}
      {successMessage && <div className="success-message" role="status">{successMessage}</div>}

      {!token ? (
        <Login onLogin={handleLogin} />
      ) : user?.role === 'seller' ? (
        <SellerDashboard 
          products={products} 
          token={token} 
          onProductsChange={handleProductsChange}
        />
      ) : (
        <div className="customer-view">
          <ProductList 
            products={products} 
            onAddToOrder={handleAddToOrder} 
          />
          {orderItems.length > 0 && (
            <OrderForm 
              orderItems={orderItems} 
              onSubmit={handlePlaceOrder}
              onClear={() => setOrderItems([])} 
            />
          )}
        </div>
      )}
    </div>
  );
}
