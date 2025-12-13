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
        // User not authenticated
        setRestaurants([]);
        return;
      }
      
      if (!response.ok) throw new Error('Failed to fetch recently viewed');
      const data = await response.json();
      setRestaurants(data);
    } catch (error) {
      console.error('Error fetching recently viewed:', error);
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
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

  if (restaurants.length === 0) {
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
        {restaurants.map((restaurant) => (
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
                  ⭐ {restaurant.overall_rating ? restaurant.overall_rating.toFixed(1) : '4.5'}
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

export default RecentlyViewed;