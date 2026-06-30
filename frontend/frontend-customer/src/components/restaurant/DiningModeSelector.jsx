// src/pages/restaurant/components/DiningModeSelector.jsx
import React from 'react';
import { ShoppingBag, Clock, UtensilsCrossed, Check } from 'lucide-react';

const DiningModeSelector = ({ currentMode, onModeChange, isDineIn, tableInfo }) => {
  const modes = [
    { id: 'delivery', label: 'Delivery', icon: ShoppingBag, description: 'Get it delivered' },
    { id: 'pickup', label: 'Pickup', icon: Clock, description: 'Order ahead, pick up' }
  ];
  
  // If dine-in mode is active (from QR scan), show banner
  if (isDineIn) {
    return (
      <div className="rhp-dinein-banner">
        <UtensilsCrossed size={20} />
        <span>You're dining in at Table {tableInfo?.table}</span>
        <span className="rhp-dinein-banner-hint">Order directly to your table</span>
      </div>
    );
  }
  
  return (
    <div className="rhp-dining-mode-selector">
      <div className="rhp-selector-label">How would you like to order?</div>
      <div className="rhp-mode-options">
        {modes.map((mode) => {
          const Icon = mode.icon;
          const isActive = currentMode === mode.id;
          
          return (
            <button
              key={mode.id}
              className={`rhp-mode-btn-large ${isActive ? 'rhp-active' : ''}`}
              onClick={() => onModeChange(mode.id)}
            >
              <Icon size={22} />
              <div className="rhp-mode-text">
                <span className="rhp-mode-label">{mode.label}</span>
                <span className="rhp-mode-description">{mode.description}</span>
              </div>
              {isActive && <Check size={18} className="rhp-active-check" />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default DiningModeSelector;