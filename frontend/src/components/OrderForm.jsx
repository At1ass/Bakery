import React, { useState, useEffect } from 'react';
import './OrderForm.css';

export default function OrderForm({ orderItems, onSubmit, onClear }) {
  const [address, setAddress] = useState(() => {
    return localStorage.getItem('orderAddress') || '';
  });
  const [phone, setPhone] = useState(() => {
    return localStorage.getItem('orderPhone') || '';
  });
  const [notes, setNotes] = useState(() => {
    return localStorage.getItem('orderNotes') || '';
  });

  // Save form data to localStorage when they change
  useEffect(() => {
    if (address) {
      localStorage.setItem('orderAddress', address);
    } else {
      localStorage.removeItem('orderAddress');
    }
  }, [address]);

  useEffect(() => {
    if (phone) {
      localStorage.setItem('orderPhone', phone);
    } else {
      localStorage.removeItem('orderPhone');
    }
  }, [phone]);

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
        quantity: item.quantity || 1
      })),
      delivery_address: address,
      contact_phone: phone,
      delivery_notes: notes || undefined
    };

    onSubmit(orderData);
    
    // Clear the form and localStorage after successful submission
    setAddress('');
    setPhone('');
    setNotes('');
    localStorage.removeItem('orderAddress');
    localStorage.removeItem('orderPhone');
    localStorage.removeItem('orderNotes');
  };

  const updateQuantity = (index, newQuantity) => {
    if (newQuantity <= 0) {
      // Remove item if quantity is 0 or less
      const newItems = [...orderItems];
      newItems.splice(index, 1);
      onClear(newItems);
    } else {
      // Update quantity
      const newItems = [...orderItems];
      newItems[index] = { ...newItems[index], quantity: newQuantity };
      onClear(newItems);
    }
  };

  const calculateTotal = () => {
    return orderItems.reduce((total, item) => {
      const quantity = item.quantity || 1;
      return total + (parseFloat(item.price) * quantity);
    }, 0).toFixed(2);
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
            <div className="item-details">
              <span className="item-name">{item.name}</span>
              <span className="item-price">${parseFloat(item.price).toFixed(2)} each</span>
            </div>
            <div className="quantity-controls">
              <button 
                onClick={() => updateQuantity(index, (item.quantity || 1) - 1)}
                className="quantity-btn"
                aria-label="Decrease quantity"
              >
                -
              </button>
              <span className="quantity">{item.quantity || 1}</span>
              <button 
                onClick={() => updateQuantity(index, (item.quantity || 1) + 1)}
                className="quantity-btn"
                aria-label="Increase quantity"
              >
                +
              </button>
              <button 
                onClick={() => updateQuantity(index, 0)}
                className="remove-item"
                aria-label={`Remove ${item.name} from order`}
              >
                ✕
              </button>
            </div>
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
            placeholder="Enter your delivery address (minimum 10 characters)"
            minLength={10}
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">Contact Phone:</label>
          <input
            type="tel"
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
            placeholder="Enter your phone number (e.g., +1234567890)"
            pattern="^\+?1?\d{9,15}$"
            title="Please enter a valid phone number (9-15 digits, optionally starting with + or +1)"
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">Delivery Notes:</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any special delivery instructions?"
            maxLength={200}
          />
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            onClick={() => {
              onClear([]);
              setAddress('');
              setPhone('');
              setNotes('');
              localStorage.removeItem('orderAddress');
              localStorage.removeItem('orderPhone');
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
