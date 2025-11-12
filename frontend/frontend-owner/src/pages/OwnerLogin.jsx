// pages/OwnerLogin.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ownerLogin, clearError, socialLogin } from '../store/slices/authSlice';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { setLoginError } from '../store/slices/authSlice';
import { useSocialAuth } from '../hooks/useSocialAuth';
import './styles/OwnerLogin.css';

const OwnerLogin = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  
  const [isFocused, setIsFocused] = useState({ username: false, password: false });
  const [isHovered, setIsHovered] = useState(false);
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loginLoading, loginError, csrfError } = useSelector(state => state.auth);
  
  const {
    loading: socialLoading,
    isInitialized,
    errors: socialErrors, // This is the errors from useSocialAuth hook
    handleGoogleLogin,
    handleAppleLogin,
    handleGoogleError,
    clearProviderError
  } = useSocialAuth();

  useEffect(() => {
    // Clear errors when component unmounts
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      const result = await handleGoogleLogin(credentialResponse);
      
      if (result.success) {
        handleSocialLoginSuccess(result.payload);
      }
    } catch (error) {
      console.error('Google login error:', error);
    }
  };

  const handleAppleSignIn = async () => {
    try {
      const result = await handleAppleLogin();
      
      if (result.success) {
        handleSocialLoginSuccess(result.payload);
      }
    } catch (error) {
      console.error('Apple login error:', error);
    }
  };

  // Handle successful social login
  const handleSocialLoginSuccess = (payload) => {
    if (payload.user && !payload.user.email_verified) {
      navigate('/verify-email', { 
        state: { email: payload.user.email }
      });
    } else {
      navigate('/owner/dashboard');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch(clearError());

    if (!credentials.username.trim() || !credentials.password.trim()) {
      dispatch(setLoginError({ error: 'Please fill in all fields' }));
      return;
    }

    try {
      const result = await dispatch(ownerLogin(credentials));
      
      if (result.type === 'auth/ownerLogin/fulfilled') {
        if (result.payload.requires_2fa) {
          navigate('/2fa', { 
            state: { 
              loginData: credentials,
              returnUrl: '/owner/dashboard'
            }
          });
        } else if (result.payload.user && !result.payload.user.email_verified) {
          navigate('/verify-email', { 
            state: { email: result.payload.user.email }
          });
        } else {
          navigate('/owner/dashboard');
        }
      }
      // NEW: Check if login failed due to unverified email
      else if (result.type === 'auth/ownerLogin/rejected') {
        if (result.payload?.requiresVerification) {
          navigate('/verify-email', { 
            state: { 
              email: result.payload.email || credentials.username,
              message: 'Your account is not activated. Please verify your email.',
              canResend: true
            }
          });
        }
      }
    } catch (error) {
      console.error('Login error:', error);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  const handleFocus = (field) => {
    setIsFocused(prev => ({ ...prev, [field]: true }));
  };

  const handleBlur = (field) => {
    setIsFocused(prev => ({ ...prev, [field]: false }));
  };

  return (
    <div className="login-container">
      {/* Animated Background Elements */}
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
        <div className="orb orb-4"></div>
      </div>

      {/* Main Content */}
      <div className="login-content">
        {/* Left Side - Branding */}
        <div className="brand-section">
          <div className="brand-logo">
            <div className="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M8 14V18C8 19.1046 8.89543 20 10 20H14C15.1046 20 16 19.1046 16 18V14" strokeWidth="1.5" strokeLinecap="round"/>
                <path d="M12 4C8.68629 4 6 6.68629 6 10V12H18V10C18 6.68629 15.3137 4 12 4Z" strokeWidth="1.5"/>
                <path d="M12 16V12" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="logo-glow"></div>
          </div>
          <h1 className="brand-title">
            Restaurant<span className="brand-accent">Pro</span>
          </h1>
          <p className="brand-subtitle">
            Premium management suite for modern restaurants
          </p>
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">✓</div>
              <span>Real-time analytics</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">✓</div>
              <span>Staff management</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">✓</div>
              <span>Multi-branch support</span>
            </div>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="form-section">
          <div 
            className={`login-glass-card ${isHovered ? 'card-hover' : ''}`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
          >
            {/* Header */}
            <div className="form-header">
              <h2 className="form-title">Welcome Back</h2>
              <p className="form-subtitle">Sign in to your owner account</p>
            </div>

            {/* Alerts */}
            {csrfError && (
              <div className="alert-glass error">
                <div className="alert-icon">⚠️</div>
                <div className="alert-content">
                  <div className="alert-title">Security Notice</div>
                  <div className="alert-message">{csrfError}</div>
                </div>
              </div>
            )}

            {loginError && !csrfError && (
              <div className="alert-glass warning">
                <div className="alert-icon">🔐</div>
                <div className="alert-content">
                  <div className="alert-title">Login Failed</div>
                  <div className="alert-message">
                    {loginError.error || 'Invalid credentials. Please try again.'}
                  </div>
                </div>
              </div>
            )}

            {/* Login Form */}
            <form className="login-form" onSubmit={handleSubmit}>
              <div className="input-group">
                <div className={`input-glass ${isFocused.username ? 'input-focused' : ''}`}>
                  <input
                    type="text"
                    name="username"
                    placeholder=" "
                    value={credentials.username}
                    onChange={handleChange}
                    onFocus={() => handleFocus('username')}
                    onBlur={() => handleBlur('username')}
                    disabled={loginLoading}
                    className="glass-input"
                  />
                  <label className="input-label">Username</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div className="input-group">
                <div className={`input-glass ${isFocused.password ? 'input-focused' : ''}`}>
                  <input
                    type="password"
                    name="password"
                    placeholder=" "
                    value={credentials.password}
                    onChange={handleChange}
                    onFocus={() => handleFocus('password')}
                    onBlur={() => handleBlur('password')}
                    disabled={loginLoading}
                    className="glass-input"
                  />
                  <label className="input-label">Password</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <button 
                type="submit" 
                disabled={loginLoading}
                className={`login-button ${loginLoading ? 'loading' : ''}`}
              >
                {loginLoading ? (
                  <>
                    <div className="button-spinner"></div>
                    Signing In...
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="2" strokeLinecap="round" d="M5 12h14m-7-7l7 7-7 7"/>
                    </svg>
                  </>
                )}
              </button>
            </form>

            {/* Footer Links */}
            <div className="form-footer">
              <p className="footer-text">
                New to RestaurantPro?{' '}
                <Link to="/register" className="footer-link">
                  Create owner account
                </Link>
              </p>
              
              {/* Social Login Section - UPDATED */}
              <div className="social-login-section">
                <div className="divider">
                  <span>Or continue with</span>
                </div>
                
                <div className="social-buttons">
                  {/* Google Login */}
                  {isInitialized.google && (
                    <div className="google-login-wrapper">
                      <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={handleGoogleError}
                        shape="rectangular"
                        size="large"
                        text="signin_with"
                        theme="filled_blue"
                        useOneTap={false}
                      />
                      {socialLoading.google && (
                        <div className="social-loading-overlay">
                          <div className="button-spinner"></div>
                          <span>Connecting...</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Apple Login */}
                  {isInitialized.apple ? (
                    <button 
                      type="button"
                      onClick={handleAppleSignIn}
                      disabled={socialLoading.apple || loginLoading}
                      className="social-button apple"
                    >
                      {socialLoading.apple ? (
                        <>
                          <div className="button-spinner"></div>
                          Connecting...
                        </>
                      ) : (
                        <>
                          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                          </svg>
                          Apple
                        </>
                      )}
                    </button>
                  ) : (
                    // Show why Apple login is not available (for debugging)
                    process.env.NODE_ENV === 'development' && (
                      <div style={{ 
                        padding: '8px', 
                        background: 'rgba(255,0,0,0.1)', 
                        borderRadius: '8px',
                        fontSize: '12px',
                        color: '#ff6b6b',
                        textAlign: 'center'
                      }}>
                        Apple login disabled: {socialErrors.apple || 'Not configured'}
                      </div>
                    )
                  )}
                </div>

                {/* Debug info in development */}
                {process.env.NODE_ENV === 'development' && (
                  <div style={{ 
                    marginTop: '10px', 
                    padding: '8px', 
                    background: 'rgba(0,0,0,0.3)', 
                    borderRadius: '8px',
                    fontSize: '11px',
                    color: '#ccc'
                  }}>
                    <div>Google: {isInitialized.google ? '✅' : '❌'} {socialErrors.google || ''}</div>
                    <div>Apple: {isInitialized.apple ? '✅' : '❌'} {socialErrors.apple || ''}</div>
                    <div>Apple Script: {typeof window !== 'undefined' && window.AppleID ? '✅ Loaded' : '❌ Missing'}</div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Security Badge */}
          <div className="security-badge">
            <div className="badge-icon">🔒</div>
            <span>Enterprise-grade security</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnerLogin;