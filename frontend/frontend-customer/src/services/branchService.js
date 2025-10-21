// services/branchService.js
import api, { parsePaginatedResponse, buildPaginationParams } from './api';

export const branchService = {
  // Get branches by restaurant with pagination
  getBranchesByRestaurant: async (restaurantId, page = 1, pageSize = 20) => {
    const params = buildPaginationParams(page, pageSize);
    const response = await api.get(`/branches/?restaurant=${restaurantId}`, { params });
    return parsePaginatedResponse(response);
  },
};