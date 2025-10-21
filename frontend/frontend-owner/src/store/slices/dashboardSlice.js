import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { analyticsService } from '../../services/analyticsService';
import { extractDataFromResponse } from '../../utils/paginationUtils';

export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchData',
  async (restaurantId) => {
    const [
      dashboardOverview,
      todaySales,
      realTimeOrders,
      kitchenQueue,
      performanceMetrics,
      customerInsights
    ] = await Promise.all([
      analyticsService.getDashboardOverview(restaurantId),
      analyticsService.getTodaySales(restaurantId),
      analyticsService.getRealTimeOrders(restaurantId),
      analyticsService.getKitchenQueue(restaurantId),
      analyticsService.getPerformanceMetrics(restaurantId),
      analyticsService.getCustomerInsights(restaurantId)
    ]);

    return {
      dashboardOverview: extractDataFromResponse(dashboardOverview),
      todaySales: extractDataFromResponse(todaySales),
      realTimeOrders: extractDataFromResponse(realTimeOrders),
      kitchenQueue: extractDataFromResponse(kitchenQueue),
      performanceMetrics: extractDataFromResponse(performanceMetrics),
      customerInsights: extractDataFromResponse(customerInsights)
    };
  }
);

export const fetchRealTimeData = createAsyncThunk(
  'dashboard/fetchRealTimeData',
  async (restaurantId) => {
    const [realTimeOrders, kitchenQueue] = await Promise.all([
      analyticsService.getRealTimeOrders(restaurantId),
      analyticsService.getKitchenQueue(restaurantId)
    ]);
    
    return {
      realTimeOrders: extractDataFromResponse(realTimeOrders),
      kitchenQueue: extractDataFromResponse(kitchenQueue)
    };
  }
);

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState: {
    // Main data
    dashboardOverview: {},
    todaySales: {},
    realTimeOrders: [],
    kitchenQueue: [],
    performanceMetrics: {},
    customerInsights: {},
    
    // UI state
    loading: false,
    error: null,
    lastUpdated: null,
    
    // Real-time updates
    realTimeLoading: false
  },
  reducers: {
    updateRealTimeData: (state, action) => {
      state.realTimeOrders = action.payload.realTimeOrders || state.realTimeOrders;
      state.kitchenQueue = action.payload.kitchenQueue || state.kitchenQueue;
      state.lastUpdated = new Date().toISOString();
    },
    clearDashboardData: (state) => {
      state.dashboardOverview = {};
      state.todaySales = {};
      state.realTimeOrders = [];
      state.kitchenQueue = [];
      state.performanceMetrics = {};
      state.customerInsights = {};
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading = false;
        state.dashboardOverview = action.payload.dashboardOverview;
        state.todaySales = action.payload.todaySales;
        state.realTimeOrders = action.payload.realTimeOrders.results || action.payload.realTimeOrders;
        state.kitchenQueue = action.payload.kitchenQueue;
        state.performanceMetrics = action.payload.performanceMetrics;
        state.customerInsights = action.payload.customerInsights;
        state.lastUpdated = new Date().toISOString();
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      })
      .addCase(fetchRealTimeData.pending, (state) => {
        state.realTimeLoading = true;
      })
      .addCase(fetchRealTimeData.fulfilled, (state, action) => {
        state.realTimeLoading = false;
        state.realTimeOrders = action.payload.realTimeOrders.results || action.payload.realTimeOrders;
        state.kitchenQueue = action.payload.kitchenQueue;
        state.lastUpdated = new Date().toISOString();
      });
  }
});

export const { updateRealTimeData, clearDashboardData } = dashboardSlice.actions;
export default dashboardSlice.reducer;