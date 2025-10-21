import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
import './Homepage.css';

const RestaurantCarousel = ({ title, restaurants, pagination, loading, onLoadMore, loadMoreLoading }) => {
  if (loading && (!restaurants || restaurants.length === 0)) {
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
  
  if (!restaurants || restaurants.length === 0) {
    return null;
  }
  
  return (
    <section className="restaurant-carousel">
      <h2>{title}</h2>
      <div className="carousel-container">
        {restaurants.restaurants.map(restaurant => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
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
                {/* ⭐ {restaurant.overall_rating ? restaurant.overall_rating.toFixed(1) : '4.5'} */}
                4.5
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
      {loading && restaurants.length > 0 && (
        <div className="loading-more">
          <div className="spinner"></div>
          <p>Loading more restaurants...</p>
        </div>
      )}

    </section>
  );
};

export default RestaurantCarousel;