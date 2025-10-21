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
    const restaurantsData = extractDataFromResponse(restaurantsResponse);

    return { 
      owner: ownerData,
      restaurants: restaurantsData
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
      state.currentRestaurant = state.restaurants.find(
        r => r.restaurant_id === action.payload
      );
    },
    logoutOwner: (state) => {
      state.owner = null;
      state.restaurants = [];
      state.currentRestaurant = null;
      authService.logout();
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
        state.currentRestaurant = action.payload.restaurants[0] || null;
      })
      .addCase(fetchOwnerProfile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});

export const { switchRestaurant, logoutOwner } = ownerAuthSlice.actions;
export default ownerAuthSlice.reducer;