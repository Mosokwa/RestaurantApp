import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './ThreeDCarousel.css';

const TrendingToday = ({ location }) => {
  const [dishes, setDishes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const carouselRef = useRef(null);

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

  const handlePrev = () => {
    if (carouselRef.current) {
      const cardWidth = 280 + 32;
      carouselRef.current.scrollLeft -= cardWidth * 2;
    }
    setCurrentPage(prev => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    if (carouselRef.current) {
      const cardWidth = 280 + 32;
      carouselRef.current.scrollLeft += cardWidth * 2;
    }
    setCurrentPage(prev => prev + 1);
  };

  if (loading && dishes.length === 0) {
    return (
      <section className="carousel-section carousel-loading">
        <div className="carousel-header">
          <h2 className="carousel-title">Trending Today</h2>
          <span className="carousel-subtitle">
            Hot right now
          </span>
        </div>
        <div className="carousel-wrapper">
          <div className="carousel-track">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="carousel-skeleton"></div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (dishes.length === 0) {
    return null;
  }

  return (
    <section className="carousel-section">
      {/* ROW 1: Header */}
      <div className="carousel-header">
        <h2 className="carousel-title">Trending Today</h2>
        <span className="carousel-subtitle">
          Hot right now
        </span>
      </div>
      
      {/* ROW 2: Cards */}
      <div className="carousel-wrapper">
        <div className="carousel-track" ref={carouselRef}>
          {dishes.map((dish) => (
            <div key={dish.item_id} className="carousel-card">
              <div className="flip-card">
                {/* Front - Dish Info */}
                <div className="card-front">
                  <div className="card-image">
                    <img 
                      src={dish.image || '/food.png'} 
                      alt={dish.name}
                      onError={(e) => {
                        e.target.src = '/food.png';
                      }}
                    />
                    <div className="card-badge trending-badge">🔥 TRENDING</div>
                    {dish.popularity_score > 0 && (
                      <div className="card-rating">
                        🔥 {dish.popularity_score}%
                      </div>
                    )}
                  </div>
                  
                  <div className="front-content">
                    <h3>{dish.name}</h3>
                    <p className="card-description">{dish.description}</p>
                    <p className="card-price">
                      ${typeof dish.price === 'number' ? dish.price.toFixed(2) : dish.price}
                    </p>
                    <p className="card-restaurant">
                      {dish.restaurant?.name}
                    </p>
                  </div>
                </div>
                
                {/* Back - Why It's Trending */}
                <div className="card-back">
                  <div className="back-content">
                    <h4>Why It's Trending</h4>
                    <p className="back-description">
                      {dish.popularity_score > 0 
                        ? `With a popularity score of ${dish.popularity_score}%, this dish is one of the most ordered items today!`
                        : 'This dish is trending high in your area with increasing orders every hour.'
                      }
                    </p>
                    
                    <div className="cta-group">
                      {dish.restaurant?.id && (
                        <Link 
                          to={`/restaurant/${dish.restaurant.id}`}
                          className="card-cta"
                        >
                          View Restaurant
                        </Link>
                      )}
                      
                      <Link 
                        to={`/dish/${dish.item_id}`}
                        className="card-cta secondary"
                      >
                        View Details →
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* ROW 3: Controls */}
      <div className="carousel-controls">
        <button 
          className="carousel-btn prev-btn" 
          onClick={handlePrev}
          aria-label="Previous dishes"
        >
          ←
        </button>
        
        <div className="carousel-dots">
          {Array.from({ length: Math.ceil(dishes.length / 4) }).map((_, index) => (
            <button
              key={index}
              className={`carousel-dot ${index === currentPage ? 'active' : ''}`}
              onClick={() => {
                if (carouselRef.current) {
                  const cardWidth = 280 + 32;
                  carouselRef.current.scrollLeft = cardWidth * 4 * index;
                }
                setCurrentPage(index);
              }}
              aria-label={`Go to page ${index + 1}`}
            />
          ))}
        </div>
        
        <button 
          className="carousel-btn next-btn" 
          onClick={handleNext}
          aria-label="Next dishes"
        >
          →
        </button>
      </div>
    </section>
  );
};

export default TrendingToday;