// components/verification/VerifyEmailRoute.jsx
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';
import EmailVerification from './EmailVerification';

const VerifyEmailRoute = () => {
  const { loading, isAuthenticated, user } = useSelector(state => state.auth);
  
  // Show loading while checking authentication state
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

  // DEBUG LOGGING - Add this to see what's happening
  console.log('🔍 VerifyEmailRoute - User structure:', {
    user,
    userKeys: user ? Object.keys(user) : 'No user',
    hasDataProperty: user?.data ? 'YES - PROBLEM!' : 'NO - GOOD',
    email_verified: user?.email_verified,
    isAuthenticated
  });

  // FIX: Handle the case where user data might be nested under .data
  const actualUser = user?.data || user;
  const isVerified = actualUser?.email_verified;

  console.log('🔍 Verification decision:', {
    hasPendingVerification,
    isVerified,
    shouldShowVerification: hasPendingVerification || (isAuthenticated && !isVerified)
  });

  // Show verification only if we have explicit need
  if (hasPendingVerification || (isAuthenticated && actualUser && !isVerified)) {
    return <EmailVerification />;
  }

  // If authenticated and verified, go to dashboard
  if (isAuthenticated && actualUser && isVerified) {
    console.log('✅ Redirecting to dashboard - User is verified');
    return <Navigate to="/owner/dashboard" replace />;
  }

  // Default to login
  return <Navigate to="/login" replace />;
};

export default VerifyEmailRoute;