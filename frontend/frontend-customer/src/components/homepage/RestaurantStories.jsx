import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './ThreeDCarousel.css';

const RestaurantStories = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(0);
  const carouselRef = useRef(null);

  useEffect(() => {
    fetchRestaurantStories();
  }, []);

  const fetchRestaurantStories = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/homepage/restaurant-stories/?limit=8');
      if (!response.ok) throw new Error('Failed to fetch restaurant stories');
      
      const data = await response.json();
      setStories(data.stories || []);
    } catch (error) {
      console.error('Error fetching restaurant stories:', error);
      setStories([]);
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

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  if (loading && stories.length === 0) {
    return (
      <section className="carousel-section carousel-loading">
        <div className="carousel-header">
          <h2 className="carousel-title">Restaurant Stories</h2>
          <span className="carousel-subtitle">
            Discover their journey
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

  if (stories.length === 0) {
    return null;
  }

  return (
    <section className="carousel-section">
      {/* ROW 1: Header */}
      <div className="carousel-header">
        <h2 className="carousel-title">Restaurant Stories</h2>
        <span className="carousel-subtitle">
          Discover their journey
        </span>
      </div>
      
      {/* ROW 2: Cards */}
      <div className="carousel-wrapper">
        <div className="carousel-track" ref={carouselRef}>
          {stories.map((restaurant) => (
            <div key={restaurant.restaurant_id} className="carousel-card">
              <div className="flip-card">
                {/* Front - Restaurant Info */}
                <div className="card-front">
                  <div className="card-image">
                    <img 
                      src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                      alt={restaurant.name}
                      onError={(e) => {
                        e.target.src = '/default-restaurant.jpg';
                      }}
                    />
                    <div className="card-badge">Story</div>
                    <div className="card-rating">
                      ⭐ {formatRating(restaurant.overall_rating)}
                    </div>
                  </div>
                  
                  <div className="front-content">
                    <h3>{restaurant.name}</h3>
                    <p className="card-description">
                      {restaurant.cuisine_names?.join(', ') || 'Various cuisines'}
                    </p>
                    <p className="card-restaurant">
                      ⭐ {formatRating(restaurant.overall_rating)} rating
                    </p>
                  </div>
                </div>
                
                {/* Back - Story Excerpt */}
                <div className="card-back">
                  <div className="back-content">
                    <h4>Their Story</h4>
                    <p className="back-description">
                      "{restaurant.story_excerpt || 'Discover their unique story and culinary journey...'}"
                    </p>
                    <Link 
                      to={`/restaurant/${restaurant.restaurant_id}`}
                      className="card-cta"
                    >
                      Read Full Story →
                    </Link>
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
          aria-label="Previous stories"
        >
          ←
        </button>
        
        <div className="carousel-dots">
          {Array.from({ length: Math.ceil(stories.length / 4) }).map((_, index) => (
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
          aria-label="Next stories"
        >
          →
        </button>
      </div>
    </section>
  );
};

export default RestaurantStories;