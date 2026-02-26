import api, { parsePaginatedResponse, buildPaginationParams } from './api';

export const explorationService = {
  // Comprehensive search with all filters
  searchRestaurants: async (filters, page = 1) => {
    try {
      const params = {
        page: page,
        page_size: 20,
        q: filters.searchQuery,
        lat: filters.location?.lat,
        lng: filters.location?.lng,
        radius: filters.location?.radius || 10,
        min_rating: filters.minRating || undefined,
        sort_by: filters.sortBy !== 'relevance' ? filters.sortBy : undefined,
        is_open_now: filters.hours?.isOpenNow || undefined,
      };

      // Remove undefined values
      Object.keys(params).forEach(key => {
        if (params[key] === undefined || params[key] === null || params[key] === '') {
          delete params[key];
        }
      });

      console.log('Search params:', params);

      const response = await api.get('/search/comprehensive/', { params });
      return parsePaginatedResponse(response);
    } catch (error) {
      console.error('Search failed:', error);
      throw error;
    }
  },

  // Get search suggestions for autocomplete
  getRestaurantSuggestions: async (query) => {
    if (!query || query.length < 2) return [];
    try {
      console.log('Calling restaurant suggestions API for:', query);
      const params = new URLSearchParams();
      params.append('q', query);
      params.append('limit', '8');
      
      const response = await api.get('/search/suggestions/restaurants/', { params });
      console.log('Restaurant suggestions response:', response.data);
      return response.data.suggestions || [];
    } catch (error) {
      console.error('Error fetching restaurant suggestions:', error);
      return [];
    }
  },


  // Get menu item suggestions (for menu explorer)
  getMenuItemSuggestions: async (query) => {
    if (!query || query.length < 2) return [];
    try {
      const params = new URLSearchParams();
      params.append('q', query);
      params.append('limit', '8');
      
      const response = await api.get('/search/suggestions/menu-items/', { params });
      return response.data.suggestions || [];
    } catch (error) {
      console.error('Error fetching menu item suggestions:', error);
      return [];
    }
  },

  // Get combined suggestions (for global search)
  getCombinedSuggestions: async (query) => {
    if (!query || query.length < 2) return [];
    try {
      const params = new URLSearchParams();
      params.append('q', query);
      params.append('limit', '8');
      
      const response = await api.get('/search/suggestions/combined/', { params });
      return response.data.suggestions || [];
    } catch (error) {
      console.error('Error fetching combined suggestions:', error);
      return [];
    }
  },

  // Get nearby restaurants based on user location
  getNearbyRestaurants: async (lat, lng, radius = 5) => {
    const response = await api.get('/restaurants/enhanced/', {
      params: { lat, lng, radius }
    });
    return parsePaginatedResponse(response);
  },

  // Get trending restaurants
  getTrendingRestaurants: async () => {
    const response = await api.get('/homepage/trending-today/');
    // Handle different response structures
    if (response.data?.results) {
      return response.data.results;
    }
    if (response.data?.restaurants) {
      return response.data.restaurants;
    }
    return response.data; // Assume it's already an array
  },

  // Get personalized recommendations
  getPersonalizedRecommendations: async () => {
    const response = await api.get('/recommendations/personalized/');
    // Handle different response structures
    if (response.data?.recommendations) {
      return response.data.recommendations;
    }
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get time-based recommendations (breakfast, lunch, dinner)
  getTimeBasedRecommendations: async () => {
    const response = await api.get('/homepage/time-based-recommendations/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get new restaurants
  getNewRestaurants: async () => {
    const response = await api.get('/homepage/new-restaurants/');
    if (response.data?.results) {
      return response.data.results;
    }
    if (response.data?.restaurants) {
      return response.data.restaurants;
    }
    return response.data;
  },

  // Get dietary picks (vegetarian, vegan, gluten-free)
  getDietaryPicks: async (dietType = 'vegetarian') => {
    const response = await api.get('/homepage/dietary-picks/');
    if (response.data?.results) {
      return response.data.results;
    }
    if (response.data?.restaurants) {
      return response.data.restaurants;
    }
    return response.data;
  },

  // Get local favorites
  getLocalFavorites: async () => {
    const response = await api.get('/homepage/local-favorites/');
    if (response.data?.results) {
      return response.data.results;
    }
    if (response.data?.restaurants) {
      return response.data.restaurants;
    }
    return response.data;
  },

  // Get all cuisines (with pagination)
  getCuisines: async (page = 1, pageSize = 100) => {
    const params = buildPaginationParams(page, pageSize);
    const response = await api.get('/cuisines/', { params });
    return parsePaginatedResponse(response);
  },

  // Get popular cuisines for quick filters
  getPopularCuisines: async (limit = 5) => {
    const response = await api.get('/cuisines/', { 
      params: { page_size: limit, popular: true } 
    });
    const parsed = parsePaginatedResponse(response);
    return parsed.items; // Return just the array
  },

  // Get restaurant by ID
  getRestaurantById: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}/`);
    return response.data;
  },

  // Get branches for a restaurant
  getRestaurantBranches: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}/branches/`);
    return response.data;
  },

  // Check if restaurant is open now
  checkRestaurantOpen: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}/availability/`);
    return response.data;
  },

  // Track user behavior for personalization
  trackInteraction: async (eventType, restaurantId = null, metadata = {}) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.log('Skipping tracking - user not authenticated');
        return null;
      }

      const payload = {
        event_type: eventType,
        restaurant_id: restaurantId,
        metadata: {
          ...metadata,
          source: 'restaurant_explorer',
          timestamp: new Date().toISOString()
        }
      };
      
      const response = await api.post('/user/track-behavior/', payload);
      return response.data;
    } catch (error) {
      console.warn('Failed to track interaction:', error.response?.data || error.message);
      return null;
    }
  },

  // Get user's current location
  getCurrentLocation: () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  },

  // Save location to cache
  saveLocationToCache: (location) => {
    try {
      localStorage.setItem('user_location', JSON.stringify({
        location,
        timestamp: Date.now()
      }));
    } catch (error) {
      console.warn('Failed to cache location:', error);
    }
  },

  // Get cached location
  getCachedLocation: () => {
    try {
      const cached = localStorage.getItem('user_location');
      if (!cached) return null;
      
      const { location, timestamp } = JSON.parse(cached);
      // Cache expires after 5 minutes
      if (Date.now() - timestamp > 300000) {
        localStorage.removeItem('user_location');
        return null;
      }
      
      return location;
    } catch {
      return null;
    }
  },

  // Get restaurants you might like (based on similar users)
  getRestaurantsYouMightLike: async () => {
    const response = await api.get('/homepage/restaurants-you-might-like/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get fast delivery restaurants
  getFastDeliveryRestaurants: async () => {
    const response = await api.get('/homepage/fast-delivery/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get price range filtered restaurants
  getPriceRangeFilter: async (priceRange) => {
    const response = await api.get('/homepage/price-ranges/', {
      params: { price_range: priceRange }
    });
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get explore other cities suggestions
  getExploreOtherCities: async () => {
    const response = await api.get('/homepage/explore-cities/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get restaurant stories/features
  getRestaurantStories: async () => {
    const response = await api.get('/homepage/restaurant-stories/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get user favorites
  getUserFavorites: async () => {
    const response = await api.get('/homepage/user-favorites/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get recently viewed restaurants
  getRecentlyViewed: async () => {
    const response = await api.get('/homepage/recently-viewed/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  },

  // Get quick categories for homepage
  getQuickCategories: async () => {
    const response = await api.get('/homepage/quick-categories/');
    if (response.data?.results) {
      return response.data.results;
    }
    return response.data;
  }
};