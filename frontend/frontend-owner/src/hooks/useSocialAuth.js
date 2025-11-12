// hooks/useSocialAuth.js
import { useState, useCallback, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { socialLogin, setLoginError, clearError } from '../store/slices/authSlice';

export const useSocialAuth = () => {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState({ google: false, apple: false });
  const [isInitialized, setIsInitialized] = useState({ google: false, apple: false });
  const [errors, setErrors] = useState({ google: null, apple: null });
  const initializationRef = useRef(false);

  // Check if Apple Sign In is available
  const isAppleSignInAvailable = useCallback(() => {
    return typeof window !== 'undefined' && 
           window.AppleID && 
           typeof window.AppleID.auth === 'object' &&
           typeof window.AppleID.auth.init === 'function' &&
           typeof window.AppleID.auth.signIn === 'function';
  }, []);

  // Initialize social auth providers
  useEffect(() => {
    if (initializationRef.current) return;
    initializationRef.current = true;
    
    initializeSocialAuth();
  }, []);

  const initializeSocialAuth = useCallback(async () => {
    try {
      // Validate environment variables
      const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
      const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID;

      const initializationStatus = {
        google: isValidGoogleClientId(googleClientId),
        apple: isValidAppleClientId(appleClientId) && isAppleSignInAvailable()
      };

      const errors = { google: null, apple: null };

      // Initialize Google Auth
      if (initializationStatus.google) {
        try {
          // Google is initialized automatically by the script
          console.log('✅ Google Auth initialized successfully');
        } catch (error) {
          console.error('Google Auth initialization failed:', error);
          initializationStatus.google = false;
          errors.google = 'Google authentication unavailable';
        }
      } else {
        if (!isValidGoogleClientId(googleClientId)) {
          errors.google = 'Google authentication not configured';
        }
      }

      // Initialize Apple Auth
      if (initializationStatus.apple) {
        try {
          // Check if Apple Sign In is actually available
          if (!isAppleSignInAvailable()) {
            throw new Error('Apple Sign In script not loaded');
          }

          // Initialize Apple Auth
          window.AppleID.auth.init({
            clientId: appleClientId,
            scope: 'name email',
            redirectURI: window.location.origin,
            usePopup: true,
          });
          console.log('✅ Apple Auth initialized successfully');
        } catch (error) {
          console.error('❌ Apple Auth initialization failed:', error);
          initializationStatus.apple = false;
          errors.apple = 'Apple authentication unavailable - script not loaded';
        }
      } else {
        if (!isValidAppleClientId(appleClientId)) {
          errors.apple = 'Apple authentication not configured';
        } else if (!isAppleSignInAvailable()) {
          errors.apple = 'Apple Sign In script not loaded';
        }
      }

      setIsInitialized(initializationStatus);
      setErrors(errors);

      // Log initialization status for debugging
      console.log('🔧 Social Auth Initialization Status:', {
        google: initializationStatus.google,
        apple: initializationStatus.apple,
        appleScriptAvailable: isAppleSignInAvailable(),
        appleClientId: appleClientId ? '✅ Set' : '❌ Missing',
        googleClientId: googleClientId ? '✅ Set' : '❌ Missing'
      });
      
    } catch (error) {
      console.error('Social auth initialization error:', error);
      setIsInitialized({ google: false, apple: false });
      setErrors({ 
        google: 'Initialization failed', 
        apple: 'Initialization failed' 
      });
    }
  }, [isAppleSignInAvailable]);

  const isValidGoogleClientId = (clientId) => {
    return clientId && 
           clientId !== 'undefined' && 
           clientId.length > 10;
  };

  const isValidAppleClientId = (clientId) => {
    return clientId && 
           clientId !== 'undefined' && 
           clientId.length > 5;
  };

  const handleSocialLogin = useCallback(async (provider, authData) => {
    try {
      setLoading(prev => ({ ...prev, [provider]: true }));
      setErrors(prev => ({ ...prev, [provider]: null }));
      dispatch(clearError());

      const result = await dispatch(socialLogin({
        provider,
        ...authData
      }));

      if (result.type === 'auth/socialLogin/fulfilled') {
        return { 
          success: true, 
          payload: result.payload
        };
      } else {
        const errorMsg = result.payload?.error || `${provider} authentication failed`;
        throw new Error(errorMsg);
      }
    } catch (error) {
      const errorMessage = error.message || `${provider} authentication failed`;
      console.error(`${provider} login error:`, error);
      
      setErrors(prev => ({ ...prev, [provider]: errorMessage }));
      dispatch(setLoginError({ error: errorMessage }));
      
      return { 
        success: false, 
        error: errorMessage
      };
    } finally {
      setLoading(prev => ({ ...prev, [provider]: false }));
    }
  }, [dispatch]);

  const handleGoogleLogin = useCallback(async (credentialResponse) => {
    if (!isInitialized.google) {
      const errorMsg = errors.google || 'Google authentication is not available';
      dispatch(setLoginError({ error: errorMsg }));
      return { success: false, error: errorMsg };
    }

    if (!credentialResponse.credential) {
      const errorMsg = 'No credential received from Google';
      dispatch(setLoginError({ error: errorMsg }));
      return { success: false, error: errorMsg };
    }

    return await handleSocialLogin('google', {
      token: credentialResponse.credential
    });
  }, [handleSocialLogin, isInitialized.google, errors.google, dispatch]);

  const handleAppleLogin = useCallback(async () => {
    if (!isInitialized.apple) {
      const errorMsg = errors.apple || 'Apple authentication is not available';
      dispatch(setLoginError({ error: errorMsg }));
      return { success: false, error: errorMsg };
    }

    try {
      console.log('🍎 Initiating Apple Sign In...');
      const response = await window.AppleID.auth.signIn();
      
      if (response.authorization) {
        console.log('✅ Apple authorization received');
        return await handleSocialLogin('apple', {
          identity_token: response.authorization.id_token,
          first_name: response.user?.name?.firstName || '',
          last_name: response.user?.name?.lastName || ''
        });
      } else {
        throw new Error('No authorization received from Apple');
      }
    } catch (error) {
      // Don't show error for user cancellation
      if (error.error === 'user_cancelled_authorize') {
        console.log('ℹ️ Apple Sign In cancelled by user');
        return { success: false, error: 'cancelled' };
      }
      
      const errorMsg = error.message || 'Apple authentication failed';
      console.error('❌ Apple Sign In error:', error);
      dispatch(setLoginError({ error: errorMsg }));
      return { success: false, error: errorMsg };
    }
  }, [handleSocialLogin, isInitialized.apple, errors.apple, dispatch]);

  const handleGoogleError = useCallback(() => {
    const errorMsg = 'Google authentication failed. Please try again.';
    console.error('❌ Google authentication error');
    dispatch(setLoginError({ error: errorMsg }));
  }, [dispatch]);

  const clearProviderError = useCallback((provider) => {
    setErrors(prev => ({ ...prev, [provider]: null }));
  }, []);

  return {
    loading,
    isInitialized,
    errors,
    handleGoogleLogin,
    handleAppleLogin,
    handleGoogleError,
    clearProviderError
  };
};