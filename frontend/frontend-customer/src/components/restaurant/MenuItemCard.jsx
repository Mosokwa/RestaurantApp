// src/pages/restaurant/components/MenuItemCard.jsx
import React from 'react';
import { motion } from 'framer-motion';
import { Plus, Clock, Flame, Zap, Leaf } from 'lucide-react';
import getImageUrl from '../../utils/imageHelper';

const MenuItemCard = ({ item, onClick }) => {
  const imageSrc = getImageUrl(item.image, 'food');
  
  return (
    <motion.div
      className={`rhp-menu-item-card ${!item.is_available ? 'rhp-unavailable' : ''}`}
      whileHover={{ y: -4 }}
      onClick={() => item.is_available && onClick()}
    >
      <div className="rhp-item-image">
        <img src={imageSrc} alt={item.name} />
        {!item.is_available && (
          <div className="rhp-unavailable-overlay">
            <span>Unavailable</span>
          </div>
        )}
      </div>
      
      <div className="rhp-item-content">
        <h3 className="rhp-item-name">{item.name}</h3>
        {item.description && (
          <p className="rhp-item-description">{item.description.substring(0, 80)}...</p>
        )}
        <div className="rhp-item-footer">
          <span className="rhp-item-price">${parseFloat(item.price).toFixed(2)}</span>
          {item.is_available && (
            <button className="rhp-add-to-cart-btn" onClick={(e) => { e.stopPropagation(); onClick(); }}>
              <Plus size={18} />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MenuItemCard;