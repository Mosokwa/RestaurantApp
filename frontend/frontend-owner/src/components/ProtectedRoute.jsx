// components/ProtectedRoute.jsx - Clean version
import { useSelector } from 'react-redux';
import { Navigate, useLocation } from 'react-router-dom';

const ProtectedRoute = ({ 
  children, 
  ownerOnly = false,
  requireEmailVerified = true
}) => {
  const { isAuthenticated, user, loading, hasPendingRestaurant } = useSelector(state => state.auth);
  const { restaurants } = useSelector(state => state.ownerAuth);
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Check if this is onboarding page
  const isOnboardingPage = location.pathname.includes('/onboarding');
  
  // Get onboarding access requirements
  const userHasRestaurants = restaurants && restaurants.length > 0;
  const hasPendingRestaurantSetup = localStorage.getItem('pendingRestaurantSetup') === 'true';

  console.log('🔐 ProtectedRoute Check:', {
    path: location.pathname,
    isOnboardingPage,
    userHasRestaurants,
    hasPendingRestaurantSetup,
    isAuthenticated
  });

  // ONBOARDING ACCESS CONTROL - FIXED LOGIC
  if (isOnboardingPage) {
    // Allow onboarding ONLY in these specific scenarios:
    const canAccessOnboarding = 
      isAuthenticated && 
      user?.email_verified && 
      // Either has pending setup OR has no restaurants (first time)
      (hasPendingRestaurantSetup || !userHasRestaurants);

    if (!canAccessOnboarding) {
      console.log('🚫 Onboarding access denied - redirecting to dashboard');
      return <Navigate to="/owner/dashboard" replace />;
    }
    
    console.log('✅ Onboarding access granted');
    return children;
  }


  // STANDARD AUTH FOR ALL OTHER ROUTES
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireEmailVerified && !user.email_verified) {
    const allowedWithoutVerification = ['/verify-email', '/logout', '/settings'];
    if (!allowedWithoutVerification.some(path => location.pathname.includes(path))) {
      return <Navigate to="/verify-email" state={{ from: location }} replace />;
    }
  }

  if (ownerOnly && user.user_type !== 'owner') {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ProtectedRoute;