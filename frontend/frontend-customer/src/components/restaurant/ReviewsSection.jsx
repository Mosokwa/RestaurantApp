// src/pages/restaurant/components/ReviewsSection.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Star, ThumbsUp, Calendar, User, ChevronDown } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';
import { authService } from '../../services/auth';

const ReviewsSection = ({ restaurantId, preview }) => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [ratingStats, setRatingStats] = useState(preview || {
    average_rating: 0,
    total_reviews: 0,
    rating_breakdown: { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 }
  });
  
  const isAuthenticated = authService.isAuthenticated();
  
  // Fetch reviews
  const fetchReviews = useCallback(async (reset = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const params = {
        page: reset ? 1 : page,
        page_size: 5
      };
      
      const response = await api.get(`/restaurants/${restaurantId}/reviews/`, { params });
      const newReviews = response.data.results || response.data.items || [];
      
      if (reset) {
        setReviews(newReviews);
        setPage(2);
      } else {
        setReviews(prev => [...prev, ...newReviews]);
        setPage(prev => prev + 1);
      }
      
      setHasMore(!!response.data.next);
      
      if (reset && response.data.rating_stats) {
        setRatingStats(response.data.rating_stats);
      }
    } catch (error) {
      console.error('Failed to fetch reviews:', error);
    } finally {
      setLoading(false);
    }
  }, [restaurantId, page, loading]);
  
  useEffect(() => {
    fetchReviews(true);
  }, []);
  
  const handleHelpful = async (reviewId) => {
    if (!isAuthenticated) {
      toast.error('Please login to mark reviews as helpful');
      return;
    }
    
    try {
      await api.post(`/reviews/${reviewId}/helpful-vote/`);
      setReviews(prev => prev.map(review => 
        review.review_id === reviewId 
          ? { ...review, helpful_count: (review.helpful_count || 0) + 1 }
          : review
      ));
      toast.success('Thanks for your feedback!');
    } catch (error) {
      toast.error('Failed to mark as helpful');
    }
  };
  
  const renderStars = (rating, size = 14) => {
    return (
      <div className="rhp-review-rating">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            size={size}
            fill={star <= rating ? '#FFD700' : 'none'}
            color={star <= rating ? '#FFD700' : 'rgba(255, 255, 255, 0.3)'}
          />
        ))}
      </div>
    );
  };
  
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };
  
  return (
    <div className="rhp-reviews-section">
      <div className="rhp-reviews-header">
        <div className="rhp-reviews-title">
          <h3>Customer Reviews</h3>
          <span className="rhp-review-count">{ratingStats.total_reviews} reviews</span>
        </div>
      </div>
      
      {/* Rating Summary */}
      <div className="rhp-rating-summary">
        <div className="rhp-overall-rating">
          <div className="rhp-rating-number">{ratingStats.average_rating?.toFixed(1) || '0.0'}</div>
          {renderStars(Math.floor(ratingStats.average_rating || 0), 16)}
          <div className="rhp-review-count">Based on {ratingStats.total_reviews} reviews</div>
        </div>
        
        <div className="rhp-rating-breakdown">
          {[5, 4, 3, 2, 1].map(star => {
            const count = ratingStats.rating_breakdown?.[star] || 0;
            const percentage = ratingStats.total_reviews > 0 
              ? (count / ratingStats.total_reviews) * 100 
              : 0;
            
            return (
              <div key={star} className="rhp-breakdown-row">
                <div>{star} <Star size={10} fill="#FFD700" color="#FFD700" /></div>
                <div className="rhp-breakdown-bar">
                  <div className="rhp-breakdown-fill" style={{ width: `${percentage}%` }} />
                </div>
                <div>{count}</div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Reviews List */}
      <div className="rhp-reviews-list">
        {reviews.map((review, index) => (
          <motion.div
            key={review.review_id}
            className="rhp-review-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <div className="rhp-review-header">
              <div>
                <div className="rhp-reviewer-name">
                  {review.customer?.name || 'Anonymous User'}
                </div>
                <div className="rhp-review-date">
                  <Calendar size={12} />
                  {formatDate(review.created_at)}
                </div>
              </div>
              <div>
                {renderStars(review.overall_rating, 14)}
              </div>
            </div>
            
            {review.comment && (
              <p className="rhp-review-comment">{review.comment}</p>
            )}
            
            <button 
              className="rhp-helpful-btn"
              onClick={() => handleHelpful(review.review_id)}
            >
              <ThumbsUp size={12} />
              <span>Helpful ({review.helpful_count || 0})</span>
            </button>
          </motion.div>
        ))}
        
        {/* Loading More */}
        {loading && (
          <div className="rhp-loading-more">
            <div className="rhp-loading-spinner-small"></div>
          </div>
        )}
        
        {/* Load More Button */}
        {hasMore && !loading && reviews.length > 0 && (
          <button className="rhp-load-more-btn" onClick={() => fetchReviews(false)}>
            Load More Reviews
            <ChevronDown size={16} />
          </button>
        )}
        
        {/* Empty State */}
        {!loading && reviews.length === 0 && (
          <div className="rhp-empty-state">
            <span className="rhp-empty-state-emoji">⭐</span>
            <p>No reviews yet</p>
            <span className="rhp-review-count">Be the first to review!</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewsSection;