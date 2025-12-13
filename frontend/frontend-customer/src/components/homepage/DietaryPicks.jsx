import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// import './Homepage.css';

const DietaryPicks = ({ location }) => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dietaryPrefs, setDietaryPrefs] = useState([]);

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
        return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  useEffect(() => {
    fetchDietaryPicks();
  }, [location]);

  const fetchDietaryPicks = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/dietary-picks/?limit=6';
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
      
      if (!response.ok) throw new Error('Failed to fetch dietary picks');
      const data = await response.json();
      
      setRestaurants(data);
      if (data.length > 0 && data[0].dietary_match?.user_preferences) {
        setDietaryPrefs(data[0].dietary_match.user_preferences);
      }
    } catch (error) {
      console.error('Error fetching dietary picks:', error);
      setRestaurants([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <section className="dietary-picks">
        <h2>Dietary Picks</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (restaurants.length === 0 || dietaryPrefs.length === 0) {
    return null;
  }

  return (
    <section className="dietary-picks">
      <div className="section-header">
        <h2>Perfect for Your Diet</h2>
        <div className="preferences-badge">
          {dietaryPrefs.map(pref => (
            <span key={pref} className="pref-tag">{pref}</span>
          ))}
        </div>
      </div>
      
      <div className="carousel-container">
        {restaurants.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card dietary-card"
          >
            <div className="dietary-match-badge">
              {restaurant.dietary_match?.match_percentage}% match
            </div>
            <div className="restaurant-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="restaurant-meta">
                <span className="match-count">
                  {restaurant.dietary_match?.match_count} matching items
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

export default DietaryPicks;