// components/Navigation.jsx
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

    // Don't render if authenticated (sidebar will be shown instead)
    if (isAuthenticated) {
        return null;
    }

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
        navigate('/login');
        closeMenu();
    };

    const handleCartClick = () => {
        navigate('/login', { state: { from: location.pathname } });
        closeMenu();
    };

    return (
        <>
            <nav className={`navigation ${isScrolled ? 'scrolled' : ''} ${isHomePage ? 'home-page' : ''}`}>
                <div className="nav-container">
                    {/* Logo on the left */}
                    <Link to="/" className="nav-logo" onClick={closeMenu}>
                        <img 
                            src="/logo.png" 
                            alt="Restaurant App Logo" 
                            className="logo-image"
                        />
                        <span className="logo-text">TastyBites</span>
                    </Link>

                    {/* Right side icons - only show when NOT authenticated */}
                    {!isAuthenticated && (
                        <div className="nav-icons">
                            {/* Search Icon */}
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
                                <span className="cart-badge">0</span>
                            </button>

                            {/* Profile Icon */}
                            <button 
                                className="nav-icon profile-icon"
                                onClick={handleProfileClick}
                                aria-label="User Profile"
                            >
                                <i className="fas fa-user"></i>
                            </button>

                            {/* Login/Register Links for desktop */}
                            <div className="desktop-auth-links">
                                <Link to="/login" className="nav-link">Login</Link>
                                <Link to="/signup" className="nav-link signup-btn">Sign Up</Link>
                            </div>

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
                    )}
                </div>
            </nav>

            {/* Mobile Menu for non-authenticated users */}
            <div className={`mobile-menu ${isMenuOpen ? 'open' : ''}`}>
                <div className="mobile-menu-content">
                    <div className="mobile-nav-links">
                        <Link to="/" className="mobile-nav-link" onClick={closeMenu}>
                            <i className="fas fa-home"></i>
                            Home
                        </Link>
                        <Link to="/restaurants" className="mobile-nav-link" onClick={closeMenu}>
                            <i className="fas fa-utensils"></i>
                            Restaurants
                        </Link>
                        <Link to="/explore" className="mobile-nav-link" onClick={closeMenu}>
                            <i className="fas fa-compass"></i>
                            Explore
                        </Link>
                    </div>

                    <div className="mobile-auth-links">
                        <Link to="/login" className="mobile-auth-link" onClick={closeMenu}>
                            <i className="fas fa-sign-in-alt"></i>
                            Login
                        </Link>
                        <Link to="/signup" className="mobile-auth-link" onClick={closeMenu}>
                            <i className="fas fa-user-plus"></i>
                            Sign Up
                        </Link>
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