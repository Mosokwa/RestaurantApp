import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useLocation } from 'react-router-dom';
import { 
  fetchMenuItems, 
  fetchMenuAnalytics,
  createMenuItem,
  updateMenuItem,
  deleteMenuItem,
  setSelectedItems
} from '../store/slices/menuSlice';
import { 
  Plus, 
  Utensils, 
  Filter,
  Search,
  TrendingUp,
  DollarSign,
  Star,
  Clock,
  Edit,
  Trash2,
  Eye,
  Tag
} from 'lucide-react';
import CreateItemModal from '../components/menu/CreateItemModal';
import ItemAnalyticsModal from '../components/menu/ItemAnalyticsModal';
import './styles/ItemsPage.css';

const ItemsPage = () => {
  const dispatch = useDispatch();
  const location = useLocation();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { 
    menuItems, 
    analytics, 
    categories,
    loading 
  } = useSelector(state => state.menu);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [editingItem, setEditingItem] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popularity');

  // Get category from navigation state
  const navigationCategory = location.state?.categoryId;

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchMenuItems({ restaurantId: currentRestaurant.restaurant_id }));
      dispatch(fetchMenuAnalytics({ 
        restaurantId: currentRestaurant.restaurant_id, 
        days: 30 
      }));
    }
  }, [dispatch, currentRestaurant]);

  useEffect(() => {
    if (navigationCategory) {
      setSelectedCategory(navigationCategory);
    }
  }, [navigationCategory]);

  const handleCreateItem = (itemData) => {
    dispatch(createMenuItem(itemData)).then(() => {
      setShowCreateModal(false);
    });
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setShowCreateModal(true);
  };

  const handleUpdateItem = (itemData) => {
    dispatch(updateMenuItem({
      id: editingItem.item_id,
      itemData
    })).then(() => {
      setShowCreateModal(false);
      setEditingItem(null);
    });
  };

  const handleDeleteItem = (itemId) => {
    if (window.confirm('Are you sure you want to delete this menu item?')) {
      dispatch(deleteMenuItem(itemId));
    }
  };

  const handleViewAnalytics = (item) => {
    setSelectedItem(item);
    setShowAnalyticsModal(true);
  };

  // Filter and sort items
  const filteredItems = menuItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || 
                           item.category.category_id.toString() === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  const sortedItems = [...filteredItems].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'price':
        return b.price - a.price;
      case 'popularity':
        return (b.popularity_score || 0) - (a.popularity_score || 0);
      case 'recent':
        return new Date(b.created_at) - new Date(a.created_at);
      default:
        return 0;
    }
  });

  const getItemAnalytics = (itemId) => {
    if (!analytics?.item_performance) return null;
    return analytics.item_performance.find(item => item.item_id === itemId);
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.category_id === categoryId);
    return category?.name || 'Uncategorized';
  };

  if (!currentRestaurant) {
    return (
      <div className="items-container">
        <div className="no-restaurant-glass">
          <Utensils size={48} className="icon-muted" />
          <h2>No Restaurant Selected</h2>
          <p>Please select a restaurant to manage menu items</p>
        </div>
      </div>
    );
  }

  return (
    <div className="items-container">
      {/* Header */}
      <div className="items-header-glass">
        <div className="header-content">
          <div className="header-title">
            <Utensils className="header-icon" />
            <div>
              <h1>Menu Items</h1>
              <p>Manage your restaurant's menu items and offerings</p>
            </div>
          </div>
          
          <button 
            className="btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={18} />
            Add Item
          </button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="filters-glass">
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
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="filter-select"
            >
              <option value="popularity">Sort by Popularity</option>
              <option value="name">Sort by Name</option>
              <option value="price">Sort by Price</option>
              <option value="recent">Sort by Recent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Analytics Overview */}
      <div className="items-analytics-glass">
        <div className="analytics-grid">
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
            <div className="stat-icon revenue">
              <DollarSign size={20} />
            </div>
            <div className="stat-content">
              <h3>Active Items</h3>
              <p className="stat-value">
                {menuItems.filter(item => item.is_available).length}
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon popular">
              <TrendingUp size={20} />
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
          
          <div className="stat-card">
            <div className="stat-icon rating">
              <Star size={20} />
            </div>
            <div className="stat-content">
              <h3>Featured</h3>
              <p className="stat-value">
                {menuItems.filter(item => item.is_featured).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Items Grid */}
      <div className="items-grid-glass">
        <div className="grid-header">
          <h3>Menu Items ({sortedItems.length})</h3>
          <div className="view-options">
            <span className="items-count">
              Showing {sortedItems.length} of {menuItems.length} items
            </span>
          </div>
        </div>
        
        <div className="items-list">
          {sortedItems.map(item => {
            const itemAnalytics = getItemAnalytics(item.item_id);
            
            return (
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
                        <span className="category-tag" style={{ 
                          backgroundColor: item.category.display_color + '20',
                          color: item.category.display_color 
                        }}>
                          {item.category.name}
                        </span>
                        <span className="item-type">{item.item_type}</span>
                      </div>
                    </div>
                    
                    <div className="item-price">
                      ${parseFloat(item.price).toFixed(2)}
                    </div>
                  </div>
                  
                  <div className="item-stats">
                    <div className="stat">
                      <TrendingUp size={14} />
                      <span>Popularity: {item.popularity_score || 0}</span>
                    </div>
                    <div className="stat">
                      <Clock size={14} />
                      <span>{item.preparation_time}min</span>
                    </div>
                    {itemAnalytics && (
                      <div className="stat">
                        <DollarSign size={14} />
                        <span>Sold: {itemAnalytics.quantity_sold || 0}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="item-actions">
                    <button 
                      className="action-btn secondary"
                      onClick={() => handleViewAnalytics(item)}
                    >
                      <Eye size={16} />
                      Analytics
                    </button>
                    <button 
                      className="action-btn"
                      onClick={() => handleEditItem(item)}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="action-btn danger"
                      onClick={() => handleDeleteItem(item.item_id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        
        {sortedItems.length === 0 && (
          <div className="empty-state">
            <Utensils size={48} className="empty-icon" />
            <h3>No Menu Items Found</h3>
            <p>
              {searchTerm || selectedCategory !== 'all' 
                ? 'Try adjusting your search or filters'
                : 'Create your first menu item to get started'
              }
            </p>
            {(searchTerm || selectedCategory !== 'all') ? (
              <button 
                className="btn-secondary"
                onClick={() => {
                  setSearchTerm('');
                  setSelectedCategory('all');
                }}
              >
                Clear Filters
              </button>
            ) : (
              <button 
                className="btn-primary"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={18} />
                Create Item
              </button>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateItemModal
          item={editingItem}
          categories={categories}
          onSubmit={editingItem ? handleUpdateItem : handleCreateItem}
          onClose={() => {
            setShowCreateModal(false);
            setEditingItem(null);
          }}
        />
      )}

      {showAnalyticsModal && selectedItem && (
        <ItemAnalyticsModal
          item={selectedItem}
          analytics={getItemAnalytics(selectedItem.item_id)}
          onClose={() => {
            setShowAnalyticsModal(false);
            setSelectedItem(null);
          }}
        />
      )}
    </div>
  );
};

export default ItemsPage;