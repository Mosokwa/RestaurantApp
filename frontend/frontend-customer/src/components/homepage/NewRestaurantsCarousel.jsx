import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
// import './Homepage.css';

const NewRestaurantsCarousel = ({ location, pagination, onLoadMore }) => {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchNewRestaurants();
  }, [location]);

  const fetchNewRestaurants = async (page = 1) => {
    try {
      const loadingState = page === 1 ? setLoading : setLoadMoreLoading;
      loadingState(true);
      
      let url = `/api/homepage/new-restaurants/?page=${page}&limit=12`;
      if (location?.city) url += `&city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch new restaurants');
      const data = await response.json();
      
      if (page === 1) {
        setRestaurants(data);
      } else {
        setRestaurants(prev => [...prev, ...data]);
      }
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching new restaurants:', error);
    } finally {
      setLoading(false);
      setLoadMoreLoading(false);
    }
  };

  const handleLoadMore = () => {
    fetchNewRestaurants(currentPage + 1);
    if (onLoadMore) onLoadMore();
  };

  // Helper function to safely format rating
  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5'; // Default rating if none exists
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  if (loading && restaurants.length === 0) {
    return (
      <section className="new-restaurants">
        <h2>New to FoodHub</h2>
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
    <section className="new-restaurants">
      <div className="section-header">
        <h2>New to FoodHub</h2>
        <span className="section-badge">
          {restaurants.length}+ recently added
        </span>
      </div>
      
      <div className="carousel-container">
        {restaurants.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card new-restaurant-card"
          >
            {restaurant.is_new && (
              <div className="new-badge">NEW</div>
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
                {restaurant.new_for_days !== undefined && (
                  <span className="new-indicator">
                    {restaurant.new_for_days <= 1 ? 'Today' : 
                     restaurant.new_for_days <= 7 ? `${restaurant.new_for_days}d ago` : 
                     'Recently added'}
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
                  <p className="distance">{restaurant.distance_km.toFixed(1)} km away</p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {restaurants.length >= 12 && (
        <LoadMoreButton
          loading={loadMoreLoading}
          onClick={handleLoadMore}
        />
      )}
    </section>
  );
};

export default NewRestaurantsCarousel;