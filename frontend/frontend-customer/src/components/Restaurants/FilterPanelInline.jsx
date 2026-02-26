import React, { useState } from 'react';
import './FilterPanelInline.css';

const FilterPanelInline = ({ filters, onFilterChange, onReset, onClose }) => {
  const [expandedSections, setExpandedSections] = useState({
    quick: true,
    cuisine: false,
    price: false,
    rating: false,
    features: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Cuisine options (would come from API)
  const cuisineOptions = [
    { id: 1, name: 'Italian', count: 24 },
    { id: 2, name: 'Japanese', count: 18 },
    { id: 3, name: 'Mexican', count: 15 },
    { id: 4, name: 'American', count: 22 },
    { id: 5, name: 'Chinese', count: 20 },
    { id: 6, name: 'Thai', count: 8 },
    { id: 7, name: 'Indian', count: 12 },
    { id: 8, name: 'Mediterranean', count: 10 }
  ];

  return (
    <div className="fp-container glass-card">
      <div className="fp-header">
        <h3 className="fp-title">
          <span className="fp-icon">⚙️</span>
          Filter Restaurants
        </h3>
        <button className="fp-close-btn" onClick={onClose} aria-label="Close filters">
          ✕
        </button>
      </div>

      <div className="fp-content">
        {/* Quick Filters Section */}
        <div className="fp-section">
          <div className="fp-section-header" onClick={() => toggleSection('quick')}>
            <div className="fp-section-title">
              <span className="fp-section-icon">⚡</span>
              <span>Quick Filters</span>
            </div>
            <span className="fp-section-arrow">{expandedSections.quick ? '−' : '+'}</span>
          </div>
          
          {expandedSections.quick && (
            <div className="fp-quick-grid">
              <button 
                className={`fp-quick-chip ${filters.nearMeActive ? 'active' : ''}`}
                onClick={() => onFilterChange('nearMeActive', !filters.nearMeActive)}
              >
                <span className="fp-chip-icon">📍</span>
                <span>Near Me</span>
              </button>
              <button 
                className={`fp-quick-chip ${filters.hours?.isOpenNow ? 'active' : ''}`}
                onClick={() => onFilterChange('hours.isOpenNow', !filters.hours?.isOpenNow, true)}
              >
                <span className="fp-chip-icon">🕒</span>
                <span>Open Now</span>
              </button>
              <button 
                className={`fp-quick-chip ${filters.popular ? 'active' : ''}`}
                onClick={() => onFilterChange('popular', !filters.popular)}
              >
                <span className="fp-chip-icon">🔥</span>
                <span>Popular</span>
              </button>
              <button 
                className={`fp-quick-chip ${filters.features?.fastDelivery ? 'active' : ''}`}
                onClick={() => onFilterChange('features.fastDelivery', !filters.features?.fastDelivery, true)}
              >
                <span className="fp-chip-icon">🚀</span>
                <span>Fast Delivery</span>
              </button>
            </div>
          )}
        </div>

        {/* Cuisine Section */}
        <div className="fp-section">
          <div className="fp-section-header" onClick={() => toggleSection('cuisine')}>
            <div className="fp-section-title">
              <span className="fp-section-icon">🍽️</span>
              <span>Cuisine</span>
            </div>
            <span className="fp-section-arrow">{expandedSections.cuisine ? '−' : '+'}</span>
          </div>
          
          {expandedSections.cuisine && (
            <div className="fp-checkbox-grid">
              {cuisineOptions.map(cuisine => (
                <label key={cuisine.id} className="fp-checkbox">
                  <input 
                    type="checkbox"
                    checked={filters.cuisines?.includes(cuisine.id)}
                    onChange={(e) => {
                      const newCuisines = e.target.checked
                        ? [...(filters.cuisines || []), cuisine.id]
                        : (filters.cuisines || []).filter(id => id !== cuisine.id);
                      onFilterChange('cuisines', newCuisines);
                    }}
                  />
                  <span className="fp-checkbox-label">{cuisine.name}</span>
                  <span className="fp-checkbox-count">{cuisine.count}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Price Range Section */}
        <div className="fp-section">
          <div className="fp-section-header" onClick={() => toggleSection('price')}>
            <div className="fp-section-title">
              <span className="fp-section-icon">💰</span>
              <span>Price Range</span>
            </div>
            <span className="fp-section-arrow">{expandedSections.price ? '−' : '+'}</span>
          </div>
          
          {expandedSections.price && (
            <div className="fp-price-grid">
              {['$', '$$', '$$$', '$$$$'].map(price => (
                <button
                  key={price}
                  className={`fp-price-chip ${filters.priceRanges?.includes(price) ? 'active' : ''}`}
                  onClick={() => {
                    const newRanges = filters.priceRanges?.includes(price)
                      ? filters.priceRanges.filter(p => p !== price)
                      : [...(filters.priceRanges || []), price];
                    onFilterChange('priceRanges', newRanges);
                  }}
                >
                  {price}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Rating Section */}
        <div className="fp-section">
          <div className="fp-section-header" onClick={() => toggleSection('rating')}>
            <div className="fp-section-title">
              <span className="fp-section-icon">⭐</span>
              <span>Minimum Rating</span>
            </div>
            <span className="fp-section-arrow">{expandedSections.rating ? '−' : '+'}</span>
          </div>
          
          {expandedSections.rating && (
            <div className="fp-rating-grid">
              {[4.5, 4.0, 3.5, 3.0].map(rating => (
                <button
                  key={rating}
                  className={`fp-rating-chip ${filters.minRating === rating ? 'active' : ''}`}
                  onClick={() => onFilterChange('minRating', rating)}
                >
                  {rating}+ ★
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="fp-section">
          <div className="fp-section-header" onClick={() => toggleSection('features')}>
            <div className="fp-section-title">
              <span className="fp-section-icon">✨</span>
              <span>Features</span>
            </div>
            <span className="fp-section-arrow">{expandedSections.features ? '−' : '+'}</span>
          </div>
          
          {expandedSections.features && (
            <div className="fp-checkbox-grid">
              <label className="fp-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.reservationEnabled}
                  onChange={(e) => onFilterChange('features.reservationEnabled', e.target.checked, true)}
                />
                <span className="fp-checkbox-label">Reservations</span>
              </label>
              <label className="fp-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.deliveryAvailable}
                  onChange={(e) => onFilterChange('features.deliveryAvailable', e.target.checked, true)}
                />
                <span className="fp-checkbox-label">Delivery</span>
              </label>
              <label className="fp-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.isVerified}
                  onChange={(e) => onFilterChange('features.isVerified', e.target.checked, true)}
                />
                <span className="fp-checkbox-label">Verified</span>
              </label>
              <label className="fp-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.hasOffers}
                  onChange={(e) => onFilterChange('features.hasOffers', e.target.checked, true)}
                />
                <span className="fp-checkbox-label">Special Offers</span>
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="fp-footer">
        <button className="fp-reset-btn" onClick={onReset}>
          Reset All
        </button>
        <button className="fp-apply-btn" onClick={onClose}>
          Apply Filters
        </button>
      </div>
    </div>
  );
};

export default FilterPanelInline;