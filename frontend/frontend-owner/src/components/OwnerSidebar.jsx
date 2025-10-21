import { useEffect, useState } from 'react';
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
  X
} from 'lucide-react';
import { extractDataFromResponse } from '../utils/paginationUtils';
import './styles/OwnerSidebar.css';

const OwnerSidebar = ({ isOpen, onToggle, isMobile }) => {
  const navigate = useNavigate();
  const location = useLocation();
  // Get real-time orders data from Redux store
  const { realTimeOrders } = useSelector(state => state.dashboard);
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

  // Calculate pending orders count
  const getPendingOrdersCount = () => {
    const ordersList = extractDataFromResponse(realTimeOrders);

    if (!Array.isArray(ordersList)) return 0;
    
    return ordersList.filter(order => 
      ['pending', 'confirmed', 'preparing'].includes(order?.status)
    ).length;
  };

  const pendingOrdersCount = getPendingOrdersCount();

  const menuItems = [
    { 
      id: 'dashboard', 
      label: 'Dashboard', 
      icon: LayoutDashboard,
      path: '/owner/dashboard', 
      badge: null },
    { 
      id: 'orders', 
      label: 'Orders', 
      icon: ShoppingCart,
      path: '/owner/orders', 
      badge: pendingOrdersCount > 0 ? pendingOrdersCount : null 
    },
    { 
      id: 'menu', label: 'Menu Management', icon: Utensils, 
      children: [
        { id: 'menu-builder', label: 'Menu Builder', path: '/owner/menu/builder' },
        { id: 'categories', label: 'Categories', path: '/owner/menu/categories'},
        { id: 'items', label: 'Items', path: '/owner/menu/items'},
        { id: 'modifiers', label: 'Modifiers', path:'/owner/menu/modifiers' }
      ]
    },
    { 
      id: 'analytics', label: 'Analytics & Reports', icon: BarChart3,
      children: [
        { id: 'sales-analytics', label: 'Sales Analytics', path: '/owner/analytics/sales' },
        { id: 'customer-insights', label: 'Customer Insights', path: '/owner/analytics/customers' },
        { id: 'menu-performance', label: 'Menu Performance', path: '/owner/analytics/menu' },
        { id: 'export-reports', label: 'Export Reports', path: '/owner/analytics/reports' }
      ]
    },
    { 
      id: 'staff', label: 'Staff Management', icon: Users,
      children: [
        { id: 'team', label: 'Team', path: '/owner/staff/team' },
        { id: 'roles', label: 'Roles & Permissions', path: '/owner/staff/roles' },
        { id: 'schedules', label: 'Schedules', path: '/owner/staff/schedules' }
      ]
    },
    { 
      id: 'settings', label: 'Restaurant Settings', icon: Settings,
      children: [
        { id: 'basic-info', label: 'Basic Info', path: '/owner/settings/basic' },
        { id: 'branches', label: 'Branches', path: '/owner/settings/branches' },
        { id: 'hours', label: 'Operating Hours', path: '/owner/settings/hours' },
        { id: 'integrations', label: 'Integrations', path: '/owner/settings/integrations' }
      ]
    },
    { 
      id: 'marketing', label: 'Marketing', icon: Megaphone,
      children: [
        { id: 'offers', label: 'Special Offers', path: '/owner/marketing/offers' },
        { id: 'loyalty', label: 'Loyalty Program', path: '/owner/marketing/loyalty' },
        { id: 'communications', label: 'Customer Communications', path: '/owner/marketing/communications' }
      ]
    }
  ];

  // Auto-expand parent menu when child is active (using original logic)
  useEffect(() => {
    const activePath = location.pathname;
    const newExpanded = new Set(expandedMenus);
    
    menuItems.forEach(item => {
      if (item.children) {
        const isChildActive = item.children.some(child => 
          child.path && activePath.startsWith(child.path.replace('/owner/', ''))
        );
        if (isChildActive) {
          newExpanded.add(item.id);
        }
      }
    });
    
    setExpandedMenus(newExpanded);
  }, [location.pathname]);

  const handleNavigation = (path) => {
    if (path) {
      navigate(path);
      if (isMobile) {
        onToggle();
      }
    }
  };

  const toggleDropdown = (menuId) => {
    const newExpanded = new Set(expandedMenus);
    if (newExpanded.has(menuId)) {
      newExpanded.delete(menuId);
    } else {
      newExpanded.add(menuId);
    }
    setExpandedMenus(newExpanded);
  };

  const handleMenuClick = (item) => {
    if (item.children) {
      toggleDropdown(item.id);
      // If it's a parent with a path, also navigate to its path
      if (item.path) {
        handleNavigation(item.path);
      }
    } else {
      handleNavigation(item.path);
    }
  };

  // Determine if item is active (using similar logic to original)
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

  // Extract orders for active count calculation
  const ordersList = extractDataFromResponse(realTimeOrders);
  const activeOrdersCount = Array.isArray(ordersList) 
    ? ordersList.filter(order => order?.status === 'preparing')?.length || 0
    : 0;

  return (
    <>
      <aside className={`owner-sidebar ${isOpen ? 'open' : 'closed'} ${isMobile ? 'mobile' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="logo-icon"><ChefHat size={20} /></div>
            {isOpen && (
              <div className="logo-text">
                <h1 className="logo-title">RestaurantOS</h1>
                <p className="logo-subtitle">Owner Portal</p>
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
            <p className="footer-title">Live Updates</p>
            <div className="footer-stats">
              <div className="stat">
                <p className="stat-label">Pending Orders</p>
                <p className="stat-value">{pendingOrdersCount}</p>
              </div>
              <div className="stat">
                <p className="stat-label">Active</p>
                <p className="stat-value">
                  {activeOrdersCount}
                </p>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
};

export default OwnerSidebar;