import React, { useState, useEffect } from 'react';
import { createProduct, updateProduct, deleteProduct, fetchOrders } from '../api';
import './SellerDashboard.css';

export default function SellerDashboard({ products, token, onProductsChange }) {
  const [orders, setOrders] = useState([]);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    tags: [],
    recipe: []
  });
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    fetchOrders(token)
      .then(response => setOrders(response.data))
      .catch(error => {
        console.error('Failed to fetch orders:', error);
        setError('Failed to load orders');
        setTimeout(() => setError(''), 5000); // Clear error after 5 seconds
      });
  }, [token]);

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    
    try {
      const productData = {
        name: newProduct.name,
        description: newProduct.description,
        price: parseFloat(newProduct.price),
        category: newProduct.category || 'Other',
        tags: newProduct.tags.length ? newProduct.tags : ['General'],
        recipe: newProduct.recipe || [],
        is_available: true
      };

      const response = await createProduct(token, productData);
      onProductsChange([...products, response.data]);
      setNewProduct({ 
        name: '', 
        description: '', 
        price: '', 
        category: '',
        tags: [],
        recipe: [] 
      });
      setSuccessMessage('Product created successfully!');
      setTimeout(() => setSuccessMessage(''), 5000); // Clear success message after 5 seconds
    } catch (error) {
      console.error('Failed to create product:', error);
      setError(error.response?.data?.detail || 'Failed to create product');
      setTimeout(() => setError(''), 5000); // Clear error after 5 seconds
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    setError('');
    setSuccessMessage('');
    
    try {
      await deleteProduct(token, productId);
      onProductsChange(products.filter(p => p.id !== productId));
      setSuccessMessage('Product deleted successfully!');
      setTimeout(() => setSuccessMessage(''), 5000); // Clear success message after 5 seconds
    } catch (error) {
      console.error('Failed to delete product:', error);
      setError('Failed to delete product');
      setTimeout(() => setError(''), 5000); // Clear error after 5 seconds
    }
  };

  return (
    <div className="seller-dashboard">
      <h2>Seller Dashboard</h2>
      
      {error && <div className="error-message" role="alert">{error}</div>}
      {successMessage && <div className="success-message" role="status">{successMessage}</div>}
      
      <section className="product-management">
        <h3>Add New Product</h3>
        <form onSubmit={handleCreateProduct} className="product-form">
          <div className="form-group">
            <label htmlFor="productName">Name:</label>
            <input
              id="productName"
              type="text"
              value={newProduct.name}
              onChange={e => setNewProduct({...newProduct, name: e.target.value})}
              required
              placeholder="Product name"
              minLength="1"
              maxLength="100"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="productDescription">Description:</label>
            <textarea
              id="productDescription"
              value={newProduct.description}
              onChange={e => setNewProduct({...newProduct, description: e.target.value})}
              required
              placeholder="Product description"
              minLength="1"
              maxLength="500"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="productPrice">Price:</label>
            <input
              id="productPrice"
              type="number"
              step="0.01"
              min="0.01"
              value={newProduct.price}
              onChange={e => setNewProduct({...newProduct, price: e.target.value})}
              required
              placeholder="0.00"
            />
          </div>

          <div className="form-group">
            <label htmlFor="productCategory">Category:</label>
            <input
              id="productCategory"
              type="text"
              value={newProduct.category}
              onChange={e => setNewProduct({...newProduct, category: e.target.value})}
              placeholder="Product category"
              maxLength="50"
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
                <th>Category</th>
                <th>Price</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map(product => (
                <tr key={product.id}>
                  <td>{product.name}</td>
                  <td>{product.description}</td>
                  <td>{product.category || 'Other'}</td>
                  <td>${parseFloat(product.price).toFixed(2)}</td>
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
                  <td>${parseFloat(order.total).toFixed(2)}</td>
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