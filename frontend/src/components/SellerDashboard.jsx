import React, { useState, useEffect } from 'react';
import { createProduct, updateProduct, deleteProduct, fetchOrders } from '../api';
import './SellerDashboard.css';

// Define valid categories based on the catalog service model
const VALID_CATEGORIES = [
  'Cakes', 'Cupcakes', 'Cookies', 'Pastries', 'Breads',
  'Pies', 'Donuts', 'Chocolates', 'Ice Cream', 'Other'
];

export default function SellerDashboard({ products = [], token, onProductsChange }) {
  const [orders, setOrders] = useState([]);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    price: '',
    category: 'Other',
    tags: [],
    recipe: [],
    is_available: true
  });
  const [tagInput, setTagInput] = useState('');
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingTagInput, setEditingTagInput] = useState('');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Ensure products is always an array
  const displayProducts = Array.isArray(products) ? products : [];
  console.log('SellerDashboard displayProducts:', displayProducts);

  useEffect(() => {
    if (!token) return;

    fetchOrders(token)
      .then(response => {
        console.log('Orders API response:', response);
        if (response?.data) {
          let ordersData;
          if (Array.isArray(response.data)) {
            ordersData = response.data;
          } else if (response.data.orders && Array.isArray(response.data.orders)) {
            ordersData = response.data.orders;
          } else if (response.data.data && Array.isArray(response.data.data)) {
            ordersData = response.data.data;
          } else {
            console.warn('Unexpected orders data format:', response.data);
            ordersData = [];
          }
          console.log('Processed orders data:', ordersData);
          setOrders(ordersData);
        }
      })
      .catch(error => {
        console.error('Failed to fetch orders:', error);
        setError('Failed to load orders');
        setTimeout(() => setError(''), 5000);
      });
  }, [token]);

  const handleAddTag = (isEditing = false) => {
    const currentTags = isEditing ? [...(editingProduct.tags || [])] : [...(newProduct.tags || [])];
    const newTag = isEditing ? editingTagInput.trim() : tagInput.trim();
    
    if (!newTag) return;
    
    // Validate tag format using regex (letters, numbers, and hyphens only)
    if (!/^[\w\-]+$/.test(newTag)) {
      setError('Tags can only contain letters, numbers, and hyphens');
      setTimeout(() => setError(''), 5000);
      return;
    }
    
    // Check if tag already exists (case insensitive)
    if (currentTags.some(tag => tag.toLowerCase() === newTag.toLowerCase())) {
      setError('This tag already exists');
      setTimeout(() => setError(''), 5000);
      return;
    }
    
    // Add tag
    if (isEditing) {
      setEditingProduct({
        ...editingProduct,
        tags: [...currentTags, newTag]
      });
      setEditingTagInput('');
    } else {
      setNewProduct({
        ...newProduct,
        tags: [...currentTags, newTag]
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove, isEditing = false) => {
    if (isEditing) {
      setEditingProduct({
        ...editingProduct,
        tags: editingProduct.tags.filter(tag => tag !== tagToRemove)
      });
    } else {
      setNewProduct({
        ...newProduct,
        tags: newProduct.tags.filter(tag => tag !== tagToRemove)
      });
    }
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    
    try {
      // Validate price is a positive number
      const price = parseFloat(newProduct.price);
      if (isNaN(price) || price <= 0 || price >= 10000) {
        setError('Price must be a positive number less than 10,000');
        return;
      }
      
      // Validate name and description
      if (!newProduct.name.trim() || !newProduct.description.trim()) {
        setError('Name and description are required');
        return;
      }
      
      // Ensure category is valid
      if (!VALID_CATEGORIES.includes(newProduct.category)) {
        setError(`Category must be one of: ${VALID_CATEGORIES.join(', ')}`);
        return;
      }

      const productData = {
        name: newProduct.name.trim(),
        description: newProduct.description.trim(),
        price: Number(price.toFixed(2)),
        category: newProduct.category,
        tags: newProduct.tags.length ? newProduct.tags : ['uncategorized'],
        recipe: [],  // Empty recipe for now
        is_available: true
      };

      console.log('Creating product with data:', productData);
      const response = await createProduct(token, productData);
      console.log('Create product response:', response);

      if (response?.data) {
        const newProductData = response.data;
        console.log('New product created:', newProductData);
        onProductsChange([...displayProducts, newProductData]);
        setNewProduct({ 
          name: '', 
          description: '', 
          price: '', 
          category: 'Other',
          tags: [],
          recipe: [],
          is_available: true
        });
        setTagInput('');
        setSuccessMessage('Product created successfully!');
        setTimeout(() => setSuccessMessage(''), 5000);
      }
    } catch (error) {
      console.error('Failed to create product:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to create product');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleUpdateProduct = async (e) => {
    e.preventDefault();
    if (!editingProduct) return;

    setError('');
    setSuccessMessage('');
    
    try {
      // Validate price is a positive number
      const price = parseFloat(editingProduct.price);
      if (isNaN(price) || price <= 0 || price >= 10000) {
        setError('Price must be a positive number less than 10,000');
        return;
      }
      
      // Validate name and description
      if (!editingProduct.name.trim() || !editingProduct.description.trim()) {
        setError('Name and description are required');
        return;
      }
      
      // Ensure category is valid
      if (!VALID_CATEGORIES.includes(editingProduct.category)) {
        setError(`Category must be one of: ${VALID_CATEGORIES.join(', ')}`);
        return;
      }

      const productData = {
        name: editingProduct.name.trim(),
        description: editingProduct.description.trim(),
        price: Number(price.toFixed(2)),
        category: editingProduct.category,
        tags: editingProduct.tags.length ? editingProduct.tags : ['uncategorized'],
        recipe: editingProduct.recipe || [],
        is_available: editingProduct.is_available !== undefined ? editingProduct.is_available : true
      };

      console.log('Updating product with data:', productData);
      const productId = editingProduct._id || editingProduct.id;
      const response = await updateProduct(token, productId, productData);
      console.log('Update product response:', response);

      if (response?.data) {
        const updatedProductData = response.data;
        console.log('Product updated:', updatedProductData);
        
        // Update the products array with the updated product
        const updatedProducts = displayProducts.map(p => 
          (p._id || p.id) === productId ? updatedProductData : p
        );
        onProductsChange(updatedProducts);
        setEditingProduct(null);
        setSuccessMessage('Product updated successfully!');
        setTimeout(() => setSuccessMessage(''), 5000);
      }
    } catch (error) {
      console.error('Failed to update product:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to update product');
      setTimeout(() => setError(''), 5000);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!productId) {
      console.error('No product ID provided for deletion');
      setError('Cannot delete product: Invalid ID');
      return;
    }

    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    setError('');
    setSuccessMessage('');
    
    try {
      console.log('Deleting product with ID:', productId);
      await deleteProduct(token, productId);
      const updatedProducts = displayProducts.filter(p => (p._id || p.id) !== productId);
      console.log('Updated products after deletion:', updatedProducts);
      onProductsChange(updatedProducts);
      setSuccessMessage('Product deleted successfully!');
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (error) {
      console.error('Failed to delete product:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to delete product');
      setTimeout(() => setError(''), 5000);
    }
  };

  const startEditingProduct = (product) => {
    setEditingProduct({...product});
    setEditingTagInput('');
  };

  const cancelEditing = () => {
    setEditingProduct(null);
    setEditingTagInput('');
  };

  // Handle tag input keypress (Enter key)
  const handleTagKeyPress = (e, isEditing = false) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag(isEditing);
    }
  };

  return (
    <div className="seller-dashboard">
      <h2>Seller Dashboard</h2>
      
      {error && <div className="error-message" role="alert">{error}</div>}
      {successMessage && <div className="success-message" role="status">{successMessage}</div>}
      
      <section className="product-management">
        {!editingProduct ? (
          <>
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
                  max="9999.99"
                  value={newProduct.price}
                  onChange={e => setNewProduct({...newProduct, price: e.target.value})}
                  required
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label htmlFor="productCategory">Category:</label>
                <select
                  id="productCategory"
                  value={newProduct.category}
                  onChange={e => setNewProduct({...newProduct, category: e.target.value})}
                  required
                >
                  {VALID_CATEGORIES.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="productTags">Tags:</label>
                <div className="tag-input-container">
                  <input
                    id="productTags"
                    type="text"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyPress={e => handleTagKeyPress(e, false)}
                    placeholder="Add tag and press Enter"
                    maxLength="30"
                  />
                  <button 
                    type="button" 
                    onClick={() => handleAddTag(false)}
                    className="add-tag-btn"
                  >
                    Add
                  </button>
                </div>
                {newProduct.tags.length > 0 && (
                  <div className="tags-container">
                    {newProduct.tags.map(tag => (
                      <span key={tag} className="tag">
                        {tag}
                        <button 
                          type="button" 
                          onClick={() => handleRemoveTag(tag, false)}
                          className="remove-tag-btn"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <button type="submit" className="submit-btn">Add Product</button>
            </form>
          </>
        ) : (
          <>
            <h3>Edit Product</h3>
            <form onSubmit={handleUpdateProduct} className="product-form">
              <div className="form-group">
                <label htmlFor="editProductName">Name:</label>
                <input
                  id="editProductName"
                  type="text"
                  value={editingProduct.name}
                  onChange={e => setEditingProduct({...editingProduct, name: e.target.value})}
                  required
                  placeholder="Product name"
                  minLength="1"
                  maxLength="100"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="editProductDescription">Description:</label>
                <textarea
                  id="editProductDescription"
                  value={editingProduct.description}
                  onChange={e => setEditingProduct({...editingProduct, description: e.target.value})}
                  required
                  placeholder="Product description"
                  minLength="1"
                  maxLength="500"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="editProductPrice">Price:</label>
                <input
                  id="editProductPrice"
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="9999.99"
                  value={editingProduct.price}
                  onChange={e => setEditingProduct({...editingProduct, price: e.target.value})}
                  required
                  placeholder="0.00"
                />
              </div>

              <div className="form-group">
                <label htmlFor="editProductCategory">Category:</label>
                <select
                  id="editProductCategory"
                  value={editingProduct.category || 'Other'}
                  onChange={e => setEditingProduct({...editingProduct, category: e.target.value})}
                  required
                >
                  {VALID_CATEGORIES.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="editProductTags">Tags:</label>
                <div className="tag-input-container">
                  <input
                    id="editProductTags"
                    type="text"
                    value={editingTagInput}
                    onChange={e => setEditingTagInput(e.target.value)}
                    onKeyPress={e => handleTagKeyPress(e, true)}
                    placeholder="Add tag and press Enter"
                    maxLength="30"
                  />
                  <button 
                    type="button" 
                    onClick={() => handleAddTag(true)}
                    className="add-tag-btn"
                  >
                    Add
                  </button>
                </div>
                {editingProduct.tags?.length > 0 && (
                  <div className="tags-container">
                    {editingProduct.tags.map(tag => (
                      <span key={tag} className="tag">
                        {tag}
                        <button 
                          type="button" 
                          onClick={() => handleRemoveTag(tag, true)}
                          className="remove-tag-btn"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="form-group checkbox-group">
                <label htmlFor="editProductAvailability">
                  <input
                    id="editProductAvailability"
                    type="checkbox"
                    checked={editingProduct.is_available !== undefined ? editingProduct.is_available : true}
                    onChange={e => setEditingProduct({...editingProduct, is_available: e.target.checked})}
                  />
                  Available for purchase
                </label>
              </div>
              
              <div className="form-actions">
                <button type="button" onClick={cancelEditing} className="cancel-btn">Cancel</button>
                <button type="submit" className="submit-btn">Update Product</button>
              </div>
            </form>
          </>
        )}
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
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {displayProducts.map(product => {
                const id = product._id || product.id;
                return (
                  <tr key={id}>
                    <td>{product.name}</td>
                    <td>{product.description}</td>
                    <td>{product.category || 'Other'}</td>
                    <td>${parseFloat(product.price).toFixed(2)}</td>
                    <td>{product.is_available !== false ? 'Available' : 'Out of Stock'}</td>
                    <td>
                      <button 
                        onClick={() => startEditingProduct(product)} 
                        className="edit-btn"
                        aria-label={`Edit ${product.name}`}
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDeleteProduct(id)} 
                        className="delete-btn"
                        aria-label={`Delete ${product.name}`}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="orders">
        <h3>Recent Orders</h3>
        {orders.length === 0 ? (
          <p>No orders yet.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Items</th>
                  <th>Total</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order._id || order.id}>
                    <td>{order._id || order.id}</td>
                    <td>{order.user_email || order.customer_email || (order.user_id ? `User ${order.user_id.slice(-8)}` : 'Unknown')}</td>
                    <td>{new Date(order.created_at || order.timestamp || Date.now()).toLocaleDateString()}</td>
                    <td>
                      {order.items && order.items.length > 0 ? (
                        <div className="order-items">
                          {order.items.map((item, index) => (
                            <div key={index} className="order-item">
                              <strong>{item.product_name || `Product ${item.product_id}`}</strong> × {item.quantity || 1}
                              {item.unit_price && (
                                <span className="item-price"> (${parseFloat(item.unit_price).toFixed(2)} each)</span>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        `${order.items?.length || 0} items`
                      )}
                    </td>
                    <td>
                      ${order.total 
                        ? parseFloat(order.total).toFixed(2) 
                        : order.total_amount 
                        ? parseFloat(order.total_amount).toFixed(2)
                        : (order.items || []).reduce((sum, item) => {
                            const price = item.unit_price || item.total_price || item.price || 0;
                            const quantity = item.quantity || 1;
                            return sum + (parseFloat(price) * quantity);
                          }, 0).toFixed(2)}
                    </td>
                    <td>{order.status || 'Pending'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
} 