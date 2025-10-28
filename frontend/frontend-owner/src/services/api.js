// services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with credentials
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Single source of truth for CSRF token
let csrfToken = localStorage.getItem('csrfToken');
let isInitialized = false;
let initializationPromise = null;
let initializationCount = 0;

// Robust CSRF token management
export const getCSRFToken = async (forceRefresh = false) => {
  if (!forceRefresh && csrfToken) {
    return csrfToken;
  }

  if (initializationPromise) {
    console.log('🔄 CSRF initialization already in progress, reusing promise...');
    return initializationPromise;
  }

  initializationCount++;
  console.log(`🔄 CSRF initialization attempt #${initializationCount}`);

  initializationPromise = (async () => {
    try {
      console.log('🔄 Fetching CSRF token...');
      
      const response = await api.get('/auth/csrf/', {
        headers: {
          'X-CSRF-Request': 'true'
        }
      });

      if (!response.data.csrfToken) {
        throw new Error('No CSRF token in response');
      }

      const newToken = response.data.csrfToken;
      csrfToken = newToken;
      localStorage.setItem('csrfToken', newToken);
      isInitialized = true;
      
      console.log('✅ CSRF token obtained');
      return newToken;
      
    } catch (error) {
      console.error('❌ CSRF token fetch failed:', error);
      
      if (error.response?.status === 403 || error.response?.status === 401) {
        csrfToken = null;
        localStorage.removeItem('csrfToken');
        isInitialized = false;
      }
      
      throw error;
    } finally {
      initializationPromise = null;
    }
  })();

  return initializationPromise;
};

// Request interceptor
api.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const isStateChangingMethod = ['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase());
    const isInternalAPI = config.url?.startsWith('/');
    const isCSRFRequest = config.headers['X-CSRF-Request'];
    
    if (isStateChangingMethod && isInternalAPI && !isCSRFRequest && csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle CSRF token errors (403)
    if (error.response?.status === 403 && 
        !originalRequest._csrfRetried &&
        !originalRequest.headers['X-CSRF-Request']) {
      
      try {
        originalRequest._csrfRetried = true;
        await getCSRFToken(true);
        
        if (csrfToken) {
          originalRequest.headers['X-CSRFToken'] = csrfToken;
          return api(originalRequest);
        }
      } catch (csrfError) {
        console.error('❌ CSRF recovery failed:', csrfError);
        return Promise.reject(new Error('Security token validation failed'));
      }
    }

    // Handle JWT token expiration (401)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await api.post('/auth/token/refresh/', {
            refresh: refreshToken
          });
          
          const newToken = response.data.access;
          localStorage.setItem('token', newToken);
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Initialize CSRF token once per app load
export const initializeApp = async () => {
  if (isInitialized && csrfToken) {
    console.log('✅ CSRF already initialized, skipping...');
    return csrfToken;
  }

  // If already initializing, wait for the existing promise
  if (initializationPromise) {
    console.log('🔄 CSRF initialization already in progress, waiting...');
    return initializationPromise;
  }

  return getCSRFToken();
  
};

// Export initialization state for external checking
export const getCSRFState = () => ({
  isInitialized,
  hasToken: !!csrfToken,
  initializationInProgress: !!initializationPromise
});

export default api;