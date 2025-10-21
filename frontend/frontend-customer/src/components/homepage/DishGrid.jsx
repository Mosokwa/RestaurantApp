import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
import './Homepage.css';

const DishGrid = ({ title, dishes, pagination, loading, onLoadMore, loadMoreLoading }) => {
  if (loading && (!dishes || dishes.length === 0)) {
    return (
      <section className="dish-grid">
        <h2>{title}</h2>
        <div className="grid-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="dish-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }
  
  if (!dishes || dishes.length === 0) {
    return null;
  }
  
  return (
    <section className="dish-grid">
      <h2>{title}</h2>
      <div className="grid-container">
        {dishes.map(dish => (
          <div key={dish.item_id || dish.id} className="dish-card">
            <div className="dish-image">
              <img 
                src={dish.image || '/food.png'} 
                alt={dish.name}
                onError={(e) => {
                  e.target.src = '/food.png';
                }}
              />
            </div>
            <div className="dish-info">
              <h3>{dish.name}</h3>
              <p className="dish-description">{dish.description}</p>
              <p className="dish-price">${typeof dish.price === 'number' ? dish.price.toFixed(2) : dish.price}</p>
              <p className="restaurant-name">{dish.restaurant?.name || dish.restaurant}</p>
              {dish.order_count && (
                <p className="popularity">{dish.order_count}+ ordered</p>
              )}
              {dish.reason && (
                <p className="recommendation-reason">{dish.reason}</p>
              )}
            </div>
            <Link 
              to={`/restaurant/${dish.restaurant?.id || dish.restaurant_id}`}
              className="order-btn"
            >
              Order Now
            </Link>
          </div>
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
      {loading && dishes.length > 0 && (
        <div className="loading-more">
          <div className="spinner"></div>
          <p>Loading more dishes...</p>
        </div>
      )}
      
    </section>
  );
};

export default DishGrid;