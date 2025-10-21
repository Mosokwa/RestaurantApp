export const extractDataFromResponse = (response) => {
  if (!response) return [];
  if (Array.isArray(response)) return response;
  if (response && Array.isArray(response.results)) return response.results;
  if (response && response.data && Array.isArray(response.data.results)) return response.data.results;
  if (response && response.data && Array.isArray(response.data)) return response.data;
  return response || [];
};

export const getPaginationInfo = (response) => {
  if (!response || Array.isArray(response)) return null;
  
  return {
    count: response.count || response.total_count || 0,
    next: response.next || null,
    previous: response.previous || null,
    totalPages: response.total_pages || response.totalPages || 0,
    currentPage: response.current_page || response.currentPage || 1,
    pageSize: response.page_size || response.pageSize || 20
  };
};

export const handleApiResponse = (response) => {
  return {
    data: extractDataFromResponse(response),
    pagination: getPaginationInfo(response),
    originalResponse: response
  };
};
