// pages/SearchResultsPage/components/SearchHeader.jsx
import { useState, useEffect, useRef } from 'react';
import { searchService } from '../../services/searchService';

const SearchHeader = ({ searchQuery, setSearchQuery, onSearch, totalResults }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const searchRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    // Only fetch suggestions if input is focused and we're typing
    const fetchSuggestions = async () => {
      if (searchQuery.length < 2 || document.activeElement !== inputRef.current) {
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

  const handleSuggestionClick = (suggestion) => {
    setSearchQuery(suggestion.name);
    setShowSuggestions(false);
    // Trigger search and remove focus from input
    onSearch({ preventDefault: () => {} });
    inputRef.current?.blur();
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Immediately hide suggestions
      setShowSuggestions(false);
      setSuggestions([]);
      // Remove focus from input
      inputRef.current?.blur();
      // Trigger search
      onSearch(e);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setShowSuggestions(false);
    setSuggestions([]);
    inputRef.current?.focus();
  };

  const handleInputFocus = () => {
    // Only show suggestions if we have them and input has value
    if (searchQuery.length >= 2 && suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className="sr-header" ref={searchRef}>
      <h1 className="sr-header-title">
        {totalResults !== undefined ? (
          <>
            <span className="sr-header-title-highlight">{totalResults}</span> results for "{searchQuery}"
          </>
        ) : (
          'Search'
        )}
      </h1>
      
      <form onSubmit={handleSearchSubmit} className="sr-header-form">
        <div className="sr-search-wrapper">
          <div className="sr-input-container">
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={handleInputFocus}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              placeholder="Search for restaurants, dishes, cuisines..."
              className="sr-search-input"
            />
            {searchQuery && (
              <button 
                type="button"
                className="sr-clear-input"
                onClick={handleClearSearch}
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
            {suggestionLoading && <div className="sr-search-loading"></div>}
          </div>
          <button type="submit" className="sr-search-btn">
            Search
          </button>

          {showSuggestions && suggestions.length > 0 && (
            <div className="sr-suggestions-dropdown">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="sr-suggestion-item"
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  <span className="sr-suggestion-icon">
                    {suggestion.type === 'restaurant' && '🏢'}
                    {suggestion.type === 'menu_item' && '🍽️'}
                    {suggestion.type === 'cuisine' && '🍜'}
                    {suggestion.type === 'category' && '📋'}
                  </span>
                  <div className="sr-suggestion-content">
                    <span className="sr-suggestion-name">{suggestion.name}</span>
                    <span className="sr-suggestion-type">
                      {suggestion.type?.replace('_', ' ')}
                      {suggestion.restaurant_name && ` • ${suggestion.restaurant_name}`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </form>
    </div>
  );
};

export default SearchHeader;