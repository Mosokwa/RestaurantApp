// src/pages/restaurant/components/MenuItemModal.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus, Minus, Clock, Flame, Leaf, Check, Info } from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../../services/api';

const MenuItemModal = ({ isOpen, onClose, item, onAddToCart, diningMode }) => {
  const [quantity, setQuantity] = useState(1);
  const [selectedModifiers, setSelectedModifiers] = useState({});
  const [modifierGroups, setModifierGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [specialInstructions, setSpecialInstructions] = useState('');
  
  // Fetch modifier groups for this menu item
  useEffect(() => {
    if (item && isOpen) {
      fetchModifierGroups();
    }
  }, [item, isOpen]);
  
  const fetchModifierGroups = async () => {
    if (!item) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/menu-items/${item.item_id}/modifiers/`);
      setModifierGroups(response.data || []);
      
      // Initialize selected modifiers
      const initialSelected = {};
      response.data.forEach(group => {
        initialSelected[group.modifier_id] = [];
      });
      setSelectedModifiers(initialSelected);
    } catch (error) {
      console.error('Failed to fetch modifier groups:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleQuantityChange = (delta) => {
    const newQuantity = quantity + delta;
    if (newQuantity >= 1 && newQuantity <= 99) {
      setQuantity(newQuantity);
    }
  };
  
  const handleModifierToggle = (groupId, modifier) => {
    setSelectedModifiers(prev => {
      const current = prev[groupId] || [];
      const isSelected = current.some(m => m.item_modifier_id === modifier.item_modifier_id);
      
      let newSelection;
      if (isSelected) {
        newSelection = current.filter(m => m.item_modifier_id !== modifier.item_modifier_id);
      } else {
        newSelection = [...current, modifier];
      }
      
      return { ...prev, [groupId]: newSelection };
    });
  };
  
  const getTotalPrice = () => {
    let total = parseFloat(item?.price || 0);
    
    Object.values(selectedModifiers).forEach(modifiers => {
      modifiers.forEach(modifier => {
        total += parseFloat(modifier.price_modifier || 0);
      });
    });
    
    return total * quantity;
  };
  
  const getModifierPrice = (modifier) => {
    const price = parseFloat(modifier.price_modifier || 0);
    if (price === 0) return 'Free';
    if (price > 0) return `+$${price.toFixed(2)}`;
    return `-$${Math.abs(price).toFixed(2)}`;
  };
  
  const handleAddToCart = () => {
    const modifiers = [];
    Object.values(selectedModifiers).forEach(modifierList => {
      modifierList.forEach(modifier => {
        modifiers.push({
          id: modifier.item_modifier_id,
          name: modifier.name,
          price_modifier: parseFloat(modifier.price_modifier || 0)
        });
      });
    });
    
    onAddToCart(item, modifiers, quantity, specialInstructions);
  };
  
  if (!isOpen || !item) return null;
  
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div className="rhp-modal-backdrop" onClick={onClose} />
          <motion.div
            className="rhp-menu-item-modal"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
          >
            <button className="rhp-modal-close" onClick={onClose}>
              <X size={24} />
            </button>
            
            {/* Image */}
            {item.image && (
              <div className="rhp-modal-gallery">
                <img src={item.image} alt={item.name} />
              </div>
            )}
            
            {/* Content */}
            <div className="rhp-modal-content">
              <div className="rhp-modal-header">
                <div>
                  <h2>{item.name}</h2>
                  {item.is_vegetarian && (
                    <span className="rhp-dietary-icon rhp-vegetarian">🌱 Vegetarian</span>
                  )}
                </div>
                <div className="rhp-modal-price">
                  <span className="rhp-price">${parseFloat(item.price).toFixed(2)}</span>
                </div>
              </div>
              
              {item.description && (
                <p className="rhp-modal-description">{item.description}</p>
              )}
              
              {/* Modifier Groups */}
              {modifierGroups.length > 0 && (
                <div className="rhp-modifier-groups">
                  <h3>Customize your order</h3>
                  {modifierGroups.map((group) => (
                    <div key={group.modifier_id} className="rhp-modifier-group">
                      <div className="rhp-group-header">
                        <span>{group.name}</span>
                        {group.is_required && <span className="rhp-required-badge">Required</span>}
                      </div>
                      <div className="rhp-modifiers-list">
                        {group.modifiers?.map((modifier) => {
                          const isSelected = selectedModifiers[group.modifier_id]?.some(
                            m => m.item_modifier_id === modifier.item_modifier_id
                          );
                          
                          return (
                            <button
                              key={modifier.item_modifier_id}
                              className={`rhp-modifier-option ${isSelected ? 'rhp-selected' : ''}`}
                              onClick={() => handleModifierToggle(group.modifier_id, modifier)}
                            >
                              <span className="rhp-modifier-name">{modifier.name}</span>
                              <span className="rhp-modifier-price">{getModifierPrice(modifier)}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Special Instructions */}
              <div className="rhp-special-instructions">
                <label>
                  <Info size={14} />
                  Special instructions (optional)
                </label>
                <textarea
                  placeholder="e.g., no onions, extra sauce, etc."
                  value={specialInstructions}
                  onChange={(e) => setSpecialInstructions(e.target.value)}
                  rows={2}
                />
              </div>
              
              {/* Quantity Selector */}
              <div className="rhp-quantity-selector">
                <span>Quantity</span>
                <div className="rhp-quantity-controls">
                  <button onClick={() => handleQuantityChange(-1)} disabled={quantity <= 1}>
                    <Minus size={16} />
                  </button>
                  <span className="rhp-quantity-value">{quantity}</span>
                  <button onClick={() => handleQuantityChange(1)} disabled={quantity >= 99}>
                    <Plus size={16} />
                  </button>
                </div>
              </div>
              
              {/* Add to Cart Button */}
              <button 
                className="rhp-add-to-cart-modal-btn"
                onClick={handleAddToCart}
              >
                Add to Cart • ${getTotalPrice().toFixed(2)}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MenuItemModal;