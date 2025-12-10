import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { GoogleOAuthProvider } from '@react-oauth/google';
import store from './store';
import { initializeCSRF, loadUserFromToken, completeOnboarding } from './store/slices/authSlice';
import OwnerLogin from './pages/OwnerLogin';
import DashboardOverview from './pages/DashboardOverview';
import RestaurantSelectionPage from './pages/RestaurantSelectionPage';
import RestaurantsManagementPage from './pages/RestaurantsManagementPage';
import OwnerRegister from './pages/OwnerRegister';
import TwoFactorAuth from './components/verification/TwoFactorAuth';
import ProtectedRoute from './components/ProtectedRoute';
import CSRFErrorBoundary from './components/CSRFErrorBoundary';
import OwnerLayout from './components/OwnerLayout';
import VerifyEmailRoute from './components/verification/VerifyEmailRoute';
import ComponentErrorBoundary from './components/ComponentErrorBoundary';
import PublicRoute from './components/PublicRoute';
import RestaurantOnboarding from './components/onboarding/RestaurantOnboarding';
import MenuBuilderPage from './pages/MenuBuilderPage';
import CategoriesPage from './pages/CategoriesPage';
import ItemsPage from './pages/ItemsPage';
import ModifiersPage from './pages/ModifiersPage';

// Placeholder components for demonstration
const OrdersPage = () => <div className="p-6">Orders Management Page</div>;
const SalesAnalyticsPage = () => <div className="p-6">Sales Analytics Page</div>;
const CustomerInsightsPage = () => <div className="p-6">Customer Insights Page</div>;
const MenuPerformancePage = () => <div className="p-6">Menu Performance Page</div>;
const ExportReportsPage = () => <div className="p-6">Export Reports Page</div>;
const TeamPage = () => <div className="p-6">Team Management Page</div>;
const RolesPage = () => <div className="p-6">Roles & Permissions Page</div>;
const SchedulesPage = () => <div className="p-6">Schedules Page</div>;
const BasicInfoPage = () => <div className="p-6">Basic Info Page</div>;
const BranchesPage = () => <div className="p-6">Branches Page</div>;
const HoursPage = () => <div className="p-6">Operating Hours Page</div>;
const IntegrationsPage = () => <div className="p-6">Integrations Page</div>;
const OffersPage = () => <div className="p-6">Special Offers Page</div>;
const LoyaltyPage = () => <div className="p-6">Loyalty Program Page</div>;
const CommunicationsPage = () => <div className="p-6">Customer Communications Page</div>;


// Auto Redirect Handler
const AutoRedirectHandler = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, requires2FA, loading } = useSelector(state => state.auth);

  useEffect(() => {
    if (loading) return;

    const currentPath = location.pathname;
    const pendingEmail = localStorage.getItem('pendingVerificationEmail');
    const isAuthPage = currentPath === '/login' || currentPath === '/register';

    console.log('🔄 AutoRedirect Check:', {
      currentPath,
      isAuthenticated,
      isAuthPage
    });

    // UNAUTHENTICATED USER: Only handle email verification
    if (!isAuthenticated) {
      if (pendingEmail && !currentPath.includes('/verify-email')) {
        navigate('/verify-email', { replace: true });
      }
      return;
    }

    // AUTHENTICATED USER: Only handle critical redirects
    if (isAuthenticated && user) {
      // Handle unverified email
      if (!user.email_verified && !currentPath.includes('/verify-email') && !currentPath.includes('/logout')) {
        navigate('/verify-email', { replace: true });
        return;
      }

      // Handle 2FA
      if (requires2FA && !currentPath.includes('/2fa')) {
        navigate('/2fa', { replace: true });
        return;
      }

      // ONLY redirect from auth pages to dashboard
      if (user.email_verified && isAuthPage) {
        navigate('/owner/dashboard', { replace: true });
        return;
      }
    }
  }, [navigate, location.pathname, isAuthenticated, user, requires2FA, loading]);

  return children;
};


