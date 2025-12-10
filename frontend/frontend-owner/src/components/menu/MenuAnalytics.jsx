import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  BarChart3, 
  TrendingUp, 
  DollarSign, 
  ShoppingCart,
  Star,
  Clock,
  Award,
  AlertTriangle
} from 'lucide-react';
import { fetchMenuAnalytics } from '../../store/slices/menuSlice';
import './styles/AnalyticsComponents.css';

const MenuAnalytics = () => {
  const dispatch = useDispatch();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { analytics, loading } = useSelector(state => state.menu);
  
  const [timeRange, setTimeRange] = useState('30d');
  const [activeView, setActiveView] = useState('overview');

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchMenuAnalytics({ 
        restaurantId: currentRestaurant.restaurant_id, 
        days: parseInt(timeRange) 
      }));
    }
  }, [dispatch, currentRestaurant, timeRange]);

  if (!analytics) {
    return (
      <div className="analytics-container">
        <div className="analytics-loading">
          <BarChart3 size={48} className="loading-icon" />
          <p>Loading analytics data...</p>
        </div>
      </div>
    );
  }

  const { summary_metrics, item_performance, category_performance, bcg_matrix } = analytics;

  const getTopItems = (count = 5) => {
    return item_performance
      .filter(item => item.quantity_sold > 0)
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, count);
  };

  const getLowPerformanceItems = (count = 5) => {
    return item_performance
      .filter(item => item.quantity_sold === 0 || item.profit_margin < 10)
      .sort((a, b) => a.quantity_sold - b.quantity_sold)
      .slice(0, count);
  };

  const getBCGItems = (category) => {
    return bcg_matrix.filter(item => item.bcg_category === category);
  };

  const renderOverview = () => (
    <div className="analytics-overview">
      {/* Summary Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon total-revenue">
            <DollarSign size={20} />
          </div>
          <div className="metric-content">
            <h3>Total Revenue</h3>
            <p className="metric-value">${summary_metrics.total_revenue?.toFixed(2)}</p>
            <p className="metric-label">from menu items</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon items-sold">
            <ShoppingCart size={20} />
          </div>
          <div className="metric-content">
            <h3>Items Sold</h3>
            <p className="metric-value">{summary_metrics.total_items_sold}</p>
            <p className="metric-label">total orders</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon profit">
            <TrendingUp size={20} />
          </div>
          <div className="metric-content">
            <h3>Profit Margin</h3>
            <p className="metric-value">{summary_metrics.overall_profit_margin?.toFixed(1)}%</p>
            <p className="metric-label">average margin</p>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon health">
            <Award size={20} />
          </div>
          <div className="metric-content">
            <h3>Menu Health</h3>
            <p className="metric-value">{summary_metrics.menu_health_score}/100</p>
            <p className="metric-label">performance score</p>
          </div>
        </div>
      </div>

      {/* Top Performers */}
      <div className="section-card">
        <h3 className="section-title">
          <Star size={18} />
          Top Performing Items
        </h3>
        <div className="items-list">
          {getTopItems().map((item, index) => (
            <div key={item.item_id} className="performance-item">
              <div className="item-rank">#{index + 1}</div>
              <div className="item-info">
                <h4 className="item-name">{item.name}</h4>
                <p className="item-category">{item.category_name}</p>
              </div>
              <div className="item-stats">
                <span className="revenue">${item.revenue.toFixed(2)}</span>
                <span className="sold">{item.quantity_sold} sold</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* BCG Matrix Overview */}
      <div className="section-card">
        <h3 className="section-title">
          <BarChart3 size={18} />
          BCG Matrix Analysis
        </h3>
        <div className="bcg-grid">
          <div className="bcg-category stars">
            <h4>Stars</h4>
            <p className="count">{getBCGItems('stars').length}</p>
            <p className="description">High popularity & profit</p>
          </div>
          <div className="bcg-category puzzles">
            <h4>Puzzles</h4>
            <p className="count">{getBCGItems('puzzles').length}</p>
            <p className="description">High profit, low popularity</p>
          </div>
          <div className="bcg-category plow-horses">
            <h4>Plow Horses</h4>
            <p className="count">{getBCGItems('plow_horses').length}</p>
            <p className="description">High popularity, low profit</p>
          </div>
          <div className="bcg-category dogs">
            <h4>Dogs</h4>
            <p className="count">{getBCGItems('dogs').length}</p>
            <p className="description">Low popularity & profit</p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderPerformance = () => (
    <div className="performance-view">
      <div className="section-card">
        <h3 className="section-title">Item Performance Details</h3>
        <div className="performance-table">
          <div className="table-header">
            <div className="col-name">Item Name</div>
            <div className="col-category">Category</div>
            <div className="col-sold">Sold</div>
            <div className="col-revenue">Revenue</div>
            <div className="col-margin">Margin</div>
            <div className="col-rating">Rating</div>
          </div>
          <div className="table-body">
            {item_performance
              .sort((a, b) => b.revenue - a.revenue)
              .map(item => (
                <div key={item.item_id} className="table-row">
                  <div className="col-name">
                    <span className="item-name">{item.name}</span>
                  </div>
                  <div className="col-category">
                    <span 
                      className="category-tag"
                      style={{ backgroundColor: item.category_display_color + '20' }}
                    >
                      {item.category_name}
                    </span>
                  </div>
                  <div className="col-sold">{item.quantity_sold}</div>
                  <div className="col-revenue">${item.revenue.toFixed(2)}</div>
                  <div className="col-margin">
                    <span className={`margin-badge ${item.profit_margin >= 30 ? 'high' : item.profit_margin >= 20 ? 'medium' : 'low'}`}>
                      {item.profit_margin.toFixed(1)}%
                    </span>
                  </div>
                  <div className="col-rating">
                    <Star size={14} />
                    {item.avg_rating.toFixed(1)}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="recommendations-view">
      <div className="section-card">
        <h3 className="section-title">
          <AlertTriangle size={18} />
          Actionable Recommendations
        </h3>
        
        <div className="recommendations-list">
          {/* Low Performance Items */}
          {getLowPerformanceItems().length > 0 && (
            <div className="recommendation-category">
              <h4>Review Low Performance Items</h4>
              <p>The following items have low sales or poor profit margins:</p>
              <div className="problem-items">
                {getLowPerformanceItems().map(item => (
                  <div key={item.item_id} className="problem-item">
                    <span className="item-name">{item.name}</span>
                    <span className="item-issue">
                      {item.quantity_sold === 0 ? 'No sales' : `${item.profit_margin.toFixed(1)}% margin`}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* BCG Recommendations */}
          <div className="recommendation-category">
            <h4>BCG Matrix Actions</h4>
            <div className="bcg-recommendations">
              {getBCGItems('puzzles').length > 0 && (
                <div className="bcg-action">
                  <strong>Puzzles ({getBCGItems('puzzles').length} items):</strong>
                  <span>Increase marketing for high-profit, low-popularity items</span>
                </div>
              )}
              {getBCGItems('plow_horses').length > 0 && (
                <div className="bcg-action">
                  <strong>Plow Horses ({getBCGItems('plow_horses').length} items):</strong>
                  <span>Optimize costs or adjust pricing for popular, low-margin items</span>
                </div>
              )}
              {getBCGItems('dogs').length > 0 && (
                <div className="bcg-action">
                  <strong>Dogs ({getBCGItems('dogs').length} items):</strong>
                  <span>Consider removing or improving low-performing items</span>
                </div>
              )}
            </div>
          </div>

          {/* Inventory Recommendations */}
          {summary_metrics.inactive_menu_items > 0 && (
            <div className="recommendation-category">
              <h4>Inventory Management</h4>
              <p>
                You have {summary_metrics.inactive_menu_items} inactive menu items. 
                Consider reactivating popular items or removing unused ones.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="menu-analytics-container">
      {/* Analytics Header */}
      <div className="analytics-header">
        <div className="header-content">
          <h2>Menu Analytics</h2>
          <div className="header-controls">
            <select 
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="time-select"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </select>
          </div>
        </div>

        <div className="view-tabs">
          <button 
            className={`tab ${activeView === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveView('overview')}
          >
            <BarChart3 size={16} />
            Overview
          </button>
          <button 
            className={`tab ${activeView === 'performance' ? 'active' : ''}`}
            onClick={() => setActiveView('performance')}
          >
            <TrendingUp size={16} />
            Performance
          </button>
          <button 
            className={`tab ${activeView === 'recommendations' ? 'active' : ''}`}
            onClick={() => setActiveView('recommendations')}
          >
            <AlertTriangle size={16} />
            Recommendations
          </button>
        </div>
      </div>

      {/* Analytics Content */}
      <div className="analytics-content">
        {activeView === 'overview' && renderOverview()}
        {activeView === 'performance' && renderPerformance()}
        {activeView === 'recommendations' && renderRecommendations()}
      </div>

      {loading && (
        <div className="analytics-loading-overlay">
          <div className="loading-spinner"></div>
          <p>Updating analytics...</p>
        </div>
      )}
    </div>
  );
};

export default MenuAnalytics;