import React, { useState } from 'react';
import './RestaurantCard.css';

// Default fallback images
const DEFAULT_RESTAURANT_IMAGE = '/banner.jpg';
const DEFAULT_FOOD_IMAGE = '/food.png';

const RestaurantCard = ({ restaurant, onClick, userLocation }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const {
    restaurant_id,
    name = 'Restaurant Name',
    banner_image,
    logo,
    overall_rating = 0,
    total_reviews = 0,
    cuisines = [],
    branches = [],
    is_featured = false,
    is_verified = false,
    reservation_enabled = false,
    distance_km,
    price_level = '$$'
  } = restaurant || {};

  // Get primary branch info
  const primaryBranch = branches[0] || {};
  const isOpenNow = primaryBranch?.is_open_now || false;
  const city = primaryBranch?.address?.city || '';

  // Format rating
  const rating = parseFloat(overall_rating || 0).toFixed(1);
  const reviewCount = total_reviews || 0;

  // Get cuisine names
  const cuisineNames = Array.isArray(cuisines) 
    ? cuisines.slice(0, 2).map(c => c?.name || '').filter(Boolean).join(' • ')
    : '';
  const remainingCuisines = Array.isArray(cuisines) ? Math.max(0, cuisines.length - 2) : 0;

  // Handle image with fallbacks - try banner first, then logo, then default
  const getImageSource = () => {
    if (imageError) return DEFAULT_RESTAURANT_IMAGE;
    
    // Try banner image first
    if (banner_image) {
      // Handle both full URLs and relative paths
      if (banner_image.startsWith('http')) {
        return banner_image;
      }
      // If it's a relative path, ensure it's properly formatted
      return banner_image.startsWith('/') ? banner_image : `/${banner_image}`;
    }
    
    // Try logo as fallback
    if (logo) {
      return logo.startsWith('/') ? logo : `/${logo}`;
    }
    
    // Default fallback
    return DEFAULT_RESTAURANT_IMAGE;
  };

  const imageUrl = getImageSource();

  return (
    <div className="restaurant-card glass-card" onClick={() => onClick(restaurant)}>
      {/* Card Badges */}
      <div className="card-badges">
        {is_featured && (
          <span className="badge featured">⭐ Featured</span>
        )}
        {is_verified && (
          <span className="badge verified">✓ Verified</span>
        )}
        {!isOpenNow && (
          <span className="badge closed">🔒 Closed</span>
        )}
        {distance_km && distance_km < 1 && (
          <span className="badge near">📍 Very Near</span>
        )}
      </div>

      {/* Image Container */}
      <div className="card-image-container">
        {!imageLoaded && !imageError && (
          <div className="image-skeleton" />
        )}
        <img
          src={imageUrl}
          alt={name}
          className={`card-image ${imageLoaded ? 'loaded' : ''}`}
          onLoad={() => setImageLoaded(true)}
          onError={() => {
            console.warn(`Failed to load image for ${name}:`, imageUrl);
            setImageError(true);
          }}
          loading="lazy"
        />
        
        {/* Offer Overlay - Example if you have offers */}
        {restaurant?.has_offer && (
          <div className="offer-badge">
            <span className="offer-text">🔥 Special Offer</span>
          </div>
        )}
      </div>

      {/* Card Content */}
      <div className="card-content">
        <div className="card-header">
          <h3 className="restaurant-name">{name}</h3>
          <div className="rating-container">
            <span className="rating-star">★</span>
            <span className="rating-value">{rating}</span>
            <span className="rating-count">({reviewCount})</span>
          </div>
        </div>

        {/* Cuisine & Location */}
        <div className="restaurant-meta">
          <div className="cuisine-info">
            <span className="meta-icon">🍽️</span>
            <span className="cuisine-text">
              {cuisineNames || 'Various Cuisines'}
              {remainingCuisines > 0 && ` +${remainingCuisines}`}
            </span>
          </div>
          
          <div className="location-info">
            <span className="meta-icon">📍</span>
            <span className="distance-text">
              {distance_km ? `${distance_km.toFixed(1)} km` : city || 'Location available'}
            </span>
            {isOpenNow && (
              <span className="open-badge">Open</span>
            )}
          </div>
        </div>

        {/* Price & Delivery */}
        <div className="restaurant-footer">
          <div className="price-info">
            <span className="price-level">{price_level}</span>
            {restaurant?.min_order_amount && (
              <span className="min-order">Min ${restaurant.min_order_amount}</span>
            )}
          </div>
          
          <div className="delivery-info">
            {restaurant?.delivery_fee !== undefined && (
              <span className="delivery-fee">
                🚲 ${Number(restaurant.delivery_fee).toFixed(2)}
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="card-actions">
          {reservation_enabled && (
            <button className="action-btn reserve-btn" onClick={(e) => e.stopPropagation()}>
              📅 Reserve
            </button>
          )}
          <button className="action-btn order-btn" onClick={(e) => e.stopPropagation()}>
            🍽️ Order
          </button>
        </div>
      </div>
    </div>
  );
};

export default RestaurantCard;