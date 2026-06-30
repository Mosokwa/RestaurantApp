// src/pages/restaurant/RestaurantHomepage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { 
  Star, Clock, MapPin, Phone, Heart, Share2, 
  ChevronLeft, ChevronRight, ShoppingBag, Calendar, 
  Award, Gift, Sparkles, Users, ExternalLink, ArrowRight,
  Utensils, Tag, MessageCircle, CheckCircle, Coffee, Pizza, Wifi, ParkingCircle, Music
} from 'lucide-react';

// Components
import HeroBanner from '../../components/restaurant/HeroBanner';
import RestaurantSearchBar from '../../components/restaurant/RestaurantSearchBar';
import OfferCarousel from '../../components/restaurant/OfferCarousel';
import CategoryTabs from '../../components/restaurant/CategoryTabs';
import MenuItemCard from '../../components/restaurant/MenuItemCard';
import MenuItemModal from '../../components/restaurant/MenuItemModal';
import ReviewsSection from '../../components/restaurant/ReviewsSection';
import LoyaltyBanner from '../../components/restaurant/LoyaltyBanner';
import StickyOrderBar from '../../components/restaurant/StickyOrderBar';
import StoryGallery from '../../components/restaurant/StoryGallery';
import HotOffersCarousel from '../../components/restaurant/HotOffersCarousel';

// Redux
import {
  fetchRestaurantHomepage,
  fetchMenuItemsByCategory,
  searchRestaurantItems,
  setCurrentCategory,
  setSearchQuery,
  toggleItemModal,
  setSelectedMenuItem,
  setActiveTab
} from '../../store/slices/restaurantHomepageSlice';

// Hooks
import { useCart } from '../../hooks/useCart';
import getImageUrl from '../../utils/imageHelper';

// Styles
import './styles/RestaurantHomepage.css';

