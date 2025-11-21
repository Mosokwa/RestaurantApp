import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { Building, Plus, Edit, Trash2, Eye } from 'lucide-react';
import { switchRestaurant } from '../store/slices/ownerAuthSlice';
import './styles/RestaurantsManagement.css';

const RestaurantsManagementPage = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { restaurants } = useSelector(state => state.ownerAuth);

  const handleViewRestaurant = (restaurantId) => {
    dispatch(switchRestaurant(restaurantId));
    navigate('/owner/dashboard');
  };

  const handleEditRestaurant = (restaurantId) => {
    navigate(`/owner/restaurants/${restaurantId}/edit`);
  };

  const handleAddNewRestaurant = () => {
    // Clear any existing pending data
    localStorage.setItem('pendingRestaurantSetup', 'true');
    navigate('/owner/onboarding');
  };

  return (
    <div className="restaurants-management">
      <div className="page-header">
        <div>
          <h1 className="page-title">My Restaurants</h1>
          <p className="page-subtitle">Manage all your restaurant locations and settings</p>
        </div>
        <button className="create-btn" onClick={handleAddNewRestaurant}>
          <Plus size={20} />
          Add New Restaurant
        </button>
      </div>

      <div className="restaurants-grid">
        {restaurants.length > 0 ? (
          restaurants.map(restaurant => (
            <div key={restaurant.restaurant_id} className="restaurant-card">
              <div className="card-header">
                <div className="restaurant-avatar">
                  <Building size={24} />
                </div>
                <div className="restaurant-info">
                  <h3 className="restaurant-name">{restaurant.name}</h3>
                  <p className="restaurant-address">{restaurant.address || 'No address provided'}</p>
                  <p className="restaurant-status">
                    Status: <span className={`status ${restaurant.is_active ? 'active' : 'inactive'}`}>
                      {restaurant.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                </div>
              </div>
              
              <div className="card-actions">
                <button 
                  className="action-btn primary"
                  onClick={() => handleViewRestaurant(restaurant.restaurant_id)}
                >
                  <Eye size={16} />
                  View Dashboard
                </button>
                <button 
                  className="action-btn secondary"
                  onClick={() => handleEditRestaurant(restaurant.restaurant_id)}
                >
                  <Edit size={16} />
                  Edit
                </button>
                <button className="action-btn danger">
                  <Trash2 size={16} />
                  Delete
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="no-restaurants">
            <Building size={48} className="no-restaurants-icon" />
            <h3>No Restaurants Yet</h3>
            <p>Get started by adding your first restaurant location</p>
            <button className="create-btn large" onClick={handleAddNewRestaurant}>
              <Plus size={20} />
              Create Your First Restaurant
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RestaurantsManagementPage;