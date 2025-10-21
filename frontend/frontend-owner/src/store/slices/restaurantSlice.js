import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { restaurantService } from '../../services/restaurantService';
import { extractDataFromResponse } from '../../utils/paginationUtils';

// Async thunks
export const fetchMyRestaurants = createAsyncThunk(
  'restaurant/fetchMyRestaurants',
  async (_, { rejectWithValue }) => {
    try {
      const response = await restaurantService.getMyRestaurants();
      return extractDataFromResponse(response);
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const createRestaurant = createAsyncThunk(
  'restaurant/createRestaurant',
  async (restaurantData, { rejectWithValue }) => {
    try {
      const response = await restaurantService.createRestaurant(restaurantData);
      return extractDataFromResponse(response);
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const fetchStaff = createAsyncThunk(
  'restaurant/fetchStaff',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await restaurantService.getStaff(restaurantId);
      return extractDataFromResponse(response);
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

export const inviteStaff = createAsyncThunk(
  'restaurant/inviteStaff',
  async (staffData, { rejectWithValue }) => {
    try {
      const response = await restaurantService.createStaff(staffData);
      return extractDataFromResponse(response);
    } catch (error) {
      return rejectWithValue(error.response.data);
    }
  }
);

const restaurantSlice = createSlice({
  name: 'restaurant',
  initialState: {
    restaurants: [],
    currentRestaurant: null,
    staff: [],
    branches: [],
    loading: false,
    error: null
  },
  reducers: {
    setCurrentRestaurant: (state, action) => {
      state.currentRestaurant = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // Fetch My Restaurants
      .addCase(fetchMyRestaurants.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMyRestaurants.fulfilled, (state, action) => {
        state.loading = false;
        state.restaurants = action.payload;
      })
      .addCase(fetchMyRestaurants.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // Create Restaurant
      .addCase(createRestaurant.fulfilled, (state, action) => {
        state.restaurants.push(action.payload);
      })
      // Fetch Staff
      .addCase(fetchStaff.fulfilled, (state, action) => {
        state.staff = action.payload;
      })
      // Invite Staff
      .addCase(inviteStaff.fulfilled, (state, action) => {
        state.staff.push(action.payload);
      });
  }
});

export const { setCurrentRestaurant, clearError } = restaurantSlice.actions;
export default restaurantSlice.reducer;