import React, { useState, useEffect } from 'react';
import { createProduct, updateProduct, deleteProduct, fetchOrders } from '../api';
import './SellerDashboard.css';

export default function SellerDashboard({ products, token, onProductsChange }) {
  const [orders, setOrders] = useState([]);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    price: '',
    recipe: []  // Initialize empty recipe array
  });
  const [error, setError] = useState('');

  useEffect(() => {
    fetchOrders(token)
      .then(response => setOrders(response.data))
      .catch(error => {
        console.error('Failed to fetch orders:', error);
        setError('Failed to load orders');
      });
  }, [token]);

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const productData = {
        name: newProduct.name,
        description: newProduct.description,
        price: parseFloat(newProduct.price),
        recipe: []  // Send empty recipe array
      };

      const response = await createProduct(token, productData);
      onProductsChange([...products, response.data]);
      setNewProduct({ name: '', description: '', price: '', recipe: [] });
    } catch (error) {
      console.error('Failed to create product:', error);
      setError(error.response?.data?.detail || 'Failed to create product');
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    try {
      await deleteProduct(token, productId);
      onProductsChange(products.filter(p => p.id !== productId));
    } catch (error) {
      console.error('Failed to delete product:', error);
      setError('Failed to delete product');
    }
  };

  return (
    <div className="seller-dashboard">
      <h2>Seller Dashboard</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <section className="product-management">
        <h3>Add New Product</h3>
        <form onSubmit={handleCreateProduct} className="product-form">
          <div className="form-group">
            <label>Name:</label>
            <input
              type="text"
              value={newProduct.name}
              onChange={e => setNewProduct({...newProduct, name: e.target.value})}
              required
              placeholder="Product name"
            />
          </div>
          
          <div className="form-group">
            <label>Description:</label>
            <textarea
              value={newProduct.description}
              onChange={e => setNewProduct({...newProduct, description: e.target.value})}
              required
              placeholder="Product description"
            />
          </div>
          
          <div className="form-group">
            <label>Price:</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={newProduct.price}
              onChange={e => setNewProduct({...newProduct, price: e.target.value})}
              required
              placeholder="0.00"
            />
          </div>
          
          <button type="submit" className="submit-btn">Add Product</button>
        </form>
      </section>

      <section className="product-list">
        <h3>Current Products</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Price</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map(product => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td>{product.description}</td>
                  <td>${product.price.toFixed(2)}</td>
                  <td>
                    <button 
                      onClick={() => handleDeleteProduct(product.id)}
                      className="delete-btn"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="orders">
        <h3>Recent Orders</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.user_email}</td>
                  <td>${order.total.toFixed(2)}</td>
                  <td>
                    <span className={`status ${order.status}`}>
                      {order.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
} 