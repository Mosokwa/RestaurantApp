// src/pages/restaurant/components/StickyOrderBar.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingBag, X, Plus, Minus, ChevronUp, ChevronDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const StickyOrderBar = ({ cartItems, cartTotal, itemCount, diningMode, onCheckout }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  
  // Hide bar when scrolling down, show when scrolling up
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY && currentScrollY > 100) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }
      setLastScrollY(currentScrollY);
    };
    
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);
  
  if (itemCount === 0) return null;
  
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="rhp-sticky-order-bar"
          initial={{ y: 100 }}
          animate={{ y: 0 }}
          exit={{ y: 100 }}
        >
          <div className="rhp-order-bar-content">
            {/* Collapsed View */}
            <div className="rhp-order-info" onClick={() => setIsExpanded(!isExpanded)}>
              <div className="rhp-cart-icon">
                <ShoppingBag size={20} />
                <span className="rhp-cart-count">{itemCount}</span>
              </div>
              <div>
                <div className="rhp-item-count">{itemCount} {itemCount === 1 ? 'item' : 'items'}</div>
                <div className="rhp-order-total">${cartTotal.toFixed(2)}</div>
              </div>
            </div>
            
            <button className="rhp-checkout-btn" onClick={onCheckout}>
              View Cart
            </button>
            
            <button className="rhp-icon-btn" onClick={() => setIsExpanded(!isExpanded)}>
              {isExpanded ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          
          {/* Expanded View */}
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                className="rhp-expanded-cart"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
              >
                <div className="rhp-cart-items">
                  {cartItems.map((item, idx) => (
                    <div key={idx} className="rhp-cart-item">
                      <div className="rhp-cart-item-info">
                        <span className="rhp-cart-item-name">{item.quantity}x {item.name}</span>
                        {item.selectedModifiers?.length > 0 && (
                          <div className="rhp-cart-item-modifiers">
                            {item.selectedModifiers.map(mod => (
                              <span key={mod.id}>+ {mod.name}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="rhp-cart-item-price">
                        ${((parseFloat(item.price) + (item.modifiersTotal || 0)) * item.quantity).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="rhp-cart-total">
                  <span>Total</span>
                  <span>${cartTotal.toFixed(2)}</span>
                </div>
                <button className="rhp-checkout-btn rhp-full-width" onClick={onCheckout}>
                  Proceed to Checkout
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default StickyOrderBar;