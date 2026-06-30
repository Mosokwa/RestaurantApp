// src/pages/restaurant/components/LoyaltyBanner.jsx
import React, { useState, useEffect } from 'react';
import { Gift, Award, ChevronRight, Sparkles, TrendingUp, Clock } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import { authService } from '../../services/auth';

const LoyaltyBanner = ({ loyaltyInfo, restaurantId }) => {
  const [userLoyalty, setUserLoyalty] = useState(null);
  const [loading, setLoading] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const isAuthenticated = authService.isAuthenticated();
  
  // Check if loyalty is enabled for this restaurant
  const isLoyaltyEnabled = loyaltyInfo?.enabled === true;
  
  // Fetch user loyalty data only if restaurant has loyalty enabled
  useEffect(() => {
    if (isAuthenticated && isLoyaltyEnabled) {
      fetchUserLoyalty();
    }
  }, [isAuthenticated, isLoyaltyEnabled]);
  
  const fetchUserLoyalty = async () => {
    setLoading(true);
    try {
      const response = await api.get('/loyalty/points/');
      setUserLoyalty(response.data);
    } catch (error) {
      console.warn('Failed to fetch loyalty data:', error.response?.data || error.message);
      setUserLoyalty(null);
    } finally {
      setLoading(false);
    }
  };
  
  const handleEnroll = async () => {
    if (!restaurantId) {
      toast.error('Unable to enroll. Restaurant information missing.');
      return;
    }
    
    setEnrolling(true);
    try {
      const response = await api.post('/loyalty/enroll/', { restaurant_id: restaurantId });
      toast.success(response.data.message || 'Successfully enrolled in loyalty program!');
      await fetchUserLoyalty();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to enroll. Please try again.';
      toast.error(errorMsg);
    } finally {
      setEnrolling(false);
    }
  };
  
  // If loyalty is not enabled for this restaurant, don't show anything
  if (!isLoyaltyEnabled) {
    return null;
  }
  
  // Not logged in - show signup prompt
  if (!isAuthenticated) {
    return (
      <div className="rhp-loyalty-banner">
        <div className="rhp-loyalty-content">
          <div className="rhp-loyalty-icon">
            <Gift size={24} />
          </div>
          <div className="rhp-loyalty-text">
            <h4>Earn Points & Get Rewards!</h4>
            <p>Join our loyalty program and earn {loyaltyInfo.points_per_dollar} points for every dollar spent</p>
          </div>
          <button 
            className="rhp-loyalty-btn" 
            onClick={() => window.location.href = `/login?redirect=/restaurant/${restaurantId}`}
          >
            Sign up to Earn
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    );
  }
  
  // Loading state
  if (loading) {
    return (
      <div className="rhp-loyalty-banner">
        <div className="rhp-loyalty-content">
          <div className="rhp-loyalty-icon">
            <Award size={24} />
          </div>
          <div className="rhp-loyalty-text">
            <h4>Loyalty Program</h4>
            <p>Loading your points...</p>
          </div>
          <div className="rhp-loading-spinner-small"></div>
        </div>
      </div>
    );
  }
  
  // Logged in but not enrolled (userLoyalty is null or has no points)
  if (!userLoyalty || userLoyalty.current_points === undefined) {
    return (
      <div className="rhp-loyalty-banner">
        <div className="rhp-loyalty-content">
          <div className="rhp-loyalty-icon">
            <Sparkles size={24} />
          </div>
          <div className="rhp-loyalty-text">
            <h4>Join Our Loyalty Program!</h4>
            <p>Earn {loyaltyInfo.points_per_dollar} points per dollar + {loyaltyInfo.signup_bonus} bonus points on signup!</p>
          </div>
          <button 
            className="rhp-loyalty-btn" 
            onClick={handleEnroll}
            disabled={enrolling}
          >
            {enrolling ? 'Enrolling...' : 'Enroll Now'}
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    );
  }
  
  // Enrolled user - show points and tier
  const getTierColor = () => {
    switch (userLoyalty.tier?.toLowerCase()) {
      case 'bronze': return '#cd7f32';
      case 'silver': return '#c0c0c0';
      case 'gold': return '#ffd700';
      case 'platinum': return '#e5e4e2';
      default: return '#cd7f32';
    }
  };
  
  const getTierIcon = () => {
    switch (userLoyalty.tier?.toLowerCase()) {
      case 'bronze': return '🥉';
      case 'silver': return '🥈';
      case 'gold': return '🥇';
      case 'platinum': return '💎';
      default: return '⭐';
    }
  };
  
  // Calculate progress to next tier
  const getNextTierProgress = () => {
    const points = userLoyalty.current_points || 0;
    if (points < 1000) {
      return { pointsNeeded: 1000 - points, nextTier: 'Silver', percentage: (points / 1000) * 100 };
    } else if (points < 5000) {
      return { pointsNeeded: 5000 - points, nextTier: 'Gold', percentage: ((points - 1000) / 4000) * 100 };
    } else if (points < 15000) {
      return { pointsNeeded: 15000 - points, nextTier: 'Platinum', percentage: ((points - 5000) / 10000) * 100 };
    }
    return null;
  };
  
  const nextTier = getNextTierProgress();
  
  return (
    <div className="rhp-loyalty-banner">
      <div className="rhp-loyalty-header">
        <div className="rhp-loyalty-tier">
          <span className="rhp-tier-icon">{getTierIcon()}</span>
          <div>
            <div className="rhp-tier-name">{userLoyalty.tier?.toUpperCase() || 'BRONZE'} MEMBER</div>
            <div className="rhp-tier-points">{userLoyalty.current_points?.toLocaleString() || 0} points</div>
          </div>
        </div>
        
        <div className="rhp-loyalty-stats">
          <div className="rhp-stat">
            <TrendingUp size={14} />
            <span>{userLoyalty.lifetime_points?.toLocaleString() || 0}</span>
            <label>Lifetime</label>
          </div>
          <div className="rhp-stat">
            <Clock size={14} />
            <span>{userLoyalty.total_orders || 0}</span>
            <label>Orders</label>
          </div>
        </div>
      </div>
      
      {nextTier && (
        <div className="rhp-tier-progress">
          <div className="rhp-progress-label">
            <span>{nextTier.pointsNeeded} points to {nextTier.nextTier}</span>
            <span>{Math.round(nextTier.percentage)}%</span>
          </div>
          <div className="rhp-progress-bar">
            <div 
              className="rhp-progress-fill" 
              style={{ width: `${Math.min(100, nextTier.percentage)}%`, backgroundColor: getTierColor() }}
            />
          </div>
        </div>
      )}
      
      <div className="rhp-loyalty-footer">
        <div className="rhp-earn-rate">
          Earn {loyaltyInfo.points_per_dollar} points per ${loyaltyInfo.minimum_order_amount > 0 ? ` (min $${loyaltyInfo.minimum_order_amount})` : ''}
        </div>
        <button 
          className="rhp-redeem-btn"
          onClick={() => toast.info('Rewards catalog coming soon!')}
        >
          Redeem Points
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default LoyaltyBanner;