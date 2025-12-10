// components/Sidebar.jsx
import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useLocation, useNavigate } from 'react-router-dom';
import LogoutButton from './LogoutButton';
import './Sidebar.css';

const Sidebar = ({ isMobileMenuOpen, onMobileMenuToggle }) => {
    const [isDesktopExpanded, setIsDesktopExpanded] = useState(true);
    const [isMobile, setIsMobile] = useState(false);
    const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
    const user = useSelector(state => state.auth.user);
    const location = useLocation();
    const navigate = useNavigate();

    // Check if mobile
    useEffect(() => {
        const checkMobile = () => {
            const mobile = window.innerWidth < 768;
            setIsMobile(mobile);
        };

        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Handle link click
    const handleLinkClick = (path) => {
        navigate(path);
        if (isMobile && onMobileMenuToggle) {
            onMobileMenuToggle(); // Close sidebar on mobile after clicking
        }
    };

    // Toggle desktop sidebar
    const toggleDesktopSidebar = () => {
        setIsDesktopExpanded(!isDesktopExpanded);
    };

    const sidebarLinks = [
        { path: '/', label: 'Home', icon: 'fas fa-home' },
        { path: '/restaurants', label: 'Restaurants', icon: 'fas fa-utensils' },
        { path: '/explore', label: 'Explore', icon: 'fas fa-compass' },
        { path: '/orders', label: 'My Orders', icon: 'fas fa-receipt' },
        { path: '/favorites', label: 'Favorites', icon: 'fas fa-heart' },
        { path: '/profile', label: 'Profile', icon: 'fas fa-user' },
        { path: '/settings', label: 'Settings', icon: 'fas fa-cog' },
    ];

    // Render sidebar content
    const renderSidebarContent = () => {
        const showLabels = isMobile ? isMobileMenuOpen : isDesktopExpanded;

        return (
            <>
                {/* User Profile Section */}
                {isAuthenticated && user && showLabels && (
                    <div className="sidebar-user">
                        <div className="user-avatar">
                            {user.profile_picture ? (
                                <img 
                                    src={user.profile_picture} 
                                    alt={user.username} 
                                />
                            ) : (
                                <i className="fas fa-user"></i>
                            )}
                        </div>
                        <div className="user-info">
                            <span className="user-name">{user.first_name || user.username}</span>
                            <span className="user-email">{user.email}</span>
                        </div>
                    </div>
                )}

                {/* Navigation Links */}
                <div className="sidebar-links">
                    {sidebarLinks.map((link, index) => (
                        <button
                            key={index}
                            className={`sidebar-link ${location.pathname === link.path ? 'active' : ''}`}
                            onClick={() => handleLinkClick(link.path)}
                            aria-label={link.label}
                            style={{ '--i': index }}
                        >
                            <i className={link.icon}></i>
                            {showLabels && <span>{link.label}</span>}
                            {!showLabels && !isMobile && (
                                <div className="tooltip">{link.label}</div>
                            )}
                        </button>
                    ))}
                </div>

                {/* Logout Button */}
                <div className="sidebar-footer">
                    <LogoutButton className="sidebar-link logout-btn">
                        <i className="fas fa-sign-out-alt"></i>
                        {showLabels && <span>Logout</span>}
                        {!showLabels && !isMobile && (
                            <div className="tooltip">Logout</div>
                        )}
                    </LogoutButton>
                </div>
            </>
        );
    };

    // Desktop sidebar
    if (!isMobile) {
        return (
            <nav className={`sidebar ${isDesktopExpanded ? 'expanded' : 'collapsed'}`}>
                <div className="sidebar-header">
                    <button 
                        className="sidebar-toggle"
                        onClick={toggleDesktopSidebar}
                        aria-label={isDesktopExpanded ? "Collapse sidebar" : "Expand sidebar"}
                    >
                        <i className={`fas fa-chevron-${isDesktopExpanded ? 'left' : 'right'}`}></i>
                    </button>
                </div>
                {renderSidebarContent()}
            </nav>
        );
    }

    // Mobile sidebar
    return (
        <>
            <nav className={`sidebar mobile ${isMobileMenuOpen ? 'expanded' : 'collapsed'}`}>
                {/* Close button at top for mobile */}
                {isMobileMenuOpen && (
                    <div className="sidebar-mobile-header">
                        <button 
                            className="sidebar-close-mobile"
                            onClick={onMobileMenuToggle}
                            aria-label="Close menu"
                        >
                            <i className="fas fa-times"></i>
                            <span>Close Menu</span>
                        </button>
                    </div>
                )}
                
                {renderSidebarContent()}
            </nav>

            {/* Overlay for mobile - NO BLUR */}
            {isMobileMenuOpen && (
                <div 
                    className="sidebar-overlay visible"
                    onClick={onMobileMenuToggle}
                ></div>
            )}
        </>
    );
};

export default Sidebar;