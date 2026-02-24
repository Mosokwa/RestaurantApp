import './LoadingSkeleton.css';

const LoadingSkeleton = () => {
  return (
    <div className="loading-skeleton-container">
      {/* Skeleton Header */}
      <div className="skeleton-header">
        <div className="skeleton-title" />
        <div className="skeleton-controls">
          <div className="skeleton-select" />
          <div className="skeleton-toggle" />
        </div>
      </div>

      {/* Skeleton Grid */}
      <div className="skeleton-grid">
        {[...Array(8)].map((_, index) => (
          <div key={index} className="skeleton-card glass-card">
            <div className="skeleton-image" />
            <div className="skeleton-content">
              <div className="skeleton-name" />
              <div className="skeleton-rating" />
              <div className="skeleton-meta">
                <div className="skeleton-cuisine" />
                <div className="skeleton-distance" />
              </div>
              <div className="skeleton-footer">
                <div className="skeleton-price" />
                <div className="skeleton-delivery" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LoadingSkeleton;