// pages/SearchResultsPage/components/RestaurantResultCard.jsx
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

const RestaurantResultCard = ({ restaurant }) => {
  const [hasTags, setHasTags] = useState(false);
  
  useEffect(() => {
    // Check if there are any match indicators
    const hasAnyTags = restaurant.direct_match || 
                      restaurant.has_cuisine || 
                      restaurant.has_category || 
                      restaurant.has_dish;
    setHasTags(hasAnyTags);
  }, [restaurant]);

  if (!restaurant) return null;

  const restaurantId = restaurant.restaurant_id || restaurant.id;
  const restaurantName = restaurant.name || 'Unknown Restaurant';
  const cuisineNames = restaurant.cuisine_names || restaurant.cuisines || [];
  const logo = restaurant.logo || '/banner.jpg';
  const rating = restaurant.overall_rating || restaurant.rating;
  const distance = restaurant.distance_km || restaurant.distance;
  const deliveryTime = restaurant.estimated_delivery_time || restaurant.deliveryTime;
  const branchCount = restaurant.branch_count || restaurant.branches?.length || 1;
  const hasOpenBranch = restaurant.has_open_branch || restaurant.openNow || false;

  const directMatch = restaurant.direct_match || false;
  const hasCuisine = restaurant.has_cuisine || false;
  const hasCategory = restaurant.has_category || false;
  const hasDish = restaurant.has_dish || false;

  if (!restaurantId) return null;

  return (
    <Link to={`/restaurants/${restaurantId}`} className="sr-restaurant-card">
      <div className="sr-card-image-container">
        <div className="sr-card-image">
          <img 
            src={logo} 
            alt={restaurantName}
            onError={(e) => { e.target.src = '/banner.jpg'; }}
          />
        </div>
        {restaurant.is_featured && (
          <span className="sr-badge-featured">⭐ Featured</span>
        )}
        {restaurant.is_verified && (
          <span className="sr-badge-verified">✓ Verified</span>
        )}
      </div>
      
      <div className="sr-card-content">
        <h3 className="sr-card-title">{restaurantName}</h3>
        
        {/* Cuisine tags - fixed height container */}
        <div className="sr-cuisine-tags-container">
          <div className="sr-cuisine-tags">
            {cuisineNames.slice(0, 3).map((cuisine, idx) => (
              <span key={idx} className="sr-cuisine-tag">{cuisine}</span>
            ))}
          </div>
        </div>
        
        {/* Match indicators - fixed height container */}
        <div className="sr-match-indicators-container" style={{ 
          minHeight: hasTags ? '28px' : '0',
          opacity: hasTags ? 1 : 0,
          visibility: hasTags ? 'visible' : 'hidden'
        }}>
          {(directMatch || hasCuisine || hasCategory || hasDish) && (
            <div className="sr-match-indicators">
              {directMatch && (
                <span className="sr-match-indicator sr-match-direct">🔍 Restaurant match</span>
              )}
              {hasCuisine && (
                <span className="sr-match-indicator sr-match-cuisine">🍜 Has cuisine</span>
              )}
              {hasCategory && (
                <span className="sr-match-indicator sr-match-category">📋 Has category</span>
              )}
              {hasDish && (
                <span className="sr-match-indicator sr-match-dish">🍽️ Has dish</span>
              )}
            </div>
          )}
        </div>
        
        {/* Restaurant meta - fixed position */}
        <div className="sr-restaurant-meta">
          <span className="sr-meta-rating">
            ⭐ {rating || 'New'}
          </span>
          
          {distance && (
            <span className="sr-meta-distance">
              📍 {distance} km
            </span>
          )}
          
          {deliveryTime && (
            <span className="sr-meta-delivery">
              ⏱️ {deliveryTime} min
            </span>
          )}
        </div>
        
        {/* Branch info - always at bottom */}
        <div className="sr-branch-info">
          {branchCount === 1 ? '1 location' : `${branchCount} locations`}
          {hasOpenBranch && (
            <span className="sr-open-now"> • Open now</span>
          )}
        </div>
      </div>
    </Link>
  );
};

export default RestaurantResultCard;