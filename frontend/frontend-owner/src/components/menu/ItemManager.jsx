import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  Utensils,
  Eye,
  EyeOff,
  Star,
  Filter,
  Search,
  Clock,
  DollarSign
} from 'lucide-react';
import { 
  fetchMenuItems,
  createMenuItem,
  updateMenuItem,
  deleteMenuItem,
  fetchCategories
} from '../../store/slices/menuSlice';
import './styles/ItemManager.css';

const ItemManager = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { menuItems, categories, loading } = useSelector(state => state.menu);
  
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [availabilityFilter, setAvailabilityFilter] = useState('all');

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    item_type: 'main',
    preparation_time: 15,
    calories: '',
    is_vegetarian: false,
    is_vegan: false,
    is_gluten_free: false,
    is_spicy: false,
    is_featured: false,
    is_available: true,
    display_order: 0
  });

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchMenuItems({ restaurantId: currentRestaurant.restaurant_id }));
      dispatch(fetchCategories(currentRestaurant.restaurant_id));
    }
  }, [dispatch, currentRestaurant]);

  // Filter items
  const filteredItems = menuItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || 
                           item.category.category_id.toString() === selectedCategory;
    const matchesAvailability = availabilityFilter === 'all' || 
                               (availabilityFilter === 'available' && item.is_available) ||
                               (availabilityFilter === 'unavailable' && !item.is_available);
    
    return matchesSearch && matchesCategory && matchesAvailability;
  });

  const handleCreateItem = () => {
    setEditingItem(null);
    setFormData({
      name: '',
      description: '',
      price: '',
      category: categories[0]?.category_id || '',
      item_type: 'main',
      preparation_time: 15,
      calories: '',
      is_vegetarian: false,
      is_vegan: false,
      is_gluten_free: false,
      is_spicy: false,
      is_featured: false,
      is_available: true,
      display_order: menuItems.length
    });
    setShowForm(true);
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setFormData({
      name: item.name,
      description: item.description || '',
      price: item.price.toString(),
      category: item.category.category_id,
      item_type: item.item_type,
      preparation_time: item.preparation_time,
      calories: item.calories?.toString() || '',
      is_vegetarian: item.is_vegetarian,
      is_vegan: item.is_vegan,
      is_gluten_free: item.is_gluten_free,
      is_spicy: item.is_spicy,
      is_featured: item.is_featured,
      is_available: item.is_available,
      display_order: item.display_order
    });
    setShowForm(true);
  };

  const handleSaveItem = () => {
    if (!formData.name.trim() || !formData.price || !formData.category) {
      alert('Name, price, and category are required');
      return;
    }

    const itemData = {
      ...formData,
      price: parseFloat(formData.price),
      calories: formData.calories ? parseInt(formData.calories) : null,
      category: parseInt(formData.category)
    };

    if (editingItem) {
      dispatch(updateMenuItem({
        id: editingItem.item_id,
        itemData
      }));
    } else {
      dispatch(createMenuItem(itemData));
    }

    setShowForm(false);
    setEditingItem(null);
  };

  const handleDeleteItem = (itemId) => {
    if (window.confirm('Are you sure you want to delete this menu item?')) {
      dispatch(deleteMenuItem(itemId));
    }
  };

  const handleToggleAvailability = (item) => {
    dispatch(updateMenuItem({
      id: item.item_id,
      itemData: {
        ...item,
        is_available: !item.is_available
      }
    }));
  };

  const handleToggleFeatured = (item) => {
    dispatch(updateMenuItem({
      id: item.item_id,
      itemData: {
        ...item,
        is_featured: !item.is_featured
      }
    }));
  };

  const handleViewAnalytics = (item) => {
    navigate('/owner/items', { state: { itemId: item.item_id } });
  };

  const itemTypes = [
    { value: 'main', label: 'Main Dish' },
    { value: 'beverage', label: 'Beverage' },
    { value: 'dessert', label: 'Dessert' },
    { value: 'side', label: 'Side Dish' },
    { value: 'combo', label: 'Combo Meal' }
  ];

  return (
    <div className="item-manager">
      {/* Header */}
      <div className="item-header">
        <div className="header-content">
          <div className="header-info">
            <Utensils className="header-icon" />
            <div>
              <h2>Menu Items</h2>
              <p>Manage your restaurant's menu items and offerings</p>
            </div>
          </div>
          <button 
            className="btn-primary"
            onClick={handleCreateItem}
          >
            <Plus size={18} />
            Add Item
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="item-filters-glass">
        <div className="filters-content">
          <div className="search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <select 
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category.category_id} value={category.category_id}>
                  {category.name}
                </option>
              ))}
            </select>
            
            <select 
              value={availabilityFilter}
              onChange={(e) => setAvailabilityFilter(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Items</option>
              <option value="available">Available</option>
              <option value="unavailable">Unavailable</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="item-stats-glass">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon total">
              <Utensils size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Items</h3>
              <p className="stat-value">{menuItems.length}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon active">
              <Eye size={20} />
            </div>
            <div className="stat-content">
              <h3>Available</h3>
              <p className="stat-value">
                {menuItems.filter(item => item.is_available).length}
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
                {menuItems.filter(item => item.is_featured).length}
              </p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon revenue">
              <DollarSign size={20} />
            </div>
            <div className="stat-content">
              <h3>Avg Price</h3>
              <p className="stat-value">
                ${menuItems.length ? 
                  (menuItems.reduce((sum, item) => sum + parseFloat(item.price), 0) / menuItems.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Items Grid */}
      <div className="items-grid-glass">
        <div className="grid-header">
          <h3>Menu Items ({filteredItems.length})</h3>
          <span className="items-count">
            Showing {filteredItems.length} of {menuItems.length} items
          </span>
        </div>

        <div className="items-grid">
          {filteredItems.map(item => (
            <div key={item.item_id} className="item-card">
              <div className="item-image">
                {item.image ? (
                  <img src={item.image} alt={item.name} />
                ) : (
                  <div className="image-placeholder">
                    <Utensils size={24} />
                  </div>
                )}
                <div className="item-badges">
                  {item.is_featured && <span className="badge featured">Featured</span>}
                  {!item.is_available && <span className="badge unavailable">Unavailable</span>}
                  {item.is_vegetarian && <span className="badge vegetarian">Vegetarian</span>}
                  {item.is_spicy && <span className="badge spicy">Spicy</span>}
                </div>
              </div>
              
              <div className="item-content">
                <div className="item-header">
                  <div className="item-info">
                    <h4 className="item-name">{item.name}</h4>
                    <p className="item-description">{item.description}</p>
                    <div className="item-meta">
                      <span 
                        className="category-tag" 
                        style={{ 
                          backgroundColor: item.category.display_color + '20',
                          color: item.category.display_color 
                        }}
                      >
                        {item.category.name}
                      </span>
                      <span className="item-type">{item.item_type}</span>
                    </div>
                  </div>
                  
                  <div className="item-price">
                    ${parseFloat(item.price).toFixed(2)}
                  </div>
                </div>
                
                <div className="item-details">
                  <div className="detail">
                    <Clock size={14} />
                    <span>{item.preparation_time}min</span>
                  </div>
                  {item.calories && (
                    <div className="detail">
                      <span>🔥 {item.calories} cal</span>
                    </div>
                  )}
                  <div className="detail">
                    <Star size={14} />
                    <span>{item.popularity_score || 0}</span>
                  </div>
                </div>
                
                <div className="item-actions">
                  <button 
                    className="action-btn"
                    onClick={() => handleToggleAvailability(item)}
                    title={item.is_available ? 'Mark Unavailable' : 'Mark Available'}
                  >
                    {item.is_available ? <Eye size={16} /> : <EyeOff size={16} />}
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handleToggleFeatured(item)}
                    title={item.is_featured ? 'Remove Featured' : 'Mark Featured'}
                  >
                    <Star size={16} className={item.is_featured ? 'featured' : ''} />
                  </button>
                  <button 
                    className="action-btn"
                    onClick={() => handleEditItem(item)}
                    title="Edit Item"
                  >
                    <Edit size={16} />
                  </button>
                  <button 
                    className="action-btn danger"
                    onClick={() => handleDeleteItem(item.item_id)}
                    title="Delete Item"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}

          {filteredItems.length === 0 && (
            <div className="empty-state">
              <Utensils size={48} className="empty-icon" />
              <h3>No Menu Items Found</h3>
              <p>
                {searchTerm || selectedCategory !== 'all' || availabilityFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Create your first menu item to get started'
                }
              </p>
              {(searchTerm || selectedCategory !== 'all' || availabilityFilter !== 'all') ? (
                <button 
                  className="btn-secondary"
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedCategory('all');
                    setAvailabilityFilter('all');
                  }}
                >
                  Clear Filters
                </button>
              ) : (
                <button 
                  className="btn-primary"
                  onClick={handleCreateItem}
                >
                  <Plus size={18} />
                  Create Item
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Item Form Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-glass large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingItem ? 'Edit Menu Item' : 'Create Menu Item'}</h3>
              <button 
                className="close-btn"
                onClick={() => setShowForm(false)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="form-row">
                <div className="form-group">
                  <label>Item Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g., Margherita Pizza, Caesar Salad"
                  />
                </div>

                <div className="form-group">
                  <label>Price *</label>
                  <div className="price-input">
                    <span className="currency-symbol">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.price}
                      onChange={(e) => setFormData({...formData, price: e.target.value})}
                      placeholder="0.00"
                    />
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="Describe your menu item..."
                  rows="3"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({...formData, category: e.target.value})}
                  >
                    <option value="">Select a category</option>
                    {categories.map(category => (
                      <option key={category.category_id} value={category.category_id}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Item Type</label>
                  <select
                    value={formData.item_type}
                    onChange={(e) => setFormData({...formData, item_type: e.target.value})}
                  >
                    {itemTypes.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Preparation Time (minutes)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.preparation_time}
                    onChange={(e) => setFormData({...formData, preparation_time: parseInt(e.target.value) || 15})}
                  />
                </div>

                <div className="form-group">
                  <label>Calories</label>
                  <input
                    type="number"
                    min="0"
                    value={formData.calories}
                    onChange={(e) => setFormData({...formData, calories: e.target.value})}
                    placeholder="Optional"
                  />
                </div>
              </div>

              <div className="form-section">
                <h4>Dietary Information</h4>
                <div className="checkbox-grid">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_vegetarian}
                      onChange={(e) => setFormData({...formData, is_vegetarian: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Vegetarian
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_vegan}
                      onChange={(e) => setFormData({...formData, is_vegan: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Vegan
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_gluten_free}
                      onChange={(e) => setFormData({...formData, is_gluten_free: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Gluten Free
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_spicy}
                      onChange={(e) => setFormData({...formData, is_spicy: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Spicy
                  </label>
                </div>
              </div>

              <div className="form-section">
                <h4>Display Settings</h4>
                <div className="checkbox-grid">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_available}
                      onChange={(e) => setFormData({...formData, is_available: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Available for ordering
                  </label>
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={formData.is_featured}
                      onChange={(e) => setFormData({...formData, is_featured: e.target.checked})}
                    />
                    <span className="checkmark"></span>
                    Featured item
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>Display Order</label>
                <input
                  type="number"
                  min="0"
                  value={formData.display_order}
                  onChange={(e) => setFormData({...formData, display_order: parseInt(e.target.value) || 0})}
                />
                <small>Lower numbers appear first in the category</small>
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
                onClick={handleSaveItem}
              >
                <Save size={16} />
                {editingItem ? 'Update Item' : 'Create Item'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ItemManager;