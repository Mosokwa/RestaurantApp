import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// import './Homepage.css';

const TimeBasedRecommendations = ({ location }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [timePeriod, setTimePeriod] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTimeBasedRecommendations();
  }, [location]);

  const fetchTimeBasedRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let url = '/api/homepage/time-based-recommendations/?limit=8';
      if (location?.city) url += `&city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch time-based recommendations');
      
      const data = await response.json();
      setRecommendations(data.restaurants || []);
      setTimePeriod(data.time_period || '');
    } catch (err) {
      setError(err.message);
      console.error('Error fetching time-based recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const getTimePeriodIcon = (period) => {
    switch (period) {
      case 'breakfast': return '☕';
      case 'lunch': return '🥗';
      case 'dinner': return '🍽️';
      case 'late_night': return '🌙';
      default: return '🕒';
    }
  };

  const getTimePeriodTitle = (period) => {
    switch (period) {
      case 'breakfast': return 'Breakfast Specials';
      case 'lunch': return 'Lunch Deals';
      case 'dinner': return 'Dinner Picks';
      case 'late_night': return 'Late Night Bites';
      default: return 'Time-Based Recommendations';
    }
  };

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  if (loading && recommendations.length === 0) {
    return (
      <section className="time-based-recommendations">
        <h2>Time-Based Recommendations</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="time-based-recommendations">
        <h2>Time-Based Recommendations</h2>
        <div className="error-message">
          <p>Couldn't load time-based recommendations</p>
          <button onClick={fetchTimeBasedRecommendations} className="retry-btn">
            Try Again
          </button>
        </div>
      </section>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <section className="time-based-recommendations">
      <div className="section-header">
        <h2>
          <span className="time-icon">{getTimePeriodIcon(timePeriod)}</span>
          {getTimePeriodTitle(timePeriod)}
        </h2>
        <div className="time-badge">
          {timePeriod ? timePeriod.replace('_', ' ').toUpperCase() : 'NOW'}
        </div>
      </div>
      
      <div className="carousel-container">
        {recommendations.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card time-card"
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
                <span className="time-reason">
                  {restaurant.time_reason || 'Perfect for now'}
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

export default TimeBasedRecommendations;