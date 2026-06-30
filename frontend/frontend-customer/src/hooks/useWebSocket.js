// src/hooks/useWebSocket.js
import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'react-hot-toast';

export const useWebSocket = (options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionError, setConnectionError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const subscriptionsRef = useRef({
    orders: new Set(),
    restaurants: new Set()
  });
  
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    authToken = localStorage.getItem('access_token')
  } = options;
  
  const getWebSocketUrl = useCallback(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = import.meta.env.VITE_WS_URL || `${wsProtocol}//${window.location.host}`;
    return wsHost;
  }, []);
  
  const connect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      setConnectionError('Unable to connect to real-time service');
      return;
    }
    
    const wsUrl = getWebSocketUrl();
    let endpoint = null;
    
    // For order tracking (customer primary use)
    if (subscriptionsRef.current.orders.size > 0) {
      const orderId = Array.from(subscriptionsRef.current.orders)[0];
      endpoint = `${wsUrl}/ws/orders/${orderId}/tracking/`;
    } 
    // For notifications (customer notifications)
    else if (authToken) {
      endpoint = `${wsUrl}/ws/notifications/`;
    }
    else {
      return;
    }
    
    wsRef.current = new WebSocket(endpoint);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setConnectionError(null);
      reconnectAttemptsRef.current = 0;
      
      // Send authentication if needed
      if (authToken) {
        sendMessage('authenticate', { token: authToken });
      }
      
      // Resubscribe to active channels
      resubscribeToActiveChannels();
      
      if (onConnect) onConnect();
    };
    
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      if (onDisconnect) onDisconnect();
      
      if (autoReconnect) {
        reconnectAttemptsRef.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, reconnectInterval * reconnectAttemptsRef.current);
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionError(error.message);
      if (onError) onError(error);
    };
    
  }, [getWebSocketUrl, authToken, onConnect, onDisconnect, onError, autoReconnect, maxReconnectAttempts, reconnectInterval]);
  
  const resubscribeToActiveChannels = () => {
    // Re-subscribe to orders
    subscriptionsRef.current.orders.forEach(orderId => {
      sendMessage('subscribe_order', { order_uuid: orderId });
    });
  };
  
  const handleIncomingMessage = (data) => {
    setLastMessage(data);
    
    // Handle different message types for customers
    switch (data.type) {
      case 'order_status':
      case 'order_update':
        handleOrderUpdate(data);
        break;
      case 'order_progress':
        handleOrderProgress(data);
        break;
      case 'delivery_location':
        handleDeliveryLocation(data);
        break;
      case 'notification':
        handleNotification(data);
        break;
      case 'unread_count':
        handleUnreadCount(data);
        break;
      case 'recent_notifications':
        handleRecentNotifications(data);
        break;
      case 'pong':
        // Heartbeat response
        break;
      default:
        if (onMessage) onMessage(data);
    }
  };
  
  const handleOrderUpdate = (data) => {
    const { order_uuid, status, order_data } = data;
    
    // Show toast notifications for order status changes
    const statusMessages = {
      'pending': 'Order received!',
      'confirmed': 'Order confirmed!',
      'preparing': 'Your order is being prepared 🍳',
      'ready': 'Your order is ready! 🎉',
      'out_for_delivery': 'Your order is out for delivery 🚚',
      'completed': 'Order completed. Enjoy your meal!',
      'cancelled': 'Order was cancelled'
    };
    
    if (statusMessages[status]) {
      toast.success(statusMessages[status], {
        id: `order-${order_uuid}`,
        duration: 5000
      });
    }
    
    if (onMessage) onMessage(data);
  };
  
  const handleOrderProgress = (data) => {
    const { items, completed_items, progress_percentage } = data;
    
    if (progress_percentage === 100) {
      toast.success('All items are ready!', { id: 'order-progress' });
    } else if (progress_percentage === 50) {
      toast.success('Halfway there!', { id: 'order-progress' });
    }
    
    if (onMessage) onMessage(data);
  };
  
  const handleDeliveryLocation = (data) => {
    const { lat, lng, driver_name, eta } = data;
    if (onMessage) onMessage(data);
  };
  
  const handleNotification = (data) => {
    const { data: notificationData } = data;
    toast(notificationData.title, {
      description: notificationData.message,
      icon: '🔔',
      duration: 7000
    });
    if (onMessage) onMessage(data);
  };
  
  const handleUnreadCount = (data) => {
    const { data: { count } } = data;
    if (onMessage) onMessage({ type: 'unread_count', count });
  };
  
  const handleRecentNotifications = (data) => {
    if (onMessage) onMessage(data);
  };
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    reconnectAttemptsRef.current = 0;
  }, []);
  
  const sendMessage = useCallback((type, data = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ type, ...data });
      wsRef.current.send(message);
      return true;
    }
    return false;
  }, []);
  
  // Order Tracking Methods (Customer)
  const subscribeToOrder = useCallback((orderId) => {
    subscriptionsRef.current.orders.add(orderId);
    if (isConnected) {
      sendMessage('subscribe_order', { order_uuid: orderId });
    } else {
      connect();
    }
  }, [isConnected, sendMessage, connect]);
  
  const unsubscribeFromOrder = useCallback((orderId) => {
    subscriptionsRef.current.orders.delete(orderId);
    if (subscriptionsRef.current.orders.size === 0) {
      disconnect();
    }
  }, [disconnect]);
  
  // Notification Methods (Customer)
  const markNotificationRead = useCallback((notificationId) => {
    return sendMessage('mark_read', { notification_id: notificationId });
  }, [sendMessage]);
  
  const markAllNotificationsRead = useCallback(() => {
    return sendMessage('mark_all_read', {});
  }, [sendMessage]);
  
  const getNotifications = useCallback((limit = 20, offset = 0) => {
    return sendMessage('get_notifications', { limit, offset });
  }, [sendMessage]);
  
  // Heartbeat
  const sendPing = useCallback(() => {
    return sendMessage('ping', {});
  }, [sendMessage]);
  
  // Auto-connect on mount if there are subscriptions
  useEffect(() => {
    const hasSubscriptions = subscriptionsRef.current.orders.size > 0;
    
    if (hasSubscriptions && !wsRef.current) {
      connect();
    }
    
    // Set up heartbeat interval
    const heartbeatInterval = setInterval(() => {
      if (isConnected) {
        sendPing();
      }
    }, 30000);
    
    return () => {
      clearInterval(heartbeatInterval);
      disconnect();
    };
  }, [connect, disconnect, isConnected, sendPing]);
  
  return {
    isConnected,
    connectionError,
    lastMessage,
    sendMessage,
    disconnect,
    
    // Order tracking (Customer)
    subscribeToOrder,
    unsubscribeFromOrder,
    
    // Notifications (Customer)
    markNotificationRead,
    markAllNotificationsRead,
    getNotifications,
    
    // Heartbeat
    sendPing
  };
};

