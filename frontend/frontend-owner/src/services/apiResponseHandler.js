import { handleApiResponse } from '../utils/paginationUtils.js';

export const handleServiceResponse = (response) => {
  try {
    const data = response.data;

    // If it's a paginated response with results
    if (data && data.results !== undefined) {
      return {
        data: data.results,
        pagination: {
          count: data.count,
          next: data.next,
          previous: data.previous
        }
      };
    }
    
    // If it's a direct data response
    if (data && typeof data === 'object') {
      return {
        data: data,
        // Don't include axios headers in the state!
      };
    }
    
    return {
      data: data,
      originalResponse: { status: response.status, statusText: response.statusText }
    };
  } catch (error) {
    console.error('Error handling API response:', error);
    return {
      data: null,
      error: error.message
    };
  }
};

export const extractServiceData = (response) => {
  const handled = handleServiceResponse(response);
  return handled.data;
};