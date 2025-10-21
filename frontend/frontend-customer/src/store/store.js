import { configureStore } from "@reduxjs/toolkit";
import authSlice from './slices/authSlice';
import restaurantReducer from './slices/restaurantSlice';
import homepageReducer from './slices/homepageSlice'

export const store = configureStore({
    reducer: {
        auth: authSlice,
        restaurant: restaurantReducer,
        homepage: homepageReducer,
    }
});

export default store;