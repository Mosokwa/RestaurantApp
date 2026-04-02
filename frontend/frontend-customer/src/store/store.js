import { configureStore } from "@reduxjs/toolkit";
import authSlice from './slices/authSlice';
import restaurantReducer from './slices/restaurantSlice';
import homepageReducer from './slices/homepageSlice'
import explorationReducer from './slices/explorationSlice';
import layoutReducer from './slices/layoutSlice';

export const store = configureStore({
    reducer: {
        auth: authSlice,
        restaurant: restaurantReducer,
        homepage: homepageReducer,
        exploration: explorationReducer,
        layout: layoutReducer,
    }
});

export default store;