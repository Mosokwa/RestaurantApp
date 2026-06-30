// src/pages/restaurant/components/CategoryTabs.jsx
import React, { useRef, useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const CategoryTabs = ({ categories, selectedCategory, onCategoryChange }) => {
  const scrollRef = useRef(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);
  
  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };
  
  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [categories]);
  
  const scroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 200;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };
  
  if (!categories || categories.length === 0) return null;
  
  return (
    <div className="rhp-category-tabs-wrapper">
      {showLeftArrow && (
        <button className="rhp-category-scroll-btn left" onClick={() => scroll('left')}>
          <ChevronLeft size={18} />
        </button>
      )}
      
      <div className="rhp-category-tabs" ref={scrollRef} onScroll={checkScroll}>
        {categories.map((category) => (
          <button
            key={category.category_id}
            className={`rhp-category-tab ${selectedCategory?.category_id === category.category_id ? 'rhp-active' : ''}`}
            onClick={() => onCategoryChange(category)}
          >
            {category.name}
            {category.item_count > 0 && (
              <span className="rhp-category-count">{category.item_count}</span>
            )}
          </button>
        ))}
      </div>
      
      {showRightArrow && (
        <button className="rhp-category-scroll-btn right" onClick={() => scroll('right')}>
          <ChevronRight size={18} />
        </button>
      )}
    </div>
  );
};

export default CategoryTabs;