// services/searchService.js
import api from './api';

const ITEMS_PER_PAGE = 20;
const PREVIEW_ITEMS = 10;

export const searchService = {
  getSuggestions: async (query) => {
    if (!query || query.length < 2) return [];
    try {
      const response = await api.get('/search/suggestions/combined/', {
        params: { q: query, limit: 8 }
      });
      return response.data.suggestions || [];
    } catch (error) {
      return [];
    }
  },

  getLocationOptions: async () => {
    try {
      const response = await api.get('/locations/');
      return response.data;
    } catch (error) {
      return [];
    }
  },

  discoverSearch: async (query, filters = {}, options = {}) => {
    try {
      const params = {
        q: query,
        page: 1,
        page_size: ITEMS_PER_PAGE,
        type: filters.type || 'all',
        sort_by: filters.sortBy || 'relevance',
      };

      if (filters.location) params.location = filters.location;
      if (filters.dietary) params.dietary = filters.dietary;
      if (filters.price_range) params.price_range = filters.price_range;

      console.log('🔍 DISCOVER SEARCH REQUEST:', params);
      
      const response = await api.get('/search/discover/', { 
        params,
        signal: options.signal
      });
      
      console.log('📦 DISCOVER SEARCH RESPONSE:', {
        restaurants: response.data.results?.restaurants?.length || 0,
        dishes: response.data.results?.menu_items?.length || 0,
        cuisines: response.data.results?.cuisines?.length || 0,
        categories: response.data.results?.categories?.length || 0,
        pagination: response.data.pagination
      });
      
      return response.data;
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      console.error('Discover search failed:', error);
      throw error;
    }
  },

  loadMoreSection: async (sectionType, query, page = 2, filters = {}) => {
    try {
      const params = {
        section: sectionType,
        q: query,
        page: page,
        page_size: ITEMS_PER_PAGE,
      };
      
      if (filters.dietary) params.dietary = filters.dietary;
      if (filters.price_range) params.price_range = filters.price_range;
      if (filters.location) params.location = filters.location;
      if (filters.sortBy) params.sort_by = filters.sortBy;

      console.log(`📤 LOAD MORE ${sectionType} PAGE ${page}:`, params);
      
      const response = await api.get('/search/load-more/', { params });
      
      return {
        items: response.data.items || [],
        pagination: {
          current_page: response.data.page,
          total_pages: response.data.total_pages,
          total_items: response.data.total,
          has_next: response.data.has_next
        }
      };
    } catch (error) {
      console.error(`Error loading more ${sectionType}:`, error);
      throw error;
    }
  },

  api: api
};