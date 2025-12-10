import { useState, useEffect } from 'react';
import { 
  X, 
  TrendingUp, 
  DollarSign, 
  Clock, 
  Star, 
  ShoppingCart,
  Calendar,
  BarChart3,
  Target
} from 'lucide-react';
import './styles/ItemAnalyticsModal.css';

const ItemAnalyticsModal = ({ item, analytics, onClose }) => {
  const [timeRange, setTimeRange] = useState('30d');
  
  if (!item) return null;

  // Calculate derived metrics
  const calculateMetrics = () => {
    const itemAnalytics = analytics || {};
    
    return {
      totalRevenue: itemAnalytics.revenue || 0,
      quantitySold: itemAnalytics.quantity_sold || 0,
      averageRating: item.avg_rating || 0,
      ratingCount: item.rating_count || 0,
      popularityScore: item.popularity_score || 0,
      preparationTime: item.preparation_time || 0,
      
      // Calculated metrics
      revenuePerOrder: itemAnalytics.quantity_sold > 0 ? 
        (itemAnalytics.revenue || 0) / itemAnalytics.quantity_sold : 0,
      
      // Performance indicators
      performanceScore: Math.min(
        ((item.popularity_score || 0) / 100) * 40 + 
        ((item.avg_rating || 0) / 5) * 30 + 
        (Math.min((itemAnalytics.quantity_sold || 0) / 50, 1) * 30),
        100
      )
    };
  };

  const metrics = calculateMetrics();

  // Mock trend data - in real app, this would come from analytics
  const getTrendData = () => {
    const baseValue = metrics.quantitySold;
    return [
      { period: 'This Week', value: baseValue, change: 12 },
      { period: 'Last Week', value: baseValue * 0.88, change: -5 },
      { period: 'This Month', value: baseValue, change: 8 },
      { period: 'Last Month', value: baseValue * 0.92, change: 15 },
    ];
  };

  const trendData = getTrendData();

  const getPerformanceLevel = (score) => {
    if (score >= 80) return { level: 'Excellent', color: 'var(--color-success)' };
    if (score >= 60) return { level: 'Good', color: 'var(--color-info)' };
    if (score >= 40) return { level: 'Average', color: 'var(--color-warning)' };
    return { level: 'Needs Attention', color: 'var(--color-accent)' };
  };

  const performance = getPerformanceLevel(metrics.performanceScore);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="analytics-modal-glass" onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div className="modal-header">
          <div className="header-content">
            <BarChart3 className="header-icon" size={24} />
            <div className="header-text">
              <h2>Item Analytics</h2>
              <p>Performance insights for {item.name}</p>
            </div>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Time Range Filter */}
        <div className="time-filter-glass">
          <div className="filter-options">
            {['7d', '30d', '90d', '1y'].map(range => (
              <button
                key={range}
                className={`time-btn ${timeRange === range ? 'active' : ''}`}
                onClick={() => setTimeRange(range)}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="metrics-grid">
          <div className="metric-card revenue">
            <div className="metric-icon">
              <DollarSign size={20} />
            </div>
            <div className="metric-content">
              <h4>Total Revenue</h4>
              <p className="metric-value">${metrics.totalRevenue.toFixed(2)}</p>
              <span className="metric-label">From {metrics.quantitySold} orders</span>
            </div>
          </div>

          <div className="metric-card sales">
            <div className="metric-icon">
              <ShoppingCart size={20} />
            </div>
            <div className="metric-content">
              <h4>Quantity Sold</h4>
              <p className="metric-value">{metrics.quantitySold}</p>
              <span className="metric-label">Total units sold</span>
            </div>
          </div>

          <div className="metric-card rating">
            <div className="metric-icon">
              <Star size={20} />
            </div>
            <div className="metric-content">
              <h4>Average Rating</h4>
              <p className="metric-value">{metrics.averageRating.toFixed(1)}</p>
              <span className="metric-label">{metrics.ratingCount} ratings</span>
            </div>
          </div>

          <div className="metric-card popularity">
            <div className="metric-icon">
              <TrendingUp size={20} />
            </div>
            <div className="metric-content">
              <h4>Popularity Score</h4>
              <p className="metric-value">{metrics.popularityScore}</p>
              <span className="metric-label">Performance index</span>
            </div>
          </div>
        </div>

        {/* Performance Overview */}
        <div className="performance-section">
          <div className="section-header">
            <Target size={20} />
            <h3>Performance Overview</h3>
          </div>
          <div className="performance-glass">
            <div className="performance-score">
              <div className="score-circle">
                <span 
                  className="score-value"
                  style={{ color: performance.color }}
                >
                  {Math.round(metrics.performanceScore)}%
                </span>
                <div 
                  className="score-ring"
                  style={{
                    background: `conic-gradient(${performance.color} ${metrics.performanceScore * 3.6}deg, rgba(255,255,255,0.1) 0deg)`
                  }}
                ></div>
              </div>
              <div className="score-info">
                <h4>{performance.level}</h4>
                <p>Overall item performance</p>
              </div>
            </div>
            <div className="performance-details">
              <div className="detail-item">
                <span className="detail-label">Prep Time</span>
                <span className="detail-value">
                  <Clock size={14} />
                  {metrics.preparationTime}min
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Revenue/Order</span>
                <span className="detail-value">
                  <DollarSign size={14} />
                  ${metrics.revenuePerOrder.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Sales Trends */}
        <div className="trends-section">
          <div className="section-header">
            <TrendingUp size={20} />
            <h3>Sales Trends</h3>
          </div>
          <div className="trends-glass">
            {trendData.map((trend, index) => (
              <div key={index} className="trend-item">
                <div className="trend-period">{trend.period}</div>
                <div className="trend-metrics">
                  <span className="trend-value">{trend.value}</span>
                  <span 
                    className={`trend-change ${trend.change >= 0 ? 'positive' : 'negative'}`}
                  >
                    {trend.change >= 0 ? '+' : ''}{trend.change}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Category Comparison */}
        <div className="comparison-section">
          <div className="section-header">
            <BarChart3 size={20} />
            <h3>Category Performance</h3>
          </div>
          <div className="comparison-glass">
            <div className="comparison-item">
              <span className="comparison-label">Item Rank in Category</span>
              <span className="comparison-value">#{Math.max(1, Math.floor(Math.random() * 10) + 1)}</span>
            </div>
            <div className="comparison-item">
              <span className="comparison-label">Category Average Rating</span>
              <span className="comparison-value">4.2</span>
            </div>
            <div className="comparison-item">
              <span className="comparison-label">Category Best Seller</span>
              <span className="comparison-value">Margherita Pizza</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn-primary">
            <Calendar size={16} />
            Export Report
          </button>
        </div>

      </div>
    </div>
  );
};

export default ItemAnalyticsModal;