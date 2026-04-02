// pages/SearchResultsPage/components/CuisineResultCard.jsx
import { Link } from 'react-router-dom';

const CuisineResultCard = ({ cuisine }) => {
  if (!cuisine) return null;

  const cuisineId = cuisine.cuisine_id || cuisine.id;
  const cuisineName = cuisine.name || 'Unknown Cuisine';
  const description = cuisine.description || `Explore ${cuisineName} restaurants`;
  const restaurantCount = cuisine.restaurant_count || cuisine.restaurantCount || 0;
  const icon = cuisine.icon || '🍽️';

  if (!cuisineId) return null;

  const getCuisineIcon = (name) => {
    const icons = {
      'italian': '🍕',
      'chinese': '🥡',
      'japanese': '🍣',
      'mexican': '🌮',
      'indian': '🍛',
      'thai': '🍜',
      'american': '🍔',
      'french': '🥖',
      'greek': '🥙',
      'mediterranean': '🥗',
    };
    
    const cuisineLower = name.toLowerCase();
    for (const [key, icon] of Object.entries(icons)) {
      if (cuisineLower.includes(key)) {
        return icon;
      }
    }
    return icon;
  };

  return (
    <Link to={`/search?q=${encodeURIComponent(cuisineName)}&type=restaurants`} 
          className="sr-cuisine-card">
      <div className="sr-cuisine-content">
        <div className="sr-cuisine-icon-wrapper">
          <span className="sr-cuisine-icon">{getCuisineIcon(cuisineName)}</span>
        </div>
        
        <div className="sr-cuisine-info">
          <h3 className="sr-cuisine-name">{cuisineName}</h3>
          
          <p className="sr-cuisine-description">{description}</p>
          
          <div className="sr-cuisine-stats">
            <span className="sr-cuisine-count">
              📍 {restaurantCount} {restaurantCount === 1 ? 'restaurant' : 'restaurants'}
            </span>
            
            <button className="sr-cuisine-explore">
              Explore →
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default CuisineResultCard;