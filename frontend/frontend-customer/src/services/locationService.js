// services/locationService.js
import api from './api';

export const locationService = {
  // Get unique cities from addresses
  getCities: async () => {
    try {
      const response = await api.get('/locations/cities/');
      return response.data;
    } catch (error) {
      console.error('Error fetching cities:', error);
      return [];
    }
  },

  // Get neighborhoods for a city
  getNeighborhoods: async (city) => {
    try {
      const response = await api.get('/locations/neighborhoods/', {
        params: { city }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching neighborhoods:', error);
      return [];
    }
  }
};