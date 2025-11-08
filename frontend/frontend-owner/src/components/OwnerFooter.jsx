import { useSelector } from 'react-redux';
import { Heart, MessageCircle, HelpCircle, Building } from 'lucide-react';
import { extractDataFromResponse } from '../utils/paginationUtils';
import './styles/OwnerFooter.css';

const OwnerFooter = () => {
  const { todaySales, realTimeOrders, performanceMetrics } = useSelector(state => state.dashboard);
  const { currentRestaurant, restaurants } = useSelector(state => state.ownerAuth);

  // Extract data from possible paginated responses
  const ordersList = extractDataFromResponse(realTimeOrders);
  const salesData = extractDataFromResponse(todaySales);
  const metricsData = extractDataFromResponse(performanceMetrics);

  const calculateOverallStats = () => {
    const totalRestaurants = restaurants.length || 0;
    
    // Calculate total active orders across all restaurants
    const totalActiveOrders = Array.isArray(ordersList) 
      ? ordersList.filter(order => ['pending', 'confirmed', 'preparing'].includes(order?.status))?.length || 0
      : 0;

    // Calculate total revenue across all restaurants (mock data for now)
    let totalRevenue = 0;
    if (restaurants.length > 0) {
      // This would come from an API in real implementation
      totalRevenue = restaurants.reduce((sum, restaurant) => sum + (restaurant.monthly_revenue || 0), 0);
    }

    return [
      { 
        label: 'Total Restaurants', 
        value: totalRestaurants.toString(), 
        change: totalRestaurants > 0 ? `${totalRestaurants} active` : 'No restaurants' 
      },
      { 
        label: 'Active Orders', 
        value: totalActiveOrders.toString(),
        change: totalActiveOrders > 0 ? `+${totalActiveOrders}` : 'No active orders'
      },
      { 
        label: 'Monthly Revenue', 
        value: `$${totalRevenue.toLocaleString()}`,
        change: totalRevenue > 0 ? '+12% this month' : 'No revenue'
      }
    ];
  };

  // Calculate single restaurant stats for dashboard
  const calculateRestaurantStats = () => {
    // Active orders (pending, confirmed, preparing)
    const activeOrders = Array.isArray(ordersList) 
      ? ordersList.filter(order => ['pending', 'confirmed', 'preparing'].includes(order?.status))?.length || 0
      : 0;

    // Today's revenue
    let todayRevenue = 0;
    if (salesData && typeof salesData === 'object' && !Array.isArray(salesData)) {
      todayRevenue = salesData.total_revenue || 0;
    } else if (Array.isArray(salesData) && salesData.length > 0) {
      todayRevenue = salesData[0]?.total_revenue || 0;
    }
    
    // Customer satisfaction (from performance metrics or default to 4.8)
    let customerSatisfaction = 4.8;
    if (metricsData && typeof metricsData === 'object') {
      customerSatisfaction = metricsData.customer_satisfaction || 4.8;
    } else if (salesData && typeof salesData === 'object') {
      customerSatisfaction = salesData.customer_satisfaction || 4.8;
    }

    return [
      { 
        label: 'Active Orders', 
        value: activeOrders.toString(), 
        change: activeOrders > 0 ? `+${activeOrders}` : '0' 
      },
      { 
        label: 'Today Revenue', 
        value: `$${todayRevenue.toLocaleString()}`,
        change: '+0%'
      },
      { 
        label: 'Satisfaction', 
        value: `${customerSatisfaction}/5`,
        change: customerSatisfaction >= 4.5 ? '+0.2' : '-0.1'
      }
    ];
  };

  // Choose which stats to display based on current state
  const quickStats = currentRestaurant ? calculateRestaurantStats() : calculateOverallStats();

  return (
    <footer className="owner-footer">
      <div className="footer-content">
        <div className="footer-stats">
          {quickStats.map((stat, index) => (
            <div key={index} className="stat-item">
              <div className="stat-icon-container">
                {currentRestaurant ? (
                  // Restaurant-specific icons
                  index === 0 ? <Building size={16} /> :
                  index === 1 ? <Heart size={16} /> :
                  <MessageCircle size={16} />
                ) : (
                  // Overall business icons
                  index === 0 ? <Building size={16} /> :
                  index === 1 ? <HelpCircle size={16} /> :
                  <Heart size={16} />
                )}
              </div>
              <div className="stat-text">
                <p className="stat-label">{stat.label}</p>
                <div className="stat-value-container">
                  <span className="stat-value">{stat.value}</span>
                  <span className={`stat-change ${
                    stat.change.includes('+') ? 'positive' : stat.change.includes('-') ? 'negative' : 'neutral'
                  }`}>
                    {stat.change}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="support-links">
          <button className="support-link">
            <HelpCircle size={16} />
            <span>Help Center</span>
          </button>
          <button className="support-link">
            <MessageCircle size={16} />
            <span>Support</span>
          </button>
          <div className="credits">
            <span>Made with</span>
            <Heart size={14} className="heart-icon" />
            <span>by RestaurantOS</span>
            {currentRestaurant && (
              <span className="restaurant-id">ID: {currentRestaurant.restaurant_id}</span>
            )}
          </div>
        </div>
      </div>
    </footer>
  );
};


export default OwnerFooter;