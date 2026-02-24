import React, { useEffect, useState, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useSearchParams } from 'react-router-dom';
import {
  searchRestaurants,
  fetchSuggestions,
  clearSuggestions,
  setSearchQuery,
  updateFilter,
  resetFilters,
  toggleView,
  fetchLocation,
  fetchTrendingRestaurants,
  fetchPersonalizedRecommendations,
  setSelectedRestaurant,
  setLocationPermissionDenied,
  setUserLocation,
  toggleMobileFilter
} from '../store/slices/explorationSlice';
import { explorationService } from '../services/explorationService';
import SearchBar from '../components/Restaurants/SearchBar';
import QuickFilters from '../components/Restaurants/QuickFilters';
import FilterPanelInline from '../components/Restaurants/FilterPanelInline'; // New inline version
import RestaurantGrid from '../components/Restaurants/RestaurantGrid';
import DynamicRow from '../components/Restaurants/DynamicRow';
import MobileFilterDrawer from '../components/Restaurants/MobileFilterDrawer';
import LocationPrompt from '../components/Restaurants/LocationPrompt';
import LoadingSkeleton from '../components/Restaurants/LoadingSkeleton';
import { useMobileDetect } from '../hooks/useMobileDetect';
import './styles/RestaurantExplorer.css';

const RestaurantExplorer = () => {
  const dispatch = useDispatch();
  const [searchParams] = useSearchParams();
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isFilterCollapsed, setIsFilterCollapsed] = useState(true);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const observerRef = useRef();
  
  // Use mobile detection
  const { isMobile, isTablet } = useMobileDetect();

  // Check for filter params from homepage
  useEffect(() => {
    const filterType = searchParams.get('filter');
    const value = searchParams.get('value');
    
    if (filterType && !initialLoadDone) {
      console.log('Applying filter from URL:', filterType, value);
      
      switch (filterType) {
        case 'recommended':
          dispatch(updateFilter({ key: 'sortBy', value: 'recommended' }));
          break;
        case 'popular':
          dispatch(updateFilter({ key: 'popular', value: true }));
          break;
        case 'fast_delivery':
          dispatch(updateFilter({ key: 'features.fastDelivery', value: true, nested: true }));
          break;
        case 'time_based':
          dispatch(updateFilter({ key: 'timeBased', value: true }));
          break;
        case 'near_you':
          dispatch(fetchLocation());
          dispatch(updateFilter({ key: 'nearMeActive', value: true }));
          break;
        default:
          break;
      }
    }
  }, [searchParams, dispatch, initialLoadDone]);

  // Redux state with safe defaults
  const {
    searchQuery = '',
    filters = {
      location: { lat: null, lng: null, radius: 10, city: '', neighborhood: '' },
      cuisines: [],
      priceRanges: [],
      minRating: 0,
      minReviews: 0,
      dietary: [],
      amenities: [],
      occasions: [],
      ambiance: [],
      hours: { isOpenNow: false, openLate: false, specificTime: null },
      features: { 
        isVerified: false, 
        isFeatured: false, 
        reservationEnabled: false, 
        hasOffers: false, 
        deliveryAvailable: false,
        fastDelivery: false 
      },
      sortBy: 'relevance',
      view: 'grid',
      nearMeActive: false,
      popular: false,
      timeBased: false
    },
    results = { restaurants: [], totalCount: 0, currentPage: 1, loading: false, hasMore: false, error: null },
    suggestions = { items: [], loading: false, showDropdown: false },
    ui = { activeView: 'grid', isFilterPanelOpen: false, isMobileFilterOpen: false, showLocationPrompt: false, isGettingLocation: false, selectedRestaurant: null },
    userLocation = { lat: null, lng: null, loading: false, error: null, permissionDenied: false },
    dynamicRows = { 
      trending: { items: [], loading: false, error: null },
      nearby: { items: [], loading: false, error: null },
      personalized: { items: [], loading: false, error: null },
      newRestaurants: { items: [], loading: false, error: null }
    }
  } = useSelector(state => state.exploration || {});

  const { isAuthenticated = false } = useSelector(state => state.auth || {});

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      // Don't auto-fetch location - let user toggle it
      dispatch(searchRestaurants({ filters, page: 1 }));
      dispatch(fetchTrendingRestaurants());
      
      if (isAuthenticated) {
        dispatch(fetchPersonalizedRecommendations());
      }
      
      setInitialLoadDone(true);
    };
    
    loadInitialData();
  }, [dispatch, isAuthenticated]);

  // Trigger search when filters change
  useEffect(() => {
    if (!initialLoadDone) return;
    
    const timer = setTimeout(() => {
      dispatch(searchRestaurants({ filters, page: 1 }));
    }, 500);

    return () => clearTimeout(timer);
  }, [filters, dispatch, initialLoadDone]);

  // Infinite scroll
  useEffect(() => {
    if (results.loading || !results.hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && results.hasMore && !results.loading) {
          setIsLoadingMore(true);
          dispatch(searchRestaurants({
            filters,
            page: (results.currentPage || 1) + 1,
            loadMore: true
          })).finally(() => setIsLoadingMore(false));
        }
      },
      { threshold: 0.5, rootMargin: '100px' }
    );

    if (observerRef.current) {
      observer.observe(observerRef.current);
    }

    return () => observer.disconnect();
  }, [results.hasMore, results.loading, results.currentPage, filters, dispatch]);

  // Handle search
  const handleSearch = (query) => {
    if (!query || !query.trim()) return;
    
    console.log('🔍 Searching for:', query);
    
    // Update search query in state
    dispatch(setSearchQuery(query));
    
    // Create updated filters with search query
    const updatedFilters = {
      ...filters,
      searchQuery: query
    };
    
    // Update filter in Redux
    dispatch(updateFilter({ key: 'searchQuery', value: query }));
    
    // Clear suggestions
    dispatch(clearSuggestions());
    
    // Trigger search immediately
    dispatch(searchRestaurants({ 
      filters: updatedFilters, 
      page: 1 
    })).then((result) => {
      console.log('📥 Search result:', result);
      if (result.payload?.items?.length === 0) {
        console.log('No results found for:', query);
      }
    });
  };

  // Handle input change
  const handleSearchChange = (e) => {
    const value = e.target.value;
    dispatch(setSearchQuery(value));
    // Don't trigger search on every keystroke
  };

  // Handle suggestion select
  const handleSuggestionSelect = (suggestion) => {
    dispatch(clearSuggestions());
    
    if (suggestion.type === 'restaurant') {
      // Navigate to restaurant detail
      window.location.href = `/restaurants/${suggestion.id}`;
    } else if (suggestion.type === 'cuisine') {
      // Filter by cuisine
      const updatedFilters = {
        ...filters,
        cuisines: [suggestion.id],
        searchQuery: suggestion.name
      };
      
      dispatch(updateFilter({ key: 'cuisines', value: [suggestion.id] }));
      dispatch(setSearchQuery(suggestion.name));
      dispatch(updateFilter({ key: 'searchQuery', value: suggestion.name }));
      dispatch(searchRestaurants({ filters: updatedFilters, page: 1 }));
    } else if (suggestion.type === 'menu_item') {
      // Search for menu item
      dispatch(setSearchQuery(suggestion.name));
      dispatch(updateFilter({ key: 'searchQuery', value: suggestion.name }));
      dispatch(searchRestaurants({ 
        filters: { ...filters, searchQuery: suggestion.name }, 
        page: 1 
      }));
    }
  };


  // Handle quick filter click
  const handleQuickFilter = (filterType) => {
    switch (filterType) {
      case 'near_me':
        // Toggle near me
        const newNearMeState = !filters.nearMeActive;
        dispatch(updateFilter({ key: 'nearMeActive', value: newNearMeState }));
        
        if (newNearMeState && !userLocation.lat) {
          dispatch(fetchLocation());
        }
        break;
        
      case 'high_rating':
        // Toggle high rating
        const newRating = filters.minRating >= 4.5 ? 0 : 4.5;
        dispatch(updateFilter({ key: 'minRating', value: newRating }));
        break;
        
      case 'open_now':
        // Toggle open now
        dispatch(updateFilter({ 
          key: 'hours.isOpenNow', 
          value: !filters.hours?.isOpenNow, 
          nested: true 
        }));
        break;
        
      case 'fast_delivery':
        // Toggle fast delivery
        dispatch(updateFilter({ 
          key: 'features.fastDelivery', 
          value: !filters.features?.fastDelivery, 
          nested: true 
        }));
        break;
        
      case 'popular':
        // Toggle popular
        const newPopular = !filters.popular;
        dispatch(updateFilter({ key: 'popular', value: newPopular }));
        if (newPopular) {
          dispatch(updateFilter({ key: 'sortBy', value: 'rating' }));
        }
        break;
        
      case 'time_based':
        // Toggle time-based
        const newTimeBased = !filters.timeBased;
        dispatch(updateFilter({ key: 'timeBased', value: newTimeBased }));
        if (newTimeBased) {
          // Get current time period
          const hour = new Date().getHours();
          let period = 'lunch';
          if (hour < 11) period = 'breakfast';
          else if (hour < 16) period = 'lunch';
          else if (hour < 22) period = 'dinner';
          else period = 'late_night';
          
          dispatch(updateFilter({ key: 'timePeriod', value: period }));
        }
        break;
        
      default:
        break;
    }
  };

  // Handle restaurant card click
  const handleRestaurantClick = (restaurant) => {
    dispatch(setSelectedRestaurant(restaurant));
    if (isAuthenticated) {
      explorationService.trackInteraction('restaurant_click', restaurant?.restaurant_id, {
        restaurant_name: restaurant?.name
      }).catch(() => {});
    }
  };

  // Handle view all from homepage
  const handleViewAll = (type) => {
    // This will redirect to this page with the appropriate filter
    window.location.href = `/restaurants?filter=${type}`;
  };

  // Toggle filter panel
  const toggleFilterPanel = () => {
    setIsFilterCollapsed(!isFilterCollapsed);
  };

  return (
    <div className="restaurant-explorer">
      <LocationPrompt 
        isOpen={ui.showLocationPrompt && !userLocation.permissionDenied && filters.nearMeActive}
        onRequestLocation={() => dispatch(fetchLocation())}
        onDismiss={() => dispatch(setLocationPermissionDenied())}
      />

      <div className="explorer-hero">
        <h1 className="explorer-title">
          Discover <span className="gradient-text">Amazing Restaurants</span>
        </h1>
        <p className="explorer-subtitle">
          Find the perfect dining experience with our smart filters
        </p>
        
        <SearchBar
          value={searchQuery}
          onChange={handleSearchChange}
          onSearch={handleSearch}
          suggestions={suggestions?.items || []}
          onSelectSuggestion={handleSuggestionSelect}
          loading={suggestions?.loading || false}
          onClear={() => {
            dispatch(setSearchQuery(''));
            dispatch(updateFilter({ key: 'searchQuery', value: '' }));
            // Refresh without search query
            const { searchQuery, ...filtersWithoutSearch } = filters;
            dispatch(searchRestaurants({ filters: filtersWithoutSearch, page: 1 }));
          }}
        />
      </div>

      <QuickFilters
        onFilterClick={handleQuickFilter}
        userLocation={userLocation}
        activeFilters={{
          minRating: filters.minRating,
          hours: filters.hours,
          dietary: filters.dietary,
          nearMeActive: filters.nearMeActive,
          popular: filters.popular,
          fastDelivery: filters.features?.fastDelivery,
          timeBased: filters.timeBased
        }}
      />

      <div className="explorer-main">
        <div className="filter-toggle-bar">
          <button 
            className={`filter-toggle-btn ${!isFilterCollapsed ? 'active' : ''}`}
            onClick={toggleFilterPanel}
            aria-expanded={!isFilterCollapsed}
          >
            <span className="filter-icon">⚙️</span>
            <span>Filters</span>
            <span className="filter-arrow">{isFilterCollapsed ? '▼' : '▲'}</span>
          </button>
          
          <div className="active-filters-summary">
            {filters.searchQuery && (
              <span className="active-filter-chip">
                🔍 "{filters.searchQuery}"
                <button 
                  className="remove-filter" 
                  onClick={() => {
                    dispatch(setSearchQuery(''));
                    dispatch(updateFilter({ key: 'searchQuery', value: '' }));
                  }}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.nearMeActive && (
              <span className="active-filter-chip">
                📍 Near Me
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'nearMeActive', value: false }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.minRating >= 4.5 && (
              <span className="active-filter-chip">
                ⭐ 4.5+
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'minRating', value: 0 }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.hours?.isOpenNow && (
              <span className="active-filter-chip">
                🕒 Open Now
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'hours.isOpenNow', value: false, nested: true }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.features?.fastDelivery && (
              <span className="active-filter-chip">
                🚀 Fast Delivery
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'features.fastDelivery', value: false, nested: true }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.popular && (
              <span className="active-filter-chip">
                🔥 Popular
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'popular', value: false }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.timeBased && (
              <span className="active-filter-chip">
                🕒 Perfect for Now
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'timeBased', value: false }))}
                >
                  ✕
                </button>
              </span>
            )}
            {filters.cuisines?.length > 0 && (
              <span className="active-filter-chip">
                {filters.cuisines.length} cuisine{filters.cuisines.length > 1 ? 's' : ''}
                <button 
                  className="remove-filter" 
                  onClick={() => dispatch(updateFilter({ key: 'cuisines', value: [] }))}
                >
                  ✕
                </button>
              </span>
            )}
            
            {(filters.searchQuery || 
              filters.nearMeActive || 
              filters.minRating > 0 || 
              filters.hours?.isOpenNow ||
              filters.features?.fastDelivery ||
              filters.popular ||
              filters.timeBased ||
              filters.cuisines?.length > 0) && (
              <button className="clear-filters-btn" onClick={() => dispatch(resetFilters())}>
                Clear All
              </button>
            )}
          </div>
        </div>

        {!isFilterCollapsed && !isMobile && (
          <FilterPanelInline
            filters={filters}
            onFilterChange={(key, value, nested) => 
              dispatch(updateFilter({ key, value, nested }))
            }
            onReset={() => dispatch(resetFilters())}
            onClose={() => setIsFilterCollapsed(true)}
          />
        )}

        <div className="results-header">
          <div className="results-count">
            <h2>
              {results.totalCount || 0} restaurant{results.totalCount !== 1 ? 's' : ''} found
              {filters.timeBased && (
                <span className="time-badge">
                  {new Date().getHours() < 11 ? '☕ Breakfast' : 
                   new Date().getHours() < 16 ? '🥗 Lunch' : 
                   new Date().getHours() < 22 ? '🍽️ Dinner' : '🌙 Late Night'}
                </span>
              )}
            </h2>
          </div>
          
          <div className="results-controls">
            <select 
              className="sort-select"
              value={filters.sortBy || 'relevance'}
              onChange={(e) => dispatch(updateFilter({ 
                key: 'sortBy', 
                value: e.target.value 
              }))}
              aria-label="Sort restaurants by"
            >
              <option value="relevance">Relevance</option>
              <option value="distance">Distance</option>
              <option value="rating">Highest Rated</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
              <option value="delivery_time">Delivery Time</option>
            </select>

            {!isMobile && (
              <div className="view-toggle">
                <button 
                  className={`view-btn ${ui.activeView === 'grid' ? 'active' : ''}`}
                  onClick={() => dispatch(toggleView('grid'))}
                  aria-label="Grid view"
                >
                  🔲
                </button>
                <button 
                  className={`view-btn ${ui.activeView === 'map' ? 'active' : ''}`}
                  onClick={() => dispatch(toggleView('map'))}
                  aria-label="Map view"
                >
                  📍
                </button>
              </div>
            )}
          </div>
        </div>

        {results.loading && (!results.restaurants || results.restaurants.length === 0) ? (
          <LoadingSkeleton />
        ) : (
          <>
            <RestaurantGrid
              restaurants={results.restaurants || []}
              onRestaurantClick={handleRestaurantClick}
              userLocation={userLocation}
            />

            {results.hasMore && (
              <div ref={observerRef} className="load-more-trigger">
                {isLoadingMore && (
                  <div className="loading-more">
                    <div className="spinner" />
                    <span>Loading more restaurants...</span>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {!isMobile && (
        <div className="dynamic-rows-container">
          <DynamicRow
            title="🔥 Trending Now"
            restaurants={dynamicRows?.trending?.items || []}
            loading={dynamicRows?.trending?.loading || false}
            onRestaurantClick={handleRestaurantClick}
            viewAllLink="/restaurants?filter=popular"
            type="trending"
            onViewAll={() => handleViewAll('popular')}
          />

          {userLocation.lat && filters.nearMeActive && (
            <DynamicRow
              title="📍 Near You"
              restaurants={dynamicRows?.nearby?.items || []}
              loading={dynamicRows?.nearby?.loading || false}
              onRestaurantClick={handleRestaurantClick}
              viewAllLink="/restaurants?filter=near_you"
              type="nearby"
              onViewAll={() => handleViewAll('near_you')}
            />
          )}

          {isAuthenticated && dynamicRows?.personalized?.items?.length > 0 && (
            <DynamicRow
              title="✨ Recommended for You"
              restaurants={dynamicRows.personalized.items}
              loading={dynamicRows.personalized.loading || false}
              onRestaurantClick={handleRestaurantClick}
              viewAllLink="/restaurants?filter=recommended"
              type="personalized"
              onViewAll={() => handleViewAll('recommended')}
            />
          )}
        </div>
      )}

      <MobileFilterDrawer
        isOpen={ui.isMobileFilterOpen || false}
        onClose={() => dispatch(toggleMobileFilter())}
        filters={filters}
        onFilterChange={(key, value, nested) => 
          dispatch(updateFilter({ key, value, nested }))
        }
        onReset={() => dispatch(resetFilters())}
        onApply={() => {
          dispatch(toggleMobileFilter());
          dispatch(searchRestaurants({ filters, page: 1 }));
        }}
      />
    </div>
  );
};

export default RestaurantExplorer;