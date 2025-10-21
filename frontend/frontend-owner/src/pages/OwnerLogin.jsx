import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ownerLogin, clearError, socialLogin } from '../store/slices/authSlice';
import { useNavigate, Link } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { initFacebookSDK, loginWithFacebook } from '../utils/facebookAuth';
import { setLoginError } from '../store/slices/authSlice';
import './styles/OwnerLogin.css';

const OwnerLogin = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  
  const [isFocused, setIsFocused] = useState({ username: false, password: false });
  const [isHovered, setIsHovered] = useState(false);
  const [socialLoading, setSocialLoading] = useState({ google: false, facebook: false });
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loginLoading, loginError, csrfError } = useSelector(state => state.auth);

  useEffect(() => {
    
    // Initialize Facebook SDK when component mounts
    initFacebookSDK();
  }, [csrfError, dispatch]);

  // Complete Google Login Handler
  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setSocialLoading(prev => ({ ...prev, google: true }));
      dispatch(clearError());
      
      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google');
      }

      const result = await dispatch(socialLogin({
        provider: 'google',
        token: credentialResponse.credential
      }));
      
      if (result.type === 'auth/socialLogin/fulfilled') {
        handleSocialLoginSuccess(result.payload);
      } else if (result.type === 'auth/socialLogin/rejected') {
        throw new Error(result.payload?.error || 'Google login failed');
      }
    } catch (error) {
      console.error('Google login error:', error);
      dispatch(setLoginError({ 
        error: error.message || 'Google authentication failed. Please try again.' 
      }));
    } finally {
      setSocialLoading(prev => ({ ...prev, google: false }));
    }
  };

  const handleGoogleError = () => {
    console.error('Google login failed');
    dispatch(setLoginError({ 
      error: 'Google authentication failed. Please try again.' 
    }));
  };

  // Complete Facebook Login Handler
  const handleFacebookLogin = async () => {
    try {
      setSocialLoading(prev => ({ ...prev, facebook: true }));
      dispatch(clearError());

      const facebookData = await loginWithFacebook();
      
      if (!facebookData.accessToken) {
        throw new Error('No access token received from Facebook');
      }

      const result = await dispatch(socialLogin({
        provider: 'facebook',
        token: facebookData.accessToken
      }));
      
      if (result.type === 'auth/socialLogin/fulfilled') {
        handleSocialLoginSuccess(result.payload);
      } else if (result.type === 'auth/socialLogin/rejected') {
        throw new Error(result.payload?.error || 'Facebook login failed');
      }
    } catch (error) {
      console.error('Facebook login error:', error);
      dispatch(setLoginError({ 
        error: error.message || 'Facebook authentication failed. Please try again.' 
      }));
    } finally {
      setSocialLoading(prev => ({ ...prev, facebook: false }));
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
              {/* Social Login Section */}
              <div className="social-login-section">
                <div className="divider">
                  <span>Or continue with</span>
                </div>
                
                <div className="social-buttons">
                  {/* Google Login */}
                  <div className="google-login-wrapper">
                    <GoogleLogin
                      onSuccess={handleGoogleSuccess}
                      onError={handleGoogleError}
                      shape="rectangular"
                      size="large"
                      // width="100%"
                      text="signin_with"
                      theme="filled_blue"
                      useOneTap={false}
                    />
                  </div>
                  
                  {/* Facebook Login */}
                  <button 
                    type="button"
                    onClick={handleFacebookLogin}
                    disabled={socialLoading.facebook || loginLoading}
                    className="social-button facebook"
                  >
                    {socialLoading.facebook ? (
                      <>
                        <div className="button-spinner"></div>
                        Connecting...
                      </>
                    ) : (
                      <>
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="#1877F2">
                          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                        Facebook
                      </>
                    )}
                  </button>
                </div>
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