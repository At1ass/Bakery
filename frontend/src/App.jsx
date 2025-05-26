import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { login, fetchProducts, createOrder, getCurrentUser, refreshToken } from './api.js';
import Login from './components/Login.jsx';
import ProductList from './components/ProductList.jsx';
import OrderForm from './components/OrderForm.jsx';
import SellerDashboard from './components/SellerDashboard.jsx';
import './App.css';

// Read from environment variables with fallback
const SESSION_TIMEOUT = parseInt(window.env?.SESSION_TIMEOUT) || 30 * 60 * 1000; // 30 minutes
const TOKEN_REFRESH_INTERVAL = parseInt(window.env?.TOKEN_REFRESH_INTERVAL) || 25 * 60 * 1000; // 25 minutes

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert" className="error-boundary">
      <p>Something went wrong:</p>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

function LoadingSpinner() {
  return <div className="loading-spinner">Loading...</div>;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  const [products, setProducts] = useState([]);
  // Initialize orderItems from localStorage if available
  const [orderItems, setOrderItems] = useState(() => {
    try {
      const savedOrderItems = localStorage.getItem('orderItems');
      return savedOrderItems ? JSON.parse(savedOrderItems) : [];
    } catch (error) {
      console.error('Failed to parse orderItems from localStorage:', error);
      return [];
    }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [sessionTimeout, setSessionTimeout] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Save orderItems to localStorage whenever it changes
  useEffect(() => {
    if (orderItems.length > 0) {
      localStorage.setItem('orderItems', JSON.stringify(orderItems));
    } else {
      localStorage.removeItem('orderItems');
    }
  }, [orderItems]);

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

  // Add token refresh mechanism
  useEffect(() => {
    if (!token) return;

    const refreshInterval = setInterval(async () => {
      try {
        const refreshTokenValue = localStorage.getItem('refreshToken');
        if (!refreshTokenValue) {
          throw new Error('No refresh token available');
        }
        
        const newToken = await refreshToken(refreshTokenValue);
        setToken(newToken);
        localStorage.setItem('token', newToken);
        resetSession();
      } catch (error) {
        console.error('Failed to refresh token:', error);
        handleLogout();
        setError('Session expired. Please log in again.');
      }
    }, TOKEN_REFRESH_INTERVAL);

    return () => clearInterval(refreshInterval);
  }, [token, resetSession]);

  const handleUserActivity = useCallback(() => {
    if (token && user) {
      resetSession();
    }
  }, [resetSession, token, user]);

  useEffect(() => {
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    
    const cleanup = () => {
      events.forEach(event => {
        window.removeEventListener(event, handleUserActivity);
      });
      if (sessionTimeout) {
        clearTimeout(sessionTimeout);
      }
    };

    events.forEach(event => {
      window.addEventListener(event, handleUserActivity);
    });

    return cleanup;
  }, [handleUserActivity, sessionTimeout]);

  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    const RETRY_DELAY = 2000;

    const initializeUser = async () => {
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
        } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
          retryCount++;
          setError(`Unable to connect to the server. Retry ${retryCount}/${MAX_RETRIES}...`);
          setTimeout(initializeUser, RETRY_DELAY);
        } else {
          handleLogout();
          setError('Failed to load user data. Please try logging in again.');
        }
        setLoading(false);
        setIsInitialized(true);
      }
    };

    initializeUser();

    return () => {
      isMounted = false;
    };
  }, [token, resetSession]);

  useEffect(() => {
    let isMounted = true;

    const loadProducts = async () => {
      if (!token || !user) {
        setProducts([]);
        return;
      }

      try {
        const response = await fetchProducts(token);
        if (!isMounted) return;

        const productsArray = Array.isArray(response?.data) ? response.data : [];
        setProducts(productsArray);
        setError('');
      } catch (error) {
        if (!isMounted) return;

        if (error.response?.status === 401) {
          handleLogout();
          setError('Session expired. Please log in again.');
        } else {
          setError('Failed to load products. Please refresh the page.');
          setProducts([]);
        }
      }
    };

    loadProducts();

    return () => {
      isMounted = false;
    };
  }, [token, user]);

  const handleLogin = useCallback((tokenData) => {
    setError('');
    setToken(tokenData.access_token);
    localStorage.setItem('token', tokenData.access_token);
    // Refresh token is stored in localStorage by the login function
    setIsInitialized(false);
  }, []);

  const handleLogout = useCallback(() => {
    setToken('');
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('orderItems');
    setUser(null);
    setOrderItems([]);
    setError('');
    setSuccessMessage('');
    setIsInitialized(true);
    if (sessionTimeout) {
      clearTimeout(sessionTimeout);
    }
  }, [sessionTimeout]);

  const handleAddToOrder = useCallback((product) => {
    setOrderItems(prevItems => [...prevItems, product]);
    setSuccessMessage('Product added to order');
    setTimeout(() => setSuccessMessage(''), 3000);
  }, []);

  const handlePlaceOrder = useCallback(async (orderData) => {
    setError('');
    setSuccessMessage('');
    
    if (!orderItems.length) {
      setError('Please add items to your order');
      setTimeout(() => setError(''), 5000);
      return;
    }

    try {
      console.log('Sending order data:', orderData);
      const response = await createOrder(token, orderData);
      console.log('Order response:', response);
      
      setOrderItems([]);
      localStorage.removeItem('orderItems');
      setSuccessMessage('Order placed successfully!');
      setTimeout(() => setSuccessMessage(''), 5000);
      
      // Refresh product list to update availability
      try {
        const productsResponse = await fetchProducts(token);
        console.log('Products response after order:', productsResponse);
        if (productsResponse?.data) {
          const productsArray = Array.isArray(productsResponse.data) ? 
            productsResponse.data : 
            productsResponse.data.products || [];
          setProducts(productsArray);
        }
      } catch (productError) {
        console.error('Failed to refresh products after order:', productError);
      }
      
      resetSession();
    } catch (error) {
      console.error('Failed to place order:', error);
      if (error.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
        handleLogout();
      } else {
        setError(error.response?.data?.detail || error.message || 'Failed to place order. Please try again.');
      }
      setTimeout(() => setError(''), 5000);
    }
  }, [token, orderItems, resetSession, handleLogout]);

  const handleProductsChange = useCallback((newProducts) => {
    setProducts(newProducts);
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={() => {
        setError('');
        setIsInitialized(false);
      }}
    >
      <div className="app" onClick={handleUserActivity}>
        <header className="app-header">
          <h1>Confectionery Store</h1>
          {user && (
            <div className="user-info">
              Welcome, {user.email}
              <button onClick={handleLogout} className="logout-btn">Logout</button>
            </div>
          )}
        </header>

        {error && (
          <div className="error-message" role="alert" aria-live="polite">
            {error}
          </div>
        )}
        {successMessage && (
          <div className="success-message" role="status" aria-live="polite">
            {successMessage}
          </div>
        )}

        <Suspense fallback={<LoadingSpinner />}>
          {!token ? (
            <Login onLogin={handleLogin} />
          ) : user?.role === 'Seller' || user?.role === 'Admin' ? (
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
                  onClear={setOrderItems} 
                />
              )}
            </div>
          )}
        </Suspense>
      </div>
    </ErrorBoundary>
  );
}
