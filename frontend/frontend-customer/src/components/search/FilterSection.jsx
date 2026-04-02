// pages/SearchResultsPage/components/FilterSection.jsx
import { useState, useEffect, useRef } from 'react';

const FilterSection = ({ activeFilters, onFilterChange, results }) => {
  const [isSticky, setIsSticky] = useState(false);
  const [expandedFilter, setExpandedFilter] = useState(null);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const filterRefs = useRef({});

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      const offset = window.scrollY;
      setIsSticky(offset > 200);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (expandedFilter) {
        const isOutside = !filterRefs.current[expandedFilter]?.contains(event.target);
        if (isOutside) {
          setExpandedFilter(null);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [expandedFilter]);

  const toggleFilter = (filterName) => {
    setExpandedFilter(expandedFilter === filterName ? null : filterName);
  };

  const filterGroups = [
    {
      id: 'type',
      title: 'Show',
      icon: '🔍',
      options: [
        { value: 'all', label: 'All Results', count: results?.total_results },
        { value: 'restaurants', label: 'Restaurants', count: results?.sections?.find(s => s.type === 'restaurants')?.count },
        { value: 'dishes', label: 'Dishes', count: results?.sections?.find(s => s.type === 'menu_items')?.count },
        { value: 'cuisines', label: 'Cuisines', count: results?.sections?.find(s => s.type === 'cuisines')?.count },
        { value: 'categories', label: 'Categories', count: results?.sections?.find(s => s.type === 'categories')?.count }
      ]
    },
    {
      id: 'dietary',
      title: 'Dietary',
      icon: '🥗',
      options: [
        { value: '', label: 'Any' },
        { value: 'vegetarian', label: 'Vegetarian' },
        { value: 'vegan', label: 'Vegan' },
        { value: 'gluten_free', label: 'Gluten Free' }
      ]
    },
    {
      id: 'price_range',
      title: 'Price',
      icon: '💰',
      options: [
        { value: '', label: 'Any' },
        { value: '$', label: '$ (Budget)' },
        { value: '$$', label: '$$ (Moderate)' },
        { value: '$$$', label: '$$$ (Expensive)' },
        { value: '$$$$', label: '$$$$ (Premium)' }
      ]
    }
  ];

  const sortOptions = [
    { value: 'relevance', label: 'Relevance' },
    { value: 'rating', label: 'Top Rated' },
    { value: 'popularity', label: 'Most Popular' },
    { value: 'price_low', label: 'Price: Low to High' },
    { value: 'price_high', label: 'Price: High to Low' }
  ];

  return (
    <div className={`sr-filter-bar ${isSticky ? 'sr-filter-sticky' : ''}`}>
      <div className="sr-filter-left">
        <div className="sr-sort-wrapper">
          <span className="sr-sort-icon">⚡</span>
          <select 
            value={activeFilters.sortBy}
            onChange={(e) => onFilterChange('sortBy', e.target.value)}
            className="sr-sort-select"
          >
            {sortOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="sr-filter-right">
        {filterGroups.map((group, index) => (
          <div 
            key={group.id} 
            className={`sr-filter-chip-wrapper ${expandedFilter === group.id ? 'sr-expanded' : ''} ${index === filterGroups.length - 1 ? 'sr-last-chip' : ''}`}
            ref={el => filterRefs.current[group.id] = el}
          >
            <button 
              className={`sr-filter-chip ${activeFilters[group.id] && activeFilters[group.id] !== 'all' && activeFilters[group.id] !== '' ? 'sr-chip-active' : ''}`}
              onClick={() => toggleFilter(group.id)}
            >
              <span>{group.icon}</span>
              <span>{group.title}</span>
              {activeFilters[group.id] && activeFilters[group.id] !== 'all' && activeFilters[group.id] !== '' && (
                <span className="sr-chip-active-dot"></span>
              )}
              <span className="sr-chip-arrow">{expandedFilter === group.id ? '▲' : '▼'}</span>
            </button>
            
            {expandedFilter === group.id && (
              <div className="sr-filter-dropdown">
                <div className="sr-dropdown-header">
                  <span className="sr-dropdown-title">{group.icon} {group.title}</span>
                  <button className="sr-dropdown-close" onClick={() => setExpandedFilter(null)}>✕</button>
                </div>
                <div className="sr-dropdown-options">
                  {group.options.map(option => (
                    <button
                      key={option.value}
                      className={`sr-dropdown-item ${activeFilters[group.id] === option.value ? 'sr-item-active' : ''}`}
                      onClick={() => {
                        onFilterChange(group.id, option.value);
                        if (isMobile) {
                          setExpandedFilter(null);
                        }
                      }}
                    >
                      <span className="sr-item-label">{option.label}</span>
                      {option.count !== undefined && option.count > 0 && (
                        <span className="sr-item-count">{option.count}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}

        {Object.values(activeFilters).some(v => v && v !== 'all' && v !== 'relevance' && v !== '') && (
          <button 
            className="sr-clear-filters"
            onClick={() => {
              onFilterChange('type', 'all');
              onFilterChange('sortBy', 'relevance');
              onFilterChange('dietary', '');
              onFilterChange('price_range', '');
            }}
            title="Clear all filters"
          >
            ✕
          </button>
        )}
      </div>

      {isMobile && expandedFilter && (
        <div className="sr-dropdown-overlay" onClick={() => setExpandedFilter(null)} />
      )}
    </div>
  );
};

export default FilterSection;