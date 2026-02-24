import React, { useState } from 'react';
import './FilterPanelInline.css';

const FilterPanelInline = ({ filters, onFilterChange, onReset, onClose }) => {
  const [expandedSections, setExpandedSections] = useState({
    cuisine: true,
    price: false,
    rating: false,
    dietary: false,
    features: false
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Cuisine options (would come from API in real implementation)
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
    <div className="filter-panel-inline glass-card">
      <div className="filter-panel-header">
        <h3>Filter Restaurants</h3>
        <button className="close-filter-btn" onClick={onClose}>✕</button>
      </div>

      <div className="filter-panel-content">
        {/* Cuisine Section */}
        <div className="filter-section">
          <div className="filter-section-header" onClick={() => toggleSection('cuisine')}>
            <span>🍽️ Cuisine</span>
            <span className="section-arrow">{expandedSections.cuisine ? '−' : '+'}</span>
          </div>
          
          {expandedSections.cuisine && (
            <div className="filter-options">
              {cuisineOptions.map(cuisine => (
                <label key={cuisine.id} className="filter-checkbox">
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
                  <span className="checkbox-label">{cuisine.name}</span>
                  <span className="filter-count">{cuisine.count}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Price Range Section */}
        <div className="filter-section">
          <div className="filter-section-header" onClick={() => toggleSection('price')}>
            <span>💰 Price Range</span>
            <span className="section-arrow">{expandedSections.price ? '−' : '+'}</span>
          </div>
          
          {expandedSections.price && (
            <div className="filter-options price-options">
              {['$', '$$', '$$$', '$$$$'].map(price => (
                <button
                  key={price}
                  className={`price-chip ${filters.priceRanges?.includes(price) ? 'active' : ''}`}
                  onClick={() => {
                    const newPrices = filters.priceRanges?.includes(price)
                      ? filters.priceRanges.filter(p => p !== price)
                      : [...(filters.priceRanges || []), price];
                    onFilterChange('priceRanges', newPrices);
                  }}
                >
                  {price}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Rating Section */}
        <div className="filter-section">
          <div className="filter-section-header" onClick={() => toggleSection('rating')}>
            <span>⭐ Minimum Rating</span>
            <span className="section-arrow">{expandedSections.rating ? '−' : '+'}</span>
          </div>
          
          {expandedSections.rating && (
            <div className="filter-options rating-options">
              {[4.5, 4.0, 3.5, 3.0].map(rating => (
                <button
                  key={rating}
                  className={`rating-chip ${filters.minRating === rating ? 'active' : ''}`}
                  onClick={() => onFilterChange('minRating', rating)}
                >
                  {rating}+ ★
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Dietary Section */}
        <div className="filter-section">
          <div className="filter-section-header" onClick={() => toggleSection('dietary')}>
            <span>🌱 Dietary</span>
            <span className="section-arrow">{expandedSections.dietary ? '−' : '+'}</span>
          </div>
          
          {expandedSections.dietary && (
            <div className="filter-options">
              {['vegetarian', 'vegan', 'gluten-free', 'halal'].map(diet => (
                <label key={diet} className="filter-checkbox">
                  <input 
                    type="checkbox"
                    checked={filters.dietary?.includes(diet)}
                    onChange={(e) => {
                      const newDietary = e.target.checked
                        ? [...(filters.dietary || []), diet]
                        : (filters.dietary || []).filter(d => d !== diet);
                      onFilterChange('dietary', newDietary);
                    }}
                  />
                  <span className="checkbox-label capitalize">{diet}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Features Section */}
        <div className="filter-section">
          <div className="filter-section-header" onClick={() => toggleSection('features')}>
            <span>✨ Features</span>
            <span className="section-arrow">{expandedSections.features ? '−' : '+'}</span>
          </div>
          
          {expandedSections.features && (
            <div className="filter-options">
              <label className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.hours?.isOpenNow}
                  onChange={(e) => onFilterChange('hours.isOpenNow', e.target.checked, true)}
                />
                <span className="checkbox-label">Open Now</span>
              </label>
              <label className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.reservationEnabled}
                  onChange={(e) => onFilterChange('features.reservationEnabled', e.target.checked, true)}
                />
                <span className="checkbox-label">Reservations Available</span>
              </label>
              <label className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.deliveryAvailable}
                  onChange={(e) => onFilterChange('features.deliveryAvailable', e.target.checked, true)}
                />
                <span className="checkbox-label">Delivery Available</span>
              </label>
              <label className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.isVerified}
                  onChange={(e) => onFilterChange('features.isVerified', e.target.checked, true)}
                />
                <span className="checkbox-label">Verified</span>
              </label>
              <label className="filter-checkbox">
                <input 
                  type="checkbox"
                  checked={filters.features?.hasOffers}
                  onChange={(e) => onFilterChange('features.hasOffers', e.target.checked, true)}
                />
                <span className="checkbox-label">Special Offers</span>
              </label>
            </div>
          )}
        </div>
      </div>

      <div className="filter-panel-footer">
        <button className="reset-filters-btn" onClick={onReset}>
          Reset All
        </button>
        <button className="apply-filters-btn" onClick={onClose}>
          Apply Filters
        </button>
      </div>
    </div>
  );
};

export default FilterPanelInline;