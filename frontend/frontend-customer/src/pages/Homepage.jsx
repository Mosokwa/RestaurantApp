import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchPopularRestaurants,
  fetchTrendingDishes,
  fetchPersonalizedRecommendations,
  fetchSpecialOffers,
  setUserLocation,
  loadMorePopularRestaurants,
  loadMoreSpecialOffers,
  loadMoreTrendingDishes
} from '../store/slices/homepageSlice';
import HeroSection from '../components/homepage/HeroSection';
import DishGrid from '../components/homepage/DishGrid';
import SpecialOffers from '../components/homepage/SpecialOffers';
import RestaurantCarousel from '../components/homepage/RestaurantCarousel';
import '../components/homepage/Homepage.css';

const Homepage = () => {
  const dispatch = useDispatch();
  const {
    popularRestaurants,
    trendingDishes,
    personalizedRecommendations,
    specialOffers,
    userLocation,
    isLoading,
    error
  } = useSelector(state => state.homepage);
  
  const { isAuthenticated } = useSelector(state => state.auth);
  const [loadingMore, setLoadingMore] = useState({
    restaurants: false,
    dishes: false,
    offers: false
  });

  

  useEffect(() => {
    const fetchDataWithLocation = async (locationData) => {
      try {
        await Promise.all([
          dispatch(fetchPopularRestaurants({ location: locationData, page: 1 })),
          dispatch(fetchTrendingDishes({ location: locationData, page: 1 })),
          dispatch(fetchSpecialOffers({ location: locationData, page: 1 }))
        ]);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    const fetchData = async () => {
      try {
        await Promise.all([
          dispatch(fetchPopularRestaurants({ page: 1 })),
          dispatch(fetchTrendingDishes({ page: 1 })),
          dispatch(fetchSpecialOffers({ page: 1 }))
        ]);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    // Try to get user's location from browser
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          try {
            const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`);
            const data = await response.json();
            const city = data.city || data.locality;
                        
            const locationData = { city, lat: latitude, lng: longitude };
            dispatch(setUserLocation(locationData));
            await fetchDataWithLocation(locationData);
          } catch (error) {
            console.error('Error getting location data:', error);
            await fetchData();
          }
        },
        (error) => {
          console.error('Error getting location:', error);
          fetchData();
        }
      );
    } else {
      fetchData();
    }
        
    // Fetch personalized recommendations if user is authenticated
    if (isAuthenticated) {
      dispatch(fetchPersonalizedRecommendations({ page: 1 }));
    }
  }, [dispatch, isAuthenticated]);

  const handleLoadMoreRestaurants = async (type) => {
    setLoadingMore(prev => ({ ...prev, restaurants: true }));
    try {
      const nextPage = popularRestaurants.currentPage + 1;
            
      const result = await dispatch(fetchPopularRestaurants({ 
        page: nextPage,
        pageSize: 12
      })).unwrap();

      dispatch(loadMorePopularRestaurants(result));
    } catch (error) {
        console.error('Error loading more:', error);
    } finally {
        setLoadingMore(prev => ({ ...prev, restaurants: false }));
    }
  };

  const handleLoadMoreDishes = async () => {
    setLoadingMore(prev => ({ ...prev, dishes: true }));
    try {
      const nextPage = trendingDishes.currentPage + 1;
      const result = await dispatch(fetchTrendingDishes({ 
        page: nextPage,
        pageSize: 12
      })).unwrap();
      
      dispatch(loadMoreTrendingDishes(result));
    } catch (error) {
      console.error('Error loading more dishes:', error);
    } finally {
      setLoadingMore(prev => ({ ...prev, dishes: false }));
    }
  };

  const handleLoadMoreOffers = async () => {
    setLoadingMore(prev => ({ ...prev, offers: true }));
    try {
      const nextPage = specialOffers.currentPage + 1;
      const result = await dispatch(fetchSpecialOffers({ 
        page: nextPage,
        pageSize: 6
      })).unwrap();
      
      dispatch(loadMoreSpecialOffers(result));
    } catch (error) {
      console.error('Error loading more offers:', error);
    } finally {
      setLoadingMore(prev => ({ ...prev, offers: false }));
    }
  };

  if (error) {
    return (
      <div className="error-container">
        <h2>Something went wrong</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  return (
    <div className="homepage">
      <HeroSection />
      
      <RestaurantCarousel 
        title="Popular Restaurants Near You" 
        restaurants={popularRestaurants.items}
        pagination={popularRestaurants.pagination}
        loading={isLoading && popularRestaurants.items.length === 0}
        onLoadMore={handleLoadMoreRestaurants}
        loadMoreLoading={loadingMore.restaurants}
      />

      <DishGrid 
        title="Trending Dishes in Your Area" 
        dishes={trendingDishes.items}
        pagination={trendingDishes.pagination}
        loading={isLoading && trendingDishes.items.length === 0}
        onLoadMore={handleLoadMoreDishes}
        loadMoreLoading={loadingMore.dishes}
      />
      
      {isAuthenticated && (
        <DishGrid 
          title="Just For You" 
          dishes={personalizedRecommendations.items}
          pagination={personalizedRecommendations.pagination}
          loading={isLoading && personalizedRecommendations.items.length === 0}
          // Note: Personalized recommendations might not need load more
        />
      )}
      
      <SpecialOffers 
        offers={specialOffers.items}
        pagination={specialOffers.pagination}
        loading={isLoading && specialOffers.items.length === 0}
        onLoadMore={handleLoadMoreOffers}
        loadMoreLoading={loadingMore.offers}
      />
      
      <RestaurantCarousel 
        title="Popular Restaurants Near You" 
        restaurants={popularRestaurants.items}
        pagination={popularRestaurants.pagination}
        loading={isLoading && popularRestaurants.items.length === 0}
        onLoadMore={handleLoadMoreRestaurants}
        loadMoreLoading={loadingMore.restaurants}
        //using the same data for demo
      />
    </div>
  );
};

export default Homepage;