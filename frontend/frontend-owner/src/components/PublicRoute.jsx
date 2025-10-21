import { useSelector } from 'react-redux';
import { Navigate, useLocation } from 'react-router-dom';

const PublicRoute = ({ 
  children, 
  restricted = false,
  redirectTo = null // Auto-detect based on user type
}) => {
  const { isAuthenticated, user } = useSelector(state => state.auth);
  const location = useLocation();

  // Auto-determine redirect destination based on user type
  const getRedirectPath = () => {
    if (redirectTo) return redirectTo;
    
    if (user?.user_type === 'owner') {
      return '/owner/dashboard';
    } else if (user?.user_type === 'staff') {
      return '/staff/dashboard';
    } 
  };

  // If route is restricted for authenticated users and user is authenticated
  if (restricted && isAuthenticated) {
    const from = location.state?.from?.pathname || getRedirectPath();
    console.log(`🔒 Redirecting authenticated user from ${location.pathname} to ${from}`);
    return <Navigate to={from} replace />;
  }

  // Handle pending verification redirect
  const hasPendingVerification = localStorage.getItem('pendingVerificationEmail');
  if (restricted && hasPendingVerification && !location.pathname.includes('/verify-email')) {
    console.log('🔒 Redirecting user with pending verification to verification page');
    return <Navigate to="/verify-email" replace />;
  }

  // Special case: if user is authenticated but not verified, and trying to access login/register
  if (restricted && isAuthenticated && !user?.email_verified && location.pathname !== '/verify-email') {
    console.log('🔒 Redirecting unverified user to verification page');
    return <Navigate to="/verify-email" replace />;
  }

  return children;
};

export default PublicRoute;