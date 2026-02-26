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

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

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

  if (!isOpen) return null;

  return (
    <>
      <div className="mobile-filter-overlay" onClick={onClose} />
      <div className="mobile-filter-drawer">
        <div className="mobile-filter-header">
          <h3>Filter Restaurants</h3>
          <button className="mobile-close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="mobile-filter-content">
          {/* Quick Filter Toggles */}
          <div className="mobile-filter-section">
            <h4>Quick Filters</h4>
            <div className="mobile-filter-grid">
              <button 
                className={`mobile-filter-chip ${localFilters.nearMeActive ? 'active' : ''}`}
                onClick={() => setLocalFilters({...localFilters, nearMeActive: !localFilters.nearMeActive})}
              >
                📍 Near Me
              </button>
              <button 
                className={`mobile-filter-chip ${localFilters.minRating >= 4.5 ? 'active' : ''}`}
                onClick={() => setLocalFilters({...localFilters, minRating: localFilters.minRating >= 4.5 ? 0 : 4.5})}
              >
                ⭐ 4.5+
              </button>
              <button 
                className={`mobile-filter-chip ${localFilters.hours?.isOpenNow ? 'active' : ''}`}
                onClick={() => setLocalFilters({
                  ...localFilters, 
                  hours: {...localFilters.hours, isOpenNow: !localFilters.hours?.isOpenNow}
                })}
              >
                🕒 Open Now
              </button>
              <button 
                className={`mobile-filter-chip ${localFilters.features?.fastDelivery ? 'active' : ''}`}
                onClick={() => setLocalFilters({
                  ...localFilters, 
                  features: {...localFilters.features, fastDelivery: !localFilters.features?.fastDelivery}
                })}
              >
                🚀 Fast Delivery
              </button>
            </div>
          </div>

          {/* Price Range */}
          <div className="mobile-filter-section">
            <h4>Price Range</h4>
            <div className="mobile-filter-grid">
              {['$', '$$', '$$$', '$$$$'].map(price => (
                <button
                  key={price}
                  className={`mobile-filter-chip ${localFilters.priceRanges?.includes(price) ? 'active' : ''}`}
                  onClick={() => {
                    const newRanges = localFilters.priceRanges?.includes(price)
                      ? localFilters.priceRanges.filter(p => p !== price)
                      : [...(localFilters.priceRanges || []), price];
                    setLocalFilters({...localFilters, priceRanges: newRanges});
                  }}
                >
                  {price}
                </button>
              ))}
            </div>
          </div>

          {/* Sort By */}
          <div className="mobile-filter-section">
            <h4>Sort By</h4>
            <select 
              className="mobile-sort-select"
              value={localFilters.sortBy || 'relevance'}
              onChange={(e) => setLocalFilters({...localFilters, sortBy: e.target.value})}
            >
              <option value="relevance">Relevance</option>
              <option value="distance">Distance</option>
              <option value="rating">Highest Rated</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
            </select>
          </div>
        </div>

        <div className="mobile-filter-footer">
          <button className="mobile-reset-btn" onClick={onReset}>Reset</button>
          <button className="mobile-apply-btn" onClick={() => {
            // Apply all changes
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
          }}>Apply Filters</button>
        </div>
      </div>
    </>
  );
};

export default MobileFilterDrawer;