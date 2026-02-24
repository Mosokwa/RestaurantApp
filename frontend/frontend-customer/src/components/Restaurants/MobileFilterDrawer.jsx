import React, { useState, useEffect } from 'react';
import './MobileFilterDrawer.css';

const MobileFilterDrawer = ({ 
  isOpen, 
  onClose, 
  filters, 
  onFilterChange, 
  onReset, 
  onApply 
}) => {
  const [localFilters, setLocalFilters] = useState(filters);
  const [expandedSections, setExpandedSections] = useState({
    cuisine: true,
    price: false,
    rating: false,
    dietary: false,
    features: false
  });

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleLocalChange = (key, value, nested = false) => {
    if (nested) {
      const [parent, child] = key.split('.');
      setLocalFilters(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setLocalFilters(prev => ({
        ...prev,
        [key]: value
      }));
    }
  };

  const handleApply = () => {
    // Apply all changes to parent
    Object.keys(localFilters).forEach(key => {
      if (typeof localFilters[key] === 'object' && !Array.isArray(localFilters[key])) {
        Object.keys(localFilters[key]).forEach(nestedKey => {
          if (localFilters[key][nestedKey] !== filters[key]?.[nestedKey]) {
            onFilterChange(`${key}.${nestedKey}`, localFilters[key][nestedKey], true);
          }
        });
      } else {
        if (localFilters[key] !== filters[key]) {
          onFilterChange(key, localFilters[key]);
        }
      }
    });
    onApply();
  };

  const handleReset = () => {
    setLocalFilters({
      location: { lat: null, lng: null, radius: 10, city: '', neighborhood: '' },
      cuisines: [],
      priceRanges: [],
      minRating: 0,
      minReviews: 0,
      dietary: [],
      amenities: [],
      occasions: [],
      ambiance: [],
      hours: { isOpenNow: false, openLate: false, specificTime: null },
      features: { isVerified: false, isFeatured: false, reservationEnabled: false, hasOffers: false },
      sortBy: 'relevance',
      view: 'grid'
    });
    onReset();
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

  if (!isOpen) return null;

  return (
    <>
      <div className="mobile-filter-overlay" onClick={onClose} />
      <div className={`mobile-filter-drawer ${isOpen ? 'open' : ''}`}>
        <div className="mobile-filter-header">
          <h3>Filter Restaurants</h3>
          <button className="mobile-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="mobile-filter-content">
          {/* Cuisine Section */}
          <div className="mobile-filter-section">
            <div className="mobile-section-header" onClick={() => toggleSection('cuisine')}>
              <span>🍽️ Cuisine</span>
              <span className="section-arrow">{expandedSections.cuisine ? '−' : '+'}</span>
            </div>
            
            {expandedSections.cuisine && (
              <div className="mobile-filter-options">
                {cuisineOptions.map(cuisine => (
                  <label key={cuisine.id} className="mobile-filter-checkbox">
                    <input 
                      type="checkbox"
                      checked={localFilters.cuisines?.includes(cuisine.id)}
                      onChange={(e) => {
                        const newCuisines = e.target.checked
                          ? [...(localFilters.cuisines || []), cuisine.id]
                          : (localFilters.cuisines || []).filter(id => id !== cuisine.id);
                        handleLocalChange('cuisines', newCuisines);
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
          <div className="mobile-filter-section">
            <div className="mobile-section-header" onClick={() => toggleSection('price')}>
              <span>💰 Price Range</span>
              <span className="section-arrow">{expandedSections.price ? '−' : '+'}</span>
            </div>
            
            {expandedSections.price && (
              <div className="mobile-filter-options price-options">
                {['$', '$$', '$$$', '$$$$'].map(price => (
                  <button
                    key={price}
                    className={`price-chip ${localFilters.priceRanges?.includes(price) ? 'active' : ''}`}
                    onClick={() => {
                      const newPrices = localFilters.priceRanges?.includes(price)
                        ? localFilters.priceRanges.filter(p => p !== price)
                        : [...(localFilters.priceRanges || []), price];
                      handleLocalChange('priceRanges', newPrices);
                    }}
                  >
                    {price}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Rating Section */}
          <div className="mobile-filter-section">
            <div className="mobile-section-header" onClick={() => toggleSection('rating')}>
              <span>⭐ Minimum Rating</span>
              <span className="section-arrow">{expandedSections.rating ? '−' : '+'}</span>
            </div>
            
            {expandedSections.rating && (
              <div className="mobile-filter-options rating-options">
                {[4.5, 4.0, 3.5, 3.0].map(rating => (
                  <button
                    key={rating}
                    className={`rating-chip ${localFilters.minRating === rating ? 'active' : ''}`}
                    onClick={() => handleLocalChange('minRating', rating)}
                  >
                    {rating}+ ★
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Dietary Section */}
          <div className="mobile-filter-section">
            <div className="mobile-section-header" onClick={() => toggleSection('dietary')}>
              <span>🌱 Dietary</span>
              <span className="section-arrow">{expandedSections.dietary ? '−' : '+'}</span>
            </div>
            
            {expandedSections.dietary && (
              <div className="mobile-filter-options">
                {['vegetarian', 'vegan', 'gluten-free', 'halal'].map(diet => (
                  <label key={diet} className="mobile-filter-checkbox">
                    <input 
                      type="checkbox"
                      checked={localFilters.dietary?.includes(diet)}
                      onChange={(e) => {
                        const newDietary = e.target.checked
                          ? [...(localFilters.dietary || []), diet]
                          : (localFilters.dietary || []).filter(d => d !== diet);
                        handleLocalChange('dietary', newDietary);
                      }}
                    />
                    <span className="checkbox-label capitalize">{diet}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          {/* Features Section */}
          <div className="mobile-filter-section">
            <div className="mobile-section-header" onClick={() => toggleSection('features')}>
              <span>✨ Features</span>
              <span className="section-arrow">{expandedSections.features ? '−' : '+'}</span>
            </div>
            
            {expandedSections.features && (
              <div className="mobile-filter-options">
                <label className="mobile-filter-checkbox">
                  <input 
                    type="checkbox"
                    checked={localFilters.hours?.isOpenNow}
                    onChange={(e) => handleLocalChange('hours.isOpenNow', e.target.checked, true)}
                  />
                  <span className="checkbox-label">Open Now</span>
                </label>
                <label className="mobile-filter-checkbox">
                  <input 
                    type="checkbox"
                    checked={localFilters.features?.reservationEnabled}
                    onChange={(e) => handleLocalChange('features.reservationEnabled', e.target.checked, true)}
                  />
                  <span className="checkbox-label">Reservations Available</span>
                </label>
                <label className="mobile-filter-checkbox">
                  <input 
                    type="checkbox"
                    checked={localFilters.features?.isVerified}
                    onChange={(e) => handleLocalChange('features.isVerified', e.target.checked, true)}
                  />
                  <span className="checkbox-label">Verified</span>
                </label>
                <label className="mobile-filter-checkbox">
                  <input 
                    type="checkbox"
                    checked={localFilters.features?.hasOffers}
                    onChange={(e) => handleLocalChange('features.hasOffers', e.target.checked, true)}
                  />
                  <span className="checkbox-label">Special Offers</span>
                </label>
              </div>
            )}
          </div>
        </div>

        <div className="mobile-filter-footer">
          <button className="mobile-reset-btn" onClick={handleReset}>
            Reset All
          </button>
          <button className="mobile-apply-btn" onClick={handleApply}>
            Show Results
          </button>
        </div>
      </div>
    </>
  );
};

export default MobileFilterDrawer;