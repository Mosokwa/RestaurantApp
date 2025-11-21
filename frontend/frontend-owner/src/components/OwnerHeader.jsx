import { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Bell, ChevronDown, Search, Menu, Building } from 'lucide-react';
import { switchRestaurant, logoutOwner, clearCurrentRestaurant } from '../store/slices/ownerAuthSlice';
import './styles/OwnerHeader.css';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';

const OwnerHeader = ({ onToggleSidebar }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { owner, restaurants, currentRestaurant } = useSelector(state => state.ownerAuth);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const dropdownRef = useRef(null);

  // Extract restaurants from possible paginated response
  const restaurantsList = Array.isArray(restaurants) ? restaurants : [];

  useEffect(() => {
    console.log('🔍 OwnerHeader - Restaurants data:', {
      restaurantsRaw: restaurants,
      restaurantsList: restaurantsList,
      currentRestaurant: currentRestaurant,
      restaurantIds: restaurantsList.map(r => r.restaurant_id)
    });
  }, [restaurants, currentRestaurant]);

  const handleRestaurantSwitch = (restaurantId) => {
    if (restaurantId && restaurantId !== currentRestaurant?.restaurant_id) {
      console.log('🔄 Switching to restaurant:', restaurantId);
      
      // Find the restaurant in the current restaurants list
      const targetRestaurant = restaurantsList.find(
        restaurant => restaurant.restaurant_id == restaurantId
      );
      
      if (targetRestaurant) {
        console.log('✅ Found restaurant:', targetRestaurant.name);
        
        // Dispatch the synchronous action
        dispatch(switchRestaurant(restaurantId));
        
        // Navigate to dashboard to refresh the view
        setTimeout(() => {
          navigate('/owner/dashboard', { replace: true });
        }, 100);
        
      } else {
        console.error('❌ Restaurant not found in current list. Available restaurants:', 
          restaurantsList.map(r => ({ id: r.restaurant_id, name: r.name }))
        );
      }
    } else {
      console.log('⚠️ Same restaurant selected or invalid ID');
    }
  };

  const handleBackToSelection = () => {
    dispatch(clearCurrentRestaurant());
    navigate('/owner/dashboard'); // This will now show RestaurantSelectionPage
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu]);


  const handleLogout = async () => {
    console.log('🔄 Logout function called!');
    
    setShowUserMenu(false);
    
    if (authService.cancelAllRequests) {
      authService.cancelAllRequests();
    }
    
    try {
      await authService.logout();
      dispatch(logoutOwner());
      
      // Clear all persisted UI state
      localStorage.removeItem('sidebarOpen');
      localStorage.removeItem('currentRestaurant');
      
      console.log('✅ Logout successful!');
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear state and redirect
      dispatch(logoutOwner());
      localStorage.removeItem('sidebarOpen');
      localStorage.removeItem('currentRestaurant');
      
      window.location.href = '/login';
    }
  };

  return (
    <header className="owner-header">
      <div className="header-content">
        <div className="left-section">
          <button onClick={onToggleSidebar} className="sidebar-toggle">
            <Menu size={20} />
          </button>

          {currentRestaurant && (
            <button 
              onClick={handleBackToSelection}
              className="back-to-selection"
              title="Back to All Restaurants"
            >
              <Building size={16} />
              <span>All Restaurants</span>
            </button>
          )}
          
          {currentRestaurant && restaurantsList.length > 0 && (
            <div className="restaurant-switcher">
              <select
                value={currentRestaurant?.restaurant_id || ''}
                onChange={(e) => handleRestaurantSwitch(e.target.value)}
                className="restaurant-select"
              >
                <option value={currentRestaurant.restaurant_id}>
                  🟢 {currentRestaurant.name}
                </option>
                
                {restaurantsList.length > 1 && (
                  <option value="" disabled>―― Switch to ――</option>
                )}
                
                {restaurantsList
                  .filter(restaurant => restaurant.restaurant_id !== currentRestaurant.restaurant_id)
                  .map(restaurant => (
                    <option key={restaurant.restaurant_id} value={restaurant.restaurant_id}>
                      {restaurant.name}
                    </option>
                  ))
                }
              </select>
              <ChevronDown className="select-icon" size={16} />
            </div>
          )}
        </div>

        <div className="right-section">
          <div className="search-container">
            <Search className="search-icon" size={18} />
            <input type="text" placeholder="Search..." className="search-input" />
          </div>

          <div className="user-menu">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setShowUserMenu(!showUserMenu);
              }} 
             className="user-button">
              <div className="user-avatar">
                {owner?.first_name?.[0]}{owner?.last_name?.[0]}
              </div>
              <span className="user-name">{owner?.first_name} {owner?.last_name}</span>
              <ChevronDown size={16} />
            </button>

            {showUserMenu && (
              <div className="user-dropdown">
                <button className="dropdown-item" 
                onClick={() => console.log('Profile clicked')}>Profile Settings</button>
                <button className="dropdown-item" 
                onClick={() => console.log('Account clicked')}>Account Settings</button>
                <hr className="dropdown-divider" />
                <button onClick={(e) => {
                      e.stopPropagation();
                      console.log('Logout clicked!');
                      handleLogout();
                    }}
                     className="dropdown-item logout-item">
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default OwnerHeader;