// Fixed DashboardRoute 
const DashboardRoute = () => {
  const { user } = useSelector(state => state.auth);
  const { currentRestaurant, restaurants, loading: restaurantsLoading } = useSelector(state => state.ownerAuth);
  
  const hasPendingRestaurantSetup = localStorage.getItem('pendingRestaurantSetup') === 'true';
  const userHasNoRestaurants = !restaurants || restaurants.length === 0;

  // Safety check for user object
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading user data...</p>
        </div>
      </div>
    );
  }

  // Show loading while restaurants are being fetched
  if (restaurantsLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your restaurants...</p>
        </div>
      </div>
    );
  }

  console.log('🏠 DashboardRoute State:', {
    hasPendingRestaurant: hasPendingRestaurantSetup,
    restaurantsCount: restaurants?.length,
    hasCurrentRestaurant: !!currentRestaurant,
    userEmail: user.email
  });

  // ONLY redirect to onboarding if user has no restaurants AND has pending setup
  if (userHasNoRestaurants && hasPendingRestaurantSetup) {
    console.log('🔄 Redirecting to onboarding - new user with pending setup');
    return <Navigate to="/owner/onboarding" replace />;
  }

  // CRITICAL: If user has restaurants but no current restaurant selected, show selection
  // This ensures user always explicitly selects a restaurant first
  if (!currentRestaurant && !userHasNoRestaurants) {
    console.log('📋 Showing restaurant selection - no restaurant selected');
    return <RestaurantSelectionPage />;
  }

  // User has restaurants and one is selected - show dashboard
  console.log('✅ Rendering dashboard for:', currentRestaurant?.name);
  return <DashboardOverview />;
};

// Add this hook to App.jsx
const useLocalStorageValidation = () => {
  useEffect(() => {
    const validateLocalStorage = () => {
      try {
        const token = localStorage.getItem('token');
        
        // If no token, clear all user-related data
        if (!token) {
          localStorage.removeItem('currentRestaurant');
          localStorage.removeItem('pendingRestaurantSetup');
          localStorage.removeItem('pendingRestaurantData');
          localStorage.removeItem('sidebarOpen');
          return;
        }
        
        // Validate token format
        if (token.split('.').length !== 3) {
          console.warn('Invalid token format, clearing...');
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('currentRestaurant');
          localStorage.removeItem('sidebarOpen');
        }
        
      } catch (error) {
        console.error('LocalStorage validation error:', error);
        // Clear only problematic items, keep others
        localStorage.removeItem('currentRestaurant');
        localStorage.removeItem('pendingRestaurantSetup');
        localStorage.removeItem('pendingRestaurantData');
      }
    };

    validateLocalStorage();
  }, []);
};

// Temporary - Add to App.jsx
const AuthStateDebug = () => {
  const auth = useSelector(state => state.auth);
  
  useEffect(() => {
    console.log('🔍 AUTH STATE INSPECTION:', {
      isAuthenticated: auth.isAuthenticated,
      user: auth.user,
      userType: typeof auth.user,
      userKeys: auth.user ? Object.keys(auth.user) : 'No user',
      hasDataProperty: auth.user?.data ? 'YES' : 'NO',
      emailVerified: auth.user?.email_verified
    });
  }, [auth]);
  
  return null;
};


