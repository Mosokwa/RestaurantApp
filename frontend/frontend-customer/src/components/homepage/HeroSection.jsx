import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { setUserLocation } from '../../store/slices/homepageSlice';
import './Homepage.css';

const HeroSection = () => {
  const dispatch = useDispatch();
  const [searchQuery, setSearchQuery] = useState('');
  const [location, setLocation] = useState('');
  const [isDetecting, setIsDetecting] = useState(false);
  
  const handleLocationDetection = () => {
    if (navigator.geolocation) {
      setIsDetecting(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          // Reverse geocode to get city name (simplified)
          fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`)
            .then(response => response.json())
            .then(data => {
              const city = data.city || data.locality;
              setLocation(city);
              dispatch(setUserLocation({ 
                city, 
                lat: latitude, 
                lng: longitude 
              }));
              setIsDetecting(false);
            })
            .catch(() => {
              setIsDetecting(false);
            });
        },
        (error) => {
          console.error('Error getting location:', error);
          setIsDetecting(false);
        }
      );
    }
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    // Implement search functionality
    console.log('Search for:', searchQuery, 'in', location);
  };
  
  return (
    <div className="hero-section">
      <div className="hero-overlay">
        <div className="hero-content">
          <h1>Discover Amazing Food Around You</h1>
          <p>Order from your favorite restaurants with just a few clicks</p>
          
          <form onSubmit={handleSearch} className="hero-search">
            <div className="location-input">
              <input
                type="text"
                placeholder="Enter your location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
              <button 
                type="button" 
                className="detect-location-btn"
                onClick={handleLocationDetection}
                disabled={isDetecting}
              >
                {isDetecting ? '⏳' : '📍'}
              </button>
            </div>
            
            <div className="search-input">
              <input
                type="text"
                placeholder="Search for restaurants or dishes..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit">Search</button>
            </div>
          </form>
        </div>
      </div>
      
      {/* Floating particles for futuristic effect */}
      <div className="floating-particles">
        {[...Array(15)].map((_, i) => (
          <div 
            key={i} 
            className="particle" 
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${15 + Math.random() * 10}s`
            }}
          ></div>
        ))}
      </div>
    </div>
  );
};

export default HeroSection;