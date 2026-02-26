import React, { forwardRef } from 'react';
import RestaurantCard from './RestaurantCard';
import './RestaurantGrid.css';

const RestaurantGrid = forwardRef(({ 
  restaurants = [], 
  onRestaurantClick,
  userLocation, 
  searchQuery 
}, ref) => {

  // Log what we're receiving
  console.log('RestaurantGrid received:', restaurants);
  console.log('Is array?', Array.isArray(restaurants));
  console.log('Length:', restaurants?.length);
  
  // Ensure restaurants is an array
  const restaurantList = React.useMemo(() => {
    // Handle different possible data structures
    if (Array.isArray(restaurants)) {
      return restaurants;
    }
    if (restaurants?.items && Array.isArray(restaurants.items)) {
      return restaurants.items;
    }
    if (restaurants?.results && Array.isArray(restaurants.results)) {
      return restaurants.results;
    }
    if (restaurants?.restaurants && Array.isArray(restaurants.restaurants)) {
      return restaurants.restaurants;
    }
    // If it's an object with numeric keys (rare case)
    if (typeof restaurants === 'object' && restaurants !== null) {
      const possibleArray = Object.values(restaurants);
      if (possibleArray.length > 0 && possibleArray.every(item => typeof item === 'object')) {
        return possibleArray;
      }
    }
    return [];
  }, [restaurants]);

  if (restaurantList.length === 0) {
    return (
      <div className="no-results glass-card">
        <span className="no-results-icon">🔍</span>
        <h3>No restaurants found</h3>
        {searchQuery && <p>No results matching "{searchQuery}"</p>}
        <p>Try adjusting your filters or search criteria</p>
        <div className="no-results-suggestions">
          <button className="suggestion-chip" onClick={() => window.location.reload()}>
            Clear Filters
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="restaurant-grid" ref={ref}>
      {restaurantList.map((restaurant) => (
        <RestaurantCard
          key={restaurant?.restaurant_id || restaurant?.id || `rest-${Math.random()}`}
          restaurant={restaurant}
          onClick={() => onRestaurantClick(restaurant)}
          userLocation={userLocation}
        />
      ))}
    </div>
  );
});

RestaurantGrid.displayName = 'RestaurantGrid';
export default RestaurantGrid;