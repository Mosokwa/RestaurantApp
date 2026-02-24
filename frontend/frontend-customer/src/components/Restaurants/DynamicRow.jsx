import React, { useRef, useMemo } from 'react';
import RestaurantMiniCard from './RestaurantMiniCard';
import './DynamicRow.css';

const DynamicRow = ({ 
  title, 
  subtitle, 
  restaurants = [], 
  loading = false,
  onRestaurantClick,
  viewAllLink,
  type
}) => {
  const scrollRef = useRef(null);

  // Extract array from various possible structures
  const restaurantList = useMemo(() => {
    if (Array.isArray(restaurants)) {
      return restaurants;
    }
    if (restaurants?.items && Array.isArray(restaurants.items)) {
      return restaurants.items;
    }
    if (restaurants?.results && Array.isArray(restaurants.results)) {
      return restaurants.results;
    }
    if (restaurants?.recommendations && Array.isArray(restaurants.recommendations)) {
      return restaurants.recommendations;
    }
    return [];
  }, [restaurants]);

  const scroll = (direction) => {
    if (scrollRef.current) {
      const { current } = scrollRef;
      const scrollAmount = direction === 'left' 
        ? -current.clientWidth * 0.8 
        : current.clientWidth * 0.8;
      
      current.scrollBy({ left: scrollAmount, behavior: 'smooth' });
    }
  };

  if (loading) {
    return (
      <div className="dynamic-row">
        <div className="row-header">
          <div>
            <div className="title-skeleton" />
            {subtitle && <div className="subtitle-skeleton" />}
          </div>
        </div>
        <div className="row-scroll-wrapper">
          <div className="row-scroll">
            {[...Array(6)].map((_, i) => (
              <div key={`skeleton-${type}-${i}`} className="mini-card-skeleton glass-card" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!restaurantList || restaurantList.length === 0) {
    return null;
  }

  return (
    <div className="dynamic-row">
      <div className="row-header">
        <div>
          <h2 className="row-title">{title}</h2>
          {subtitle && <p className="row-subtitle">{subtitle}</p>}
        </div>
        <div className="row-actions">
          {viewAllLink && (
            <a href={viewAllLink} className="view-all-link">
              View All <span className="arrow">→</span>
            </a>
          )}
          <div className="scroll-buttons">
            <button 
              className="scroll-btn glass-card" 
              onClick={() => scroll('left')}
              aria-label="Scroll left"
              type="button"
            >
              ←
            </button>
            <button 
              className="scroll-btn glass-card" 
              onClick={() => scroll('right')}
              aria-label="Scroll right"
              type="button"
            >
              →
            </button>
          </div>
        </div>
      </div>

      <div className="row-scroll-wrapper">
        <div className="row-scroll" ref={scrollRef}>
          {restaurantList.map((restaurant, index) => (
            <RestaurantMiniCard
              key={restaurant?.restaurant_id || restaurant?.id || `${type}-row-${index}`}
              restaurant={restaurant}
              onClick={() => onRestaurantClick(restaurant)}
              type={type}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default DynamicRow;