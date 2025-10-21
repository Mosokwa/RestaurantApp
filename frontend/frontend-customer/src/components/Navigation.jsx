// components/Navigation.jsx
import LogoutButton from './LogoutButton';
import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import './Navigation.css';

const Navigation = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const user = useSelector(state => state.auth.user);
  const location = useLocation();
  const navigate = useNavigate();

  const isRestaurantPage = location.pathname.includes('/restaurant/');
  const isHomePage = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const handleProfileClick = () => {
    if (isAuthenticated) {
      navigate('/profile');
    } else {
      navigate('/login');
    }
    closeMenu();
  };

  const handleCartClick = () => {
    if (isAuthenticated) {
      navigate('/cart');
    } else {
      navigate('/login', { state: { from: location.pathname } });
    }
    closeMenu();
  };

  // Restaurant page navigation links
  const restaurantLinks = [
    { path: '#home', label: 'Home' },
    { path: '#menu', label: 'Menu' },
    { path: '#about', label: 'About Us' },
    { path: '#reservation', label: 'Book a Table' }
  ];

  // General navigation links
  const generalLinks = [
    { path: '/', label: 'Home' },
    { path: '/restaurants', label: 'Restaurants' },
    { path: '/explore', label: 'Explore' }
  ];

  const currentLinks = isRestaurantPage ? restaurantLinks : generalLinks;

  return (
    <>
      <nav className={`navigation ${isScrolled ? 'scrolled' : ''} ${isHomePage ? 'home-page' : ''}`}>
        <div className="nav-container">
          {/* Logo */}
          <Link to="/" className="nav-logo" onClick={closeMenu}>
            <img 
              src="/logo.png" 
              alt="Restaurant App Logo" 
              className="logo-image"
            />
            <span className="logo-text">TastyBites</span>
          </Link>

          {/* Desktop Navigation Links */}
          <div className="nav-links">
            {currentLinks.map((link, index) => (
              <a
                key={index}
                href={link.path}
                className="nav-link"
                onClick={(e) => {
                  if (link.path.startsWith('#')) {
                    e.preventDefault();
                    const element = document.querySelector(link.path);
                    if (element) {
                      element.scrollIntoView({ behavior: 'smooth' });
                    }
                  }
                  closeMenu();
                }}
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Right Side Icons */}
          <div className="nav-icons">
            {/* Search Icon (optional) */}
            <button className="nav-icon" aria-label="Search">
              <i className="fas fa-search"></i>
            </button>

            {/* Cart Icon */}
            <button 
              className="nav-icon cart-icon" 
              onClick={handleCartClick}
              aria-label="Shopping Cart"
            >
              <i className="fas fa-shopping-cart"></i>
              <span className="cart-badge">3</span>
            </button>

            {/* Profile Icon */}
            <button 
              className="nav-icon profile-icon"
              onClick={handleProfileClick}
              aria-label="User Profile"
            >
              {isAuthenticated && user?.profile_picture ? (
                <img 
                  src={user.profile_picture} 
                  alt="Profile" 
                  className="profile-image"
                />
              ) : (
                <i className="fas fa-user"></i>
              )}
            </button>
            { isAuthenticated && <LogoutButton className='logout-btn'>Logout</LogoutButton>}

            {/* Mobile Menu Toggle */}
            <button 
              className="mobile-menu-toggle"
              onClick={toggleMenu}
              aria-label="Toggle menu"
            >
              <span className={`hamburger ${isMenuOpen ? 'open' : ''}`}>
                <span></span>
                <span></span>
                <span></span>
              </span>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Menu */}
      <div className={`mobile-menu ${isMenuOpen ? 'open' : ''}`}>
        <div className="mobile-menu-content">
          {/* Mobile Navigation Links */}
          <div className="mobile-nav-links">
            {currentLinks.map((link, index) => (
              <a
                key={index}
                href={link.path}
                className="mobile-nav-link"
                onClick={(e) => {
                  if (link.path.startsWith('#')) {
                    e.preventDefault();
                    const element = document.querySelector(link.path);
                    if (element) {
                      element.scrollIntoView({ behavior: 'smooth' });
                    }
                  }
                  closeMenu();
                }}
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Mobile Auth Links */}
          <div className="mobile-auth-links">
            {isAuthenticated ? (
              <>
                <Link to="/profile" className="mobile-auth-link" onClick={closeMenu}>
                  <i className="fas fa-user"></i>
                  My Profile
                </Link>
                <Link to="/orders" className="mobile-auth-link" onClick={closeMenu}>
                  <i className="fas fa-receipt"></i>
                  My Orders
                </Link>
                <button 
                  className="mobile-auth-link logout-btn"
                  onClick={() => {
                    authService.logout();
                    closeMenu();
                  }}
                >
                  <i className="fas fa-sign-out-alt"></i>
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="mobile-auth-link" onClick={closeMenu}>
                  <i className="fas fa-sign-in-alt"></i>
                  Login
                </Link>
                <Link to="/signup" className="mobile-auth-link" onClick={closeMenu}>
                  <i className="fas fa-user-plus"></i>
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Overlay for mobile menu */}
      {isMenuOpen && (
        <div className="mobile-menu-overlay" onClick={closeMenu}></div>
      )}
    </>
  );
};

export default Navigation;