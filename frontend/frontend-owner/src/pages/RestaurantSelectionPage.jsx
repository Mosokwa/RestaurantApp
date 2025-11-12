import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { Building, TrendingUp, Users, DollarSign, Clock, ChevronRight } from 'lucide-react';
import { switchRestaurant } from '../store/slices/ownerAuthSlice';
import './styles/RestaurantSelection.css';

const RestaurantSelectionPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { owner, restaurants } = useSelector(state => state.ownerAuth);
  
  // Mock data for restaurant comparisons (you'll replace with real API data)
  const restaurantStats = {
    totalRevenue: 125000,
    totalOrders: 2450,
    activeCustomers: 1240,
    averageRating: 4.7
  };

  const handleRestaurantSelect = (restaurantId) => {
    dispatch(switchRestaurant(restaurantId));
    navigate('/owner/dashboard');
  };

  const handleManageRestaurants = () => {
    navigate('/owner/restaurants');
  };

  const QuickStats = () => (
    <div className="dashboard-card">
      <h2 className="card-title">Business Overview</h2>
      <div className="overview-stats">
        <div className="overview-stat">
          <div className="stat-icon revenue">
            <DollarSign size={20} />
          </div>
          <div>
            <p className="stat-value">${restaurantStats.totalRevenue.toLocaleString()}</p>
            <p className="stat-label">Total Revenue</p>
          </div>
        </div>
        
        <div className="overview-stat">
          <div className="stat-icon orders">
            <TrendingUp size={20} />
          </div>
          <div>
            <p className="stat-value">{restaurantStats.totalOrders}</p>
            <p className="stat-label">Total Orders</p>
          </div>
        </div>
        
        <div className="overview-stat">
          <div className="stat-icon customers">
            <Users size={20} />
          </div>
          <div>
            <p className="stat-value">{restaurantStats.activeCustomers}</p>
            <p className="stat-label">Active Customers</p>
          </div>
        </div>
        
        <div className="overview-stat">
          <div className="stat-icon rating">
            <Clock size={20} />
          </div>
          <div>
            <p className="stat-value">{restaurantStats.averageRating}/5</p>
            <p className="stat-label">Avg Rating</p>
          </div>
        </div>
      </div>
    </div>
  );

  const RestaurantCard = ({ restaurant }) => (
    <div 
      className="restaurant-card"
      onClick={() => handleRestaurantSelect(restaurant.restaurant_id)}
    >
      <div className="restaurant-card-header">
        <div className="restaurant-avatar">
          <Building size={24} />
        </div>
        <div className="restaurant-info">
          <h3 className="restaurant-name">{restaurant.name}</h3>
          <p className="restaurant-address">{restaurant.address || 'No address provided'}</p>
        </div>
        <ChevronRight className="chevron-icon" size={20} />
      </div>
      
      <div className="restaurant-stats">
        <div className="restaurant-stat">
          <span className="stat-label">Today's Revenue</span>
          <span className="stat-value">${(restaurant.today_revenue || 0).toLocaleString()}</span>
        </div>
        <div className="restaurant-stat">
          <span className="stat-label">Active Orders</span>
          <span className="stat-value">{restaurant.active_orders || 0}</span>
        </div>
        <div className="restaurant-stat">
          <span className="stat-label">Rating</span>
          <span className="stat-value">{restaurant.rating || 'N/A'}/5</span>
        </div>
      </div>
      
      <div className="restaurant-status">
        <span className={`status-badge ${restaurant.is_open ? 'open' : 'closed'}`}>
          {restaurant.is_open ? 'Open Now' : 'Closed'}
        </span>
      </div>
    </div>
  );

  return (
    <div className="restaurant-selection">
      <div className="selection-header">
        <div>
          <h1 className="page-title">Welcome back, {owner?.first_name}!</h1>
          <p className="page-subtitle">Select a restaurant to manage or view overall performance</p>
        </div>
        {restaurants.length > 0 && (
          <button className="manage-btn" onClick={handleManageRestaurants}>
            <Building size={16} />
            Manage All Restaurants
          </button>
        )}
      </div>

      <QuickStats />
      
      <div className="dashboard-card">
        <div className="card-header">
          <h2 className="card-title">Your Restaurants</h2>
          <span className="restaurants-count">{restaurants.length} restaurants</span>
        </div>
        
        <div className="restaurants-grid">
          {restaurants.length > 0 ? (
            restaurants.map(restaurant => (
              <RestaurantCard key={restaurant.restaurant_id} restaurant={restaurant} />
            ))
          ) : (
            <div className="no-restaurants">
              <Building size={48} className="no-restaurants-icon" />
              <h3>No Restaurants Found</h3>
              <p>You haven't added any restaurants yet.</p>
              <button className="add-restaurant-btn">
                Add Your First Restaurant
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RestaurantSelectionPage;