import React, { useState, useEffect } from 'react';
import './OrderForm.css';

export default function OrderForm({ orderItems, onSubmit, onClear }) {
  const [address, setAddress] = useState(() => {
    return localStorage.getItem('orderAddress') || '';
  });
  const [notes, setNotes] = useState(() => {
    return localStorage.getItem('orderNotes') || '';
  });

  // Save address and notes to localStorage when they change
  useEffect(() => {
    if (address) {
      localStorage.setItem('orderAddress', address);
    } else {
      localStorage.removeItem('orderAddress');
    }
  }, [address]);

  useEffect(() => {
    if (notes) {
      localStorage.setItem('orderNotes', notes);
    } else {
      localStorage.removeItem('orderNotes');
    }
  }, [notes]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const orderData = {
      items: orderItems.map(item => ({
        product_id: item._id || item.id,
        quantity: 1,
        price: item.price
      })),
      delivery_address: address,
      notes: notes
    };

    onSubmit(orderData);
    
    // Clear the form and localStorage after successful submission
    setAddress('');
    setNotes('');
    localStorage.removeItem('orderAddress');
    localStorage.removeItem('orderNotes');
  };

  const calculateTotal = () => {
    return orderItems.reduce((total, item) => total + parseFloat(item.price), 0).toFixed(2);
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
            <span>{item.name} - ${parseFloat(item.price).toFixed(2)}</span>
            <button 
              onClick={() => {
                const newItems = [...orderItems];
                newItems.splice(index, 1);
                onClear(newItems); // Pass updated items to parent
              }}
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
            onClick={() => {
              onClear([]);
              setAddress('');
              setNotes('');
              localStorage.removeItem('orderAddress');
              localStorage.removeItem('orderNotes');
            }}
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
