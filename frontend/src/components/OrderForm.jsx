import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import './OrderForm.css';

export default function OrderForm({ orderItems, onSubmit, onClear }) {
  const { t } = useTranslation();
  const [address, setAddress] = useState(() => {
    return localStorage.getItem('orderAddress') || '';
  });
  const [phone, setPhone] = useState(() => {
    return localStorage.getItem('orderPhone') || '';
  });
  const [notes, setNotes] = useState(() => {
    return localStorage.getItem('orderNotes') || '';
  });

  const clearForm = () => {
    setAddress('');
    setPhone('');
    setNotes('');
    localStorage.removeItem('orderAddress');
    localStorage.removeItem('orderPhone');
    localStorage.removeItem('orderNotes');
  };

  // Clear form when orderItems becomes empty (successful order placement)
  useEffect(() => {
    if (orderItems.length === 0) {
      clearForm();
    }
  }, [orderItems.length]);

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
    
    // Validate address length
    if (address.trim().length < 10) {
      alert(t('orderForm.addressTooShort') || 'Delivery address must be at least 10 characters long');
      return;
    }
    
    const orderData = {
      items: orderItems.map(item => ({
        product_id: item._id || item.id,
        quantity: item.quantity || 1
      })),
      delivery_address: address.trim(),
      contact_phone: phone.trim(),
      delivery_notes: notes.trim() || undefined
    };

    onSubmit(orderData);
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
      <h2>{t('orderForm.title')}</h2>
      
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
                aria-label={t('orderForm.decreaseQuantity')}
              >
                -
              </button>
              <span className="quantity">{item.quantity || 1}</span>
              <button 
                onClick={() => updateQuantity(index, (item.quantity || 1) + 1)}
                className="quantity-btn"
                aria-label={t('orderForm.increaseQuantity')}
              >
                +
              </button>
              <button 
                onClick={() => updateQuantity(index, 0)}
                className="remove-item"
                aria-label={t('orderForm.removeItem', { itemName: item.name })}
              >
                ✕
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="order-total">
        {t('orderForm.total')}: ${calculateTotal()}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="address">{t('orderForm.deliveryAddress')}:</label>
          <textarea
            id="address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            required
            placeholder={t('orderForm.deliveryAddressPlaceholder')}
            maxLength={200}
          />
        </div>

        <div className="form-group">
          <label htmlFor="phone">{t('orderForm.contactPhone')}:</label>
          <input
            type="tel"
            id="phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
            placeholder={t('orderForm.phonePlaceholder')}
            pattern="^\+?1?\d{9,15}$"
            title={t('orderForm.phoneTitle')}
          />
        </div>

        <div className="form-group">
          <label htmlFor="notes">{t('orderForm.deliveryNotes')}:</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={t('orderForm.deliveryNotesPlaceholder')}
            maxLength={200}
          />
        </div>

        <div className="form-actions">
          <button 
            type="button" 
            onClick={() => {
              onClear([]);
              clearForm();
            }}
            className="clear-order"
          >
            {t('orderForm.clearOrder')}
          </button>
          <button 
            type="submit"
            className="place-order"
          >
            {t('orderForm.placeOrder')}
          </button>
        </div>
      </form>
    </div>
  );
}
