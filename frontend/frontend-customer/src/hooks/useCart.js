// src/hooks/useCart.js
import { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

const CART_STORAGE_KEY = 'restaurant_cart';

export const useCart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [cartRestaurant, setCartRestaurant] = useState(null);
  
  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = localStorage.getItem(CART_STORAGE_KEY);
    if (savedCart) {
      try {
        const { items, restaurant } = JSON.parse(savedCart);
        setCartItems(items || []);
        setCartRestaurant(restaurant);
      } catch (e) {
        console.error('Failed to load cart:', e);
      }
    }
  }, []);
  
  // Save cart to localStorage
  useEffect(() => {
    if (cartItems.length > 0) {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify({
        items: cartItems,
        restaurant: cartRestaurant
      }));
    } else {
      localStorage.removeItem(CART_STORAGE_KEY);
    }
  }, [cartItems, cartRestaurant]);
  
  const addToCart = useCallback((item) => {
    setCartItems(prev => {
      // Check if item already exists in cart (by item_id and same modifiers)
      const existingIndex = prev.findIndex(
        i => i.item_id === item.item_id && 
        JSON.stringify(i.selectedModifiers) === JSON.stringify(item.selectedModifiers)
      );
      
      if (existingIndex >= 0) {
        // Update quantity
        const updated = [...prev];
        updated[existingIndex].quantity += item.quantity;
        return updated;
      }
      
      // Add new item
      return [...prev, item];
    });
    
    // Set restaurant info if not set
    if (!cartRestaurant && item.restaurantId) {
      setCartRestaurant({
        id: item.restaurantId,
        name: item.restaurantName
      });
    }
  }, [cartRestaurant]);
  
  const updateQuantity = useCallback((itemId, modifierKey, newQuantity) => {
    setCartItems(prev => {
      const index = prev.findIndex(
        i => i.item_id === itemId && 
        (i.selectedModifiers ? JSON.stringify(i.selectedModifiers) : '') === modifierKey
      );
      
      if (index >= 0) {
        const updated = [...prev];
        if (newQuantity <= 0) {
          updated.splice(index, 1);
        } else {
          updated[index].quantity = newQuantity;
        }
        return updated;
      }
      return prev;
    });
  }, []);
  
  const removeFromCart = useCallback((itemId, modifierKey) => {
    setCartItems(prev => {
      return prev.filter(
        i => !(i.item_id === itemId && 
          (i.selectedModifiers ? JSON.stringify(i.selectedModifiers) : '') === modifierKey)
      );
    });
  }, []);
  
  const clearCart = useCallback(() => {
    setCartItems([]);
    setCartRestaurant(null);
    localStorage.removeItem(CART_STORAGE_KEY);
  }, []);
  
  const getCartTotal = useCallback(() => {
    return cartItems.reduce((total, item) => {
      let itemTotal = parseFloat(item.price) * item.quantity;
      
      // Add modifier prices
      if (item.selectedModifiers && item.selectedModifiers.length > 0) {
        item.selectedModifiers.forEach(modifier => {
          itemTotal += parseFloat(modifier.price_modifier || 0) * item.quantity;
        });
      }
      
      return total + itemTotal;
    }, 0);
  }, [cartItems]);
  
  const getItemCount = useCallback(() => {
    return cartItems.reduce((count, item) => count + item.quantity, 0);
  }, [cartItems]);
  
  return {
    cartItems,
    cartRestaurant,
    addToCart,
    updateQuantity,
    removeFromCart,
    clearCart,
    getCartTotal,
    getItemCount
  };
};

export default useCart;