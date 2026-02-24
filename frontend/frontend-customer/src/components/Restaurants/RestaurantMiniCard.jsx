import React, { useState } from 'react';
import './RestaurantMiniCard.css';

// Default fallback images
const DEFAULT_RESTAURANT_IMAGE = '/banner.jpg';
const DEFAULT_FOOD_IMAGE = '/food.png';

const RestaurantMiniCard = ({ restaurant, onClick, type }) => {
  const [imageError, setImageError] = useState(false);
  
  // Safely access properties with defaults
  const {
    restaurant_id,
    id,
    name = 'Restaurant',
    banner_image,
    logo,
    overall_rating = 0,
    total_reviews = 0,
    cuisines = [],
    distance_km
  } = restaurant || {};

  const rating = parseFloat(overall_rating || 0).toFixed(1);
  
  // Safely get cuisine name
  const cuisineNames = Array.isArray(cuisines) && cuisines.length > 0
    ? cuisines[0]?.name || ''
    : '';

  // Handle image with fallbacks
  const getImageSource = () => {
    if (imageError) return DEFAULT_RESTAURANT_IMAGE;
    
    if (banner_image) {
      return banner_image.startsWith('http') ? banner_image : 
             banner_image.startsWith('/') ? banner_image : `/${banner_image}`;
    }
    
    if (logo) {
      return logo.startsWith('/') ? logo : `/${logo}`;
    }
    
    // Use food.png for menu items, banner.jpg for restaurants
    return type === 'menu_item' ? DEFAULT_FOOD_IMAGE : DEFAULT_RESTAURANT_IMAGE;
  };

  const imageUrl = getImageSource();

  return (
    <div 
      className="restaurant-mini-card glass-card" 
      onClick={() => onClick(restaurant)}
      role="button"
      tabIndex={0}
      onKeyPress={(e) => e.key === 'Enter' && onClick(restaurant)}
    >
      <div className="mini-card-image">
        <img 
          src={imageUrl} 
          alt={name}
          loading="lazy"
          onError={() => setImageError(true)}
        />
      </div>
      
      <div className="mini-card-content">
        <h4 className="mini-card-title">{name}</h4>
        
        <div className="mini-card-meta">
          <span className="mini-rating">
            ★ {rating} {total_reviews > 0 && `(${total_reviews})`}
          </span>
          
          {cuisineNames && (
            <span className="mini-cuisine">{cuisineNames}</span>
          )}
          
          {distance_km && (
            <span className="mini-distance">{distance_km.toFixed(1)} km</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default RestaurantMiniCard;