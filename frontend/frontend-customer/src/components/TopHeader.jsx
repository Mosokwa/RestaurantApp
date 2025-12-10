// components/TopHeader.jsx
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import './TopHeader.css';

const TopHeader = ({ onMenuToggle, isMobileMenuOpen }) => {  // ADD isMobileMenuOpen parameter
    const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
    const user = useSelector(state => state.auth.user);
    const navigate = useNavigate();

    const handleProfileClick = () => {
        navigate('/profile');
    };

    const handleCartClick = () => {
        navigate('/cart');
    };

    return (
        <header className="top-header">
            <div className="header-container">
                {/* Left section: Logo + Hamburger (mobile) */}
                <div className="header-left">
                    {/* Logo */}
                    <div className="header-logo">
                        <img 
                            src="/logo.png" 
                            alt="TastyBites" 
                            className="logo-image"
                        />
                        <span className="logo-text">TastyBites</span>
                    </div>
                    
                    {/* Mobile hamburger menu */}
                    <button 
                        className="mobile-menu-toggle"
                        onClick={onMenuToggle}
                        aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
                    >
                        <span className={`hamburger ${isMobileMenuOpen ? 'open' : ''}`}>
                            <span></span>
                            <span></span>
                            <span></span>
                        </span>
                    </button>
                </div>

                {/* Right side icons */}
                <div className="header-icons">
                    {/* Search Icon */}
                    <button className="header-icon" aria-label="Search">
                        <i className="fas fa-search"></i>
                    </button>

                    {/* Cart Icon */}
                    <button 
                        className="header-icon cart-icon" 
                        onClick={handleCartClick}
                        aria-label="Shopping Cart"
                    >
                        <i className="fas fa-shopping-cart"></i>
                        <span className="cart-badge">0</span>
                    </button>

                    {/* Profile Icon */}
                    <button 
                        className="header-icon profile-icon"
                        onClick={handleProfileClick}
                        aria-label="User Profile"
                    >
                        {user?.profile_picture ? (
                            <img 
                                src={user.profile_picture} 
                                alt="Profile" 
                                className="profile-image"
                            />
                        ) : (
                            <i className="fas fa-user"></i>
                        )}
                    </button>
                </div>
            </div>
        </header>
    );
};

export default TopHeader;