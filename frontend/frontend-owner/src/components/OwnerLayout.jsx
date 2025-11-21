import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Outlet } from 'react-router-dom';
import OwnerHeader from './OwnerHeader';
import OwnerSidebar from './OwnerSidebar';
import OwnerFooter from './OwnerFooter';
import { fetchOwnerProfile } from '../store/slices/ownerAuthSlice';
import './styles/OwnerLayout.css';

const OwnerLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector(state => state.auth);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchOwnerProfile());
    }
    
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
      if (window.innerWidth <= 768) {
        setSidebarOpen(false);
      } else {
        // Restore sidebar state from localStorage
        const savedSidebarState = localStorage.getItem('sidebarOpen');
        setSidebarOpen(savedSidebarState ? JSON.parse(savedSidebarState) : true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, [dispatch, isAuthenticated]);

  const toggleSidebar = () => {
    const newState = !sidebarOpen;
    setSidebarOpen(newState);
    // Persist sidebar state
    localStorage.setItem('sidebarOpen', JSON.stringify(newState));
  };

  const closeSidebar = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  return (
    <div className="owner-layout">
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div className="sidebar-overlay" onClick={closeSidebar} />
      )}
      
      <OwnerSidebar 
        isOpen={sidebarOpen}
        onToggle={toggleSidebar}
        isMobile={isMobile}
      />
      
      <div className={`main-content ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <OwnerHeader 
          onToggleSidebar={toggleSidebar}
          sidebarOpen={sidebarOpen}
        />
        <main className="content-area" onClick={closeSidebar}>
          <Outlet />
        </main>
        <OwnerFooter />
      </div>
    </div>
  );
};

export default OwnerLayout;