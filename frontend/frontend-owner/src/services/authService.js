// services/authService.js
import api from './api';
import { extractServiceData, handleServiceResponse } from './apiResponseHandler';

export const authService = {
  // Owner-specific authentication
  ownerLogin: async (credentials) => {
    const response = await api.post('/owner/auth/login/', credentials);
    
    if (response.data.tokens?.refresh) {
      localStorage.setItem('refreshToken', response.data.tokens.refresh);
    }
    
    return response.data;
  },

  ownerRegister: async (ownerData) => {
    const response = await api.post('/owner/auth/register/', ownerData);
    return response.data;
  },

  getCurrentOwner: async () => {
    const response = await api.get('/owner/auth/me/');
  
    // FIX: Extract only the data, not the entire axios response
    const handledResponse = handleServiceResponse(response);
    
    // Ensure we're returning just the user data, not axios wrapper
    if (handledResponse && handledResponse.data) {
      return handledResponse.data; // Extract the actual user data
    }
    
    return handledResponse;
  },

  getOwnerRestaurants: async () => {
    const response = await api.get('/owner/restaurants/');
    return handleServiceResponse(response);
  },

  inviteStaff: async (staffData) => {
    const response = await api.post('/owner/staff/invite/', staffData);
    return response.data;
  },

  ownerVerifyEmail: async (email) => {
    const response = await api.post('/owner/auth/verify-email/', { email });
    return extractServiceData(response);
  },

  ownerVerifyCode: async (email, code) => {
    const response = await api.post('/owner/auth/verify-code/', { email, code });
    return extractServiceData(response);
  },

  // General auth
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials);
    
    if (response.data.tokens?.refresh) {
      localStorage.setItem('refreshToken', response.data.tokens.refresh);
    }
    
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout/');
    
    // Clear all tokens
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('csrfToken');
    
    return response.data;
  },

  // Staff management
  getRestaurantStaff: async (restaurantId) => {
    const response = await api.get(`/staff/?restaurant=${restaurantId}`);
    return handleServiceResponse(response);
  },

  updateStaffPermissions: async (staffId, permissions) => {
    const response = await api.patch(`/staff/${staffId}/`, permissions);
    return response.data;
  },

  // Password management
  changePassword: async (passwordData) => {
    const response = await api.put('/auth/password/change/', passwordData);
    return response.data;
  },

  resetPassword: async (email) => {
    const response = await api.post('/auth/password/reset/', { email });
    return response.data;
  }, 

  googleLogin: async (data) => {
    const response = await api.post('/auth/google/login/', data);
    return response.data;
  },

  facebookLogin: async (data) => {
    const response = await api.post('/auth/facebook/login/', data);
    return response.data;
  },

  verifyEmailCode: async (data) => {
    const response = await api.post('/auth/verify-code/', data);
    return response.data;
  },

  resendVerificationEmail: async (email) => {
    const response = await api.post('/auth/verify-email/', { email });
    return response.data;
  },

};