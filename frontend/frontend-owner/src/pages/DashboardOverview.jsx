import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  ShoppingCart,
  DollarSign,
  Users,
  Clock,
  ChefHat,
  Truck,
  CheckCircle2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { fetchDashboardData, fetchRealTimeData } from '../store/slices/dashboardSlice';
import './styles/DashboardOverview.css';

const DashboardOverview = () => {
  const dispatch = useDispatch();
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const { 
    dashboardOverview, 
    todaySales, 
    realTimeOrders, 
    kitchenQueue, 
    performanceMetrics,
    customerInsights,
    loading, 
    realTimeLoading,
    lastUpdated 
  } = useSelector(state => state.dashboard);
  
  const { currentRestaurant } = useSelector(state => state.ownerAuth);

  useEffect(() => {
    if (currentRestaurant?.restaurant_id) {
      dispatch(fetchDashboardData(currentRestaurant.restaurant_id))
        .unwrap()
        .catch(error => {
          console.error('Dashboard data fetch failed:', error);
          // Handle gracefully - maybe show error state
        });
    }
  }, [dispatch, currentRestaurant?.restaurant_id]); // Add proper dependency

  // Auto-refresh real-time data every 30 seconds
  useEffect(() => {
    if (!autoRefresh || !currentRestaurant) return;

    const interval = setInterval(() => {
      dispatch(fetchRealTimeData(currentRestaurant.restaurant_id));
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, currentRestaurant, dispatch]);

  const handleRefresh = () => {
    if (currentRestaurant) {
      dispatch(fetchRealTimeData(currentRestaurant.restaurant_id));
    }
  };

  // Calculate real-time metrics from API data
  const calculateRealTimeMetrics = () => {
    const pendingOrders = realTimeOrders?.filter(order => 
      ['pending', 'confirmed'].includes(order.status)
    )?.length || 0;

    const preparingOrders = realTimeOrders?.filter(order => 
      order.status === 'preparing'
    )?.length || 0;

    const deliveryOrders = realTimeOrders?.filter(order => 
      order.status === 'out_for_delivery'
    )?.length || 0;

    const completedOrders = todaySales?.completed_orders || 0;

    // Calculate kitchen load based on kitchen queue
    const kitchenLoad = kitchenQueue?.length > 0 
      ? Math.min(100, (kitchenQueue.length / 10) * 100) // Assuming 10 orders max capacity
      : 0;

    return {
      pendingOrders,
      preparingOrders,
      deliveryOrders,
      completedOrders,
      kitchenLoad: Math.round(kitchenLoad)
    };
  };

  const realTimeMetrics = calculateRealTimeMetrics();

  // Generate alerts based on real data
  const generateAlerts = () => {
    const alerts = [];

    // High cancellation rate alert
    if (todaySales?.cancellation_rate > 20) {
      alerts.push({
        id: 1,
        type: 'warning',
        title: 'High Cancellation Rate',
        message: `Cancellation rate is ${todaySales.cancellation_rate}% - consider reviewing order process`,
        time: 'Just now'
      });
    }

    // Low stock alert (if inventory data available)
    if (performanceMetrics?.low_stock_items > 5) {
      alerts.push({
        id: 2,
        type: 'danger',
        title: 'Low Stock Alert',
        message: `${performanceMetrics.low_stock_items} menu items are running low on inventory`,
        time: '30 minutes ago'
      });
    }

    // Kitchen overload alert
    if (realTimeMetrics.kitchenLoad > 80) {
      alerts.push({
        id: 3,
        type: 'warning',
        title: 'Kitchen at High Capacity',
        message: `Kitchen load is at ${realTimeMetrics.kitchenLoad}% - consider pausing new orders`,
        time: '5 minutes ago'
      });
    }

    // New reviews alert (if reviews data available)
    if (customerInsights?.pending_reviews > 0) {
      alerts.push({
        id: 4,
        type: 'info',
        title: 'New Customer Reviews',
        message: `You have ${customerInsights.pending_reviews} new reviews to moderate`,
        time: '1 hour ago'
      });
    }

    return alerts;
  };

  const alerts = generateAlerts();

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard data...</p>
      </div>
    );
  }

  const TodaySnapshot = () => (
    <div className="dashboard-card">
      <div className="card-header">
        <h2 className="card-title">Today's Snapshot</h2>
        <div className="last-updated">
          Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Never'}
        </div>
      </div>
      <div className="snapshot-grid">
        <div className="snapshot-item">
          <div className="snapshot-content">
            <div>
              <p className="snapshot-label">Total Orders</p>
              <p className="snapshot-value">{todaySales?.total_orders || 0}</p>
              <p className="snapshot-growth">
                {todaySales?.orders_growth !== undefined ? `${todaySales.orders_growth}%` : '0%'} vs yesterday
              </p>
            </div>
            <div className="snapshot-icon orders-icon">
              <ShoppingCart size={24} />
            </div>
          </div>
        </div>

        <div className="snapshot-item">
          <div className="snapshot-content">
            <div>
              <p className="snapshot-label">Revenue</p>
              <p className="snapshot-value">${todaySales?.total_revenue ? todaySales.total_revenue.toLocaleString() : '0'}</p>
              <p className="snapshot-growth">
                {todaySales?.revenue_growth !== undefined ? `${todaySales.revenue_growth}%` : '0%'} vs yesterday
              </p>
            </div>
            <div className="snapshot-icon revenue-icon">
              <DollarSign size={24} />
            </div>
          </div>
        </div>

        <div className="snapshot-item">
          <div className="snapshot-content">
            <div>
              <p className="snapshot-label">Customers</p>
              <p className="snapshot-value">{todaySales?.total_customers || 0}</p>
              <p className="snapshot-growth">
                {todaySales?.new_customers || 0} new today
              </p>
            </div>
            <div className="snapshot-icon customers-icon">
              <Users size={24} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const RealTimeMetrics = () => (
    <div className="dashboard-card">
      <div className="card-header">
        <h2 className="card-title">Real-time Metrics</h2>
        <div className="real-time-controls">
          <button 
            onClick={handleRefresh}
            disabled={realTimeLoading}
            className="refresh-btn"
          >
            <RefreshCw size={16} className={realTimeLoading ? 'spinning' : ''} />
          </button>
          <label className="auto-refresh">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
        </div>
      </div>
      <div className="metrics-grid">
        <div className="metric-item">
          <div className="metric-icon pending-icon">
            <Clock size={20} />
          </div>
          <p className="metric-label">Pending Orders</p>
          <p className="metric-value">{realTimeMetrics.pendingOrders}</p>
        </div>

        <div className="metric-item">
          <div className="metric-icon kitchen-icon">
            <ChefHat size={20} />
          </div>
          <p className="metric-label">Kitchen Load</p>
          <p className="metric-value">{realTimeMetrics.kitchenLoad}%</p>
        </div>

        <div className="metric-item">
          <div className="metric-icon delivery-icon">
            <Truck size={20} />
          </div>
          <p className="metric-label">Active Delivery</p>
          <p className="metric-value">{realTimeMetrics.deliveryOrders}</p>
        </div>

        <div className="metric-item">
          <div className="metric-icon completed-icon">
            <CheckCircle2 size={20} />
          </div>
          <p className="metric-label">Completed</p>
          <p className="metric-value">{realTimeMetrics.completedOrders}</p>
        </div>
      </div>
    </div>
  );

  const PerformanceAlerts = () => (
    <div className="dashboard-card">
      <div className="card-header">
        <h2 className="card-title">Performance Alerts</h2>
        <span className="alerts-count">{alerts.length} active</span>
      </div>
      <div className="alerts-list">
        {alerts.length > 0 ? (
          alerts.slice(0, 4).map((alert) => (
            <div
              key={alert.id}
              className={`alert-item ${
                alert.type === 'warning' 
                  ? 'warning-alert' 
                  : alert.type === 'danger'
                  ? 'danger-alert'
                  : 'info-alert'
              }`}
            >
              <AlertCircle className="alert-icon" size={20} />
              <div className="alert-content">
                <p className="alert-title">{alert.title}</p>
                <p className="alert-message">{alert.message}</p>
                <span className="alert-time">{alert.time}</span>
              </div>
            </div>
          ))
        ) : (
          <div className="no-alerts-container">
            <CheckCircle2 size={32} className="no-alerts-icon" />
            <p className="no-alerts">No active alerts</p>
            <span className="no-alerts-subtitle">Everything is running smoothly</span>
          </div>
        )}
      </div>
    </div>
  );

  const AdditionalMetrics = () => (
    <div className="dashboard-card">
      <h2 className="card-title">Performance Insights</h2>
      <div className="insights-grid">
        <div className="insight-item">
          <div className="insight-value">
            {performanceMetrics?.average_order_value ? `$${performanceMetrics.average_order_value}` : '$0'}
          </div>
          <div className="insight-label">Average Order Value</div>
        </div>
        
        <div className="insight-item">
          <div className="insight-value">
            {todaySales?.completion_rate ? `${todaySales.completion_rate}%` : '0%'}
          </div>
          <div className="insight-label">Order Completion Rate</div>
        </div>
        
        <div className="insight-item">
          <div className="insight-value">
            {customerInsights?.customer_satisfaction ? `${customerInsights.customer_satisfaction}/5` : '0/5'}
          </div>
          <div className="insight-label">Customer Satisfaction</div>
        </div>
        
        <div className="insight-item">
          <div className="insight-value">
            {performanceMetrics?.peak_hour_orders || 0}
          </div>
          <div className="insight-label">Peak Hour Orders</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="dashboard-overview">
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Dashboard Overview</h1>
          <p className="dashboard-subtitle">
            Real-time analytics for {currentRestaurant?.name}
          </p>
        </div>
        <div className="restaurant-info">
          <p className="restaurant-label">Current Restaurant</p>
          <p className="restaurant-name">{currentRestaurant?.name}</p>
        </div>
      </div>

      <TodaySnapshot />
      
      <div className="dashboard-grid">
        <RealTimeMetrics />
        <PerformanceAlerts />
      </div>

      <AdditionalMetrics />
    </div>
  );
};

export default DashboardOverview;