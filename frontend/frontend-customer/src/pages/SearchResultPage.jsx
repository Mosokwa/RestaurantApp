// pages/SearchResultsPage/index.jsx
import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { searchService } from '../services/searchService';
import { useDebounce } from '../hooks/useDebounce';
import SearchHeader from '../components/search/SearchHeader';
import FilterSection from '../components/search/FilterSection';
import ResultsSection from '../components/search/ResultsSection';
import AllResultsModal from '../components/search/AllResultsModal';
import './styles/SearchResultsPage.css';

const SearchResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const { isSidebarCollapsed } = useSelector(state => state.layout || { sidebarCollapsed: false });
  
  const queryParams = new URLSearchParams(location.search);
  const initialQuery = queryParams.get('q') || '';
  
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilters, setActiveFilters] = useState({
    type: 'all',
    sortBy: 'relevance',
    dietary: '',
    price_range: ''
  });
  
  const isFirstLoad = useRef(true);
  const ongoingRequest = useRef(null);
  
  const debouncedFilters = useDebounce(activeFilters, 500);
  const prevFiltersRef = useRef(debouncedFilters);
  
  const [modalState, setModalState] = useState({
    isOpen: false,
    sectionType: null,
    sectionTitle: '',
    sectionIcon: '',
    sectionColor: '',
    items: [],
    totalCount: 0,
    currentPage: 1,
    totalPages: 1,
    loading: false
  });

  const { userLocation } = useSelector(state => state.exploration);

  const performSearch = useCallback(async () => {
    if (!searchQuery.trim()) return;
    
    if (ongoingRequest.current) {
      ongoingRequest.current.abort();
    }
    
    const filtersChanged = JSON.stringify(prevFiltersRef.current) !== JSON.stringify(debouncedFilters);
    
    if (results && !filtersChanged && results.query === searchQuery && !isFirstLoad.current) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    const controller = new AbortController();
    ongoingRequest.current = controller;
    
    try {
      const data = await searchService.discoverSearch(
        searchQuery, 
        debouncedFilters,
        { signal: controller.signal }
      );
      
      if (ongoingRequest.current === controller) {
        console.log('Search results received:', data);
        setResults(data);
        prevFiltersRef.current = debouncedFilters;
        isFirstLoad.current = false;
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError('Failed to load search results. Please try again.');
        console.error('Search error:', err);
      }
    } finally {
      if (ongoingRequest.current === controller) {
        setLoading(false);
        ongoingRequest.current = null;
      }
    }
  }, [searchQuery, debouncedFilters, results]);

  useEffect(() => {
    if (initialQuery) {
      const timer = setTimeout(() => {
        performSearch();
      }, 300);
      
      return () => clearTimeout(timer);
    }
  }, [initialQuery, debouncedFilters, performSearch]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setResults(null);
      isFirstLoad.current = true;
    }
  };

  const handleFilterChange = (filterType, value) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const handleViewAll = useCallback((sectionInfo) => {
    if (modalState.isOpen) return;
    
    // Get pagination info for this section
    const sectionPagination = results?.pagination?.[sectionInfo.type];
    
    console.log('View All clicked:', {
      type: sectionInfo.type,
      itemsCount: sectionInfo.items.length,
      totalCount: sectionInfo.totalCount,
      pagination: sectionPagination
    });
    
    setModalState({
      isOpen: true,
      sectionType: sectionInfo.type,
      sectionTitle: sectionInfo.title,
      sectionIcon: sectionInfo.icon,
      sectionColor: sectionInfo.color,
      items: sectionInfo.items,
      totalCount: sectionInfo.totalCount,
      currentPage: sectionPagination?.current_page || 1,
      totalPages: sectionPagination?.total_pages || 1,
      loading: false
    });
  }, [modalState.isOpen, results]);

  const handleModalLoadMore = useCallback(async (page) => {
    if (modalState.loading) return { items: [], pagination: {} };
    
    try {
      const result = await searchService.loadMoreSection(
        modalState.sectionType,
        searchQuery,
        page,
        activeFilters
      );
      
      console.log('Load more result in parent:', result);
      
      // Update modal state with new items AND updated pagination
      setModalState(prev => ({
        ...prev,
        items: [...prev.items, ...result.items],
        currentPage: result.pagination.current_page,
        totalPages: result.pagination.total_pages,
        loading: false
      }));
      
      return result;
    } catch (error) {
      console.error('Error loading more items:', error);
      throw error;
    }
  }, [modalState.sectionType, searchQuery, activeFilters]);

  // ✅ ADD THIS MISSING FUNCTION
  const handleCloseModal = useCallback(() => {
    setModalState(prev => ({ ...prev, isOpen: false }));
  }, []);

  return (
    <div className={`sr-page ${isSidebarCollapsed ? 'sr-sidebar-expanded' : ''}`}>
      <SearchHeader 
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearch={handleSearch}
        totalResults={results?.total_results}
      />
      
      <div className="sr-content">
        <FilterSection 
          activeFilters={activeFilters}
          onFilterChange={handleFilterChange}
          results={results}
        />
        
        <div className="sr-results-area">
          {loading && !results ? (
            <div className="sr-loading-container">
              <div className="sr-loading-spinner"></div>
              <p>Searching for "{searchQuery}"...</p>
            </div>
          ) : error ? (
            <div className="sr-error-container">
              <h3>Oops!</h3>
              <p>{error}</p>
              <button onClick={performSearch}>Try Again</button>
            </div>
          ) : results?.total_results === 0 ? (
            <div className="sr-no-results">
              <h2>No results found for "{searchQuery}"</h2>
              <p>Try searching with different keywords or filters</p>
            </div>
          ) : (
            <div className="sr-results-sections">
              {/* Dishes */}
              {results?.sections
                ?.filter(s => s.type === 'menu_items')
                .map(section => (
                  <ResultsSection
                    key={section.type}
                    section={section}
                    items={results.results[section.type] || []}
                    searchQuery={searchQuery}
                    onViewAll={handleViewAll}
                  />
                ))}
              
              {/* Categories */}
              {results?.sections
                ?.filter(s => s.type === 'categories')
                .map(section => (
                  <ResultsSection
                    key={section.type}
                    section={section}
                    items={results.results[section.type] || []}
                    searchQuery={searchQuery}
                    onViewAll={handleViewAll}
                  />
                ))}
              
              {/* Cuisines */}
              {results?.sections
                ?.filter(s => s.type === 'cuisines')
                .map(section => (
                  <ResultsSection
                    key={section.type}
                    section={section}
                    items={results.results[section.type] || []}
                    searchQuery={searchQuery}
                    onViewAll={handleViewAll}
                  />
                ))}
              
              {/* Restaurants */}
              {results?.sections
                ?.filter(s => s.type === 'restaurants')
                .map(section => (
                  <ResultsSection
                    key={section.type}
                    section={section}
                    items={results.results[section.type] || []}
                    searchQuery={searchQuery}
                    onViewAll={handleViewAll}
                  />
                ))}
            </div>
          )}
        </div>
      </div>

      <AllResultsModal
        isOpen={modalState.isOpen}
        onClose={handleCloseModal}
        sectionType={modalState.sectionType}
        sectionTitle={modalState.sectionTitle}
        sectionIcon={modalState.sectionIcon}
        sectionColor={modalState.sectionColor}
        initialItems={modalState.items}
        totalCount={modalState.totalCount}
        searchQuery={searchQuery}
        onLoadPage={handleModalLoadMore}
        currentPage={modalState.currentPage}
        totalPages={modalState.totalPages}
      />
    </div>
  );
};

export default SearchResultsPage;