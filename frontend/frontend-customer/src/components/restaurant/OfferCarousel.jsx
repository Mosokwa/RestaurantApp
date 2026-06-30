// src/pages/restaurant/components/OfferCarousel.jsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Percent, Tag, Gift } from 'lucide-react';

const OfferCarousel = ({ offers }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  if (!offers || offers.length === 0) return null;
  
  const nextOffer = () => {
    setCurrentIndex((prev) => (prev + 1) % offers.length);
  };
  
  const prevOffer = () => {
    setCurrentIndex((prev) => (prev - 1 + offers.length) % offers.length);
  };
  
  const getOfferIcon = (offerType) => {
    switch (offerType) {
      case 'percentage':
        return <Percent size={24} />;
      case 'fixed':
        return <Tag size={24} />;
      case 'bogo':
        return <Gift size={24} />;
      default:
        return <Tag size={24} />;
    }
  };
  
  const getOfferBadge = (offer) => {
    if (offer.offer_type === 'percentage') {
      return `${offer.discount_value}% OFF`;
    } else if (offer.offer_type === 'fixed') {
      return `$${offer.discount_value} OFF`;
    } else if (offer.offer_type === 'bogo') {
      return 'BUY 1 GET 1';
    }
    return 'SPECIAL OFFER';
  };
  
  return (
    <div className="rhp-offer-carousel">
      <div className="rhp-carousel-container">
        {offers.length > 1 && (
          <button className="rhp-carousel-nav-btn" onClick={prevOffer}>
            <ChevronLeft size={20} />
          </button>
        )}
        
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            className="rhp-offer-card"
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <div className="rhp-offer-icon">
              {getOfferIcon(offers[currentIndex].offer_type)}
            </div>
            <div className="rhp-offer-content">
              <div className="rhp-offer-badge">{getOfferBadge(offers[currentIndex])}</div>
              <h3>{offers[currentIndex].title}</h3>
              <p>{offers[currentIndex].description}</p>
              {offers[currentIndex].min_order_amount > 0 && (
                <div className="rhp-offer-min-order">
                  Min. order: ${offers[currentIndex].min_order_amount}
                </div>
              )}
            </div>
          </motion.div>
        </AnimatePresence>
        
        {offers.length > 1 && (
          <button className="rhp-carousel-nav-btn" onClick={nextOffer}>
            <ChevronRight size={20} />
          </button>
        )}
      </div>
      
      {offers.length > 1 && (
        <div className="rhp-carousel-dots" style={{ position: 'relative', marginTop: '12px' }}>
          {offers.map((_, idx) => (
            <button
              key={idx}
              className={`rhp-dot ${idx === currentIndex ? 'rhp-active' : ''}`}
              onClick={() => setCurrentIndex(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default OfferCarousel;