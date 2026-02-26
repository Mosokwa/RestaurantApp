import React, { useState, useEffect } from 'react';
import './RestaurantCard.css';

const RestaurantCard = ({ restaurant, onClick, userLocation }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [imgSrc, setImgSrc] = useState('');

  const {
    name = 'Restaurant Name',
    banner_image,
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

  // Determine the image source on component mount and when banner_image changes
  useEffect(() => {
    
    // Determine the correct image path
    let imagePath = '';
    
    if (banner_image) {
      // If banner_image is a full URL, use it as is
      if (banner_image.startsWith('http')) {
        imagePath = banner_image;
      } 
      // If it starts with /, it's already a root-relative path
      else if (banner_image.startsWith('/')) {
        imagePath = banner_image;
      }
      // Otherwise, assume it's in the media folder
      else {
        // Try different possible paths
        imagePath = `/media/${banner_image}`;
      }
    } else {
      // No banner image, use default
      imagePath = '/banner.jpg';
    }
    
    setImgSrc(imagePath);
    setImageLoaded(false);
    setImageError(false);
  }, [banner_image, name]);

  const handleImageError = () => {
    console.log('Image failed to load:', imgSrc);
    setImageError(true);
    
    // Try the default banner as last resort
    if (imgSrc !== '/images/banner.jpg') {
      setImgSrc('/images/banner.jpg');
    }
  };

  const handleImageLoad = () => {
    console.log('Image loaded successfully:', imgSrc);
    setImageLoaded(true);
    setImageError(false);
  };

  const primaryBranch = branches[0] || {};
  const isOpenNow = primaryBranch?.is_open_now || false;
  const city = primaryBranch?.address?.city || '';

  const rating = parseFloat(overall_rating || 0).toFixed(1);
  const reviewCount = total_reviews || 0;

  const cuisineNames = Array.isArray(cuisines) 
    ? cuisines.slice(0, 2).map(c => c?.name || '').filter(Boolean).join(' • ')
    : '';
  const remainingCuisines = Array.isArray(cuisines) ? Math.max(0, cuisines.length - 2) : 0;

  return (
    <div className="rex-card" onClick={() => onClick(restaurant)}>
      <div className="rex-card-badges">
        {is_featured && <span className="rex-badge featured">⭐ Featured</span>}
        {is_verified && <span className="rex-badge verified">✓ Verified</span>}
        {!isOpenNow && <span className="rex-badge closed">🔒 Closed</span>}
        {distance_km && distance_km < 1 && (
          <span className="rex-badge near">📍 Very Near</span>
        )}
      </div>

      <div className="rex-card-image-container">
        {!imageLoaded && !imageError && (
          <div className="rex-image-skeleton">
            <span>Loading...</span>
          </div>
        )}
        {imgSrc && (
          <img
            src={imgSrc}
            alt={name}
            className={`rex-card-image ${imageLoaded ? 'loaded' : ''}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            loading="lazy"
          />
        )}
        {imageError && (
          <div className="rex-image-error">
            <span>📸</span>
            <span>Image not available</span>
          </div>
        )}
      </div>

      <div className="rex-card-content">
        <div className="rex-card-header">
          <h3 className="rex-restaurant-name" title={name}>{name}</h3>
          <div className="rex-rating-container">
            <span className="rex-rating-star">★</span>
            <span className="rex-rating-value">{rating}</span>
            <span className="rex-rating-count">({reviewCount})</span>
          </div>
        </div>

        <div className="rex-restaurant-meta">
          <div className="rex-cuisine-info">
            <span className="rex-meta-icon">🍽️</span>
            <span className="rex-cuisine-text" title={cuisineNames}>
              {cuisineNames || 'Various Cuisines'}
              {remainingCuisines > 0 && ` +${remainingCuisines}`}
            </span>
          </div>
          
          <div className="rex-location-info">
            <span className="rex-meta-icon">📍</span>
            <span className="rex-distance-text">
              {distance_km ? `${distance_km.toFixed(1)} km` : city || 'Location available'}
            </span>
            {isOpenNow && <span className="rex-open-badge">Open</span>}
          </div>
        </div>

        <div className="rex-restaurant-footer">
          <div className="rex-price-info">
            <span className="rex-price-level">{price_level}</span>
          </div>
          <div className="rex-delivery-info">
            {restaurant?.delivery_fee !== undefined && (
              <span className="rex-delivery-fee">🚲 ${Number(restaurant.delivery_fee).toFixed(2)}</span>
            )}
          </div>
        </div>

        <div className="rex-card-actions">
          {reservation_enabled && (
            <button className="rex-action-btn rex-reserve-btn" onClick={(e) => e.stopPropagation()}>
              📅 Reserve
            </button>
          )}
          <button className="rex-action-btn rex-view-btn" onClick={(e) => e.stopPropagation()}>
            👁️ View
          </button>
        </div>
      </div>
    </div>
  );
};

export default RestaurantCard;