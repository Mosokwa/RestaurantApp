import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// import './Homepage.css';

const QuickCategories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/homepage/quick-categories/');
      if (!response.ok) throw new Error('Failed to fetch categories');
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching categories:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (category) => {
    // Navigate to search with category filter
    navigate(`/search?category=${encodeURIComponent(category.search_query || category.name)}`);
  };

  if (loading) {
    return (
      <section className="quick-categories">
        <h2>Quick Categories</h2>
        <div className="categories-container loading">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="category-btn skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="quick-categories">
        <h2>Quick Categories</h2>
        <div className="error-message">
          <p>Failed to load categories. Please try again.</p>
          <button onClick={fetchCategories} className="retry-btn">
            Retry
          </button>
        </div>
      </section>
    );
  }

  if (!categories || categories.length === 0) {
    return null;
  }

  return (
    <section className="quick-categories">
      <h2>Quick Categories</h2>
      <div className="categories-container">
        {categories.map((category) => (
          <button
            key={category.id}
            className="category-btn"
            onClick={() => handleCategoryClick(category)}
            style={{
              '--category-color': category.color || '#FF6B35',
              '--category-hover-color': `${category.color}CC` || '#FF6B35CC'
            }}
          >
            <div className="category-icon">
              {category.icon ? (
                <i className={category.icon}></i>
              ) : (
                <span>🍕</span>
              )}
            </div>
            <div className="category-info">
              <span className="category-name">{category.name}</span>
              {category.restaurant_count > 0 && (
                <span className="restaurant-count">
                  {category.restaurant_count} {category.restaurant_count === 1 ? 'place' : 'places'}
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
};

export default QuickCategories;