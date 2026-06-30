// src/pages/customer/OrderTracking.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  Clock, 
  Package, 
  Truck, 
  MapPin, 
  Phone,
  ChevronLeft,
  Receipt,
  ShoppingBag,
  User,
  Star,
  MessageCircle
} from 'lucide-react';
import { useOrderTracking } from '../../hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';
import './styles/OrderTracking.css';

const OrderTracking = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const { isConnected, orderStatus, progress, driverLocation, orderDetails } = useOrderTracking(orderId);
  const [showDriverInfo, setShowDriverInfo] = useState(false);
  
  const orderSteps = [
    { key: 'pending', label: 'Order Received', icon: Clock, description: 'We\'ve received your order' },
    { key: 'confirmed', label: 'Confirmed', icon: CheckCircle, description: 'Restaurant has confirmed your order' },
    { key: 'preparing', label: 'Preparing', icon: Package, description: 'Chef is preparing your meal' },
    { key: 'ready', label: 'Ready', icon: Package, description: 'Your order is ready!' },
    { key: 'out_for_delivery', label: 'Out for Delivery', icon: Truck, description: 'Driver is on the way' },
    { key: 'completed', label: 'Delivered', icon: CheckCircle, description: 'Enjoy your meal!' }
  ];
  
  // Find current step index
  const currentStepIndex = orderSteps.findIndex(step => step.key === orderStatus?.status);
  const currentStatus = orderStatus?.status || 'pending';
  
  // Calculate estimated time remaining
  const getEstimatedTimeRemaining = () => {
    if (orderStatus?.data?.estimated_time) {
      return orderStatus.data.estimated_time;
    }
    if (currentStatus === 'preparing') return '15-20 min';
    if (currentStatus === 'ready') return 'Ready for pickup/delivery';
    if (currentStatus === 'out_for_delivery') return '10-15 min';
    return 'Calculating...';
  };
  
  // Get order type specific display
  const orderType = orderDetails?.order_type || 'delivery';
  const isDelivery = orderType === 'delivery';
  
  return (
    <div className="order-tracking-page">
      <div className="tracking-container">
        {/* Header */}
        <div className="tracking-header">
          <button className="back-btn" onClick={() => navigate(-1)}>
            <ChevronLeft size={20} />
          </button>
          <h1>Track Your Order</h1>
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Live' : '○ Connecting...'}
          </div>
        </div>
        
        {/* Order ID */}
        <div className="order-id-card glass-card">
          <Receipt size={20} />
          <span>Order #{orderId?.slice(0, 8)}</span>
          <span className="order-type-badge">{orderType.toUpperCase()}</span>
        </div>
        
        {/* Progress Section */}
        <div className="progress-section glass-card">
          <div className="progress-header">
            <span className="status-text">{orderSteps[currentStepIndex]?.label}</span>
            <span className="estimated-time">
              <Clock size={14} />
              {getEstimatedTimeRemaining()}
            </span>
          </div>
          
          <div className="progress-bar-container">
            <motion.div 
              className="progress-fill"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="progress-percentage">{Math.round(progress)}% Complete</div>
        </div>
        
        {/* Order Steps Timeline */}
        <div className="timeline-section glass-card">
          <h3>Order Timeline</h3>
          <div className="timeline">
            {orderSteps.map((step, index) => {
              const isCompleted = index <= currentStepIndex;
              const isCurrent = index === currentStepIndex;
              const StepIcon = step.icon;
              
              return (
                <div key={step.key} className={`timeline-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}`}>
                  <div className="timeline-marker">
                    <div className="marker-icon">
                      {isCompleted ? <CheckCircle size={20} /> : <StepIcon size={20} />}
                    </div>
                    {index < orderSteps.length - 1 && (
                      <div className={`timeline-line ${isCompleted ? 'completed' : ''}`} />
                    )}
                  </div>
                  <div className="timeline-content">
                    <div className="step-label">{step.label}</div>
                    <div className="step-description">{step.description}</div>
                    {isCurrent && (
                      <motion.div 
                        className="current-indicator"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                      >
                        Current
                      </motion.div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        
        {/* Order Details */}
        {orderDetails && (
          <div className="order-details-section glass-card">
            <h3>
              <ShoppingBag size={18} />
              Order Summary
            </h3>
            <div className="items-list">
              {orderDetails.items?.map((item, idx) => (
                <div key={idx} className="order-item">
                  <div className="item-info">
                    <span className="item-quantity">{item.quantity}x</span>
                    <span className="item-name">{item.name}</span>
                  </div>
                  <div className="item-price">${(item.price * item.quantity).toFixed(2)}</div>
                </div>
              ))}
            </div>
            <div className="order-totals">
              <div className="total-row">
                <span>Subtotal</span>
                <span>${orderDetails.subtotal?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="total-row">
                <span>Tax</span>
                <span>${orderDetails.tax?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="total-row delivery-fee">
                <span>Delivery Fee</span>
                <span>${orderDetails.delivery_fee?.toFixed(2) || '0.00'}</span>
              </div>
              <div className="total-row grand-total">
                <span>Total</span>
                <span>${orderDetails.total_amount?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Restaurant Info */}
        {orderDetails?.restaurant && (
          <div className="restaurant-info glass-card">
            <h3>Restaurant</h3>
            <div className="restaurant-details">
              <div className="restaurant-name">{orderDetails.restaurant.name}</div>
              <div className="restaurant-address">{orderDetails.restaurant.address}</div>
              <button className="call-restaurant-btn">
                <Phone size={16} />
                Call Restaurant
              </button>
            </div>
          </div>
        )}
        
        {/* Driver Info (for delivery orders) */}
        {isDelivery && driverLocation && (
          <div className="driver-section glass-card">
            <div className="driver-header" onClick={() => setShowDriverInfo(!showDriverInfo)}>
              <div className="driver-avatar">
                <Truck size={24} />
              </div>
              <div className="driver-info">
                <div className="driver-name">{driverLocation.driver_name || 'Your Driver'}</div>
                <div className="driver-eta">ETA: {driverLocation.eta || '10'} minutes</div>
              </div>
              <ChevronLeft className={`expand-icon ${showDriverInfo ? 'expanded' : ''}`} size={20} />
            </div>
            
            <AnimatePresence>
              {showDriverInfo && (
                <motion.div
                  className="driver-details"
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                >
                  <div className="driver-contact">
                    <button className="contact-driver-btn">
                      <MessageCircle size={16} />
                      Message Driver
                    </button>
                    <button className="call-driver-btn">
                      <Phone size={16} />
                      Call Driver
                    </button>
                  </div>
                  <div className="driver-location">
                    <MapPin size={16} />
                    <span>Driver is on the way to your location</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="action-buttons">
          <button className="btn-secondary" onClick={() => navigate(`/restaurant/${orderDetails?.restaurant?.id}`)}>
            Order Again
          </button>
          <button className="btn-primary" onClick={() => navigate('/')}>
            Browse More Restaurants
          </button>
        </div>
        
        {/* Need Help Section */}
        <div className="help-section">
          <p>Need help with your order?</p>
          <button className="help-btn">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderTracking;