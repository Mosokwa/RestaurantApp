// src/components/customer/NotificationsPanel.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, CheckCircle, Truck, Tag, Star, Gift, Clock } from 'lucide-react';
import { useCustomerNotifications } from '../../hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';

const NotificationsPanel = ({ isOpen, onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, refresh } = useCustomerNotifications();
  const [selectedTab, setSelectedTab] = useState('all'); // all, unread
  
  useEffect(() => {
    if (isOpen) {
      refresh();
    }
  }, [isOpen, refresh]);
  
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'order_update':
        return <Truck size={16} />;
      case 'offer':
        return <Tag size={16} />;
      case 'loyalty':
        return <Gift size={16} />;
      case 'review':
        return <Star size={16} />;
      default:
        return <Bell size={16} />;
    }
  };
  
  const getNotificationColor = (type) => {
    switch (type) {
      case 'order_update':
        return '#4caf50';
      case 'offer':
        return '#ffb703';
      case 'loyalty':
        return '#e63946';
      case 'review':
        return '#FFD700';
      default:
        return '#888';
    }
  };
  
  const filteredNotifications = selectedTab === 'unread' 
    ? notifications.filter(n => !n.is_read)
    : notifications;
  
  const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await markAsRead(notification.notification_id);
    }
    // Handle navigation based on notification type
    if (notification.link) {
      window.location.href = notification.link;
    }
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div className="notifications-overlay" onClick={onClose} />
          <motion.div
            className="notifications-panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25 }}
          >
            <div className="notifications-header">
              <div className="header-title">
                <Bell size={20} />
                <h3>Notifications</h3>
                {unreadCount > 0 && <span className="unread-badge">{unreadCount}</span>}
              </div>
              <button className="close-btn" onClick={onClose}>
                <X size={20} />
              </button>
            </div>
            
            <div className="notifications-tabs">
              <button 
                className={`tab ${selectedTab === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedTab('all')}
              >
                All
              </button>
              <button 
                className={`tab ${selectedTab === 'unread' ? 'active' : ''}`}
                onClick={() => setSelectedTab('unread')}
              >
                Unread
                {unreadCount > 0 && <span className="count">{unreadCount}</span>}
              </button>
            </div>
            
            {unreadCount > 0 && (
              <button className="mark-all-read" onClick={markAllAsRead}>
                Mark all as read
              </button>
            )}
            
            <div className="notifications-list">
              {filteredNotifications.length === 0 ? (
                <div className="empty-state">
                  <Bell size={48} />
                  <p>No notifications yet</p>
                  <span>We'll notify you when something arrives</span>
                </div>
              ) : (
                filteredNotifications.map((notification, index) => (
                  <motion.div
                    key={notification.notification_id || index}
                    className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    onClick={() => handleNotificationClick(notification)}
                  >
                    <div 
                      className="notification-icon"
                      style={{ backgroundColor: `${getNotificationColor(notification.type)}20` }}
                    >
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="notification-content">
                      <div className="notification-title">{notification.title}</div>
                      <div className="notification-message">{notification.message}</div>
                      <div className="notification-time">
                        <Clock size={12} />
                        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                      </div>
                    </div>
                    {!notification.is_read && <div className="unread-dot" />}
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default NotificationsPanel;