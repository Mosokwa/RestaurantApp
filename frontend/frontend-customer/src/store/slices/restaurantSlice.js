// store/slices/restaurantSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { menuService } from '../../services/menuService';

// Async thunks
export const getCuisines = createAsyncThunk(
  'restaurant/getCuisines',
  async ({ page = 1, pageSize = 100, loadMore = false } = {}, { rejectWithValue, getState }) => {
    try {
      const response = await menuService.getCuisines(page, pageSize);
      console.log('Cuisines API response:', response);
      return { ...response, loadMore };
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

const initialState = {
  currentRestaurant: null,
  currentBranch: null,
  cuisines: {
    items: [],
    pagination: null,
    currentPage: 1,
    hasMore: false,
    loading: false
  },
  menuCategories: [],
  menuItems: [],
  loading: false,
  error: null,
  onboardingStep: 1,
  onboardingComplete: false
};

const restaurantSlice = createSlice({
  name: 'restaurant',
  initialState,
  reducers: {
    setCurrentRestaurant: (state, action) => {
      state.currentRestaurant = action.payload;
    },
    setCurrentBranch: (state, action) => {
      state.currentBranch = action.payload;
    },
    setCuisines: (state, action) => {
      state.cuisines = action.payload;
    },
    clearRestaurantState: (state) => {
      state.currentRestaurant = null;
      state.currentBranch = null;
      state.cuisines = {
        items: [],
        pagination: null,
        currentPage: 1,
        hasMore: false,
        loading: false
      };
      state.menuCategories = [];
      state.menuItems = [];
      state.onboardingStep = 1;
      state.onboardingComplete = false;
      state.error = null;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    loadMoreCuisines: (state, action) => {
      state.cuisines.items = [...state.cuisines.items, ...action.payload.items];
      state.cuisines.pagination = action.payload.pagination;
      state.cuisines.currentPage += 1;
      state.cuisines.hasMore = !!action.payload.pagination?.next;
    }
  },
  extraReducers: (builder) => {
    builder
      // Get Cuisines
      .addCase(getCuisines.pending, (state, action) => {
        if (action.meta.arg.loadMore) {
          state.cuisines.loading = true;
        } else {
          state.cuisines.loading = true;
          state.error = null;
        }
      })
      .addCase(getCuisines.fulfilled, (state, action) => {
        state.cuisines.loading = false;
        
        const { items, pagination, loadMore } = action.payload;
        
        if (loadMore) {
          // Append for infinite scroll
          state.cuisines.items = [...state.cuisines.items, ...items];
          state.cuisines.pagination = pagination;
          state.cuisines.currentPage += 1;
        } else {
          // Replace for initial load
          state.cuisines.items = items;
          state.cuisines.pagination = pagination;
          state.cuisines.currentPage = 1;
        }
        
        state.cuisines.hasMore = !!pagination?.next;
        console.log('Cuisines loaded:', items.length, 'Has more:', state.cuisines.hasMore);
      })
      .addCase(getCuisines.rejected, (state, action) => {
        state.cuisines.loading = false;
        state.error = action.payload;
        if (!action.meta.arg.loadMore) {
          state.cuisines.items = [];
        }
      });
  }
});

export const {
  setCurrentRestaurant,
  setCurrentBranch,
  setCuisines,
  clearRestaurantState,
  setError,
  clearError,
  loadMoreCuisines,
} = restaurantSlice.actions;

export default restaurantSlice.reducer;