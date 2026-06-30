// components/homepage/FastDeliverySection.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// import './Homepage.css';

const FastDeliverySection = ({ location }) => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFastDeliveryRestaurants();
  }, [location]);

  const fetchFastDeliveryRestaurants = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/fast-delivery/?limit=6';
      if (location?.city) url += `&city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch fast delivery restaurants');
      
      const data = await response.json();
      setRestaurants(data.restaurants || []);
    } catch (error) {
      console.error('Error fetching fast delivery restaurants:', error);
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
  };

  // Helper function to safely format rating
  const formatRating = (rating) => {
    if (rating === null || rating === undefined || rating === '') {
      return '4.5';
    }
    const numRating = typeof rating === 'string' ? parseFloat(rating) : rating;
    if (isNaN(numRating)) return '4.5';
    return numRating.toFixed(1);
  };

  // Helper to safely format distance
  const formatDistance = (distance) => {
    if (distance === null || distance === undefined) return null;
    const numDistance = typeof distance === 'string' ? parseFloat(distance) : distance;
    if (isNaN(numDistance)) return null;
    return numDistance.toFixed(1);
  };

  if (loading && restaurants.length === 0) {
    return (
      <section className="fast-delivery">
        <h2>Fast Delivery</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  // Remove duplicates by restaurant_id
  const seenIds = new Set();
  const uniqueRestaurants = (restaurants || []).filter(restaurant => {
    if (seenIds.has(restaurant.restaurant_id)) {
      return false;
    }
    seenIds.add(restaurant.restaurant_id);
    return true;
  });

  if (uniqueRestaurants.length === 0) {
    return null;
  }

  return (
    <section className="fast-delivery">
      <div className="section-header">
        <h2>Fast Delivery</h2>
        <span className="section-badge">
          Quickest near you
        </span>
      </div>
      
      <div className="carousel-container">
        {uniqueRestaurants.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card fast-delivery-card"
          >
            {restaurant.delivery_info?.is_fast_delivery && (
              <div className="fast-badge">⚡ FAST</div>
            )}
            <div className="restaurant-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="restaurant-meta">
                <span className="delivery-time">
                  {restaurant.delivery_info?.estimated_time || '25-35 min'}
                </span>
                <div className="restaurant-rating">
                  ⭐ {formatRating(restaurant.overall_rating)}
                </div>
              </div>
            </div>
            <div className="restaurant-info">
              <h3>{restaurant.name}</h3>
              <p className="cuisines">
                {restaurant.cuisine_names?.join(', ') || 'Various cuisines'}
              </p>
              <div className="restaurant-footer">
                <p className="delivery-info">{restaurant.delivery_info?.estimated_time || '25-35 min'} • $1.99 delivery</p>
                {restaurant.distance_km && (
                  <p className="distance">{formatDistance(restaurant.distance_km)} km away</p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};

export default FastDeliverySection;