import api from './api';
import { handleServiceResponse, extractServiceData } from './apiResponseHandler';

export const analyticsService = {
  // Dashboard Overview Data
  getDashboardOverview: async (restaurantId) => {
    const response = await api.get(`/api/analytics/dashboard/${restaurantId}/`);
    return handleServiceResponse(response);
  },

  // Today's Sales Data
  getTodaySales: async (restaurantId) => {
    const response = await api.get(`/api/sales/daily-report/?restaurant_id=${restaurantId}`);
    return handleServiceResponse(response);
  },

  // Real-time Orders
  getRealTimeOrders: async (restaurantId) => {
    const response = await api.get(`/orders/?restaurant=${restaurantId}&status__in=pending,preparing`);
    return handleServiceResponse(response);
  },

  // Kitchen Queue
  getKitchenQueue: async (restaurantId) => {
    const response = await api.get(`/api/owner/kitchen/queue/?restaurant_id=${restaurantId}`);
    return handleServiceResponse(response);
  },

  // Performance Metrics
  getPerformanceMetrics: async (restaurantId) => {
    const response = await api.get(`/api/sales/performance-metrics/${restaurantId}/`);
    return handleServiceResponse(response);
  },

  // Customer Insights
  getCustomerInsights: async (restaurantId) => {
    const response = await api.get(`/api/analytics/customer-insights/${restaurantId}/`);
    return handleServiceResponse(response);
  },

  // Recent Alerts/Notifications
  getRecentAlerts: async (restaurantId) => {
    const response = await api.get(`/api/analytics/alerts/${restaurantId}/`);
    return handleServiceResponse(response);
  }
};