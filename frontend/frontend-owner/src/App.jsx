import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Provider, useDispatch, useSelector } from 'react-redux';
import { GoogleOAuthProvider } from '@react-oauth/google';
import store from './store';
import { initializeCSRF, loadUserFromToken } from './store/slices/authSlice';
import OwnerLogin from './pages/OwnerLogin';
import DashboardOverview from './pages/DashboardOverview';
import OwnerRegister from './pages/OwnerRegister';
import TwoFactorAuth from './components/verification/TwoFactorAuth';
import ProtectedRoute from './components/ProtectedRoute';
import CSRFErrorBoundary from './components/CSRFErrorBoundary';
import OwnerLayout from './components/OwnerLayout';
import VerifyEmailRoute from './components/verification/VerifyEmailRoute';
import ComponentErrorBoundary from './components/ComponentErrorBoundary';
import PublicRoute from './components/PublicRoute';

// Placeholder components for demonstration
const OrdersPage = () => <div className="p-6">Orders Management Page</div>;
const MenuBuilderPage = () => <div className="p-6">Menu Builder Page</div>;
const CategoriesPage = () => <div className="p-6">Categories Page</div>;
const ItemsPage = () => <div className="p-6">Items Page</div>;
const ModifiersPage = () => <div className="p-6">Modifiers Page</div>;
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


const useRouteDebug = () => {
  const location = useLocation();
  const auth = useSelector(state => state.auth);
  
  useEffect(() => {
    console.log('🔍 ROUTE DEBUG:', {
      path: location.pathname,
      isAuthenticated: auth.isAuthenticated,
      userEmail: auth.user?.email,
      emailVerified: auth.user?.email_verified,
      pendingVerification: localStorage.getItem('pendingVerificationEmail'),
      requires2FA: auth.requires2FA
    });
  }, [location.pathname, auth]);
};

// Auto Redirect Handler
const AutoRedirectHandler = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user, requires2FA, loading } = useSelector(state => state.auth);
  const [initialCheckComplete, setInitialCheckComplete] = useState(false);

  useRouteDebug(); // Enable debugging

  useEffect(() => {
    // Don't run redirects while still loading
    if (loading || !initialCheckComplete) {
      return;
    }

    // Don't redirect if we're already on the correct page
    const currentPath = location.pathname;
    const pendingEmail = localStorage.getItem('pendingVerificationEmail');

    console.log('🔄 AutoRedirectHandler Analysis:', {
      currentPath,
      isAuthenticated,
      userEmail: user?.email,
      emailVerified: user?.email_verified,
      requires2FA,
      shouldRedirect: isAuthenticated && user?.email_verified && currentPath === '/login'
    });

    // CASE 1: Authenticated & verified user on login/verify pages
    if (isAuthenticated && user?.email_verified) {
      if (currentPath === '/login' || currentPath === '/verify-email') {
        console.log('✅ Redirecting verified user to dashboard');
        navigate('/owner/dashboard', { replace: true });
        return;
      }
    }

    // CASE 2: Handle 2FA requirement
    if (requires2FA && !currentPath.includes('/2fa')) {
      navigate('/2fa', { replace: true });
      return;
    }

    // CASE 3: Handle pending verification for unauthenticated users
    if (!isAuthenticated && pendingEmail && !currentPath.includes('/verify-email')) {
      navigate('/verify-email', { replace: true });
      return;
    }

    // CASE 4: Handle authenticated but unverified users accessing protected routes
    if (isAuthenticated && user && !user.email_verified && currentPath.includes('/owner')) {
      navigate('/verify-email', { replace: true });
      return;
    }

  }, [navigate, location.pathname, isAuthenticated, user, requires2FA, loading, initialCheckComplete]);

  // Mark initial check as complete after first load
  useEffect(() => {
    if (!loading && !initialCheckComplete) {
      setInitialCheckComplete(true);
    }
  }, [loading, initialCheckComplete]);

  return children;
};

// Dashboard Route Component - FIXED
const DashboardRoute = () => {
  const { user } = useSelector(state => state.auth);
  
  // Add safety check for user object
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

  // Now we can safely check user.email_verified
  return user.email_verified ? (
    <DashboardOverview />
  ) : (
    <Navigate to="/verify-email" replace />
  );
};

// Add this hook to App.jsx
const useLocalStorageValidation = () => {
  useEffect(() => {
    const validateLocalStorage = () => {
      try {
        const token = localStorage.getItem('token');
        // Basic token validation (JWT should have 3 parts)
        if (token && token.split('.').length !== 3) {
          console.warn('Invalid token format, clearing...');
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
        }
      } catch (error) {
        console.error('LocalStorage validation error:', error);
        // If localStorage is corrupted, clear it
        localStorage.clear();
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
  const [appInitialized, setAppInitialized] = useState(false);


  useEffect(() => {
    const initializeApp = async () => {
      try {
        console.log('🔄 Starting app initialization...');
        
        // Initialize CSRF first
        await dispatch(initializeCSRF()).unwrap();
        
        // Check for token and load user
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
    
    initializeApp();
  }, [dispatch]);


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
              {/* Dashboard */}
              <Route 
                path="dashboard" 
                element={<DashboardRoute />} 
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