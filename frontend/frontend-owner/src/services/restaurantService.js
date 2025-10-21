import api from './api';
import { handleServiceResponse } from './apiResponseHandler';

export const restaurantService = {
  // Owner restaurant management
  getMyRestaurants: async () => {
    const response = await api.get('/restaurants/my/');
    return handleServiceResponse(response);
  },

  createRestaurant: async (restaurantData) => {
    const response = await api.post('/restaurants/create/', restaurantData);
    return handleServiceResponse(response);
  },

  updateRestaurant: async (id, restaurantData) => {
    const response = await api.put(`/restaurants/${id}/update/`, restaurantData);
    return handleServiceResponse(response);
  },

  // Staff management
  getStaff: async (restaurantId) => {
    const response = await api.get(`/staff/?restaurant=${restaurantId}`);
    return handleServiceResponse(response);
  },

  createStaff: async (staffData) => {
    const response = await api.post('/staff/', staffData);
    return handleServiceResponse(response);
  },

  updateStaff: async (id, staffData) => {
    const response = await api.put(`/staff/${id}/`, staffData);
    return handleServiceResponse(response);
  },

  // Branch management
  getBranches: async (restaurantId) => {
    const response = await api.get(`/restaurants/${restaurantId}/branches/`);
    return handleServiceResponse(response);
  },

  createBranch: async (branchData) => {
    const response = await api.post('/branches/create/', branchData);
    return handleServiceResponse(response);
  }
};