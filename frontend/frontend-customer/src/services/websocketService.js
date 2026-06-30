// src/services/websocketService.js
import { useWebSocket } from '../hooks/useWebSocket';

// Singleton pattern for global WebSocket management
class WebSocketServiceSingleton {
  constructor() {
    this.connections = new Map();
    this.listeners = new Map();
  }
  
  getConnection(key, options = {}) {
    if (!this.connections.has(key)) {
      const connection = useWebSocket(options);
      this.connections.set(key, connection);
    }
    return this.connections.get(key);
  }
  
  removeConnection(key) {
    const connection = this.connections.get(key);
    if (connection) {
      connection.disconnect();
      this.connections.delete(key);
    }
  }
  
  addListener(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }
  
  removeListener(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }
  
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }
}

export const WebSocketService = new WebSocketServiceSingleton();

// Helper to get WebSocket URL
export const getWebSocketUrl = (path, params = {}) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = import.meta.env.VITE_WS_HOST || window.location.host;
  const queryString = new URLSearchParams(params).toString();
  return `${protocol}//${host}${path}${queryString ? `?${queryString}` : ''}`;
};

// Reconnection manager
export class ReconnectionManager {
  constructor(maxAttempts = 5, baseDelay = 1000) {
    this.maxAttempts = maxAttempts;
    this.baseDelay = baseDelay;
    this.attempts = 0;
    this.timeoutId = null;
  }
  
  reset() {
    this.attempts = 0;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
  
  scheduleReconnect(callback) {
    if (this.attempts >= this.maxAttempts) {
      return false;
    }
    
    const delay = this.baseDelay * Math.pow(2, this.attempts);
    this.timeoutId = setTimeout(() => {
      this.attempts++;
      callback();
    }, delay);
    
    return true;
  }
  
  cancel() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
  }
}