import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Homepage.css';

const RestaurantStories = () => {
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRestaurantStories();
  }, []);

  const fetchRestaurantStories = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/homepage/restaurant-stories/?limit=4');
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

  const formatRating = (rating) => {
    if (rating === null || rating === undefined || isNaN(rating)) {
      return '4.5';
    }
    return typeof rating === 'number' ? rating.toFixed(1) : rating;
  };

  if (loading && stories.length === 0) {
    return (
      <section className="restaurant-stories">
        <h2>Restaurant Stories</h2>
        <div className="stories-container loading">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="story-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (stories.length === 0) {
    return null;
  }

  return (
    <section className="restaurant-stories">
      <div className="section-header">
        <h2>Restaurant Stories</h2>
        <span className="section-badge">
          Discover their journey
        </span>
      </div>
      
      <div className="stories-container">
        {stories.map((restaurant) => (
          <Link 
            key={restaurant.restaurant_id} 
            to={`/restaurant/${restaurant.restaurant_id}`}
            className="story-card"
          >
            <div className="story-image">
              <img 
                src={restaurant.banner_image || restaurant.logo || '/banner.jpg'} 
                alt={restaurant.name}
                onError={(e) => {
                  e.target.src = '/default-restaurant.jpg';
                }}
              />
              <div className="story-overlay">
                <div className="restaurant-rating">
                  ⭐ {formatRating(restaurant.overall_rating)}
                </div>
              </div>
            </div>
            <div className="story-content">
              <h3>{restaurant.name}</h3>
              <p className="story-excerpt">
                "{restaurant.story_excerpt || 'Discover their unique story...'}"
              </p>
              <div className="story-footer">
                <p className="cuisines">
                  {restaurant.cuisine_names?.join(', ') || 'Various cuisines'}
                </p>
                <span className="read-story">Read full story →</span>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};

export default RestaurantStories;