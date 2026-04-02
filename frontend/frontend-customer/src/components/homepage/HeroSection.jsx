// components/homepage/HeroSection.jsx
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchService } from '../../services/searchService';
import './Homepage.css';

const HeroSection = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchQuery.length < 2) {
        setSuggestions([]);
        return;
      }

      setSuggestionLoading(true);
      try {
        const data = await searchService.getSuggestions(searchQuery);
        setSuggestions(data);
        setShowSuggestions(true);
      } catch (error) {
        console.error('Error fetching suggestions:', error);
      } finally {
        setSuggestionLoading(false);
      }
    };

    const timeoutId = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setSearchQuery(suggestion.name);
    setShowSuggestions(false);
    navigate(`/search?q=${encodeURIComponent(suggestion.name)}`);
  };

  return (
    <div className="hero-section">
      <div className="hero-overlay">
        <div className="hero-content">
          <h1>Discover Amazing Food Around You</h1>
          <p>Search for restaurants, dishes, cuisines and more</p>
          
          <form onSubmit={handleSearch} className="hero-search" ref={searchRef}>
            <div className="search-input-wrapper">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                placeholder="Search for restaurants, dishes, cuisines..."
              />
              {suggestionLoading && <div className="suggestion-loading"></div>}
              <button type="submit">Search</button>
            </div>

            {/* Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="homepage-suggestions">
                {suggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    className="suggestion-item"
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <span className="suggestion-icon">
                      {suggestion.type === 'restaurant' && '🏢'}
                      {suggestion.type === 'menu_item' && '🍽️'}
                      {suggestion.type === 'cuisine' && '🍜'}
                      {suggestion.type === 'category' && '📋'}
                    </span>
                    <div className="suggestion-content">
                      <span className="suggestion-name">{suggestion.name}</span>
                      <span className="suggestion-type">
                        {suggestion.type?.replace('_', ' ')}
                        {suggestion.restaurant_name && ` • ${suggestion.restaurant_name}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </form>
        </div>
      </div>
      
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