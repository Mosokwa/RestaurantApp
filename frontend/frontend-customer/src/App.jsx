// src/App.jsx
import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Homepage from './pages/Homepage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import EmailVerification from './pages/EmailVerification';
import Restaurants from './pages/Restaurants';
import SearchResultsPage from './pages/SearchResultPage';
import csrfService from './services/csrf';
import RestaurantsExplorer from './pages/RestaurantsExplorer';

function App() {
  useEffect(() =>{
    const initializeCSRF = async () =>{
      try {
        await csrfService.ensureToken();
      }
      catch (error) {
        console.warn('CSRF token initialization failed:', error);
      }
    };
    initializeCSRF();
  }, []);

  useEffect(() => {
    // Force viewport recalculation on mobile devices
    const handleViewport = () => {
      const viewport = document.querySelector('meta[name="viewport"]');
      if (viewport) {
        // Toggle the viewport to force recalculation
        viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
      }
    };

    // Run on mount and after a short delay to ensure DOM is ready
    handleViewport();
    setTimeout(handleViewport, 100);
    
    // Also run on resize
    window.addEventListener('resize', handleViewport);
    return () => window.removeEventListener('resize', handleViewport);
  }, []);

  return (
    <Provider store={store}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout/>}>
            <Route index element={
              <ProtectedRoute>
                <Homepage/>
              </ProtectedRoute>
              }/>
            <Route path="/login" element={
              <ProtectedRoute requireAuth={false}>
                <Login/>
              </ProtectedRoute>
            }/>
            <Route path="/signup" element={
              <ProtectedRoute requireAuth={false}>
                <Signup />
              </ProtectedRoute>
            }/>
            <Route path="/verify-email" element={
              <ProtectedRoute requireAuth={false}>
                <EmailVerification />
              </ProtectedRoute>
            }/>
            <Route path='/restaurants' element={
              <ProtectedRoute>
                <RestaurantsExplorer />
              </ProtectedRoute>
            }/>
            <Route path="/search" element={
              <ProtectedRoute>
                <SearchResultsPage />
              </ProtectedRoute>
            } />
          </Route>
        </Routes>
      </Router>
    </Provider>
  );
}

export default App;