// src/pages/restaurant/components/HotOffersCarousel.jsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Percent, Tag, Gift, Flame } from 'lucide-react';
import getImageUrl from '../../utils/imageHelper';

const HotOffersCarousel = ({ offers, title = "Hot Offers" }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  if (!offers || offers.length === 0) return null;
  
  const nextOffer = () => {
    setCurrentIndex((prev) => (prev + 1) % offers.length);
  };
  
  const prevOffer = () => {
    setCurrentIndex((prev) => (prev - 1 + offers.length) % offers.length);
  };
  
  const getOfferIcon = (type) => {
    switch (type) {
      case 'percentage': return <Percent size={24} />;
      case 'fixed': return <Tag size={24} />;
      case 'bogo': return <Gift size={24} />;
      default: return <Flame size={24} />;
    }
  };
  
  const getOfferBadge = (offer) => {
    if (offer.offer_type === 'percentage') return `${offer.discount_value}% OFF`;
    if (offer.offer_type === 'fixed') return `$${offer.discount_value} OFF`;
    if (offer.offer_type === 'bogo') return 'BUY 1 GET 1';
    return 'HOT OFFER';
  };
  
  const currentOffer = offers[currentIndex];
  
  return (
    <div className="rhp-hot-offers-carousel">
      <div className="rhp-hot-offers-header">
        <div className="rhp-hot-offers-title">
          <Flame size={20} color="#e63946" />
          <h3>{title}</h3>
        </div>
        {offers.length > 1 && (
          <div className="rhp-hot-offers-nav">
            <button onClick={prevOffer} className="rhp-hot-nav prev">
              <ChevronLeft size={18} />
            </button>
            <span className="rhp-hot-counter">{currentIndex + 1}/{offers.length}</span>
            <button onClick={nextOffer} className="rhp-hot-nav next">
              <ChevronRight size={18} />
            </button>
          </div>
        )}
      </div>
      
      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          className="rhp-hot-offer-card"
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -50 }}
          transition={{ duration: 0.3 }}
        >
          {currentOffer.image && (
            <div className="rhp-hot-offer-image">
              <img src={getImageUrl(currentOffer.image, 'banner')} alt={currentOffer.title} />
            </div>
          )}
          <div className="rhp-hot-offer-content">
            <div className="rhp-hot-offer-badge">{getOfferBadge(currentOffer)}</div>
            <h4>{currentOffer.title}</h4>
            <p>{currentOffer.description}</p>
            {currentOffer.min_order_amount > 0 && (
              <div className="rhp-hot-offer-min">Min. order: ${currentOffer.min_order_amount}</div>
            )}
            <button className="rhp-hot-offer-btn">Grab Offer</button>
          </div>
          <div className="rhp-hot-offer-icon">
            {getOfferIcon(currentOffer.offer_type)}
          </div>
        </motion.div>
      </AnimatePresence>
      
      {offers.length > 1 && (
        <div className="rhp-hot-offers-dots">
          {offers.map((_, idx) => (
            <button
              key={idx}
              className={`rhp-hot-dot ${idx === currentIndex ? 'active' : ''}`}
              onClick={() => setCurrentIndex(idx)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default HotOffersCarousel;