import React from 'react';
import { useTranslation } from 'react-i18next';
import './ProductList.css';

export default function ProductList({ products, onAddToOrder }) {
  const { t } = useTranslation();
  console.log('ProductList received products:', products);
  
  if (!products || !products.length) {
    console.log('No products to display');
    return (
      <div className="no-products">
        {t('products.noProducts')}
      </div>
    );
  }

  return (
    <div className="product-list">
      <h2>{t('products.title')}</h2>
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
                  aria-label={`${t('products.addToCart')} ${product.name}`}
                >
                  {isAvailable ? t('products.addToCart') : t('products.outOfStock')}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
