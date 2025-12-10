/**
 * Standardized API response handler for consistent error handling
 */

export const handleServiceResponse = (response) => {
  try {
    const data = response.data;

    // Handle paginated responses
    if (data && data.results !== undefined) {
      return {
        data: data.results,
        pagination: {
          count: data.count,
          next: data.next,
          previous: data.previous
        },
        status: response.status,
        success: true
      };
    }
    
    // Handle direct data responses
    if (data && typeof data === 'object') {
      return {
        data: data,
        status: response.status,
        success: true
      };
    }
    
    return {
      data: data,
      status: response.status,
      success: true
    };
  } catch (error) {
    console.error('Error handling API response:', error);
    return {
      data: null,
      error: error.message,
      status: 500,
      success: false
    };
  }
};

export const extractServiceData = (response) => {
  const handled = handleServiceResponse(response);
  return handled.data;
};

export const handleServiceError = (error, defaultMessage = 'An error occurred') => {
  console.error('Service Error:', error);

  // Handle network errors
  if (!error.response) {
    return {
      success: false,
      error: 'Network error - please check your connection',
      status: 0,
      data: null
    };
  }

  // Handle server errors with response
  const response = error.response;
  const errorData = response.data;

  // Extract error message from different response formats
  let errorMessage = defaultMessage;
  
  if (typeof errorData === 'string') {
    errorMessage = errorData;
  } else if (errorData.error) {
    errorMessage = errorData.error;
  } else if (errorData.detail) {
    errorMessage = errorData.detail;
  } else if (errorData.message) {
    errorMessage = errorData.message;
  } else if (typeof errorData === 'object') {
    // Handle validation errors
    const firstError = Object.values(errorData)[0];
    if (Array.isArray(firstError)) {
      errorMessage = firstError[0];
    } else if (typeof firstError === 'string') {
      errorMessage = firstError;
    }
  }

  return {
    success: false,
    error: errorMessage,
    errors: errorData.errors || null,
    status: response.status,
    data: null
  };
};

/**
 * Retry mechanism for failed requests
 */
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const result = await requestFn();
      return result;
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, delay * attempt));
      console.warn(`Retrying request (attempt ${attempt + 1}/${maxRetries})...`);
    }
  }
};

/**
 * Cache wrapper for API calls
 */
export const withCache = (fn, ttl = 5 * 60 * 1000) => { // 5 minutes default
  const cache = new Map();
  
  return async (...args) => {
    const key = JSON.stringify(args);
    const now = Date.now();
    
    if (cache.has(key)) {
      const { data, timestamp } = cache.get(key);
      if (now - timestamp < ttl) {
        return data;
      }
    }
    
    const result = await fn(...args);
    cache.set(key, { data: result, timestamp: now });
    
    return result;
  };
};

/**
 * Debounce API calls
 */
export const debounce = (fn, delay) => {
  let timeoutId;
  
  return (...args) => {
    clearTimeout(timeoutId);
    return new Promise((resolve) => {
      timeoutId = setTimeout(() => resolve(fn(...args)), delay);
    });
  };
};