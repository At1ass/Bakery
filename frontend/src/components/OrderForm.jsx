import React from 'react';
import './OrderForm.css';

export default function OrderForm({ items, products, onSubmit, onClear }) {
  const getProduct = (productId) => {
    return products.find(p => p.id === productId);
  };

  const calculateTotal = () => {
    return items.reduce((total, item) => {
      const product = getProduct(item.product_id);
      return total + (product ? product.price * item.quantity : 0);
    }, 0);
  };

  return (
    <div className="order-form">
      <h3>Your Order</h3>
      <div className="order-items">
        {items.map((item, index) => {
          const product = getProduct(item.product_id);
          if (!product) return null;
          
          return (
            <div key={index} className="order-item">
              <div className="item-info">
                <span className="item-name">{product.name}</span>
                <span className="item-quantity">x{item.quantity}</span>
              </div>
              <span className="item-price">
                ${(product.price * item.quantity).toFixed(2)}
              </span>
            </div>
          );
        })}
      </div>
      
      <div className="order-total">
        <span>Total:</span>
        <span className="total-amount">${calculateTotal().toFixed(2)}</span>
      </div>
      
      <div className="order-actions">
        <button onClick={onClear} className="clear-btn">
          Clear Order
        </button>
        <button onClick={onSubmit} className="submit-btn">
          Place Order
        </button>
      </div>
    </div>
  );
}
