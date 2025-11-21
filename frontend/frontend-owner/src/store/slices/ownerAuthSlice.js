import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../services/authService';
import { extractDataFromResponse } from '../../utils/paginationUtils';


// Helper to get persisted restaurant
const getPersistedRestaurant = () => {
  try {
    const persisted = localStorage.getItem('currentRestaurant');
    return persisted ? JSON.parse(persisted) : null;
  } catch {
    return null;
  }
};

export const fetchOwnerProfile = createAsyncThunk(
  'ownerAuth/fetchProfile',
  async (_, { getState }) => {
    const [ownerResponse, restaurantsResponse] = await Promise.all([
      authService.getCurrentOwner(),
      authService.getOwnerRestaurants()
    ]);

    const ownerData = extractDataFromResponse(ownerResponse);
    const restaurantsData = restaurantsResponse.data;
    const restaurantsArray = restaurantsData?.restaurants || [];

    console.log('🔄 Fetched owner profile with restaurants:', restaurantsArray.length);

    // Get persisted restaurant - but don't auto-select if user wants explicit selection
    const persistedRestaurant = getPersistedRestaurant();
    let currentRestaurant = null;

    // Only auto-select if there's a valid persisted restaurant
    if (persistedRestaurant && restaurantsArray.length > 0) {
      currentRestaurant = restaurantsArray.find(
        r => r.restaurant_id === persistedRestaurant.restaurant_id
      );
      // If persisted restaurant doesn't exist anymore, clear it
      if (!currentRestaurant) {
        localStorage.removeItem('currentRestaurant');
      }
    }

    // Don't auto-select first restaurant - let user choose explicitly
    // This ensures user always goes through restaurant selection first

    return { 
      owner: ownerData,
      restaurants: restaurantsArray,
      currentRestaurant // This will be null on first login
    };
  }
);

const ownerAuthSlice = createSlice({
  name: 'ownerAuth',
  initialState: {
    owner: null,
    restaurants: [],
    currentRestaurant: getPersistedRestaurant(),
    loading: false,
    error: null
  },
  reducers: {
    switchRestaurant: (state, action) => {
      if (action.payload === null) {
        state.currentRestaurant = null;
        localStorage.removeItem('currentRestaurant');
        console.log('✅ Cleared current restaurant');
      } else {
        // Convert to string for comparison to handle both string and number IDs
        const targetId = String(action.payload);
        
        const restaurant = state.restaurants.find(
          r => String(r.restaurant_id) === targetId
        );
        
        if (restaurant) {
          state.currentRestaurant = restaurant;
          // Persist to localStorage
          localStorage.setItem('currentRestaurant', JSON.stringify(restaurant));
          console.log('✅ Restaurant switched to:', restaurant.name, '(ID:', restaurant.restaurant_id, ')');
        } else {
          console.error('❌ Restaurant not found. Looking for:', targetId, 'Available:', 
            state.restaurants.map(r => ({ id: r.restaurant_id, name: r.name }))
          );
        }
      }
    },

    clearCurrentRestaurant: (state) => {
      state.currentRestaurant = null;
      localStorage.removeItem('currentRestaurant');
    },

    setCurrentRestaurant: (state, action) => {
      state.currentRestaurant = action.payload;
      if (action.payload) {
        localStorage.setItem('currentRestaurant', JSON.stringify(action.payload));
      } else {
        localStorage.removeItem('currentRestaurant');
      }
    },

    logoutOwner: (state) => {
      state.owner = null;
      state.restaurants = [];
      state.currentRestaurant = null;
      localStorage.removeItem('currentRestaurant');
      authService.logout();
      if (authService.cancelAllRequests) {
        authService.cancelAllRequests();
      }
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchOwnerProfile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOwnerProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.owner = action.payload.owner;
        state.restaurants = action.payload.restaurants;
        
        // Only update currentRestaurant if we don't already have one persisted
        if (!state.currentRestaurant && action.payload.currentRestaurant) {
          state.currentRestaurant = action.payload.currentRestaurant;
          localStorage.setItem('currentRestaurant', JSON.stringify(action.payload.currentRestaurant));
        }
        
        console.log('✅ Owner profile loaded with restaurants:', action.payload.restaurants.length);
      })
      .addCase(fetchOwnerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
        console.error('❌ Failed to load owner profile:', action.error.message);
      });
  }
});

export const { switchRestaurant, clearCurrentRestaurant, setCurrentRestaurant, logoutOwner } = ownerAuthSlice.actions;
export default ownerAuthSlice.reducer;