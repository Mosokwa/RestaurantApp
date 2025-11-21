// services/cuisineService.js
import api from './api';
import { handleServiceResponse } from './apiResponseHandler';

export const cuisineService = {
  getCuisines: async () => {
    const response = await api.get('/cuisines/');
    return handleServiceResponse(response);
  },

  createCuisine: async (cuisineData) => {
    const response = await api.post('/cuisines/create/', cuisineData);
    return handleServiceResponse(response);
  },

  updateCuisine: async (id, cuisineData) => {
    const response = await api.put(`/cuisines/${id}/update/`, cuisineData);
    return handleServiceResponse(response);
  },

  deleteCuisine: async (id) => {
    const response = await api.delete(`/cuisines/${id}/delete/`);
    return handleServiceResponse(response);
  }
};