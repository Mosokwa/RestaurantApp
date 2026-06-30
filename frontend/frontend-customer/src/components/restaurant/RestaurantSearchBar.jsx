// src/pages/restaurant/components/RestaurantSearchBar.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Clock, Utensils, Tag, ArrowRight } from 'lucide-react';
import { debounce } from 'lodash';
import api from '../../services/api';

const RestaurantSearchBar = ({ onSearch, searchQuery, isSearching, restaurantId }) => {
  const [query, setQuery] = useState(searchQuery || '');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [localIsSearching, setLocalIsSearching] = useState(false);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);
  
  const debouncedSearch = useCallback(
    debounce((searchTerm) => {
      if (searchTerm && searchTerm.length >= 2) {
        onSearch(searchTerm);
      } else if (searchTerm === '') {
        onSearch('');
      }
    }, 500),
    [onSearch]
  );
  
  useEffect(() => {
    debouncedSearch(query);
    return () => debouncedSearch.cancel();
  }, [query, debouncedSearch]);
  
  useEffect(() => {
    if (query.length >= 2) {
      fetchSuggestions(query);
    } else {
      setSuggestions([]);
    }
  }, [query]);
  
  const fetchSuggestions = async (searchTerm) => {
    if (!searchTerm || searchTerm.length < 2) return;
    
    setLocalIsSearching(true);
    try {
      const response = await api.get(`/search/suggestions/menu-items/`, {
        params: { restaurant_id: restaurantId, q: searchTerm, limit: 5 }
      });
      setSuggestions(response.data.suggestions || response.data.results || []);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
      setSuggestions([]);
    } finally {
      setLocalIsSearching(false);
    }
  };
  
  const handleSearch = (searchTerm) => {
    setQuery(searchTerm);
    setShowSuggestions(false);
    if (searchTerm && searchTerm.trim().length >= 2) {
      onSearch(searchTerm);
    } else if (!searchTerm || searchTerm.trim() === '') {
      onSearch('');
    }
  };
  
  const handleClear = () => {
    setQuery('');
    onSearch('');
    inputRef.current?.focus();
  };
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (query.length >= 2) {
        handleSearch(query);
      } else if (query.length === 0) {
        onSearch('');
      }
    }
  };
  
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  const getSuggestionIcon = (type) => {
    if (type === 'menu_item') return <Utensils size={14} />;
    if (type === 'offer') return <Tag size={14} />;
    return <Search size={14} />;
  };
  
  const showLoading = (localIsSearching || isSearching) && query.length >= 2;
  
  return (
    <div className="rhp-search-bar">
      <div className="rhp-search-container">
        <div className="rhp-search-input-wrapper">
          <div className="rhp-search-icon">
            <Search size={20} />
          </div>
          
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search menu items or offers..."
            className="rhp-search-input"
          />
          
          {query && (
            <button className="rhp-search-clear-btn" onClick={handleClear} aria-label="Clear search">
              <X size={18} />
            </button>
          )}
        </div>
        
        <AnimatePresence>
          {showSuggestions && query.length >= 2 && (
            <motion.div
              ref={suggestionsRef}
              className="rhp-search-suggestions"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
            >
              {showLoading ? (
                <div className="rhp-no-suggestions">
                  <div className="rhp-loading-spinner-small"></div>
                  <span>Searching...</span>
                </div>
              ) : suggestions.length > 0 ? (
                <>
                  <div className="rhp-suggestions-header">
                    <span>Suggestions</span>
                  </div>
                  {suggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      className="rhp-suggestion-item"
                      onClick={() => handleSearch(suggestion.name || suggestion.query)}
                    >
                      {getSuggestionIcon(suggestion.type)}
                      <div className="rhp-suggestion-content">
                        <span className="rhp-suggestion-name">{suggestion.name || suggestion.query}</span>
                        {suggestion.price && (
                          <span className="rhp-suggestion-price">${suggestion.price}</span>
                        )}
                      </div>
                      <ArrowRight size={14} />
                    </button>
                  ))}
                  <button 
                    className="rhp-suggestion-item rhp-view-all"
                    onClick={() => handleSearch(query)}
                  >
                    <Search size={14} />
                    <span className="rhp-suggestion-name">View all results for "{query}"</span>
                  </button>
                </>
              ) : (
                <div className="rhp-no-suggestions">
                  <span>No items found for "{query}"</span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default RestaurantSearchBar;