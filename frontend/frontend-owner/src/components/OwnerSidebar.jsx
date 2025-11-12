import { useEffect, useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  ShoppingCart,
  Utensils,
  BarChart3,
  Users,
  Settings,
  Megaphone,
  ChevronRight,
  ChefHat,
  X,
  Plus,
  Building,
  FileText,
  BarChart,
  Globe
} from 'lucide-react';
import { extractDataFromResponse } from '../utils/paginationUtils';
import './styles/OwnerSidebar.css';

const OwnerSidebar = ({ isOpen, onToggle, isMobile }) => {
  const navigate = useNavigate();
  const location = useLocation();
  // Get real-time orders data from Redux store and auth state
  const { realTimeOrders } = useSelector(state => state.dashboard);
  const { currentRestaurant, restaurants } = useSelector(state => state.ownerAuth);
  const [expandedMenus, setExpandedMenus] = useState(new Set());
  
  useEffect(() => {
    // Add/remove body class for mobile scroll prevention
    if (isMobile && isOpen) {
      document.body.classList.add('sidebar-open-mobile');
    } else {
      document.body.classList.remove('sidebar-open-mobile');
    }

    return () => {
      document.body.classList.remove('sidebar-open-mobile');
    };
  }, [isMobile, isOpen]);

  // Calculate pending orders count (only when restaurant is selected)
  const getPendingOrdersCount = () => {
    if (!currentRestaurant) return 0;
    
    const ordersList = extractDataFromResponse(realTimeOrders);
    if (!Array.isArray(ordersList)) return 0;
    
    return ordersList.filter(order => 
      ['pending', 'confirmed', 'preparing'].includes(order?.status)
    ).length;
  };

  const pendingOrdersCount = getPendingOrdersCount();

  // Menu items when NO restaurant is selected
  const noRestaurantMenuItems = useMemo(() => [
    { 
      id: 'overview', 
      label: 'Business Overview', 
      icon: BarChart,
      path: '/owner/dashboard'
    },
    { 
      id: 'restaurants', 
      label: 'My Restaurants', 
      icon: Building,
      path: '/owner/restaurants'
    },
    { 
      id: 'create-restaurant', 
      label: 'Add New Restaurant', 
      icon: Plus,
      path: '/owner/restaurants/new'
    },
    { 
      id: 'business-analytics', 
      label: 'Business Analytics', 
      icon: BarChart3,
      children: [
        { id: 'performance', label: 'Performance Overview', path: '/owner/business/performance' },
        { id: 'comparison', label: 'Restaurant Comparison', path: '/owner/business/comparison' },
        { id: 'reports', label: 'Business Reports', path: '/owner/business/reports' }
      ]
    },
    { 
      id: 'account', 
      label: 'Account Management', 
      icon: Users,
      children: [
        { id: 'billing', label: 'Billing & Subscription', path: '/owner/account/billing' },
        { id: 'team', label: 'Team Members', path: '/owner/account/team' },
        { id: 'settings', label: 'Account Settings', path: '/owner/account/settings' }
      ]
    }
  ], []);

  // Menu items when a restaurant IS selected
  const restaurantMenuItems = useMemo(() => [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: LayoutDashboard,
      path: '/owner/dashboard', 
      badge: null 
    },
    { 
      id: 'orders', 
      label: 'Orders', 
      icon: ShoppingCart,
      path: '/owner/orders', 
      badge: pendingOrdersCount > 0 ? pendingOrdersCount : null 
    },
    { 
      id: 'menu', 
      label: 'Menu Management', 
      icon: Utensils, 
      children: [
        { id: 'menu-builder', label: 'Menu Builder', path: '/owner/menu/builder' },
        { id: 'categories', label: 'Categories', path: '/owner/menu/categories'},
        { id: 'items', label: 'Items', path: '/owner/menu/items'},
        { id: 'modifiers', label: 'Modifiers', path:'/owner/menu/modifiers' }
      ]
    },
    { 
      id: 'analytics', 
      label: 'Analytics & Reports', 
      icon: BarChart3,
      children: [
        { id: 'sales-analytics', label: 'Sales Analytics', path: '/owner/analytics/sales' },
        { id: 'customer-insights', label: 'Customer Insights', path: '/owner/analytics/customers' },
        { id: 'menu-performance', label: 'Menu Performance', path: '/owner/analytics/menu' },
        { id: 'export-reports', label: 'Export Reports', path: '/owner/analytics/reports' }
      ]
    },
    { 
      id: 'staff', 
      label: 'Staff Management', 
      icon: Users,
      children: [
        { id: 'team', label: 'Team', path: '/owner/staff/team' },
        { id: 'roles', label: 'Roles & Permissions', path: '/owner/staff/roles' },
        { id: 'schedules', label: 'Schedules', path: '/owner/staff/schedules' }
      ]
    },
    { 
      id: 'settings', 
      label: 'Restaurant Settings', 
      icon: Settings,
      children: [
        { id: 'basic-info', label: 'Basic Info', path: '/owner/settings/basic' },
        { id: 'branches', label: 'Branches', path: '/owner/settings/branches' },
        { id: 'hours', label: 'Operating Hours', path: '/owner/settings/hours' },
        { id: 'integrations', label: 'Integrations', path: '/owner/settings/integrations' }
      ]
    },
    { 
      id: 'marketing', 
      label: 'Marketing', 
      icon: Megaphone,
      children: [
        { id: 'homepage', label: 'My Restaurant Page', path: '/owner/marketing/homepage' },
        { id: 'offers', label: 'Special Offers', path: '/owner/marketing/offers' },
        { id: 'loyalty', label: 'Loyalty Program', path: '/owner/marketing/loyalty' },
        { id: 'communications', label: 'Customer Communications', path: '/owner/marketing/communications' }
      ]
    }
  ], [pendingOrdersCount]);

  // Choose which menu to display based on current restaurant
  const menuItems = currentRestaurant ? restaurantMenuItems : noRestaurantMenuItems;

  // Auto-expand parent menu when child is active - FIXED
  useEffect(() => {
    const activePath = location.pathname;
    const newExpanded = new Set(expandedMenus);
    
    let hasChanges = false;
    
    menuItems.forEach(item => {
      if (item.children) {
        const isChildActive = item.children.some(child => 
          child.path && activePath === child.path // Use exact match instead of startsWith
        );
        if (isChildActive && !newExpanded.has(item.id)) {
          newExpanded.add(item.id);
          hasChanges = true;
        } else if (!isChildActive && newExpanded.has(item.id)) {
          newExpanded.delete(item.id);
          hasChanges = true;
        }
      }
    });
    
    // Only update state if there are actual changes
    if (hasChanges) {
      setExpandedMenus(newExpanded);
    }
  }, [location.pathname, currentRestaurant?.restaurant_id]); // Fixed dependencies

  const handleNavigation = (path) => {
    if (path) {
      navigate(path);
      if (isMobile) {
        onToggle();
      }
    }
  };

  const toggleDropdown = (menuId) => {
    setExpandedMenus(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(menuId)) {
        newExpanded.delete(menuId);
      } else {
        newExpanded.add(menuId);
      }
      return newExpanded;
    });
  };

  const handleMenuClick = (item) => {
    if (item.children) {
      toggleDropdown(item.id);
      // Don't navigate if it's just a parent with children
      if (item.path && !item.children.some(child => child.path === location.pathname)) {
        handleNavigation(item.path);
      }
    } else {
      handleNavigation(item.path);
    }
  };

  // Determine if item is active
  const isActive = (item) => {
    if (item.path) {
      return location.pathname === item.path;
    }
    
    // For parent items, check if any child is active
    if (item.children) {
      return item.children.some(child => 
        child.path && location.pathname === child.path
      );
    }
    
    return false;
  };

  const isExpanded = (menuId) => {
    return expandedMenus.has(menuId);
  };

  const renderMenuItem = (item, level = 0) => {
    const Icon = item.icon;
    const active = isActive(item);
    const hasChildren = item.children && item.children.length > 0;
    const expanded = isExpanded(item.id);

    return (
      <div key={item.id}>
        <button
          onClick={() => handleMenuClick(item)}
          className={`menu-item ${active ? 'active' : ''} ${level > 0 ? 'nested' : ''}`}
        >
          <div className="menu-item-content">
            {Icon && <Icon className="menu-icon" size={18} />}
            {isOpen && <span className="menu-label">{item.label}</span>}
          </div>
          
          <div className="menu-item-badges">
            {item.badge !== null && item.badge > 0 && (
              <span className="badge">{item.badge}</span>
            )}
            {hasChildren && isOpen && (
              <ChevronRight className={`chevron ${expanded ? 'expanded' : ''}`} size={16} />
            )}
          </div>
        </button>

        {hasChildren && expanded && isOpen && (
          <div className="child-menu">
            {item.children.map(child => renderMenuItem({ ...child, icon: null }, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Calculate stats for sidebar footer
  const getFooterStats = () => {
    if (currentRestaurant) {
      // Restaurant-specific stats
      const ordersList = extractDataFromResponse(realTimeOrders);
      const activeOrdersCount = Array.isArray(ordersList) 
        ? ordersList.filter(order => order?.status === 'preparing')?.length || 0
        : 0;

      return {
        primaryLabel: "Active Orders",
        primaryValue: pendingOrdersCount,
        secondaryLabel: "In Kitchen",
        secondaryValue: activeOrdersCount
      };
    } else {
      // Business overview stats
      const totalRestaurants = restaurants.length;
      const activeRestaurants = restaurants.filter(r => r.is_active).length;

      return {
        primaryLabel: "Total Restaurants",
        primaryValue: totalRestaurants,
        secondaryLabel: "Active",
        secondaryValue: activeRestaurants
      };
    }
  };

  const footerStats = getFooterStats();

  return (
    <>
      <aside className={`owner-sidebar ${isOpen ? 'open' : 'closed'} ${isMobile ? 'mobile' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon">
              {currentRestaurant ? <ChefHat size={20} /> : <Building size={20} />}
            </div>
            {isOpen && (
              <div className="logo-text">
                <h1 className="logo-title">RestaurantOS</h1>
                <p className="logo-subtitle">
                  {currentRestaurant ? currentRestaurant.name : 'Business Portal'}
                </p>
              </div>
            )}
          </div>
          
          {isMobile && isOpen && (
            <button className="close-sidebar" onClick={onToggle}>
              <X size={20} />
            </button>
          )}
        </div>

        <nav className="sidebar-navigation">
          {menuItems.map(item => renderMenuItem(item))}
        </nav>

        {isOpen && (
          <div className="sidebar-footer">
            <p className="footer-title">
              {currentRestaurant ? 'Live Updates' : 'Business Overview'}
            </p>
            <div className="footer-stats">
              <div className="stat">
                <p className="stat-label">{footerStats.primaryLabel}</p>
                <p className="stat-value">{footerStats.primaryValue}</p>
              </div>
              <div className="stat">
                <p className="stat-label">{footerStats.secondaryLabel}</p>
                <p className="stat-value">{footerStats.secondaryValue}</p>
              </div>
            </div>
            
            {/* Quick action button */}
            {!currentRestaurant && restaurants.length === 0 && (
              <button 
                className="quick-action-btn"
                onClick={() => navigate('/owner/restaurants/new')}
              >
                <Plus size={16} />
                Create Your First Restaurant
              </button>
            )}
          </div>
        )}
      </aside>
    </>
  );
};

export default OwnerSidebar;