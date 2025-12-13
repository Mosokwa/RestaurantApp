import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
// import './Homepage.css';

const UserFavorites = ({ location }) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadMoreLoading, setLoadMoreLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
        return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  useEffect(() => {
    fetchFavorites();
  }, [location]);

  const fetchFavorites = async (page = 1) => {
    try {
      const loadingState = page === 1 ? setLoading : setLoadMoreLoading;
      loadingState(true);
      
      let url = `/api/homepage/user-favorites/?page=${page}&limit=8`;
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
        // User not authenticated, hide this section
        setFavorites([]);
        return;
      }
      
      if (!response.ok) throw new Error('Failed to fetch favorites');
      const data = await response.json();
      
      if (page === 1) {
        setFavorites(data);
      } else {
        setFavorites(prev => [...prev, ...data]);
      }
      setCurrentPage(page);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    } finally {
      setLoading(false);
      setLoadMoreLoading(false);
    }
  };

  const handleLoadMore = () => {
    fetchFavorites(currentPage + 1);
  };

  if (loading && favorites.length === 0) {
    return (
      <section className="user-favorites">
        <h2>Your Favorites</h2>
        <div className="carousel-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="restaurant-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (favorites.length === 0) {
    return null; // Don't show section if no favorites
  }

  return (
    <section className="user-favorites">
      <div className="section-header">
        <h2>Your Favorites</h2>
        <span className="section-badge">
          {favorites.length} saved
        </span>
      </div>
      
      <div className="carousel-container">
        {favorites.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="restaurant-card favorite-card"
          >
            <div className="favorite-badge">❤️</div>
            <div className="restaurant-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="restaurant-meta">
                {restaurant.favorited_at && (
                  <span className="favorite-date">
                    Saved {new Date(restaurant.favorited_at).toLocaleDateString()}
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

      {favorites.length >= 8 && (
        <LoadMoreButton
          loading={loadMoreLoading}
          onClick={handleLoadMore}
        />
      )}
    </section>
  );
};

export default UserFavorites;