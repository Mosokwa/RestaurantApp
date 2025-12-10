import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  FolderOpen,
  Eye,
  EyeOff,
  Star,
  MoreVertical
} from 'lucide-react';
import { 
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  fetchMenuItems
} from '../../store/slices/menuSlice';
import './styles/CategoryManager.css';

const CategoryManager = () => {
  const dispatch = useDispatch();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { categories, menuItems, loading } = useSelector(state => state.menu);
  
  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    display_order: 0,
    is_active: true,
    is_featured: false,
    display_color: '#FF6B35'
  });

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchCategories(currentRestaurant.restaurant_id));
      dispatch(fetchMenuItems({ restaurantId: currentRestaurant.restaurant_id }));
    }
  }, [dispatch, currentRestaurant]);

  // Filter categories
  const filteredCategories = categories.filter(category =>
    category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    category.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getItemsCount = (categoryId) => {
    return menuItems.filter(item => item.category.category_id === categoryId).length;
  };

  const getActiveItemsCount = (categoryId) => {
    return menuItems.filter(item => 
      item.category.category_id === categoryId && item.is_available
    ).length;
  };

  const handleCreateCategory = () => {
    setEditingCategory(null);
    setFormData({
      name: '',
      description: '',
      display_order: categories.length,
      is_active: true,
      is_featured: false,
      display_color: '#FF6B35'
    });
    setShowForm(true);
  };

  const handleEditCategory = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      display_order: category.display_order,
      is_active: category.is_active,
      is_featured: category.is_featured,
      display_color: category.display_color
    });
    setShowForm(true);
  };

  const handleSaveCategory = () => {
    if (!formData.name.trim()) {
      alert('Category name is required');
      return;
    }

    const categoryData = {
      ...formData,
      restaurant: currentRestaurant.restaurant_id
    };

    if (editingCategory) {
      dispatch(updateCategory({
        id: editingCategory.category_id,
        categoryData
      }));
    } else {
      dispatch(createCategory(categoryData));
    }

    setShowForm(false);
    setEditingCategory(null);
  };

  const handleDeleteCategory = (categoryId) => {
    const itemsCount = getItemsCount(categoryId);
    if (itemsCount > 0) {
      alert(`Cannot delete category with ${itemsCount} menu items. Please move or delete the items first.`);
      return;
    }

    if (window.confirm('Are you sure you want to delete this category?')) {
      dispatch(deleteCategory(categoryId));
    }
  };

  const handleToggleActive = (category) => {
    dispatch(updateCategory({
      id: category.category_id,
      categoryData: {
        ...category,
        is_active: !category.is_active
      }
    }));
  };

  const handleToggleFeatured = (category) => {
    dispatch(updateCategory({
      id: category.category_id,
      categoryData: {
        ...category,
        is_featured: !category.is_featured
      }
    }));
  };

  const colorOptions = [
    '#FF6B35', '#2EC4B6', '#E71D36', '#FF9F1C', '#662E9B',
    '#00A8E8', '#51CB20', '#FF4D80', '#7209B7', '#3A86FF'
  ];

  return (
    <div className="category-manager">
      {/* Header */}
      <div className="category-header">
        <div className="header-content">
          <div className="header-info">
            <FolderOpen className="header-icon" />
            <div>
              <h2>Menu Categories</h2>
              <p>Organize your menu with categories and sub-sections</p>
            </div>
          </div>
          <button 
            className="btn-primary"
            onClick={handleCreateCategory}
          >
            <Plus size={18} />
            Add Category
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="category-stats-glass">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon total">
              <FolderOpen size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Categories</h3>
              <p className="stat-value">{categories.length}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon active">
              <Eye size={20} />
            </div>
            <div className="stat-content">
              <h3>Active Categories</h3>
              <p className="stat-value">
                {categories.filter(cat => cat.is_active).length}
              </p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon featured">
              <Star size={20} />
            </div>
            <div className="stat-content">
              <h3>Featured</h3>
              <p className="stat-value">
                {categories.filter(cat => cat.is_featured).length}
              </p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon items">
              <FolderOpen size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Items</h3>
              <p className="stat-value">{menuItems.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="categories-grid-glass">
        <div className="grid-header">
          <h3>Categories ({filteredCategories.length})</h3>
          <div className="search-box">
            <input
              type="text"
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="categories-grid">
          {filteredCategories.map(category => (
            <div 
              key={category.category_id} 
              className="category-card"
              style={{ 
                borderLeftColor: category.display_color,
                background: `linear-gradient(135deg, ${category.display_color}20, ${category.display_color}08)`
              }}
            >
              <div className="category-header">
                <div className="category-color" style={{ backgroundColor: category.display_color }}></div>
                <div className="category-info">
                  <h4 className="category-name">{category.name}</h4>
                  {category.description && (
                    <p className="category-description">{category.description}</p>
                  )}
                  <div className="category-meta">
                    <span className="meta-item">
                      {getItemsCount(category.category_id)} items
                    </span>
                    <span className="meta-item">
                      {getActiveItemsCount(category.category_id)} active
                    </span>
                    <span className="meta-item">
                      Order: {category.display_order}
                    </span>
                  </div>
                </div>
                <div className="category-actions">
                  <div className="status-badges">
                    {!category.is_active && (
                      <span className="badge inactive">Hidden</span>
                    )}
                    {category.is_featured && (
                      <span className="badge featured">Featured</span>
                    )}
                  </div>
                  <div className="action-buttons">
                    <button 
                      className="action-btn"
                      onClick={() => handleToggleActive(category)}
                      title={category.is_active ? 'Hide Category' : 'Show Category'}
                    >
                      {category.is_active ? <Eye size={16} /> : <EyeOff size={16} />}
                    </button>
                    <button 
                      className="action-btn"
                      onClick={() => handleToggleFeatured(category)}
                      title={category.is_featured ? 'Remove Featured' : 'Mark Featured'}
                    >
                      <Star size={16} className={category.is_featured ? 'featured' : ''} />
                    </button>
                    <button 
                      className="action-btn"
                      onClick={() => handleEditCategory(category)}
                      title="Edit Category"
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="action-btn danger"
                      onClick={() => handleDeleteCategory(category.category_id)}
                      title="Delete Category"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Items Preview */}
              <div className="items-preview">
                <div className="preview-header">
                  <span>Menu Items</span>
                  <span className="items-count">
                    {getItemsCount(category.category_id)} items
                  </span>
                </div>
                <div className="items-list">
                  {menuItems
                    .filter(item => item.category.category_id === category.category_id)
                    .slice(0, 3)
                    .map(item => (
                      <div key={item.item_id} className="preview-item">
                        <span className="item-name">{item.name}</span>
                        <span className="item-price">${parseFloat(item.price).toFixed(2)}</span>
                        {!item.is_available && (
                          <span className="item-status unavailable">Unavailable</span>
                        )}
                      </div>
                    ))
                  }
                  {getItemsCount(category.category_id) > 3 && (
                    <div className="more-items">
                      +{getItemsCount(category.category_id) - 3} more items
                    </div>
                  )}
                  {getItemsCount(category.category_id) === 0 && (
                    <div className="no-items">
                      No items in this category
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {filteredCategories.length === 0 && (
            <div className="empty-state">
              <FolderOpen size={48} className="empty-icon" />
              <h3>No Categories Found</h3>
              <p>
                {searchTerm 
                  ? 'Try adjusting your search terms'
                  : 'Create your first category to organize your menu'
                }
              </p>
              {!searchTerm && (
                <button 
                  className="btn-primary"
                  onClick={handleCreateCategory}
                >
                  <Plus size={18} />
                  Create Category
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Category Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingCategory ? 'Edit Category' : 'Create Category'}</h3>
              <button 
                className="close-btn"
                onClick={() => setShowForm(false)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="form-group">
                <label>Category Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Appetizers, Main Course, Desserts"
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Optional description for this category"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Display Order</label>
                <input
                  type="number"
                  min="0"
                  value={formData.display_order}
                  onChange={(e) => setFormData({...formData, display_order: parseInt(e.target.value) || 0})}
                />
                <small>Lower numbers appear first in the menu</small>
              </div>

              <div className="form-group">
                <label>Display Color</label>
                <div className="color-picker">
                  {colorOptions.map(color => (
                    <button
                      key={color}
                      className={`color-option ${formData.display_color === color ? 'selected' : ''}`}
                      style={{ backgroundColor: color }}
                      onClick={() => setFormData({...formData, display_color: color})}
                    />
                  ))}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Active (Visible to customers)
                  </label>
                </div>

                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({...formData, is_featured: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Featured Category
                  </label>
                </div>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowForm(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={handleSaveCategory}
              >
                <Save size={16} />
                {editingCategory ? 'Update Category' : 'Create Category'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManager;