import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Homepage.css';

const TrendingToday = ({ location }) => {
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendingToday();
  }, [location]);

  const fetchTrendingToday = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/trending-today/?limit=8';
      if (location?.city) url += `&city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `&lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch trending dishes');
      
      const data = await response.json();
      setDishes(data || []);
    } catch (error) {
      console.error('Error fetching trending today:', error);
      setDishes([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading && dishes.length === 0) {
    return (
      <section className="trending-today">
        <h2>Trending Today</h2>
        <div className="grid-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="dish-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (dishes.length === 0) {
    return null;
  }

  return (
    <section className="trending-today">
      <div className="section-header">
        <h2>Trending Today</h2>
        <span className="section-badge">
          Hot right now
        </span>
      </div>
      
      <div className="grid-container">
        {dishes.map((dish) => (
          <div key={dish.item_id} className="dish-card trending-card">
            <div className="trending-badge">🔥 TRENDING</div>
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
              <p className="restaurant-name">{dish.restaurant?.name}</p>
              {dish.popularity_score > 0 && (
                <p className="popularity">Popularity score: {dish.popularity_score}</p>
              )}
            </div>
            <Link 
              to={`/restaurant/${dish.restaurant?.id}`}
              className="order-btn"
            >
              Order Now
            </Link>
          </div>
        ))}
      </div>
    </section>
  );
};

export default TrendingToday;