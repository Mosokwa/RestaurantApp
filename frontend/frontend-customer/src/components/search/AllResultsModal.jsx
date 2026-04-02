// pages/SearchResultsPage/components/AllResultsModal.jsx
import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import RestaurantResultCard from './RestaurantResultCard';
import DishResultCard from './DishResultCard';
import CuisineResultCard from './CuisineResultcard';
import CategoryResultCard from './CategoryResultCard';

const AllResultsModal = ({ 
  isOpen, 
  onClose, 
  sectionType, 
  sectionTitle, 
  sectionIcon, 
  sectionColor,
  initialItems = [],
  totalCount,
  searchQuery,
  onLoadPage,
  currentPage = 1,
  totalPages = 1
}) => {
  const [items, setItems] = useState(initialItems);
  const [page, setPage] = useState(currentPage);
  const [pages, setPages] = useState(totalPages);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Log modal opening for debugging
  useEffect(() => {
    if (isOpen) {
      console.log(`📊 MODAL OPENED - ${sectionTitle}:`, {
        initialItems: initialItems.length,
        totalCount: totalCount,
        currentPage: currentPage,
        totalPages: totalPages,
        hasMore: currentPage < totalPages,
        remaining: totalCount - initialItems.length
      });
    }
  }, [isOpen, initialItems.length, totalCount, currentPage, totalPages, sectionTitle]);

  // Reset when modal opens with new data
  useEffect(() => {
    if (isOpen) {
      setItems(initialItems);
      setPage(currentPage);
      setPages(totalPages);
      setError(null);
    }
  }, [isOpen, initialItems, currentPage, totalPages]);

  // Body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => { document.body.style.overflow = 'unset'; };
    }
  }, [isOpen]);

  // Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleLoadMore = async () => {
    if (isLoading) return;
    if (page >= pages) {
      setError('All items loaded');
      return;
    }
    
    const nextPage = page + 1;
    setIsLoading(true);
    setError(null);
    
    try {
      console.log(`📤 Loading page ${nextPage} of ${pages} for ${sectionType}`);
      const result = await onLoadPage(nextPage);
      
      console.log('📥 Load more result:', {
        newItems: result.items?.length,
        pagination: result.pagination
      });
      
      if (result.items && result.items.length > 0) {
        setItems(prev => [...prev, ...result.items]);
        setPage(result.pagination.current_page);
        setPages(result.pagination.total_pages);
      } else {
        setError('No more items to load');
      }
    } catch (err) {
      console.error('Load more error:', err);
      setError('Failed to load more items');
    } finally {
      setIsLoading(false);
    }
  };

  const getComponent = () => {
    switch (sectionType) {
      case 'restaurants': return RestaurantResultCard;
      case 'menu_items': return DishResultCard;
      case 'cuisines': return CuisineResultCard;
      case 'categories': return CategoryResultCard;
      default: return null;
    }
  };

  const Component = getComponent();
  const hasMore = page < pages;
  const remaining = totalCount - items.length;

  if (!isOpen) return null;

  return createPortal(
    <div className="sr-modal-overlay" onClick={onClose}>
      <div className="sr-modal-container" onClick={e => e.stopPropagation()}>
        <div className="sr-modal-header" style={{ borderBottomColor: sectionColor }}>
          <div className="sr-modal-title-wrapper">
            <span className="sr-modal-icon" style={{ backgroundColor: `${sectionColor}20`, color: sectionColor }}>
              {sectionIcon}
            </span>
            <h2 className="sr-modal-title">
              {sectionTitle}
              <span className="sr-modal-count" style={{ backgroundColor: sectionColor }}>
                {totalCount}
              </span>
            </h2>
          </div>
          <button className="sr-modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="sr-modal-context">
          Showing results for "<span className="sr-modal-query">{searchQuery}</span>"
        </div>

        <div className="sr-modal-results">
          {/* Status Bar */}
          <div style={{
            background: 'rgba(0,0,0,0.2)',
            padding: '0.8rem 1rem',
            marginBottom: '1.5rem',
            borderRadius: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            borderLeft: `4px solid ${sectionColor}`
          }}>
            <span>📊 Showing {items.length} of {totalCount} results</span>
            <span>📄 Page {page} of {pages}</span>
          </div>

          {items.length > 0 ? (
            <>
              <div className="sr-modal-grid">
                {items.map((item, index) => (
                  <div key={`${sectionType}-${page}-${index}`} className="sr-modal-grid-item">
                    {Component && (
                      <Component 
                        {...(sectionType === 'menu_items' ? { dish: item } : 
                            sectionType === 'restaurants' ? { restaurant: item } :
                            sectionType === 'cuisines' ? { cuisine: item } :
                            { category: item })} 
                      />
                    )}
                  </div>
                ))}
              </div>

              {hasMore && (
                <div className="sr-modal-load-more-container">
                  <button 
                    className="sr-modal-load-more-btn"
                    onClick={handleLoadMore}
                    disabled={isLoading}
                    style={{ borderColor: sectionColor, color: sectionColor }}
                  >
                    {isLoading ? (
                      <>Loading page {page + 1} of {pages}...</>
                    ) : (
                      <>Load More ({remaining} remaining)</>
                    )}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="sr-modal-no-results">
              <p>No {sectionTitle.toLowerCase()} found</p>
            </div>
          )}
        </div>

        <div className="sr-modal-footer">
          <div className="sr-modal-pagination">
            {items.length === totalCount ? (
              <span style={{ color: '#4cc9f0' }}>✓ All {totalCount} results loaded</span>
            ) : (
              <span>Showing {items.length} of {totalCount} results</span>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};

export default AllResultsModal;