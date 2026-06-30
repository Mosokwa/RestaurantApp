// src/pages/restaurant/components/StoryGallery.jsx
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, ExternalLink, Wifi, ParkingCircle, Music, Users } from 'lucide-react';
import getImageUrl from '../../utils/imageHelper';

const StoryGallery = ({ restaurant, storyText, galleryImages }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [showFullStory, setShowFullStory] = useState(false);
  
  const previewStory = storyText.length > 200 ? storyText.substring(0, 200) + '...' : storyText;
  const displayImages = galleryImages.slice(0, 4);
  
  return (
    <div className="rhp-story-gallery">
      <div className="rhp-story-gallery-container">
        {/* Left Side - Gallery Images */}
        <div className="rhp-gallery-side">
          <div className="rhp-gallery-grid-small">
            {displayImages.map((img, idx) => (
              <div 
                key={idx} 
                className="rhp-gallery-small-item"
                onClick={() => setSelectedImage(img)}
              >
                <img src={getImageUrl(img, 'banner')} alt={`Gallery ${idx + 1}`} />
                <div className="rhp-gallery-small-overlay">
                  <ExternalLink size={16} />
                </div>
              </div>
            ))}
          </div>
          {galleryImages.length > 4 && (
            <button className="rhp-view-more-gallery">
              +{galleryImages.length - 4} more photos
            </button>
          )}
        </div>
        
        {/* Right Side - Story */}
        <div className="rhp-story-side">
          <div className="rhp-story-side-header">
            <h3>Our Story</h3>
            <div className="rhp-story-line"></div>
          </div>
          <div className="rhp-story-side-text">
            <p>{showFullStory ? storyText : previewStory}</p>
            {storyText.length > 200 && (
              <button className="rhp-read-more-story" onClick={() => setShowFullStory(!showFullStory)}>
                {showFullStory ? 'Read Less' : 'Read More'}
              </button>
            )}
          </div>
          {restaurant.amenities?.length > 0 && (
            <div className="rhp-story-amenities">
              <h4>Amenities</h4>
              <div className="rhp-amenities-list">
                {restaurant.amenities.map((a, idx) => (
                  <span key={idx} className="rhp-amenity-tag">
                    {a === 'WiFi' && <Wifi size={12} />}
                    {a === 'Parking' && <ParkingCircle size={12} />}
                    {a === 'Outdoor Seating' && <Users size={12} />}
                    {a === 'Live Music' && <Music size={12} />}
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Lightbox Modal */}
      <AnimatePresence>
        {selectedImage && (
          <div className="rhp-lightbox" onClick={() => setSelectedImage(null)}>
            <div className="rhp-lightbox-content" onClick={(e) => e.stopPropagation()}>
              <button className="rhp-lightbox-close" onClick={() => setSelectedImage(null)}>✕</button>
              <img src={getImageUrl(selectedImage, 'banner')} alt="Full view" />
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default StoryGallery;