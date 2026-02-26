import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchRestaurantSuggestions, clearSuggestions } from '../../store/slices/explorationSlice';
import './SearchBar.css';

const SearchBar = ({
  value = '',
  onChange,
  onSearch,
  onSelectSuggestion,
  onClear
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(true);
  const searchRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const dispatch = useDispatch();

  // Get suggestions from Redux state
  const { items: suggestions = [], loading } = useSelector(
    (state) => state.exploration?.suggestions || { items: [], loading: false }
  );

  // Debug: Log suggestions when they change
  useEffect(() => {
    console.log('SearchBar - suggestions from Redux:', suggestions);
    console.log('Loading state:', loading);
  }, [suggestions, loading]);

  // Check if browser supports speech recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setVoiceSupported(false);
    }
  }, []);

  // Initialize speech recognition
  useEffect(() => {
    if (voiceSupported) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (onChange) {
          onChange({ target: { value: transcript } });
        }
        setTimeout(() => {
          if (onSearch) onSearch(transcript);
        }, 100);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [voiceSupported, onChange, onSearch]);

  // Debounced suggestion fetch
  useEffect(() => {
    const timer = setTimeout(() => {
      if (value && value.length >= 2) {
        console.log('Dispatching fetchRestaurantSuggestions for:', value);
        dispatch(fetchRestaurantSuggestions(value));
      } else {
        dispatch(clearSuggestions());
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [value, dispatch]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsFocused(false);
        dispatch(clearSuggestions());
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [dispatch]);

  const handleVoiceSearch = () => {
    if (!voiceSupported) {
      alert('Voice search is not supported in your browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (error) {
        setIsListening(false);
      }
    }
  };

  const handleKeyDown = (e) => {
    if (!suggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        e.preventDefault();
        onSearch(value);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && suggestions[selectedIndex]) {
          onSelectSuggestion(suggestions[selectedIndex]);
        } else {
          onSearch(value);
        }
        dispatch(clearSuggestions());
        break;
      case 'Escape':
        setIsFocused(false);
        dispatch(clearSuggestions());
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (value && value.trim()) {
      onSearch(value);
      dispatch(clearSuggestions());
      setIsFocused(false);
    }
  };

  // Get icon for suggestion type
  const getSuggestionIcon = (type) => {
    switch (type) {
      case 'restaurant': return '🍽️';
      case 'menu_item': return '🍲';
      case 'cuisine': return '🍜';
      default: return '🔍';
    }
  };

  return (
    <div className="search-container" ref={searchRef}>
      <form onSubmit={handleSearchSubmit} className="search-form">
        <div className={`search-bar glass-card ${isFocused ? 'focused' : ''}`}>
          <button type="submit" className="search-icon-btn" aria-label="Search">
            <span className="search-icon">🔍</span>
          </button>
          
          <input
            ref={inputRef}
            type="text"
            className="search-input"
            placeholder="Search for restaurants by name, cuisine, or dish..."
            value={value}
            onChange={onChange}
            onFocus={() => setIsFocused(true)}
            onKeyDown={handleKeyDown}
            aria-label="Search restaurants"
            autoComplete="off"
          />
          
          {loading && (
            <span className="search-loading">
              <div className="spinner-small" />
            </span>
          )}
          
          {value && !loading && (
            <button 
              type="button" 
              className="clear-btn" 
              onClick={onClear}
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
          
          {voiceSupported && (
            <button 
              type="button" 
              className={`voice-btn ${isListening ? 'listening' : ''}`} 
              onClick={handleVoiceSearch}
              aria-label={isListening ? 'Stop voice search' : 'Start voice search'}
            >
              🎤
            </button>
          )}
        </div>
      </form>

      {/* Suggestions Dropdown */}
      {suggestions && suggestions.length > 0 && isFocused && (
        <div className="suggestions-dropdown glass-card">
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id || index}
              className={`suggestion-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => {
                onSelectSuggestion(suggestion);
                dispatch(clearSuggestions());
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="suggestion-icon">
                {getSuggestionIcon(suggestion.type)}
              </span>
              
              <div className="suggestion-content">
                <span className="suggestion-name">{suggestion.name}</span>
                
                {suggestion.type === 'restaurant' && (
                  <span className="suggestion-meta">
                    {suggestion.cuisine || 'Restaurant'} 
                    {suggestion.rating && ` • ⭐ ${suggestion.rating}`}
                    {suggestion.match_type === 'by_menu_item' && suggestion.menu_item && 
                      ` • Serves "${suggestion.menu_item}"`}
                  </span>
                )}
              </div>
              
              <span className="suggestion-badge">
                {suggestion.match_type === 'direct' ? 'Restaurant' : 
                 suggestion.match_type === 'by_cuisine' ? 'By Cuisine' : 
                 suggestion.match_type === 'by_menu_item' ? 'Has Dish' : 'Restaurant'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;