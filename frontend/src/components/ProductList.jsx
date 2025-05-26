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
        {products.map((product) => (
          <div key={product.id} className="product-card">
            <h3>{product.name}</h3>
            <p className="description">{product.description}</p>
            <div className="product-details">
              <span className="price">${product.price.toFixed(2)}</span>
              <button
                onClick={() => onAddToOrder(product)}
                className="add-to-order"
                disabled={!product.is_available}
                aria-label={`Add ${product.name} to order`}
              >
                {product.is_available ? 'Add to Order' : 'Out of Stock'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
