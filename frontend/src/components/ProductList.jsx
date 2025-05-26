import React from 'react';
import './ProductList.css';

export default function ProductList({ products, onAddToOrder }) {
  console.log('ProductList received products:', products);
  
  if (!products || !products.length) {
    console.log('No products to display');
    return (
      <div className="no-products">
        No products available at the moment.
      </div>
    );
  }

  return (
    <div className="product-list">
      <h2>Available Products</h2>
      <div className="products-grid">
        {products.map((product) => {
          // Handle different product ID formats
          const productId = product._id || product.id;
          // Ensure price is a number
          const price = parseFloat(product.price);
          // Default is_available to true if not specified
          const isAvailable = product.is_available !== undefined ? product.is_available : true;
          
          return (
            <div key={productId} className="product-card">
              <h3>{product.name}</h3>
              <p className="description">{product.description}</p>
              {product.category && (
                <span className="category">{product.category}</span>
              )}
              <div className="product-details">
                <span className="price">${isNaN(price) ? '0.00' : price.toFixed(2)}</span>
                <button
                  onClick={() => onAddToOrder(product)}
                  className={`add-to-order ${!isAvailable ? 'disabled' : ''}`}
                  disabled={!isAvailable}
                  aria-label={`Add ${product.name} to order`}
                >
                  {isAvailable ? 'Add to Order' : 'Out of Stock'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
