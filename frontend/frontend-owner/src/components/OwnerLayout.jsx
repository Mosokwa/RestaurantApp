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
  const { owner, currentRestaurant } = useSelector(state => state.ownerAuth);

  useEffect(() => {
    dispatch(fetchOwnerProfile());
    
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
      if (window.innerWidth <= 768) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, [dispatch]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
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