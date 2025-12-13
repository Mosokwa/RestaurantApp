import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
import './Homepage.css';

const RestaurantCarousel = ({ title, restaurants, pagination, loading, onLoadMore, loadMoreLoading }) => {
  // Helper function to safely format rating
  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  // Get the actual restaurants array from the data
  const getRestaurantsArray = () => {
    if (!restaurants) return [];
    
    // If restaurants is an array, return it directly
    if (Array.isArray(restaurants)) return restaurants;
    
    // If restaurants is an object with a restaurants property
    if (restaurants.restaurants && Array.isArray(restaurants.restaurants)) {
      return restaurants.restaurants;
    }
    
    // If restaurants is an object with a results property
    if (restaurants.results && Array.isArray(restaurants.results)) {
      return restaurants.results;
    }
    
    // If restaurants is an object with an items property
    if (restaurants.items && Array.isArray(restaurants.items)) {
      return restaurants.items;
    }
    
    return [];
  };

  const restaurantsArray = getRestaurantsArray();

  if (loading && restaurantsArray.length === 0) {
    return (
      <section className="restaurant-carousel">
        <h2>{title}</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }
  
  if (!restaurantsArray || restaurantsArray.length === 0) {
    return null;
  }
  
  return (
    <section className="restaurant-carousel">
      <h2>{title}</h2>
      <div className="carousel-container">
        {restaurantsArray.map(restaurant => (
          <Link 
            key={restaurant.restaurant_id || restaurant.id} 
            to={`/restaurant/${restaurant.restaurant_id || restaurant.id}`}
            className="restaurant-card"
          >
            <div className="restaurant-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="restaurant-rating">
                ⭐ {formatRating(restaurant.overall_rating)}
              </div>
            </div>
            <div className="restaurant-info">
              <h3>{restaurant.name}</h3>
              <p className="cuisines">
                {restaurant.cuisine_names?.join(', ') || restaurant.cuisines?.map(c => c.name).join(', ') || 'Various cuisines'}
              </p>
              <p className="delivery-info">25-35 min • $1.99 delivery</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Load More Button for pagination */}
      {pagination?.next && onLoadMore && (
        <LoadMoreButton
          loading={loadMoreLoading}
          onClick={onLoadMore}
        />
      )}
      
      {/* Loading indicator for additional items */}
      {loading && restaurantsArray.length > 0 && (
        <div className="loading-more">
          <div className="spinner"></div>
          <p>Loading more restaurants...</p>
        </div>
      )}

    </section>
  );
};

export default RestaurantCarousel;