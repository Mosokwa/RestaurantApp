// services/menuService.js
import api, { parsePaginatedResponse, buildPaginationParams } from './api';

export const menuService = {
  // Get restaurant menu with pagination
  getRestaurantMenu: async (restaurantId, page = 1, pageSize = 50) => {
    const params = buildPaginationParams(page, pageSize);
    const response = await api.get(`/menu/restaurant/${restaurantId}/`, { params });
    return parsePaginatedResponse(response);
  },

  // Get all cuisines with pagination
  getCuisines: async (page = 1, pageSize = 100) => {
    const params = buildPaginationParams(page, pageSize);
    const response = await api.get('/cuisines/', { params });
    return parsePaginatedResponse(response);
  }
};