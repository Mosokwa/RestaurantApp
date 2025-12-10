import api from './api';
import { handleServiceResponse } from './apiResponseHandler';

export const menuService = {
  // Categories
  getCategories: async (restaurantId) => {
    const response = await api.get(`/menu/categories/?restaurant=${restaurantId}`);
    return handleServiceResponse(response);
  },

  createCategory: async (categoryData) => {
    const response = await api.post('/menu/categories/create/', categoryData);
    return handleServiceResponse(response);
  },

  updateCategory: async (id, categoryData) => {
    const response = await api.put(`/menu/categories/${id}/update/`, categoryData);
    return handleServiceResponse(response);
  },

  deleteCategory: async (id) => {
    const response = await api.delete(`/menu/categories/${id}/delete/`);
    return handleServiceResponse(response);
  },

  // Menu Items
  getMenuItems: async (restaurantId, categoryId = null) => {
    const params = { restaurant: restaurantId };
    if (categoryId) params.category = categoryId;
    
    const response = await api.get('/menu/items/', { params });
    return handleServiceResponse(response);
  },

  createMenuItem: async (itemData) => {
    const response = await api.post('/menu/items/create/', itemData);
    return handleServiceResponse(response);
  },

  updateMenuItem: async (id, itemData) => {
    const response = await api.put(`/menu/items/${id}/update/`, itemData);
    return handleServiceResponse(response);
  },

  deleteMenuItem: async (id) => {
    const response = await api.delete(`/menu/items/${id}/delete/`);
    return handleServiceResponse(response);
  },

  // Analytics
  getMenuAnalytics: async (restaurantId, days = 30) => {
    const response = await api.get('/analytics/enhanced-menu-performance/', {
      params: { restaurant_id: restaurantId, days }
    });
    return handleServiceResponse(response);
  },

  getCategoryAnalytics: async (restaurantId) => {
    const response = await api.get('/analytics/category-analytics/', {
      params: { restaurant_id: restaurantId }
    });
    return handleServiceResponse(response);
  },

  getItemAssociations: async (itemId) => {
    const response = await api.get(`/analytics/item-associations/${itemId}/`);
    return handleServiceResponse(response);
  },

  // Bulk Operations
  bulkUpdateMenuItems: async (updates) => {
    const response = await api.post('/analytics/bulk-menu-operations/', updates);
    return handleServiceResponse(response);
  },

  // Real-time Metrics
  getRealTimeMetrics: async (restaurantId) => {
    const response = await api.get(`/analytics/real-time-metrics/${restaurantId}/`);
    return handleServiceResponse(response);
  },

    // Modifier Groups
    getModifierGroups: async () => {
    const response = await api.get('/modifier-groups/');
    return handleServiceResponse(response);
    },

    createModifierGroup: async (groupData) => {
    const response = await api.post('/modifier-groups/create/', groupData);
    return handleServiceResponse(response);
    },

    updateModifierGroup: async (id, groupData) => {
    const response = await api.put(`/modifier-groups/${id}/update/`, groupData);
    return handleServiceResponse(response);
    },

    deleteModifierGroup: async (id) => {
    const response = await api.delete(`/modifier-groups/${id}/delete/`);
    return handleServiceResponse(response);
    },

    // Modifiers
    createModifier: async (modifierData) => {
    const response = await api.post('/modifiers/create/', modifierData);
    return handleServiceResponse(response);
    },

    updateModifier: async (id, modifierData) => {
    const response = await api.put(`/modifiers/${id}/update/`, modifierData);
    return handleServiceResponse(response);
    },

    deleteModifier: async (id) => {
    const response = await api.delete(`/modifiers/${id}/delete/`);
    return handleServiceResponse(response);
    },
};