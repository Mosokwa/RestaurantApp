// src/store/slices/restaurantHomepageSlice.js

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// ============================================
// Async Thunks
// ============================================

/**
 * Fetch complete restaurant homepage data
 */
export const fetchRestaurantHomepage = createAsyncThunk(
  'restaurantHomepage/fetch',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await api.get(`/routes/restaurant-homepage/${restaurantId}/homepage/`);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Fetch menu items by category
 */
export const fetchMenuItemsByCategory = createAsyncThunk(
  'restaurantHomepage/fetchMenuByCategory',
  async ({ restaurantId, categoryId, page = 1 }, { rejectWithValue }) => {
    try {
      const params = {
        restaurant: restaurantId,
        page,
        page_size: 20
      };
      
      // Only add category filter if provided
      if (categoryId) {
        params.category = categoryId;
      }
      
      const response = await api.get('/menu/items/', { params });
      
      return { 
        categoryId, 
        data: {
          results: response.data.results || response.data,
          next: response.data.next,
          count: response.data.count
        }, 
        page 
      };
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Search menu items within a restaurant - Only called when query has 2+ chars
 */
export const searchRestaurantItems = createAsyncThunk(
  'restaurantHomepage/search',
  async ({ restaurantId, query, page = 1 }, { rejectWithValue }) => {
    // Don't make the API call if query is empty or too short
    if (!query || query.length < 2) {
      return { results: [] };
    }
    
    try {
      const response = await api.get(`/search/menu-items/`, {
        params: { restaurant_id: restaurantId, q: query, page, page_size: 20 }
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

/**
 * Fetch user loyalty points
 */
export const fetchUserLoyalty = createAsyncThunk(
  'restaurantHomepage/fetchLoyalty',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/loyalty/points/');
      return response.data;
    } catch (error) {
      console.warn('Loyalty endpoint not available:', error.message);
      return null;
    }
  }
);

/**
 * Enroll user in loyalty program
 */
export const enrollInLoyalty = createAsyncThunk(
  'restaurantHomepage/enrollLoyalty',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await api.post('/loyalty/enroll/', { restaurant_id: restaurantId });
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// ============================================
// Initial State
// ============================================

const initialState = {
  restaurant: null,
  specialOffers: [],
  menuPreview: {
    featuredCategories: [],
    popularItems: []
  },
  reservationInfo: null,
  reviewsPreview: null,
  loyaltyInfo: null,
  operationalInfo: null,
  
  // Menu state
  currentCategory: null,
  categories: [],
  menuItems: [],
  currentMenuPage: 1,
  hasMoreMenu: false,
  menuLoading: false,
  
  // Search state
  searchQuery: '',
  searchResults: [],
  isSearching: false,
  
  // Loyalty state
  userLoyalty: null,
  loyaltyLoading: false,
  loyaltyEnrolling: false,
  
  // UI state
  loading: false,
  error: null,
  selectedMenuItem: null,
  itemModalOpen: false,
  activeTab: 'menu',
  
  // Real-time updates
  realTimeUpdates: []
};

// ============================================
// Slice
// ============================================

const restaurantHomepageSlice = createSlice({
  name: 'restaurantHomepage',
  initialState,
  reducers: {
    setCurrentCategory: (state, action) => {
      state.currentCategory = action.payload;
      state.menuItems = [];
      state.currentMenuPage = 1;
      // Clear search when changing category
      state.searchQuery = '';
      state.searchResults = [];
      state.isSearching = false;
    },
    
    setSearchQuery: (state, action) => {
      state.searchQuery = action.payload;
      // Clear results if query is empty
      if (!action.payload || action.payload.length < 2) {
        state.isSearching = false;
        state.searchResults = [];
      }
    },
    
    toggleItemModal: (state, action) => {
      state.itemModalOpen = action.payload ?? !state.itemModalOpen;
      if (!state.itemModalOpen) {
        state.selectedMenuItem = null;
      }
    },
    
    setSelectedMenuItem: (state, action) => {
      state.selectedMenuItem = action.payload;
    },
    
    setActiveTab: (state, action) => {
      state.activeTab = action.payload;
    },
    
    updateMenuItemAvailability: (state, action) => {
      const { itemId, isAvailable } = action.payload;
      if (state.menuPreview.popularItems) {
        const item = state.menuPreview.popularItems.find(i => i.item_id === itemId);
        if (item) item.is_available = isAvailable;
      }
      const menuItem = state.menuItems.find(i => i.item_id === itemId);
      if (menuItem) menuItem.is_available = isAvailable;
    },
    
    addRealTimeUpdate: (state, action) => {
      state.realTimeUpdates.unshift({
        ...action.payload,
        timestamp: new Date().toISOString()
      });
      if (state.realTimeUpdates.length > 10) {
        state.realTimeUpdates = state.realTimeUpdates.slice(0, 10);
      }
    },
    
    clearRealTimeUpdates: (state) => {
      state.realTimeUpdates = [];
    },
    
    clearRestaurantHomepage: () => initialState
  },
  
  extraReducers: (builder) => {
    builder
      // Fetch Restaurant Homepage
      .addCase(fetchRestaurantHomepage.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchRestaurantHomepage.fulfilled, (state, action) => {
        state.loading = false;
        state.restaurant = action.payload.restaurant;
        state.specialOffers = action.payload.special_offers || [];
        state.menuPreview = action.payload.menu_preview || { 
          featuredCategories: [], 
          popularItems: [] 
        };
        state.reservationInfo = action.payload.reservation_info;
        state.reviewsPreview = action.payload.reviews_preview;
        state.loyaltyInfo = action.payload.loyalty_info;
        state.operationalInfo = action.payload.operational_info;
        
        if (action.payload.menu_preview?.featured_categories) {
          state.categories = action.payload.menu_preview.featured_categories;
          if (state.categories.length > 0 && !state.currentCategory) {
            state.currentCategory = state.categories[0];
          }
        }
      })
      .addCase(fetchRestaurantHomepage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
      // Fetch Menu Items by Category
      .addCase(fetchMenuItemsByCategory.pending, (state) => {
        state.menuLoading = true;
      })
      .addCase(fetchMenuItemsByCategory.fulfilled, (state, action) => {
        state.menuLoading = false;
        const { categoryId, data, page } = action.payload;
        
        // MenuItemListView returns results directly
        const items = data.results || data.items || [];
        
        console.log('Extracted menu items:', items);
        console.log('First item has item_id?', items[0]?.item_id);
        
        if (page === 1) {
          state.menuItems = items;
        } else {
          state.menuItems = [...state.menuItems, ...items];
        }
        state.hasMoreMenu = !!data.next;
        state.currentMenuPage = page;
      })
      .addCase(fetchMenuItemsByCategory.rejected, (state, action) => {
        state.menuLoading = false;
        console.error('Menu fetch rejected:', action.payload);
      })
      
      // Search Restaurant Items - Only update state when there are results
      .addCase(searchRestaurantItems.pending, (state) => {
        state.isSearching = true;
      })
      .addCase(searchRestaurantItems.fulfilled, (state, action) => {
        state.isSearching = false;
        // Only update search results if we have actual data
        if (action.payload && action.payload.results) {
          state.searchResults = action.payload.results;
        } else if (action.payload && action.payload.items) {
          state.searchResults = action.payload.items;
        } else {
          state.searchResults = [];
        }
      })
      .addCase(searchRestaurantItems.rejected, (state, action) => {
        state.isSearching = false;
        state.searchResults = [];
        // Don't log error for empty searches
        if (action.meta.arg?.query && action.meta.arg.query.length >= 2) {
          console.error('Search rejected:', action.payload);
        }
      })
      
      // Fetch User Loyalty
      .addCase(fetchUserLoyalty.pending, (state) => {
        state.loyaltyLoading = true;
      })
      .addCase(fetchUserLoyalty.fulfilled, (state, action) => {
        state.loyaltyLoading = false;
        if (action.payload && action.payload.current_points !== undefined) {
          state.userLoyalty = action.payload;
        } else {
          state.userLoyalty = null;
        }
      })
      .addCase(fetchUserLoyalty.rejected, (state) => {
        state.loyaltyLoading = false;
        state.userLoyalty = null;
      })
      
      // Enroll in Loyalty
      .addCase(enrollInLoyalty.pending, (state) => {
        state.loyaltyEnrolling = true;
      })
      .addCase(enrollInLoyalty.fulfilled, (state, action) => {
        state.loyaltyEnrolling = false;
        if (action.payload?.loyalty_profile) {
          state.userLoyalty = action.payload.loyalty_profile;
        }
      })
      .addCase(enrollInLoyalty.rejected, (state) => {
        state.loyaltyEnrolling = false;
      });
  }
});

// ============================================
// Actions
// ============================================

export const {
  setCurrentCategory,
  setSearchQuery,
  toggleItemModal,
  setSelectedMenuItem,
  setActiveTab,
  updateMenuItemAvailability,
  addRealTimeUpdate,
  clearRealTimeUpdates,
  clearRestaurantHomepage
} = restaurantHomepageSlice.actions;

// ============================================
// Selectors
// ============================================

export const selectRestaurant = (state) => state.restaurantHomepage.restaurant;
export const selectRestaurantLoading = (state) => state.restaurantHomepage.loading;
export const selectRestaurantError = (state) => state.restaurantHomepage.error;
export const selectCurrentCategory = (state) => state.restaurantHomepage.currentCategory;
export const selectCategories = (state) => state.restaurantHomepage.categories;
export const selectMenuItems = (state) => state.restaurantHomepage.menuItems;
export const selectMenuLoading = (state) => state.restaurantHomepage.menuLoading;
export const selectSpecialOffers = (state) => state.restaurantHomepage.specialOffers;
export const selectReviewsPreview = (state) => state.restaurantHomepage.reviewsPreview;
export const selectLoyaltyInfo = (state) => state.restaurantHomepage.loyaltyInfo;
export const selectUserLoyalty = (state) => state.restaurantHomepage.userLoyalty;
export const selectActiveTab = (state) => state.restaurantHomepage.activeTab;
export const selectItemModalOpen = (state) => state.restaurantHomepage.itemModalOpen;
export const selectSelectedMenuItem = (state) => state.restaurantHomepage.selectedMenuItem;
export const selectSearchQuery = (state) => state.restaurantHomepage.searchQuery;
export const selectSearchResults = (state) => state.restaurantHomepage.searchResults;
export const selectIsSearching = (state) => state.restaurantHomepage.isSearching;
export const selectRealTimeUpdates = (state) => state.restaurantHomepage.realTimeUpdates;

export default restaurantHomepageSlice.reducer;