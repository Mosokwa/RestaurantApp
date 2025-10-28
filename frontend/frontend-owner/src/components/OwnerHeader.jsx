import { useState, useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Bell, ChevronDown, Search, Menu } from 'lucide-react';
import { switchRestaurant, logoutOwner } from '../store/slices/ownerAuthSlice';
import { extractDataFromResponse } from '../utils/paginationUtils';
import './styles/OwnerHeader.css';
import { useNavigate } from 'react-router-dom';

const OwnerHeader = ({ onToggleSidebar }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { owner, restaurants, currentRestaurant } = useSelector(state => state.ownerAuth);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const dropdownRef = useRef(null);

  // Extract restaurants from possible paginated response
  const restaurantsList = Array.isArray(restaurants) ? restaurants : extractDataFromResponse(restaurants);

  const safeRestaurantsList = Array.isArray(restaurantsList) ? restaurantsList : [];

  const handleRestaurantSwitch = (restaurantId) => {
    dispatch(switchRestaurant(restaurantId));
  };

  console.log('🔍 OwnerHeader Debug:', {
    restaurantsRaw: restaurants,
    restaurantsType: typeof restaurants,
    isArray: Array.isArray(restaurants),
    restaurantsList: restaurantsList,
    restaurantsListType: typeof restaurantsList,
    restaurantsListIsArray: Array.isArray(restaurantsList)
  });

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
    console.log('Logout function called!');
    try {
      await authService.logout();
      dispatch(logoutOwner());
      navigate('/login');
      console.log('Logout successful!');
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear state and redirect
      dispatch(logoutOwner());
      navigate('/login');
    }
  };

  return (
    <header className="owner-header">
      <div className="header-content">
        <div className="left-section">
          <button onClick={onToggleSidebar} className="sidebar-toggle">
            <Menu size={20} />
          </button>
          
          <div className="restaurant-switcher">
            <select
              value={currentRestaurant?.restaurant_id || ''}
              onChange={(e) => handleRestaurantSwitch(e.target.value)}
              className="restaurant-select"
            >
              {safeRestaurantsList.length > 0 ? (
                safeRestaurantsList.map(restaurant => (
                  <option key={restaurant.restaurant_id} value={restaurant.restaurant_id}>
                    {restaurant.name}
                  </option>
                ))
              ) : (
                <option value="">No restaurants</option>
              )}
            </select>
            <ChevronDown className="select-icon" size={16} />
          </div>
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