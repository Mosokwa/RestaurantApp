import { useState } from 'react';
import Navigation from './Navigation';
import Footer from "./Footer";
import Sidebar from "./Sidebar";
import TopHeader from "./TopHeader";
import { Outlet, useLocation } from "react-router-dom";
import { useSelector } from 'react-redux';
import "./Layout.css"

const Layout = () => {
    const location = useLocation();
    const { isAuthenticated } = useSelector(state => state.auth);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    
    // Check if we're on auth pages
    const isAuthPage = ['/login', '/signup', '/verify-email'].includes(location.pathname);
    
    const toggleMobileMenu = () => {
        setIsMobileMenuOpen(!isMobileMenuOpen);
    };

    return (
        <div className={`layout ${isAuthPage ? 'auth-page' : ''}`}>
            {/* Top Header only for authenticated users (not on auth pages) */}
            {!isAuthPage && isAuthenticated && (
                <TopHeader 
                    onMenuToggle={toggleMobileMenu}
                    isMobileMenuOpen={isMobileMenuOpen}  // ADD THIS LINE
                />
            )}
            
            {/* Navigation only for non-authenticated users */}
            {!isAuthPage && !isAuthenticated && <Navigation />}
            
            {/* Sidebar only for authenticated users */}
            {!isAuthPage && isAuthenticated && (
                <Sidebar 
                    isMobileMenuOpen={isMobileMenuOpen}
                    onMobileMenuToggle={toggleMobileMenu}
                />
            )}
            
            <main className={`main-content ${!isAuthPage && isAuthenticated ? 'with-sidebar with-header' : ''}`}>
                <Outlet/>
            </main>
            
            {!isAuthPage && <Footer/>}
        </div>
    );
};

export default Layout;