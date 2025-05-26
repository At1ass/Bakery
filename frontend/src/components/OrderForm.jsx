import React, { useState } from 'react';
import './OrderForm.css';

export default function OrderForm({ orderItems, onPlaceOrder, setOrderItems }) {
  const [address, setAddress] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const orderData = {
      items: orderItems,
      delivery_address: address,
      notes: notes
    };

    onPlaceOrder(orderData);
    setAddress('');
    setNotes('');
  };

  const calculateTotal = () => {
    return orderItems.reduce((total, item) => total + item.price, 0).toFixed(2);
  };

  const removeItem = (index) => {
    setOrderItems(orderItems.filter((_, i) => i !== index));
  };

  if (!orderItems.length) {
    return null;
  }

  return (
    <div className="order-form">
      <h2>Your Order</h2>
      
      <div className="order-items">
        {orderItems.map((item, index) => (
          <div key={index} className="order-item">
            <span>{item.name} - ${item.price.toFixed(2)}</span>
            <button 
              onClick={() => removeItem(index)}
              className="remove-item"
              aria-label={`Remove ${item.name} from order`}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="order-total">
        Total: ${calculateTotal()}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="address">Delivery Address:</label>
          <textarea
            id="address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            required
            placeholder="Enter your delivery address"
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">Order Notes:</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any special instructions?"
          />
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            onClick={() => setOrderItems([])}
            className="clear-order"
          >
            Clear Order
          </button>
          <button 
            type="submit"
            className="place-order"
          >
            Place Order
          </button>
        </div>
      </form>
    </div>
  );
}
