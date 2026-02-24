const LOCATION_CACHE_KEY = 'user_location';
const LOCATION_CACHE_TTL = 300000; // 5 minutes

export const getCachedLocation = () => {
  try {
    const cached = localStorage.getItem(LOCATION_CACHE_KEY);
    if (!cached) return null;
    
    const { location, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp > LOCATION_CACHE_TTL) {
      localStorage.removeItem(LOCATION_CACHE_KEY);
      return null;
    }
    
    return location;
  } catch (error) {
    console.warn('Failed to retrieve cached location:', error);
    return null;
  }
};

export const saveLocationToCache = (location) => {
  try {
    localStorage.setItem(LOCATION_CACHE_KEY, JSON.stringify({
      location,
      timestamp: Date.now()
    }));
  } catch (error) {
    console.warn('Failed to cache location:', error);
  }
};