// Component to handle CSRF initialization
const AppContent = () => {
  useLocalStorageValidation();
  const dispatch = useDispatch();
  const { csrfInitialized, loading, isAuthenticated, user } = useSelector(state => state.auth);
  const { restaurants } = useSelector(state => state.ownerAuth);
  const [appInitialized, setAppInitialized] = useState(false);


  useEffect(() => {
    const initializeAppSafely = async () => {
      // Prevent multiple initializations
      if (appInitialized) {
        console.log('✅ App already initialized, skipping...');
        return;
      }

      try {
        console.log('🔄 Starting app initialization...');
        
        // Initialize CSRF first - this will prevent duplicates internally
        await dispatch(initializeCSRF()).unwrap();
        
        // Check for token and load user only if we have one
        const token = localStorage.getItem('token');
        if (token) {
          console.log('🔐 Token found, loading user...');
          await dispatch(loadUserFromToken()).unwrap();
        } else {
          console.log('❌ No token found, skipping user load');
        }
        
        console.log('✅ App initialization complete');
        setAppInitialized(true);
      } catch (error) {
        console.error('App initialization error:', error);
        setAppInitialized(true); // Still mark as initialized to prevent blocking
      }
    };
    
    initializeAppSafely();
  }, [dispatch, appInitialized]);

  useEffect(() => {
    if (isAuthenticated && restaurants && restaurants.length > 0) {
      const hasPendingFlag = localStorage.getItem('pendingRestaurantSetup') === 'true';
      if (hasPendingFlag) {
        console.log('🧹 Cleaning up stale pending restaurant flag - user has restaurants');
        localStorage.removeItem('pendingRestaurantSetup');
        localStorage.removeItem('pendingRestaurantData');
        dispatch(completeOnboarding());
      }
    }
  }, [isAuthenticated, restaurants, dispatch]);



  if (!appInitialized || (csrfInitialized === false && loading)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Initializing security...</p>
        </div>
      </div>
    );
  }
  
  return (
    <CSRFErrorBoundary>
      <AuthStateDebug />
      <Router>
        <AutoRedirectHandler>
          <Routes>
            {/* Public Routes - No Layout */}
            <Route path="/register" element={
              <PublicRoute restricted redirectTo='/owner/dashboard'>
                <OwnerRegister />
              </PublicRoute>
            } />
            <Route path="/login" element={
              <PublicRoute restricted redirectTo='/owner/dashboard'>
                <OwnerLogin />
              </PublicRoute>
            } />

            {/* Auth Flow Routes - No Layout */}
            <Route 
              path="/verify-email" 
              element={ 
                <PublicRoute restricted>
                  <VerifyEmailRoute />
                </PublicRoute>
               }  
            />
            <Route path="/2fa" element={
              <PublicRoute restricted={false}>
                <TwoFactorAuth />
              </PublicRoute>
            } />

            {/* Protected Routes - With Layout */}
            <Route 
              path="/owner" 
              element={
                <ProtectedRoute ownerOnly>
                  <ComponentErrorBoundary>
                    <OwnerLayout />
                  </ComponentErrorBoundary>
                </ProtectedRoute>
              }
            >
              <Route 
                path="onboarding" 
                element={<RestaurantOnboarding />} 
              />
              {/* Dashboard */}
              <Route 
                path="dashboard" 
                element={<DashboardRoute />} 
              />

              <Route 
                path="restaurants" 
                element={<RestaurantsManagementPage />} 
              />
              
              {/* Orders */}
              <Route path="orders" element={<OrdersPage />} />
              
              {/* Menu Management */}
              <Route path="menu/builder" element={<MenuBuilderPage />} />
              <Route path="menu/categories" element={<CategoriesPage />} />
              <Route path="menu/items" element={<ItemsPage />} />
              <Route path="menu/modifiers" element={<ModifiersPage />} />
              
              {/* Analytics & Reports */}
              <Route path="analytics/sales" element={<SalesAnalyticsPage />} />
              <Route path="analytics/customers" element={<CustomerInsightsPage />} />
              <Route path="analytics/menu" element={<MenuPerformancePage />} />
              <Route path="analytics/reports" element={<ExportReportsPage />} />
              
              {/* Staff Management */}
              <Route path="staff/team" element={<TeamPage />} />
              <Route path="staff/roles" element={<RolesPage />} />
              <Route path="staff/schedules" element={<SchedulesPage />} />
              
              {/* Restaurant Settings */}
              <Route path="settings/basic" element={<BasicInfoPage />} />
              <Route path="settings/branches" element={<BranchesPage />} />
              <Route path="settings/hours" element={<HoursPage />} />
              <Route path="settings/integrations" element={<IntegrationsPage />} />
              
              {/* Marketing */}
              <Route path="marketing/offers" element={<OffersPage />} />
              <Route path="marketing/loyalty" element={<LoyaltyPage />} />
              <Route path="marketing/communications" element={<CommunicationsPage />} />
              
              {/* Catch-all for /owner - redirect to dashboard */}
              <Route path="" element={<Navigate to="dashboard" replace />} />

            </Route>
            
            {/* Redirects */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            {/* 404 Page - You might want to add this */}
            <Route path="*" element={<div className="min-h-screen flex items-center justify-center">Page Not Found</div>} />
            
          </Routes>
        </AutoRedirectHandler>
      </Router>
    </CSRFErrorBoundary>
  );
};

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <Provider store={store}>
        <AppContent />
      </Provider>
    </GoogleOAuthProvider>
  );
}

export default App;