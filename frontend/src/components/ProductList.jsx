import React, { useState } from 'react';
import './ProductList.css';

export default function ProductList({ products, onSelect }) {
  const [quantities, setQuantities] = useState({});

  const handleQuantityChange = (productId, value) => {
    setQuantities({
      ...quantities,
      [productId]: Math.max(1, parseInt(value) || 1)
    });
  };

  const handleAddToOrder = (product) => {
    const quantity = quantities[product.id] || 1;
    onSelect([{ product_id: product.id, quantity }]);
    // Reset quantity after adding
    setQuantities({
      ...quantities,
      [product.id]: 1
    });
  };

  return (
    <div className="product-list">
      <h2>Available Products</h2>
      <div className="products-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <div className="product-info">
              <h3>{product.name}</h3>
              <p className="description">{product.description}</p>
              <p className="price">${product.price.toFixed(2)}</p>
            </div>
            <div className="product-actions">
              <input
                type="number"
                min="1"
                value={quantities[product.id] || 1}
                onChange={(e) => handleQuantityChange(product.id, e.target.value)}
                className="quantity-input"
              />
              <button 
                onClick={() => handleAddToOrder(product)}
                className="add-to-order-btn"
              >
                Add to Order
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
