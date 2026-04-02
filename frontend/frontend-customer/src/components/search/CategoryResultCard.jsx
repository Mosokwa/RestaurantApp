// pages/SearchResultsPage/components/CategoryResultCard.jsx
import { Link } from 'react-router-dom';

const CategoryResultCard = ({ category }) => {
  if (!category) return null;
  
  const restaurantId = category.restaurant_id || category.restaurantId;
  const restaurantName = category.restaurant_name || category.restaurantName || 'Unknown restaurant';
  const categoryId = category.category_id || category.id;
  const categoryName = category.name || 'Unnamed Category';
  const itemCount = category.item_count || category.itemCount || 0;
  const description = category.description || '';

  if (!restaurantId || !categoryId) return null;

  return (
    <Link to={`/restaurants/${restaurantId}/menu?category=${categoryId}`} 
          className="sr-category-card">
      <div className="sr-category-content">
        <div className="sr-category-header">
          <h3 className="sr-category-name">{categoryName}</h3>
          <span className="sr-category-count">{itemCount} items</span>
        </div>
        
        <div className="sr-category-restaurant">
          <span className="sr-restaurant-icon">🏢</span>
          <span className="sr-restaurant-name">{restaurantName}</span>
        </div>
        
        {description && (
          <p className="sr-category-description">{description}</p>
        )}
        
        <div className="sr-category-footer">
          <button className="sr-view-menu-btn">
            View Menu →
          </button>
        </div>
      </div>
    </Link>
  );
};

export default CategoryResultCard;