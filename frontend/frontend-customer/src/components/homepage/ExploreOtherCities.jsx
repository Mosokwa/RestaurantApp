import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Homepage.css';

const ExploreOtherCities = ({ currentCity }) => {
  const [citiesData, setCitiesData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOtherCities();
  }, [currentCity]);

  const fetchOtherCities = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/explore-cities/';
      if (currentCity) {
        url += `?current_city=${encodeURIComponent(currentCity)}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch other cities');
      
      const data = await response.json();
      setCitiesData(data || []);
    } catch (error) {
      console.error('Error fetching other cities:', error);
      setCitiesData([]);
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

  if (loading && citiesData.length === 0) {
    return (
      <section className="explore-cities">
        <h2>Explore Other Cities</h2>
        <div className="loading">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="city-section skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (citiesData.length === 0) {
    return null;
  }

  return (
    <section className="explore-cities">
      <div className="section-header">
        <h2>Explore Other Cities</h2>
        <span className="section-badge">
          Discover new places
        </span>
      </div>
      
      <div className="cities-container">
        {citiesData.map((cityData) => (
          <div key={cityData.city} className="city-section">
            <div className="city-header">
              <h3>{cityData.city}</h3>
              <span className="city-count">
                {cityData.restaurant_count}+ restaurants
              </span>
            </div>
            
            <div className="city-restaurants">
              {cityData.restaurants.map((restaurant) => (
                <Link 
                  key={restaurant.restaurant_id} 
                  to={`/restaurant/${restaurant.restaurant_id}`}
                  className="restaurant-card city-card"
                >
                  <div className="city-badge">{cityData.city}</div>
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
                    <h4>{restaurant.name}</h4>
                    <p className="cuisines">
                      {restaurant.cuisine_names?.join(', ') || 'Various cuisines'}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default ExploreOtherCities;