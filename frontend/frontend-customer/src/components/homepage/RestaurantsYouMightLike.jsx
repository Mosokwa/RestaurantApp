import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
// import './Homepage.css';

const RestaurantsYouMightLike = ({ location }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPersonalized, setIsPersonalized] = useState(false);

  useEffect(() => {
    fetchRestaurantsYouMightLike();
  }, [location]);

  const fetchRestaurantsYouMightLike = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let url = '/api/homepage/restaurants-you-might-like/?limit=8';
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
        setRecommendations([]);
        return;
      }
      
      if (!response.ok) throw new Error('Failed to fetch recommendations');
      
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setIsPersonalized(data.is_personalized || false);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching restaurants you might like:', err);
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

  if (loading && recommendations.length === 0) {
    return (
      <section className="restaurants-you-might-like">
        <h2>Restaurants You Might Like</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <section className="restaurants-you-might-like">
      <div className="section-header">
        <h2>
          {isPersonalized ? 'Restaurants You Might Like' : 'Try These Popular Spots'}
        </h2>
        <span className="section-badge">
          {isPersonalized ? 'Personalized for you' : 'Based on popularity'}
        </span>
      </div>
      
      <div className="carousel-container">
        {recommendations.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card recommendation-card"
          >
            {restaurant.has_significant_match && restaurant.match_score > 0 && (
              <div className="match-badge">
                {restaurant.match_score}% match
              </div>
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
                <span className="recommendation-reason">
                  {restaurant.recommendation_reason || 'Recommended for you'}
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

export default RestaurantsYouMightLike;