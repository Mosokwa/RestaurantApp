import React from 'react';
import './QuickFilters.css';

const QuickFilters = ({ onFilterClick, activeFilters = {}, userLocation }) => {
  const quickFilters = [
    { 
      id: 'near_me', 
      icon: '📍', 
      label: 'Near Me', 
      active: activeFilters?.nearMeActive || false,
      tooltip: 'Show restaurants near your location'
    },
    { 
      id: 'high_rating', 
      icon: '⭐', 
      label: '4.5+',
      active: activeFilters?.minRating >= 4.5,
      tooltip: 'Restaurants rated 4.5 and above'
    },
    { 
      id: 'open_now', 
      icon: '🕒', 
      label: 'Open Now',
      active: activeFilters?.hours?.isOpenNow,
      tooltip: 'Restaurants currently open'
    },
    { 
      id: 'fast_delivery', 
      icon: '🚀', 
      label: 'Fast Delivery',
      active: activeFilters?.fastDelivery || false,
      tooltip: 'Restaurants with fast delivery'
    },
    { 
      id: 'popular', 
      icon: '🔥', 
      label: 'Popular',
      active: activeFilters?.popular || false,
      tooltip: 'Most popular restaurants'
    },
    { 
      id: 'time_based', 
      icon: '🕒', 
      label: 'Perfect for Now',
      active: activeFilters?.timeBased || false,
      tooltip: 'Restaurants perfect for this time of day'
    }
  ];

  return (
    <div className="quick-filters-section">
      <div className="quick-filters-container">
        <div className="quick-filters-scroll">
          {quickFilters.map(filter => (
            <button
              key={filter.id}
              className={`quick-filter-chip ${filter.active ? 'active' : ''}`}
              onClick={() => onFilterClick(filter.id)}
              title={filter.tooltip}
              aria-label={filter.tooltip}
            >
              <span className="chip-icon">{filter.icon}</span>
              <span className="chip-label">{filter.label}</span>
              {filter.active && <span className="chip-check">✓</span>}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickFilters;