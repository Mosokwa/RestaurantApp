// components/ProtectedRoute.jsx
import { useSelector } from 'react-redux';
import { Navigate, useLocation } from 'react-router-dom';
import { hasPermission } from '../utils/permissions';

const ProtectedRoute = ({ 
  children, 
  requiredPermission, 
  restaurantId,
  ownerOnly = false,
  requireEmailVerified = true,
  allowUnverified = false 
}) => {
  const { isAuthenticated, user, loading } = useSelector(state => state.auth);
  const location = useLocation();

  // Show loading while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  const hasPendingVerification = localStorage.getItem('pendingVerificationEmail');

  console.log('🔐 ProtectedRoute Analysis:', {
    path: location.pathname,
    isAuthenticated,
    userEmail: user?.email,
    emailVerified: user?.email_verified,
    isLoginPage: location.pathname === '/login'
  });

  if (isAuthenticated && user?.email_verified && location.pathname === '/login') {
    console.log('🔄 ProtectedRoute: Redirecting authenticated user from login to dashboard');
    return <Navigate to="/owner/dashboard" replace />;
  }

  // Redirect to login if not authenticated AND no pending verification
  if (!isAuthenticated && !hasPendingVerification) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Handle pending verification redirect
  if (!isAuthenticated && hasPendingVerification && !location.pathname.includes('/verify-email')) {
    return <Navigate to="/verify-email" replace />;
  }

  // For authenticated users, check email verification
  if (isAuthenticated && requireEmailVerified && !user?.email_verified) {
    const allowedWithoutVerification = [
      '/verify-email',
      '/logout',
      '/settings'
    ].some(path => location.pathname.includes(path));

    if (!allowedWithoutVerification && !allowUnverified) {
      return <Navigate to="/verify-email" state={{ from: location }} replace />;
    }
  }

  // Owner-only route protection
  if (isAuthenticated && ownerOnly && user.user_type !== 'owner') {
    return <Navigate to="/unauthorized" replace />;
  }

  // Permission-based route protection
  if (isAuthenticated && requiredPermission && !hasPermission(user, requiredPermission, restaurantId)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ProtectedRoute;