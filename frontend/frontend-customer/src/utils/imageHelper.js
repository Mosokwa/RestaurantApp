// src/utils/imageHelpers.js
const FALLBACK_IMAGES = {
  logo: '/logo.png',
  banner: '/banner.jpg',
  food: '/food.png'
};

export const getImageUrl = (imageUrl, type = 'food') => {
  // If imageUrl exists and is a valid string, use it
  if (imageUrl && typeof imageUrl === 'string' && imageUrl.trim() !== '') {
    return imageUrl;
  }
  // Otherwise return fallback
  return FALLBACK_IMAGES[type];
};

export default getImageUrl;