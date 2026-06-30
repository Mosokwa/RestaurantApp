// src/pages/restaurant/components/HeroBanner.jsx
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Heart, Share2, ChevronLeft, ChevronRight, ShoppingBag, Calendar,
  Clock, MapPin, Star
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import getImageUrl from '../../utils/imageHelper';

const HeroBanner = ({ restaurant, operationalInfo, diningMode, onDiningModeChange, isDineIn, tableInfo }) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  const bannerImages = [
    restaurant.banner_image,
    ...(restaurant.gallery_images || [])
  ].filter(Boolean);
  
  const hasMultipleImages = bannerImages.length > 1;
  
  const nextImage = () => {
    if (hasMultipleImages) {
      setCurrentImageIndex((prev) => (prev + 1) % bannerImages.length);
    }
  };
  
  const prevImage = () => {
    if (hasMultipleImages) {
      setCurrentImageIndex((prev) => (prev - 1 + bannerImages.length) % bannerImages.length);
    }
  };
  
  const handleFavorite = () => {
    setIsFavorited(!isFavorited);
    toast.success(isFavorited ? 'Removed from favorites' : 'Added to favorites');
  };
  
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: restaurant.name,
          text: restaurant.description,
          url: window.location.href
        });
      } catch (err) {
        navigator.clipboard.writeText(window.location.href);
        toast.success('Link copied!');
      }
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast.success('Link copied!');
    }
  };
  
  const currentBannerUrl = bannerImages.length > 0 
    ? getImageUrl(bannerImages[currentImageIndex], 'banner')
    : getImageUrl(null, 'banner');
  
  return (
    <div className="rhp-hero">
      {/* Banner Image */}
      <div className="rhp-hero-image-container">
        <img 
          src={currentBannerUrl}
          alt={restaurant.name}
          className="rhp-hero-background"
        />
        <div className="rhp-hero-overlay"></div>
        
        {hasMultipleImages && (
          <>
            <div className="rhp-hero-dots">
              {bannerImages.map((_, idx) => (
                <button
                  key={idx}
                  className={`rhp-hero-dot ${idx === currentImageIndex ? 'active' : ''}`}
                  onClick={() => setCurrentImageIndex(idx)}
                />
              ))}
            </div>
            <button className="rhp-hero-arrow prev" onClick={prevImage}>
              <ChevronLeft size={24} />
            </button>
            <button className="rhp-hero-arrow next" onClick={nextImage}>
              <ChevronRight size={24} />
            </button>
          </>
        )}
      </div>
      
      {/* Content Overlay */}
      <div className="rhp-hero-content">
        {/* Logo */}
        <div className="rhp-hero-logo">
          <img src={getImageUrl(restaurant.logo, 'logo')} alt={restaurant.name} />
        </div>
        
        {/* Restaurant Info */}
        <div className="rhp-hero-info">
          <h1>{restaurant.name}</h1>
          
          {/* Dining Mode Selector - Integrated Here */}
          <div className="rhp-hero-dining-mode">
            <button 
              className={`rhp-dining-btn ${diningMode === 'delivery' ? 'active' : ''}`}
              onClick={() => onDiningModeChange('delivery')}
            >
              <ShoppingBag size={14} />
              Delivery
            </button>
            <button 
              className={`rhp-dining-btn ${diningMode === 'pickup' ? 'active' : ''}`}
              onClick={() => onDiningModeChange('pickup')}
            >
              <Clock size={14} />
              Pickup
            </button>
            {!isDineIn && (
              <button 
                className="rhp-hero-btn primary"
                onClick={() => document.querySelector('.rhp-main-toggle')?.click()}
              >
                <ShoppingBag size={16} />
                Order Now
              </button>
            )}
          </div>
          
          {/* Action Buttons */}
          <div className="rhp-hero-actions">
            {restaurant.reservation_enabled && (
              <button className="rhp-hero-btn secondary">
                <Calendar size={16} />
                Reserve
              </button>
            )}
            <button className="rhp-hero-btn icon" onClick={handleFavorite}>
              <Heart fill={isFavorited ? '#e63946' : 'none'} />
            </button>
            <button className="rhp-hero-btn icon" onClick={handleShare}>
              <Share2 size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;