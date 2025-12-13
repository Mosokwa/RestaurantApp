import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// import './Homepage.css';

const PriceRangeFilter = ({ location }) => {
  const [priceRanges, setPriceRanges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeRange, setActiveRange] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPriceRanges();
  }, [location]);

  const fetchPriceRanges = async () => {
    try {
      setLoading(true);
      
      let url = '/api/homepage/price-ranges/';
      if (location?.city) url += `?city=${encodeURIComponent(location.city)}`;
      if (location?.lat && location?.lng) {
        url += `${location.city ? '&' : '?'}lat=${location.lat}&lng=${location.lng}`;
      }

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch price ranges');
      
      const data = await response.json();
      setPriceRanges(data);
    } catch (error) {
      console.error('Error fetching price ranges:', error);
      setPriceRanges([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePriceRangeClick = (priceRange) => {
    setActiveRange(priceRange.range);
    
    // Navigate to search with price filter
    navigate(`/search?min_price=${priceRange.min_price}&max_price=${priceRange.max_price}`);
  };

  const getRangeColor = (range) => {
    switch (range) {
      case '$': return '#90BE6D'; // Green for budget
      case '$$': return '#F9C74F'; // Yellow for moderate
      case '$$$': return '#F8961E'; // Orange for expensive
      case '$$$$': return '#F94144'; // Red for luxury
      default: return '#4D908E';
    }
  };

  if (loading && priceRanges.length === 0) {
    return (
      <section className="price-range-filter">
        <h2>Filter by Price</h2>
        <div className="price-ranges-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="price-range-btn skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (priceRanges.length === 0) {
    return null;
  }

  return (
    <section className="price-range-filter">
      <h2>Filter by Price</h2>
      <div className="price-ranges-container">
        {priceRanges.map((range) => (
          <button
            key={range.range}
            className={`price-range-btn ${activeRange === range.range ? 'active' : ''}`}
            onClick={() => handlePriceRangeClick(range)}
            style={{
              '--range-color': getRangeColor(range.range),
              '--range-hover-color': `${getRangeColor(range.range)}CC`
            }}
          >
            <div className="price-range-header">
              <span className="range-symbol">{range.range}</span>
              <span className="range-label">{range.label}</span>
            </div>
            <p className="range-description">{range.description}</p>
            <div className="range-stats">
              <span className="restaurant-count">
                {range.count} {range.count === 1 ? 'restaurant' : 'restaurants'}
              </span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
};

export default PriceRangeFilter;