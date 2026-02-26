import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { explorationService } from '../../services/explorationService';

// Async Thunks
export const searchRestaurants = createAsyncThunk(
  'exploration/searchRestaurants',
  async ({ filters, page = 1, loadMore = false }, { rejectWithValue, getState }) => {
    try {
      const response = await explorationService.searchRestaurants(filters, page);
      return { ...response, loadMore, page };
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchRestaurantSuggestions = createAsyncThunk(
  'exploration/fetchRestaurantSuggestions',
  async (query, { rejectWithValue }) => {
    try {
      console.log('Fetching restaurant suggestions for:', query);
      const suggestions = await explorationService.getRestaurantSuggestions(query);
      console.log('Suggestions received:', suggestions);
      return suggestions;
    } catch (error) {
      console.error('Error in fetchRestaurantSuggestions:', error);
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchLocation = createAsyncThunk(
  'exploration/fetchLocation',
  async (_, { rejectWithValue }) => {
    try {
      const location = await explorationService.getCurrentLocation();
      return location;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchTrendingRestaurants = createAsyncThunk(
  'exploration/fetchTrendingRestaurants',
  async (_, { rejectWithValue }) => {
    try {
      const response = await explorationService.getTrendingRestaurants();
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchPersonalizedRecommendations = createAsyncThunk(
  'exploration/fetchPersonalizedRecommendations',
  async (_, { rejectWithValue }) => {
    try {
      const response = await explorationService.getPersonalizedRecommendations();
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

const initialState = {
  searchQuery: '',
  
  // Filter state
  filters: {
    location: {
      lat: null,
      lng: null,
      radius: 10,
      city: '',
      neighborhood: ''
    },
    cuisines: [],
    priceRanges: [],
    minRating: 0,
    minReviews: 0,
    dietary: [],
    amenities: [],
    occasions: [],
    ambiance: [],
    hours: {
      isOpenNow: false,
      openLate: false,
      specificTime: null
    },
    features: {
      isVerified: false,
      isFeatured: false,
      reservationEnabled: false,
      hasOffers: false,
      deliveryAvailable: false
    },
    sortBy: 'relevance',
    view: 'grid'
  },

  // Search results
  results: {
    restaurants: [],
    totalCount: 0,
    currentPage: 1,
    pageSize: 20,
    hasMore: false,
    loading: false,
    error: null
  },

  // Autocomplete suggestions
  suggestions: {
    items: [],
    loading: false,
    showDropdown: false
  },

  // Dynamic rows data
  dynamicRows: {
    trending: { items: [], loading: false, error: null },
    nearby: { items: [], loading: false, error: null },
    personalized: { items: [], loading: false, error: null },
    newRestaurants: { items: [], loading: false, error: null },
    dietaryPicks: { items: [], loading: false, error: null },
    timeBased: { items: [], loading: false, error: null },
    localFavorites: { items: [], loading: false, error: null }
  },

  // UI state
  ui: {
    activeView: 'grid',
    isFilterPanelOpen: false,
    isMobileFilterOpen: false,
    isMapView: false,
    selectedRestaurant: null,
    showLocationPrompt: false,
    isGettingLocation: false
  },

  // Cached data
  cuisines: {
    items: [],
    loading: false,
    error: null
  },

  userLocation: {
    lat: null,
    lng: null,
    loading: false,
    error: null,
    permissionDenied: false
  }
};

const explorationSlice = createSlice({
  name: 'exploration',
  initialState,
  reducers: {
    setSearchQuery: (state, action) => {
      state.searchQuery = action.payload;
    },
    
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    
    updateFilter: (state, action) => {
      const { key, value, nested } = action.payload;
      if (nested) {
        const [parent, child] = key.split('.');
        state.filters[parent][child] = value;
      } else {
        state.filters[key] = value;
      }
    },
    
    resetFilters: (state) => {
      state.filters = initialState.filters;
    },
    
    clearSuggestions: (state) => {
      state.suggestions.items = [];
      state.suggestions.showDropdown = false;
    },
    
    toggleView: (state, action) => {
      state.ui.activeView = action.payload || (state.ui.activeView === 'grid' ? 'map' : 'grid');
    },
    
    toggleFilterPanel: (state) => {
      state.ui.isFilterPanelOpen = !state.ui.isFilterPanelOpen;
    },
    
    toggleMobileFilter: (state) => {
      state.ui.isMobileFilterOpen = !state.ui.isMobileFilterOpen;
    },
    
    setSelectedRestaurant: (state, action) => {
      state.ui.selectedRestaurant = action.payload;
    },
    
    clearResults: (state) => {
      state.results.restaurants = [];
      state.results.currentPage = 1;
      state.results.hasMore = false;
    },

    clearSuggestions: (state) => {
      state.suggestions.items = [];
      state.suggestions.showDropdown = false;
      state.suggestions.loading = false;
    },
    
    setUserLocation: (state, action) => {
      state.userLocation = { ...state.userLocation, ...action.payload };
      if (action.payload.lat && action.payload.lng) {
        state.filters.location.lat = action.payload.lat;
        state.filters.location.lng = action.payload.lng;
      }
    },
    
    setLocationPermissionDenied: (state) => {
      state.userLocation.permissionDenied = true;
      state.ui.showLocationPrompt = false;
    }
  },
  
  extraReducers: (builder) => {
    builder
      // Search Restaurants
      .addCase(searchRestaurants.pending, (state, action) => {
        if (action.meta.arg.loadMore) {
          state.results.loading = true;
        } else {
          state.results.loading = true;
          state.results.error = null;
        }
      })
      .addCase(searchRestaurants.fulfilled, (state, action) => {
        state.results.loading = false;
        const { items, pagination, loadMore, page } = action.payload;
        
        if (loadMore) {
          state.results.restaurants = [...state.results.restaurants, ...items];
        } else {
          state.results.restaurants = items;
        }
        
        state.results.totalCount = pagination?.count || items.length;
        state.results.currentPage = page || 1;
        state.results.hasMore = !!pagination?.next;
      })
      .addCase(searchRestaurants.rejected, (state, action) => {
        state.results.loading = false;
        state.results.error = action.payload;
      })
      
      // Fetch Restaurant Suggestions
      .addCase(fetchRestaurantSuggestions.pending, (state) => {
        state.suggestions.loading = true;
      })
      .addCase(fetchRestaurantSuggestions.fulfilled, (state, action) => {
        state.suggestions.loading = false;
        state.suggestions.items = action.payload || [];
        state.suggestions.showDropdown = true;
        console.log('Suggestions stored in state:', state.suggestions.items);
      })
      .addCase(fetchRestaurantSuggestions.rejected, (state, action) => {
        state.suggestions.loading = false;
        state.suggestions.items = [];
        state.suggestions.error = action.payload;
      })
      
      // Fetch Location
      .addCase(fetchLocation.pending, (state) => {
        state.userLocation.loading = true;
        state.ui.isGettingLocation = true;
      })
      .addCase(fetchLocation.fulfilled, (state, action) => {
        state.userLocation.loading = false;
        state.userLocation.lat = action.payload.lat;
        state.userLocation.lng = action.payload.lng;
        state.userLocation.error = null;
        state.filters.location.lat = action.payload.lat;
        state.filters.location.lng = action.payload.lng;
        state.ui.isGettingLocation = false;
        state.ui.showLocationPrompt = false;
      })
      .addCase(fetchLocation.rejected, (state, action) => {
        state.userLocation.loading = false;
        state.userLocation.error = action.payload;
        state.ui.isGettingLocation = false;
        state.ui.showLocationPrompt = true;
      })
      
      // Dynamic Rows
      .addCase(fetchTrendingRestaurants.pending, (state) => {
        state.dynamicRows.trending.loading = true;
      })
      .addCase(fetchTrendingRestaurants.fulfilled, (state, action) => {
        state.dynamicRows.trending.loading = false;
        // Handle both direct array and paginated response
        const data = action.payload;
        if (Array.isArray(data)) {
          state.dynamicRows.trending.items = data;
        } else if (data?.items) {
          state.dynamicRows.trending.items = data.items;
        } else if (data?.restaurants) {
          state.dynamicRows.trending.items = data.restaurants;
        } else {
          state.dynamicRows.trending.items = [];
        }
      })
      .addCase(fetchTrendingRestaurants.rejected, (state, action) => {
        state.dynamicRows.trending.loading = false;
        state.dynamicRows.trending.error = action.payload;
      })
      
      .addCase(fetchPersonalizedRecommendations.pending, (state) => {
        state.dynamicRows.personalized.loading = true;
      })
      .addCase(fetchPersonalizedRecommendations.fulfilled, (state, action) => {
        state.dynamicRows.personalized.loading = false;
        const data = action.payload;
        // Handle different response structures
        if (Array.isArray(data)) {
          state.dynamicRows.personalized.items = data;
        } else if (data?.recommendations) {
          state.dynamicRows.personalized.items = data.recommendations;
        } else if (data?.items) {
          state.dynamicRows.personalized.items = data.items;
        } else if (data?.results) {
          state.dynamicRows.personalized.items = data.results;
        } else {
          state.dynamicRows.personalized.items = [];
        }
      })
      .addCase(fetchPersonalizedRecommendations.rejected, (state, action) => {
        state.dynamicRows.personalized.loading = false;
        state.dynamicRows.personalized.error = action.payload;
      });
  }
});

export const {
  setSearchQuery,
  setFilters,
  updateFilter,
  resetFilters,
  clearSuggestions,
  toggleView,
  toggleFilterPanel,
  toggleMobileFilter,
  setSelectedRestaurant,
  clearResults,
  setUserLocation,
  setLocationPermissionDenied
} = explorationSlice.actions;

export default explorationSlice.reducer;