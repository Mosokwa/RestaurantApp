import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../services/authService';
import { extractDataFromResponse } from '../../utils/paginationUtils';

export const fetchOwnerProfile = createAsyncThunk(
  'ownerAuth/fetchProfile',
  async () => {
    const [ownerResponse, restaurantsResponse] = await Promise.all([
      authService.getCurrentOwner(),
      authService.getOwnerRestaurants()
    ]);

    const ownerData = extractDataFromResponse(ownerResponse);
    const restaurantsData = restaurantsResponse.data;
    const restaurantsArray = restaurantsData?.restaurants || [];

    console.log(restaurantsResponse);
    console.log(restaurantsArray);

    return { 
      owner: ownerData,
      restaurants: restaurantsArray
    };
  }
);

const ownerAuthSlice = createSlice({
  name: 'ownerAuth',
  initialState: {
    owner: null,
    restaurants: [],
    currentRestaurant: null,
    loading: false,
    error: null
  },
  reducers: {
    switchRestaurant: (state, action) => {
      if (action.payload === null) {
        // Clear current restaurant
        state.currentRestaurant = null;
      } else {
        // Set specific restaurant
        state.currentRestaurant = state.restaurants.find(
          r => r.restaurant_id === action.payload
        );
      }
    },

    clearCurrentRestaurant: (state) => {
      state.currentRestaurant = null;
    },

    logoutOwner: (state) => {
      state.owner = null;
      state.restaurants = [];
      state.currentRestaurant = null;
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
      })
      .addCase(fetchOwnerProfile.fulfilled, (state, action) => {
        state.loading = false;
        state.owner = action.payload.owner;
        state.restaurants = action.payload.restaurants;
        state.currentRestaurant = null;
      })
      .addCase(fetchOwnerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});

export const { switchRestaurant, clearCurrentRestaurant, logoutOwner } = ownerAuthSlice.actions;
export default ownerAuthSlice.reducer;