// Specialized hook for order tracking (Customer)
export const useOrderTracking = (orderId) => {
  const [orderStatus, setOrderStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [driverLocation, setDriverLocation] = useState(null);
  const [orderDetails, setOrderDetails] = useState(null);
  
  const {
    isConnected,
    subscribeToOrder,
    unsubscribeFromOrder,
    lastMessage
  } = useWebSocket({
    onMessage: (data) => {
      if (data.type === 'order_status' || data.type === 'order_update') {
        setOrderStatus(data);
        if (data.order_data) {
          setOrderDetails(data.order_data);
        }
      } else if (data.type === 'order_progress') {
        setProgress(data.progress_percentage || 0);
      } else if (data.type === 'delivery_location') {
        setDriverLocation(data);
      }
    }
  });
  
  useEffect(() => {
    if (orderId) {
      subscribeToOrder(orderId);
      return () => unsubscribeFromOrder(orderId);
    }
  }, [orderId, subscribeToOrder, unsubscribeFromOrder]);
  
  return {
    isConnected,
    orderStatus,
    progress,
    driverLocation,
    orderDetails
  };
};

// Specialized hook for customer notifications
export const useCustomerNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const {
    isConnected,
    markNotificationRead,
    markAllNotificationsRead,
    getNotifications,
    lastMessage
  } = useWebSocket({
    onMessage: (data) => {
      if (data.type === 'notification') {
        setNotifications(prev => [data.data, ...prev]);
        setUnreadCount(prev => prev + 1);
        toast(data.data.title, {
          description: data.data.message,
          icon: '🔔'
        });
      } else if (data.type === 'unread_count') {
        setUnreadCount(data.count);
      } else if (data.type === 'recent_notifications') {
        setNotifications(data.notifications);
      }
    }
  });
  
  useEffect(() => {
    if (isConnected) {
      getNotifications();
    }
  }, [isConnected, getNotifications]);
  
  return {
    isConnected,
    notifications,
    unreadCount,
    markAsRead: markNotificationRead,
    markAllAsRead: markAllNotificationsRead,
    refresh: getNotifications
  };
};

export default useWebSocket;