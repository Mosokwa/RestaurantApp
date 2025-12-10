import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  fetchCategories, 
  fetchMenuItems, 
  createCategory,
  createMenuItem,
  clearError 
} from '../store/slices/menuSlice';
import { 
  Plus, 
  Utensils, 
  FolderOpen, 
  Tags,
  BarChart3,
  Search,
  Filter
} from 'lucide-react';
import CategoryManager from '../components/menu/CategoryManager';
import ItemManager from '../components/menu/ItemManager';
import ModifierManager from '../components/menu/ModifierManager';
import MenuAnalytics from '../components/menu/MenuAnalytics';
import './styles/MenuManagement.css';

const MenuBuilderPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { categories, menuItems, loading, error } = useSelector(state => state.menu);
  
  const [activeTab, setActiveTab] = useState('categories');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchCategories(currentRestaurant.restaurant_id));
      dispatch(fetchMenuItems({ restaurantId: currentRestaurant.restaurant_id }));
    }
  }, [dispatch, currentRestaurant]);

  useEffect(() => {
    if (error) {
      // Auto clear error after 5 seconds
      const timer = setTimeout(() => {
        dispatch(clearError());
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, dispatch]);

  if (!currentRestaurant) {
    return (
      <div className="menu-management-container">
        <div className="no-restaurant-glass">
          <Utensils size={48} className="icon-muted" />
          <h2>No Restaurant Selected</h2>
          <p>Please select a restaurant to manage its menu</p>
          <button 
            className="btn-primary"
            onClick={() => navigate('/owner/restaurants')}
          >
            Select Restaurant
          </button>
        </div>
      </div>
    );
  }

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'categories':
        return <CategoryManager />;
      case 'items':
        return <ItemManager />;
      case 'modifiers':
        return <ModifierManager />;
      case 'analytics':
        return <MenuAnalytics />;
      default:
        return <CategoryManager />;
    }
  };

  return (
    <div className="menu-management-container">
      {/* Header */}
      <div className="menu-header-glass">
        <div className="header-content">
          <div className="header-title">
            <Utensils className="header-icon" />
            <div>
              <h1>Menu Management</h1>
              <p>{currentRestaurant.name}</p>
            </div>
          </div>
          
          <div className="header-actions">
            <div className="search-box">
              <Search size={18} />
              <input
                type="text"
                placeholder="Search menu..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="btn-secondary">
              <Filter size={18} />
              Filter
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="tabs-container-glass">
        <div className="tabs-navigation">
          <button
            className={`tab-btn ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}
          >
            <FolderOpen size={18} />
            Categories
            <span className="tab-badge">{categories.length}</span>
          </button>
          
          <button
            className={`tab-btn ${activeTab === 'items' ? 'active' : ''}`}
            onClick={() => setActiveTab('items')}
          >
            <Utensils size={18} />
            Menu Items
            <span className="tab-badge">{menuItems.length}</span>
          </button>
          
          <button
            className={`tab-btn ${activeTab === 'modifiers' ? 'active' : ''}`}
            onClick={() => setActiveTab('modifiers')}
          >
            <Tags size={18} />
            Modifiers
          </button>
          
          <button
            className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
            onClick={() => setActiveTab('analytics')}
          >
            <BarChart3 size={18} />
            Analytics
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-glass">
          <div className="error-content">
            <span className="error-message">{error}</span>
            <button 
              className="error-close"
              onClick={() => dispatch(clearError())}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Loading menu data...</p>
        </div>
      )}

      {/* Main Content */}
      <div className="menu-content-glass">
        {renderActiveTab()}
      </div>
    </div>
  );
};

export default MenuBuilderPage;