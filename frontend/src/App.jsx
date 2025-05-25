import React, { useState, useEffect } from 'react';
import { login, fetchProducts, createOrder, getCurrentUser } from './api.js';
import Login from './components/Login.jsx';
import ProductList from './components/ProductList.jsx';
import OrderForm from './components/OrderForm.jsx';
import SellerDashboard from './components/SellerDashboard.jsx';
import './App.css';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  const [products, setProducts] = useState([]);
  const [orderItems, setOrderItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      // Fetch user data and products
      Promise.all([
        getCurrentUser(token),
        fetchProducts(token)
      ])
        .then(([userResponse, productsResponse]) => {
          setUser(userResponse.data);
          setProducts(productsResponse.data);
          setLoading(false);
        })
        .catch((error) => {
          console.error('Failed to initialize:', error);
          setToken('');
          setError('Failed to load user data. Please log in again.');
          setTimeout(() => setError(''), 5000);
          setLoading(false);
        });
    } else {
      localStorage.removeItem('token');
      setUser(null);
      setLoading(false);
    }
  }, [token]);

  const handleLogin = (newToken) => {
    setError('');
    setToken(newToken);
  };

  const handleLogout = () => {
    setToken('');
    setOrderItems([]);
    setError('');
    setSuccessMessage('');
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
    } catch (error) {
      console.error('Failed to place order:', error);
      setError(error.response?.data?.detail || 'Failed to place order. Please try again.');
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
