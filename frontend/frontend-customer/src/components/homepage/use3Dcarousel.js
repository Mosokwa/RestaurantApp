import { useState, useEffect, useCallback } from 'react';

const use3DCarousel = (items, itemsToShow = 5) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isHovering, setIsHovering] = useState(false);

  const totalItems = items?.length || 0;

  // Auto-rotate when not hovering
  useEffect(() => {
    if (!isHovering && totalItems > itemsToShow) {
      const interval = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % totalItems);
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [isHovering, totalItems, itemsToShow]);

  const handlePrev = useCallback(() => {
    setCurrentIndex(prev => (prev - 1 + totalItems) % totalItems);
  }, [totalItems]);

  const handleNext = useCallback(() => {
    setCurrentIndex(prev => (prev + 1) % totalItems);
  }, [totalItems]);

  const calculateCardPosition = useCallback((index) => {
    if (totalItems === 0) return { transform: 'none' };

    // Calculate how far this item is from current index
    let relativeIndex = index - currentIndex;
    
    // Handle wrap-around for proper positioning
    if (relativeIndex > Math.floor(totalItems / 2)) {
      relativeIndex -= totalItems;
    } else if (relativeIndex < -Math.floor(totalItems / 2)) {
      relativeIndex += totalItems;
    }

    // Calculate position based on relative index
    const angleStep = 360 / Math.min(totalItems, itemsToShow);
    const angle = relativeIndex * angleStep;
    const radius = 500; // Base radius
    
    // Convert to radians
    const angleRad = (angle * Math.PI) / 180;
    
    // Calculate 3D position
    const x = radius * Math.sin(angleRad);
    const z = radius * Math.cos(angleRad) - radius;
    
    // Adjust opacity and scale based on position
    const distance = Math.abs(relativeIndex);
    const opacity = Math.max(0.3, 1 - distance * 0.3);
    const scale = Math.max(0.7, 1 - distance * 0.15);
    
    return {
      transform: `translate3d(${x}px, 0, ${z}px) rotateY(${angle}deg) scale(${scale})`,
      opacity: opacity,
      zIndex: 100 - distance,
      pointerEvents: distance <= 2 ? 'auto' : 'none'
    };
  }, [currentIndex, totalItems, itemsToShow]);

  return {
    currentIndex,
    setCurrentIndex,
    handlePrev,
    handleNext,
    setIsHovering,
    calculateCardPosition,
    totalItems
  };
};

export default use3DCarousel;