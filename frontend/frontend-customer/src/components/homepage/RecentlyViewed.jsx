// components/homepage/RecentlyViewed.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// import './Homepage.css';

const RecentlyViewed = ({ location }) => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentlyViewed();
  }, [location]);

  const fetchRecentlyViewed = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/recently-viewed/?limit=6';
      if (location?.city) url += `&city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (response.status === 401) {
        setRestaurants([]);
        return;
      }
      
      if (!response.ok) throw new Error('Failed to fetch recently viewed');
      const data = await response.json();
      setRestaurants(data || []);
    } catch (error) {
      console.error('Error fetching recently viewed:', error);
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
    // Convert to number if it's a string
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

  if (loading) {
    return (
      <section className="recently-viewed">
        <h2>Recently Viewed</h2>
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
    <section className="recently-viewed">
      <div className="section-header">
        <h2>Recently Viewed</h2>
        <span className="section-badge">
          Continue browsing
        </span>
      </div>
      
      <div className="carousel-container">
        {uniqueRestaurants.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card recent-card"
          >
            <div className="restaurant-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="restaurant-meta">
                {restaurant.last_viewed && (
                  <span className="view-time">
                    Viewed {new Date(restaurant.last_viewed).toLocaleDateString()}
                  </span>
                )}
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
                <p className="delivery-info">25-35 min • $1.99 delivery</p>
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

export default RecentlyViewed;