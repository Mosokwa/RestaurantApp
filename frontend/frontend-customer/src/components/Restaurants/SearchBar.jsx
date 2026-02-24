import React, { useState, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { fetchSuggestions, clearSuggestions, setSearchQuery } from '../../store/slices/explorationSlice';
import './SearchBar.css';

const SearchBar = ({
  value = '',
  onChange,
  onSearch,
  suggestions = [],
  onSelectSuggestion,
  loading = false,
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

  // Check if browser supports speech recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setVoiceSupported(false);
      console.warn('Speech recognition not supported in this browser');
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
        // Automatically search after voice input
        setTimeout(() => {
          if (onSearch) onSearch(transcript);
        }, 100);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
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
        dispatch(fetchSuggestions(value));
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

  // Handle voice search
  const handleVoiceSearch = () => {
    if (!voiceSupported) {
      alert('Voice search is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (error) {
        console.error('Failed to start voice recognition:', error);
        setIsListening(false);
      }
    }
  };

  // Keyboard navigation
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

  // Handle search submit
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
            placeholder="Search for restaurants, cuisines, or dishes..."
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
              title={isListening ? 'Listening...' : 'Voice search'}
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
              key={`${suggestion.type}-${suggestion.id || suggestion.name || index}`}
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
                    {suggestion.cuisine || 'Restaurant'} • ★ {suggestion.rating || 'N/A'}
                  </span>
                )}
                
                {suggestion.type === 'menu_item' && (
                  <span className="suggestion-meta">
                    at {suggestion.restaurant_name || 'Restaurant'}
                  </span>
                )}
                
                {suggestion.type === 'cuisine' && (
                  <span className="suggestion-meta">
                    Cuisine
                  </span>
                )}
              </div>
              
              {suggestion.type === 'restaurant' && (
                <span className="suggestion-badge">
                  Restaurant
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;