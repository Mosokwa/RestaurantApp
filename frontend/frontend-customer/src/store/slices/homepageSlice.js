// store/slices/homepageSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api, { parsePaginatedResponse, buildPaginationParams } from '../../services/api';

// Async thunks for fetching homepage data with pagination
export const fetchPopularRestaurants = createAsyncThunk(
    'homepage/fetchPopularRestaurants',
    async ({ location = null, page = 1, pageSize = 12 } = {}) => {
        let params = buildPaginationParams(page, pageSize);
        
        if (location) {
            params = { ...params, city: location.city };
            if (location.lat && location.lng) {
                params.lat = location.lat;
                params.lng = location.lng;
            }
        }

        console.log(params);
        
        const response = await api.get('/homepage/popular-restaurants/', { params });
        console.log(response.data);
        return parsePaginatedResponse(response);
    }
);

export const fetchTrendingDishes = createAsyncThunk(
    'homepage/fetchTrendingDishes',
    async ({ location = null, page = 1, pageSize = 12 } = {}) => {
        let params = buildPaginationParams(page, pageSize);
        console.log(params)
        if (location) {
            params.city = location.city;
        }
        
        const response = await api.get('/homepage/trending-dishes/', { params });
        return parsePaginatedResponse(response);
    }
);

export const fetchPersonalizedRecommendations = createAsyncThunk(
    'homepage/fetchPersonalizedRecommendations',
    async ({ page = 1, pageSize = 6 } = {}) => {
        const params = buildPaginationParams(page, pageSize);
        const response = await api.get('/homepage/personalized-recommendations/', { params });
        return parsePaginatedResponse(response);
    }
);

export const fetchSpecialOffers = createAsyncThunk(
    'homepage/fetchSpecialOffers',
    async ({ location = null, page = 1, pageSize = 6 } = {}) => {
        let params = buildPaginationParams(page, pageSize);
        
        if (location) {
            params.city = location.city;
        }
        
        const response = await api.get('/homepage/special-offers/', { params });
        return parsePaginatedResponse(response);
    }
);

// Homepage slice with pagination state
const homepageSlice = createSlice({
    name: 'homepage',
    initialState: {
        popularRestaurants: {
            items: [],
            pagination: null,
            currentPage: 1
        },
        trendingDishes: {
            items: [],
            pagination: null,
            currentPage: 1
        },
        personalizedRecommendations: {
            items: [],
            pagination: null,
            currentPage: 1
        },
        specialOffers: {
            items: [],
            pagination: null,
            currentPage: 1
        },
        userLocation: null,
        isLoading: false,
        error: null
    },
    reducers: {
        setUserLocation: (state, action) => {
            state.userLocation = action.payload;
        },
        clearHomepageData: (state) => {
            state.popularRestaurants = { items: [], pagination: null, currentPage: 1 };
            state.trendingDishes = { items: [], pagination: null, currentPage: 1 };
            state.personalizedRecommendations = { items: [], pagination: null, currentPage: 1 };
            state.specialOffers = { items: [], pagination: null, currentPage: 1 };
        },
        setPopularRestaurantsPage: (state, action) => {
            state.popularRestaurants.currentPage = action.payload;
        },
        loadMorePopularRestaurants: (state, action) => {
            state.popularRestaurants.items = [
                ...state.popularRestaurants.items,
                ...action.payload.items
            ];
            state.popularRestaurants.pagination = action.payload.pagination;
            state.popularRestaurants.currentPage += 1;
        },
        loadMorePopularRestaurants: (state, action) => {
            state.popularRestaurants.items = [
                ...state.popularRestaurants.items,
                ...action.payload.items
            ];
            state.popularRestaurants.pagination = action.payload.pagination;
            state.popularRestaurants.currentPage += 1;
        },
        loadMoreTrendingDishes: (state, action) => {
        state.trendingDishes.items = [
            ...state.trendingDishes.items,
            ...action.payload.items
        ];
        state.trendingDishes.pagination = action.payload.pagination;
        state.trendingDishes.currentPage += 1;
        },
        loadMoreSpecialOffers: (state, action) => {
        state.specialOffers.items = [
            ...state.specialOffers.items,
            ...action.payload.items
        ];
        state.specialOffers.pagination = action.payload.pagination;
        state.specialOffers.currentPage += 1;
        }
    },
    extraReducers: (builder) => {
        builder
            // Popular restaurants
            .addCase(fetchPopularRestaurants.pending, (state) => {
                state.isLoading = true;
            })
            .addCase(fetchPopularRestaurants.fulfilled, (state, action) => {
                state.isLoading = false;
                state.popularRestaurants.items = action.payload.items;
                state.popularRestaurants.pagination = action.payload.pagination;
                state.popularRestaurants.currentPage = 1;
            })
            .addCase(fetchPopularRestaurants.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.error.message;
            })
            // Trending dishes
            .addCase(fetchTrendingDishes.pending, (state) => {
                state.isLoading = true;
            })
            .addCase(fetchTrendingDishes.fulfilled, (state, action) => {
                state.isLoading = false;
                state.trendingDishes.items = action.payload.items;
                state.trendingDishes.pagination = action.payload.pagination;
                state.trendingDishes.currentPage = 1;
            })
            .addCase(fetchTrendingDishes.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.error.message;
            })
            // Personalized recommendations
            .addCase(fetchPersonalizedRecommendations.pending, (state) => {
                state.isLoading = true;
            })
            .addCase(fetchPersonalizedRecommendations.fulfilled, (state, action) => {
                state.isLoading = false;
                state.personalizedRecommendations.items = action.payload.items;
                state.personalizedRecommendations.pagination = action.payload.pagination;
                state.personalizedRecommendations.currentPage = 1;
            })
            .addCase(fetchPersonalizedRecommendations.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.error.message;
            })
            // Special offers
            .addCase(fetchSpecialOffers.pending, (state) => {
                state.isLoading = true;
            })
            .addCase(fetchSpecialOffers.fulfilled, (state, action) => {
                state.isLoading = false;
                state.specialOffers.items = action.payload.items;
                state.specialOffers.pagination = action.payload.pagination;
                state.specialOffers.currentPage = 1;
            })
            .addCase(fetchSpecialOffers.rejected, (state, action) => {
                state.isLoading = false;
                state.error = action.error.message;
            });
    }
});

export const { 
    setUserLocation, 
    clearHomepageData, 
    setPopularRestaurantsPage,
    loadMorePopularRestaurants,
    loadMoreSpecialOffers,
    loadMoreTrendingDishes 
} = homepageSlice.actions;

export default homepageSlice.reducer;