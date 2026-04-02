// pages/SearchResultsPage/components/DishResultCard.jsx
import { Link } from 'react-router-dom';

const DishResultCard = ({ dish }) => {
  if (!dish) return null;

  const itemId = dish.item_id || dish.id;
  const itemName = dish.name || 'Unknown Dish';
  const restaurantId = dish.restaurant_id || dish.restaurantId;
  const restaurantName = dish.restaurant_name || dish.restaurantName || 'Unknown restaurant';
  const price = dish.price || 0;
  const description = dish.description || '';
  const image = dish.image || '/food.png';
  const distance = dish.distance_km || dish.distance;
  const popularity = dish.popularity_score || dish.popularity || 0;
  const restaurantRating = dish.restaurant_rating || dish.restaurantRating;

  const isVegetarian = dish.is_vegetarian || dish.vegetarian || false;
  const isVegan = dish.is_vegan || dish.vegan || false;
  const isGlutenFree = dish.is_gluten_free || dish.glutenFree || false;
  const isSpicy = dish.is_spicy || dish.spicy || false;

  if (!itemId || !restaurantId) return null;

  return (
    <Link to={`/restaurants/${restaurantId}/menu?item=${itemId}`} 
          className="sr-dish-card">
      <div className="sr-card-image">
        <img 
          src={image} 
          alt={itemName}
          onError={(e) => { e.target.src = '/food.png'; }}
        />
        <div className="sr-dietary-icons">
          {isVegetarian && <span className="sr-dietary sr-dietary-veg">🥬 Veg</span>}
          {isVegan && <span className="sr-dietary sr-dietary-vegan">🌱 Vegan</span>}
          {isGlutenFree && <span className="sr-dietary sr-dietary-gf">🌾 GF</span>}
          {isSpicy && <span className="sr-dietary sr-dietary-spicy">🔥 Spicy</span>}
        </div>
      </div>
      
      <div className="sr-card-content">
        <h3 className="sr-card-title">{itemName}</h3>
        
        <div className="sr-dish-restaurant">
          <span className="sr-restaurant-name">{restaurantName}</span>
          {restaurantRating && (
            <span className="sr-restaurant-rating">⭐ {restaurantRating}</span>
          )}
        </div>
        
        {description && (
          <p className="sr-dish-description">{description.substring(0, 60)}...</p>
        )}
        
        <div className="sr-dish-footer">
          <span className="sr-dish-price">${price}</span>
          
          {popularity > 50 && (
            <span className="sr-popular-badge">🔥 Popular</span>
          )}
          
          {distance && (
            <span className="sr-dish-distance">{distance} km</span>
          )}
        </div>
      </div>
    </Link>
  );
};

export default DishResultCard;