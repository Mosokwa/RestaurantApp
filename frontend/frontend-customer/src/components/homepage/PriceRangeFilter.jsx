import { useState, useEffect } from 'react';
import './Homepage.css';

const PriceRangeFilter = ({ location }) => {
  const [selectedRange, setSelectedRange] = useState(null);
  const [loading, setLoading] = useState(true);
  const [ranges, setRanges] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPriceRangeData();
  }, [location]);

  const fetchPriceRangeData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let url = '/api/homepage/price-ranges/';
      
      const params = new URLSearchParams();
      if (location?.city) params.append('city', location.city);
      if (location?.lat && location?.lng) {
        params.append('lat', location.lat);
        params.append('lng', location.lng);
      }
      
      if (params.toString()) url += `?${params.toString()}`;

      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch price ranges');
      
      const data = await response.json();
      
      const rangeColors = {
        '$': { color: '#90BE6D', label: 'Budget Eats' },
        '$$': { color: '#4D908E', label: 'Mid Range' },
        '$$$': { color: '#F8961E', label: 'Premium Dining' },
        '$$$$': { color: '#F94144', label: 'Luxury Experience' }
      };
      
      const formattedRanges = data.map(range => ({
        id: range.range,
        range: range.range,
        label: rangeColors[range.range]?.label || range.label,
        description: range.description || `$${range.min_price}+ per person`,
        symbol: range.range,
        color: rangeColors[range.range]?.color || '#4D908E',
        minPrice: range.min_price,
        maxPrice: range.max_price,
        restaurantCount: range.count
      }));
      
      setRanges(formattedRanges);
    } catch (error) {
      console.error('Error fetching price range data:', error);
      setError('Unable to load price ranges');
      setRanges([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRangeSelect = (rangeId) => {
    setSelectedRange(rangeId === selectedRange ? null : rangeId);
    console.log(`Selected price range: ${rangeId}`);
  };

  if (loading && ranges.length === 0) {
    return (
      <section className="price-range-filter">
        <div className="section-header">
          <h2>Filter by Price Range</h2>
          <span className="section-badge">
            Find your price point
          </span>
        </div>
        <div className="price-ranges-container loading">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="price-range-btn skeleton"></div>
          ))}
        </div>
      </section>
    );
  }

  if (error || ranges.length === 0) {
    return null;
  }

  return (
    <section className="price-range-filter">
      <div className="section-header">
        <h2>Filter by Price Range</h2>
        <span className="section-badge">
          Find your price point
        </span>
      </div>
      
      <div className="price-ranges-container">
        {ranges.map((range) => (
          <button
            key={range.id}
            className={`price-range-btn ${selectedRange === range.id ? 'active' : ''}`}
            onClick={() => handleRangeSelect(range.id)}
            style={{
              '--range-color': range.color,
            }}
          >
            <div className="price-range-header">
              <span className="range-symbol" style={{ color: range.color }}>
                {range.symbol}
              </span>
              <span className="range-label">{range.label}</span>
            </div>
            <p className="range-description">{range.description}</p>
            <div className="range-stats">
              <span className="price-display">
                ${range.minPrice}+
              </span>
              <span className="restaurant-count">
                {range.restaurantCount} {range.restaurantCount === 1 ? 'restaurant' : 'restaurants'}
              </span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
};

export default PriceRangeFilter;