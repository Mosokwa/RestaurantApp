// services/restaurantService.js
import api, { parsePaginatedResponse, buildPaginationParams } from './api';

export const restaurantService = {
  // Get restaurant by ID
  getRestaurant: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}/`);
    return response.data;
  },

  // Get restaurants with pagination
  getRestaurants: async (page = 1, pageSize = 20, filters = {}) => {
    const params = {
      ...buildPaginationParams(page, pageSize),
      ...filters
    };
        
    const response = await api.get('/restaurants/', { params });
    return parsePaginatedResponse(response);
  },
};