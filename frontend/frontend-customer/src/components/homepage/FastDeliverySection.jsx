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

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
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

  if (restaurants.length === 0) {
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
        {restaurants.map((restaurant) => (
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
                  <p className="distance">{restaurant.distance_km.toFixed(1)} km away</p>
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