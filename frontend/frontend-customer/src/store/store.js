import { configureStore } from "@reduxjs/toolkit";
import authSlice from './slices/authSlice';
import restaurantReducer from './slices/restaurantSlice';
import homepageReducer from './slices/homepageSlice'
import explorationReducer from './slices/explorationSlice';

export const store = configureStore({
    reducer: {
        auth: authSlice,
        restaurant: restaurantReducer,
        homepage: homepageReducer,
        exploration: explorationReducer,
    }
});

export default store;