// components/common/LoadMoreButton.jsx
import './LoadMoreButton.css';

const LoadMoreButton = ({ loading, onClick, disabled = false }) => {
  return (
    <div className="load-more-container">
      <button
        className="load-more-btn"
        onClick={onClick}
        disabled={loading || disabled}
      >
        {loading ? 'Loading...' : 'Load More'}
      </button>
    </div>
  );
};

export default LoadMoreButton;