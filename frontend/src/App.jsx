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
        .catch(() => {
          setToken('');
          setLoading(false);
        });
    } else {
      localStorage.removeItem('token');
      setUser(null);
      setLoading(false);
    }
  }, [token]);

  const handleLogin = (newToken) => {
    setToken(newToken);
  };

  const handleLogout = () => {
    setToken('');
    setOrderItems([]);
  };

  const handleOrder = async () => {
    try {
      await createOrder(token, { items: orderItems });
      setOrderItems([]);
      alert('Order placed successfully!');
    } catch (error) {
      console.error('Failed to place order:', error);
      setError('Failed to place order');
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

      {error && <div className="error-message">{error}</div>}

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
            onSelect={(items) => setOrderItems([...orderItems, ...items])}
          />
          {orderItems.length > 0 && (
            <OrderForm
              items={orderItems}
              products={products}
              onSubmit={handleOrder}
              onClear={() => setOrderItems([])}
            />
          )}
        </div>
      )}
    </div>
  );
}