const RestaurantHomepage = () => {
  const { restaurantId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { addToCart, cartItems, getCartTotal, getItemCount } = useCart();
  
  const {
    restaurant,
    specialOffers,
    reservationInfo,
    reviewsPreview,
    loyaltyInfo,
    operationalInfo,
    currentCategory,
    categories,
    menuItems,
    searchQuery,
    searchResults,
    isSearching,
    loading,
    error,
    activeTab,
    itemModalOpen,
    selectedMenuItem,
    menuLoading
  } = useSelector((state) => state.restaurantHomepage);
  
  const [diningMode, setDiningMode] = useState('delivery');
  const [tableQRCode, setTableQRCode] = useState(null);
  const [selectedGalleryIndex, setSelectedGalleryIndex] = useState(null);
  const [showFullStory, setShowFullStory] = useState(false);
  const [menuCarouselIndex, setMenuCarouselIndex] = useState(0);
  const [previewSection, setPreviewSection] = useState('reviews');
  
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const table = urlParams.get('table');
    const branch = urlParams.get('branch');
    
    if (table && branch) {
      setDiningMode('dine_in');
      setTableQRCode({ table, branch });
      toast.success(`Welcome! You're dining at Table ${table}`);
    }
  }, []);
  
  useEffect(() => {
    if (restaurantId) {
      dispatch(fetchRestaurantHomepage(restaurantId));
    }
  }, [restaurantId, dispatch]);
  
  useEffect(() => {
    if (currentCategory && !searchQuery && activeTab === 'menu') {
      dispatch(fetchMenuItemsByCategory({
        restaurantId,
        categoryId: currentCategory.category_id,
        page: 1
      }));
    }
  }, [currentCategory, restaurantId, searchQuery, activeTab, dispatch]);
  
  const handleSearch = (query) => {
    dispatch(setSearchQuery(query));
    if (query && query.length >= 2) {
      dispatch(searchRestaurantItems({ restaurantId, query }));
    }
  };
  
  const handleCategoryChange = (category) => {
    dispatch(setCurrentCategory(category));
    setMenuCarouselIndex(0);
  };
  
  const handleMenuItemClick = (item) => {
    dispatch(setSelectedMenuItem(item));
    dispatch(toggleItemModal(true));
  };
  
  const handleAddToCart = (item, selectedModifiers, quantity, specialInstructions) => {
    const cartItem = {
      item_id: item.item_id,
      name: item.name,
      price: parseFloat(item.price),
      image: item.image,
      quantity,
      selectedModifiers,
      specialInstructions,
      diningMode,
      tableInfo: diningMode === 'dine_in' ? tableQRCode : null,
      restaurantId: restaurant?.restaurant_id,
      restaurantName: restaurant?.name,
      preparationTime: item.preparation_time
    };
    
    addToCart(cartItem);
    toast.success(`Added ${quantity}x ${item.name} to cart`);
    dispatch(toggleItemModal(false));
  };
  
  const previewMenuItems = menuItems.slice(0, 4);
  const hasMoreItems = menuItems.length > 4;
  
  const nextMenuSlide = () => {
    if (menuCarouselIndex + 2 < previewMenuItems.length) {
      setMenuCarouselIndex(menuCarouselIndex + 2);
    }
  };
  
  const prevMenuSlide = () => {
    if (menuCarouselIndex - 2 >= 0) {
      setMenuCarouselIndex(menuCarouselIndex - 2);
    }
  };
  
  const allGalleryImages = restaurant?.gallery_images || [];
  const storyText = restaurant?.story_description || restaurant?.description || '';
  const previewStory = storyText.length > 150 ? storyText.substring(0, 150) + '...' : storyText;
  
  if (loading && !restaurant) {
    return (
      <div className="rhp-loading">
        <div className="rhp-loading-spinner"></div>
        <p>Loading restaurant...</p>
      </div>
    );
  }
  
  if (error || !restaurant) {
    let errorMessage = 'Unable to load restaurant information';
    if (typeof error === 'string') errorMessage = error;
    else if (error?.detail) errorMessage = error.detail;
    
    return (
      <div className="rhp-error">
        <span className="rhp-error-emoji">🍽️</span>
        <h2>Restaurant Not Found</h2>
        <p>{errorMessage}</p>
        <button onClick={() => navigate('/')} className="rhp-btn-primary">
          Back to Home
        </button>
      </div>
    );
  }
  
  return (
    <div className="rhp-main-content">
      {/* Hero Banner */}
      <HeroBanner
        restaurant={restaurant}
        operationalInfo={operationalInfo}
        diningMode={diningMode}
        onDiningModeChange={setDiningMode}
        isDineIn={diningMode === 'dine_in'}
        tableInfo={tableQRCode}
      />

      {/* Quick Stats */}
      <div className="rhp-quick-stats">
        <div className="rhp-stat">
          <Star size={16} fill="#FFD700" color="#FFD700" />
          <span>{restaurant.overall_rating}</span>
          <small>({restaurant.total_reviews})</small>
        </div>
        <div className="rhp-stat-divider"></div>
        <div className="rhp-stat">
          <Clock size={16} />
          <span>{operationalInfo?.is_open_now ? 'Open Now' : 'Closed'}</span>
        </div>
        <div className="rhp-stat-divider"></div>
        <div className="rhp-stat">
          <MapPin size={16} />
          <span>{restaurant.contact_info?.address?.split(',')[0] || 'Location'}</span>
        </div>
        <div className="rhp-stat-divider"></div>
        <div className="rhp-stat">
          <Phone size={16} />
          <span>{restaurant.phone_number}</span>
        </div>
      </div>

      {/* Search Bar */}
      <RestaurantSearchBar
        onSearch={handleSearch}
        searchQuery={searchQuery}
        isSearching={isSearching}
        restaurantId={restaurantId}
      />

      {/* Main Toggle Buttons */}
      <div className="rhp-main-toggles">
        <button 
          className={`rhp-toggle-main ${activeTab === 'menu' ? 'active' : ''}`}
          onClick={() => dispatch(setActiveTab('menu'))}
        >
          <Utensils size={18} />
          <span>Menu</span>
        </button>
        <button 
          className={`rhp-toggle-main ${activeTab === 'offers' ? 'active' : ''}`}
          onClick={() => dispatch(setActiveTab('offers'))}
        >
          <Tag size={18} />
          <span>Offers</span>
        </button>
        <button 
          className={`rhp-toggle-main ${activeTab === 'bestselling' ? 'active' : ''}`}
          onClick={() => dispatch(setActiveTab('bestselling'))}
        >
          <Award size={18} />
          <span>Best Selling</span>
        </button>
      </div>

      {/* Category Tabs */}
      {activeTab === 'menu' && categories.length > 0 && (
        <CategoryTabs
          categories={categories}
          selectedCategory={currentCategory}
          onCategoryChange={handleCategoryChange}
        />
      )}

      {/* Content Area */}
      <div className="rhp-content-area">
        {/* Menu Tab */}
        {activeTab === 'menu' && (
          <div className="rhp-menu-carousel">
            <div className="rhp-carousel-header">
              <h3>{currentCategory?.name || 'Popular Items'}</h3>
              {hasMoreItems && (
                <button className="rhp-view-all">View All <ArrowRight size={14} /></button>
              )}
            </div>
            <div className="rhp-carousel-wrapper">
              {previewMenuItems.length > 2 && (
                <button className="rhp-arrow prev" onClick={prevMenuSlide} disabled={menuCarouselIndex === 0}>
                  <ChevronLeft size={24} />
                </button>
              )}
              <div className="rhp-carousel-track">
                {(isSearching ? searchResults : previewMenuItems).slice(menuCarouselIndex, menuCarouselIndex + 2).map((item) => (
                  <MenuItemCard key={item.item_id} item={item} onClick={() => handleMenuItemClick(item)} />
                ))}
              </div>
              {previewMenuItems.length > 2 && (
                <button className="rhp-arrow next" onClick={nextMenuSlide} disabled={menuCarouselIndex + 2 >= previewMenuItems.length}>
                  <ChevronRight size={24} />
                </button>
              )}
            </div>
          </div>
        )}

        {/* Offers Tab */}
        {activeTab === 'offers' && specialOffers?.length > 0 && (
          <OfferCarousel offers={specialOffers} />
        )}

        {/* Best Selling Tab */}
        {activeTab === 'bestselling' && (
          <div className="rhp-bestselling-grid">
            {menuItems.filter(item => item.popularity_score > 100).slice(0, 4).map((item) => (
              <MenuItemCard key={item.item_id} item={item} onClick={() => handleMenuItemClick(item)} />
            ))}
          </div>
        )}
      </div>

      {/* Hot Offers Section */}
      {specialOffers && specialOffers.length > 0 && (
        <HotOffersCarousel offers={specialOffers} title="🔥 Hot Offers" />
      )}

      {/* Trending Offers Section */}
      {specialOffers && specialOffers.filter(o => o.is_featured).length > 0 && (
        <HotOffersCarousel 
          offers={specialOffers.filter(o => o.is_featured)} 
          title="⭐ Trending Offers" 
        />
      )}

      {/* Story & Gallery Section */}
      {storyText && (
        <StoryGallery 
          restaurant={restaurant}
          storyText={storyText}
          galleryImages={allGalleryImages}
        />
      )}

      {/* Toggleable Sections */}
      <div className="rhp-toggle-section">
        <div className="rhp-toggle-headers">
          <button className={`rhp-toggle-header ${previewSection === 'reviews' ? 'active' : ''}`} onClick={() => setPreviewSection('reviews')}>
            <MessageCircle size={16} /> Reviews
          </button>
          {loyaltyInfo?.enabled && (
            <button className={`rhp-toggle-header ${previewSection === 'loyalty' ? 'active' : ''}`} onClick={() => setPreviewSection('loyalty')}>
              <Gift size={16} /> Loyalty
            </button>
          )}
          {reservationInfo?.has_reservations && (
            <button className={`rhp-toggle-header ${previewSection === 'reservations' ? 'active' : ''}`} onClick={() => setPreviewSection('reservations')}>
              <Calendar size={16} /> Reserve
            </button>
          )}
        </div>
        <div className="rhp-toggle-body">
          {previewSection === 'reviews' && reviewsPreview && <ReviewsSection restaurantId={restaurantId} preview={reviewsPreview} />}
          {previewSection === 'loyalty' && loyaltyInfo?.enabled && <LoyaltyBanner loyaltyInfo={loyaltyInfo} restaurantId={restaurant?.restaurant_id} />}
          {previewSection === 'reservations' && reservationInfo?.has_reservations && (
            <div className="rhp-reserve-card">
              <Calendar size={32} />
              <div>
                <h4>Table Reservation</h4>
                <p>Up to {reservationInfo.party_size_limits?.max || 20} guests</p>
                {reservationInfo.deposit_required && <small>Deposit: ${reservationInfo.deposit_amount}</small>}
              </div>
              <button className="rhp-btn-primary" onClick={() => toast.info('Reservation coming soon')}>Book Now</button>
            </div>
          )}
        </div>
      </div>

      {/* Sticky Cart */}
      {getItemCount() > 0 && (
        <StickyOrderBar
          cartItems={cartItems}
          cartTotal={getCartTotal()}
          itemCount={getItemCount()}
          diningMode={diningMode}
          onCheckout={() => navigate('/checkout', { state: { restaurant, diningMode, tableInfo: tableQRCode, cartItems } })}
        />
      )}

      {/* Modals */}
      <MenuItemModal isOpen={itemModalOpen} onClose={() => dispatch(toggleItemModal(false))} item={selectedMenuItem} onAddToCart={handleAddToCart} diningMode={diningMode} />
      
      <AnimatePresence>
        {selectedGalleryIndex !== null && (
          <div className="rhp-lightbox" onClick={() => setSelectedGalleryIndex(null)}>
            <div className="rhp-lightbox-content" onClick={(e) => e.stopPropagation()}>
              <button className="rhp-lightbox-close" onClick={() => setSelectedGalleryIndex(null)}>✕</button>
              <img src={getImageUrl(allGalleryImages[selectedGalleryIndex], 'banner')} alt="Gallery" />
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RestaurantHomepage;