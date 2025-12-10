import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  fetchCategories, 
  fetchCategoryAnalytics,
  createCategory,
  updateCategory,
  deleteCategory,
  setSelectedCategory
} from '../store/slices/menuSlice';
import { 
  Plus, 
  FolderOpen, 
  TrendingUp, 
  DollarSign,
  ShoppingCart,
  Star,
  MoreVertical,
  Edit,
  Trash2
} from 'lucide-react';
import CreateCategoryModal from '../components/menu/CreateCategoryModal';
import './styles/CategoriesPage.css';

const CategoriesPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { 
    categories, 
    categoryAnalytics, 
    loading, 
    selectedCategory 
  } = useSelector(state => state.menu);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchCategories(currentRestaurant.restaurant_id));
      dispatch(fetchCategoryAnalytics(currentRestaurant.restaurant_id));
    }
  }, [dispatch, currentRestaurant]);

  const handleCreateCategory = (categoryData) => {
    dispatch(createCategory({
      ...categoryData,
      restaurant: currentRestaurant.restaurant_id
    })).then(() => {
      setShowCreateModal(false);
    });
  };

  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setShowCreateModal(true);
  };

  const handleUpdateCategory = (categoryData) => {
    dispatch(updateCategory({
      id: editingCategory.category_id,
      categoryData
    })).then(() => {
      setShowCreateModal(false);
      setEditingCategory(null);
    });
  };

  const handleDeleteCategory = (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category? This will also remove all items in this category.')) {
      dispatch(deleteCategory(categoryId));
    }
  };

  const handleSelectCategory = (category) => {
    dispatch(setSelectedCategory(category));
    // Navigate to items page with category filter
    navigate('/owner/menu/items', { state: { categoryId: category.category_id } });
  };

  const getCategoryStats = (categoryId) => {
    if (!categoryAnalytics) return null;
    return categoryAnalytics.find(cat => cat.category_id === categoryId);
  };

  if (!currentRestaurant) {
    return (
      <div className="categories-container">
        <div className="no-restaurant-glass">
          <FolderOpen size={48} className="icon-muted" />
          <h2>No Restaurant Selected</h2>
          <p>Please select a restaurant to manage categories</p>
        </div>
      </div>
    );
  }

  return (
    <div className="categories-container">
      {/* Header */}
      <div className="categories-header-glass">
        <div className="header-content">
          <div className="header-title">
            <FolderOpen className="header-icon" />
            <div>
              <h1>Menu Categories</h1>
              <p>Manage your menu categories and organization</p>
            </div>
          </div>
          
          <button 
            className="btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={18} />
            Add Category
          </button>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="analytics-overview-glass">
        <div className="analytics-grid">
          <div className="stat-card">
            <div className="stat-icon revenue">
              <DollarSign size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Categories</h3>
              <p className="stat-value">{categories.length}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon orders">
              <ShoppingCart size={20} />
            </div>
            <div className="stat-content">
              <h3>Active Items</h3>
              <p className="stat-value">
                {categoryAnalytics?.reduce((sum, cat) => sum + cat.active_items, 0) || 0}
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon growth">
              <TrendingUp size={20} />
            </div>
            <div className="stat-content">
              <h3>Top Category</h3>
              <p className="stat-value">
                {categoryAnalytics?.[0]?.name || 'N/A'}
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon rating">
              <Star size={20} />
            </div>
            <div className="stat-content">
              <h3>Avg Rating</h3>
              <p className="stat-value">
                {categoryAnalytics?.length ? 
                  (categoryAnalytics.reduce((sum, cat) => sum + (cat.avg_rating || 0), 0) / categoryAnalytics.length).toFixed(1) 
                  : '0.0'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="categories-grid-glass">
        <div className="grid-header">
          <h3>All Categories</h3>
          <span className="items-count">{categories.length} categories</span>
        </div>
        
        <div className="categories-list">
          {categories.map(category => {
            const stats = getCategoryStats(category.category_id);
            
            return (
              <div key={category.category_id} className="category-card">
                <div className="category-header">
                  <div className="category-color" style={{ backgroundColor: category.display_color }}></div>
                  <div className="category-info">
                    <h4 className="category-name">{category.name}</h4>
                    <p className="category-description">{category.description}</p>
                  </div>
                  <div className="category-actions">
                    <button 
                      className="action-btn"
                      onClick={() => handleEditCategory(category)}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="action-btn danger"
                      onClick={() => handleDeleteCategory(category.category_id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="category-stats">
                  <div className="stat">
                    <span className="stat-label">Items</span>
                    <span className="stat-value">{stats?.active_items || 0}</span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Revenue</span>
                    <span className="stat-value">
                      ${stats ? (stats.revenue_30d / 100).toFixed(0) : '0'}
                    </span>
                  </div>
                  <div className="stat">
                    <span className="stat-label">Rating</span>
                    <span className="stat-value">{stats?.avg_rating?.toFixed(1) || '0.0'}</span>
                  </div>
                </div>
                
                <div className="category-footer">
                  <button 
                    className="view-items-btn"
                    onClick={() => handleSelectCategory(category)}
                  >
                    View Items
                  </button>
                  <div className="performance-badge">
                    {stats?.performance_score >= 80 ? 'High' : 
                     stats?.performance_score >= 60 ? 'Medium' : 'Low'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {categories.length === 0 && (
          <div className="empty-state">
            <FolderOpen size={48} className="empty-icon" />
            <h3>No Categories Yet</h3>
            <p>Create your first category to start organizing your menu</p>
            <button 
              className="btn-primary"
              onClick={() => setShowCreateModal(true)}
            >
              <Plus size={18} />
              Create Category
            </button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <CreateCategoryModal
          category={editingCategory}
          onSubmit={editingCategory ? handleUpdateCategory : handleCreateCategory}
          onClose={() => {
            setShowCreateModal(false);
            setEditingCategory(null);
          }}
        />
      )}
    </div>
  );
};

export default CategoriesPage;