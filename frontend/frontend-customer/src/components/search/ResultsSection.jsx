// pages/SearchResultsPage/components/ResultsSection.jsx
import RestaurantResultCard from './RestaurantResultCard';
import DishResultCard from './DishResultCard';
import CuisineResultCard from './CuisineResultcard';
import CategoryResultCard from './CategoryResultCard';

const PREVIEW_ITEMS = 10;

const ResultsSection = ({ 
  section, 
  items, 
  searchQuery, 
  onViewAll 
}) => {
  if (!items || items.length === 0) return null;

  const sectionConfig = {
    menu_items: {
      title: 'Dishes',
      icon: '🍽️',
      color: '#4cc9f0',
      component: DishResultCard,
      propName: 'dish'
    },
    categories: {
      title: 'Categories',
      icon: '📋',
      color: '#F9C74F',
      component: CategoryResultCard,
      propName: 'category'
    },
    cuisines: {
      title: 'Cuisines',
      icon: '🍜',
      color: '#90BE6D',
      component: CuisineResultCard,
      propName: 'cuisine'
    },
    restaurants: {
      title: 'Restaurants',
      icon: '🏢',
      color: '#e63946',
      component: RestaurantResultCard,
      propName: 'restaurant'
    }
  };

  const config = sectionConfig[section.type];
  if (!config) return null;

  const Component = config.component;
  const color = config.color;

  // Show only first 10 items in the main results page
  const previewItems = items.slice(0, PREVIEW_ITEMS);
  
  // Use total_count from section to determine if we need View All button
  const totalCount = section.total_count || items.length;
  const hasMore = totalCount > PREVIEW_ITEMS;

  console.log(`ResultsSection - ${section.type}:`, {
    previewItems: previewItems.length,
    totalCount: totalCount,
    hasMore: hasMore,
    itemsLength: items.length
  });

  const handleViewAll = () => {
    onViewAll({
      type: section.type,
      title: config.title,
      icon: config.icon,
      color: color,
      items: items, // Pass current items (first page)
      totalCount: totalCount
    });
  };

  return (
    <div className="sr-results-section" style={{ borderLeftColor: color }}>
      <div className="sr-section-header">
        <div className="sr-section-title-wrapper">
          <span className="sr-section-icon" style={{ backgroundColor: `${color}20` }}>
            {config.icon}
          </span>
          <h2 className="sr-section-title">
            {config.title}
            <span className="sr-section-count" style={{ backgroundColor: color }}>
              {totalCount}
            </span>
          </h2>
        </div>
        
        {hasMore && (
          <button 
            onClick={handleViewAll}
            className="sr-view-all-btn"
            style={{ color }}
          >
            View All ({totalCount}) →
          </button>
        )}
      </div>

      <div className="sr-section-grid">
        {previewItems.map((item, index) => (
          <div key={`${section.type}-${index}`} className="sr-grid-item">
            <div className="sr-item-badge" style={{ backgroundColor: color }}>
              {config.icon} {section.type.replace('_', ' ')}
            </div>
            <Component {...{ [config.propName]: item }} />
          </div>
        ))}
      </div>
      
      {previewItems.length === 0 && (
        <div className="sr-section-empty">
          <p>No {config.title.toLowerCase()} to display</p>
        </div>
      )}
    </div>
  );
};

export default ResultsSection;