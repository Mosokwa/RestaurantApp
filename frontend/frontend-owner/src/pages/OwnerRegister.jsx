import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { ownerRegister, clearError, setRegisterError } from '../store/slices/authSlice';
import { useNavigate, Link } from 'react-router-dom';
import './styles/OwnerLogin.css';
import { get } from 'jquery';


// Production-ready validation utility
const validateFormData = (data) => {
  const errors = {};

  // Required fields validation
  if (!data.firstName?.trim()) errors.firstName = 'First name is required';
  if (!data.lastName?.trim()) errors.lastName = 'Last name is required';
  if (!data.email?.trim()) errors.email = 'Email is required';
  if (!data.username?.trim()) errors.username = 'Username is required';
  if (!data.password) errors.password = 'Password is required';
  if (!data.passwordConfirm) errors.passwordConfirm = 'Please confirm your password';

  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (data.email && !emailRegex.test(data.email)) {
    errors.email = 'Please enter a valid email address';
  }

  // Password strength validation
  if (data.password) {
    if (data.password.length < 8) {
      errors.password = 'Password must be at least 8 characters long';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(data.password)) {
      errors.password = 'Password must contain uppercase, lowercase letters and numbers';
    }
  }

  // Password confirmation
  if (data.password && data.passwordConfirm && data.password !== data.passwordConfirm) {
    errors.passwordConfirm = 'Passwords do not match';
  }

  // Username validation
  const usernameRegex = /^[a-zA-Z0-9_]+$/;
  if (data.username && !usernameRegex.test(data.username)) {
    errors.username = 'Username can only contain letters, numbers, and underscores';
  }

  // Phone number validation (optional but if provided, validate)
  const phoneRegex = /^\+?[\d\s\-\(\)]{10,}$/;
  if (data.phoneNumber && !phoneRegex.test(data.phoneNumber.replace(/\s/g, ''))) {
    errors.phoneNumber = 'Please enter a valid phone number';
  }

  return errors;
};

// Data transformation utility
const transformToBackendFormat = (frontendData) => {
  return {
    username: frontendData.username?.trim(),
    email: frontendData.email?.trim().toLowerCase(),
    password: frontendData.password,
    password_confirm: frontendData.passwordConfirm,
    first_name: frontendData.firstName?.trim(),
    last_name: frontendData.lastName?.trim(),
    phone_number: frontendData.phoneNumber?.trim() || '',
    restaurant_name: frontendData.restaurantName?.trim() || ''
  };
};


const OwnerRegister = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
    firstName: '',
    lastName: '',
    phoneNumber: '',
    restaurantName: ''
  });
  
  const [fieldErrors, setFieldErrors] = useState({});
  const [isFocused, setIsFocused] = useState({
    username: false, email: false, password: false, 
    passwordConfirm: false, firstName: false, lastName: false,
    phoneNumber: false, restaurantName: false
  });
  const [isHovered, setIsHovered] = useState(false);
  const [touched, setTouched] = useState({});
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { registerLoading, registerError, csrfError, successMessage } = useSelector(state => state.auth);

  // Real-time validation on blur
  const handleBlur = (field) => {
    setIsFocused(prev => ({ ...prev, [field]: false }));
    setTouched(prev => ({ ...prev, [field]: true }));
    
    const errors = validateFormData(formData);
    setFieldErrors(prev => ({ ...prev, [field]: errors[field] }));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleFocus = (field) => {
    setIsFocused(prev => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    dispatch(clearError());
    setFieldErrors({});

    // Comprehensive form validation
    const errors = validateFormData(formData);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setTouched(Object.keys(errors).reduce((acc, key) => ({ ...acc, [key]: true }), {}));
      
      // Scroll to first error
      const firstErrorField = Object.keys(errors)[0];
      const element = document.querySelector(`[name="${firstErrorField}"]`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.focus();
      }
      
      dispatch(setRegisterError({ 
        error: 'Please fix the validation errors below.' 
      }));
      return;
    }

    try {
      console.log('🚀 Starting registration process...');

      // Transform data to match backend expectations
      const backendFormData = transformToBackendFormat(formData);
      
      const result = await dispatch(ownerRegister(backendFormData));
      
      if (result.type === 'auth/ownerRegister/fulfilled') {
        // Registration successful - redirect to email verification
        localStorage.setItem('pendingVerificationEmail', formData.email);
        localStorage.setItem('pendingUserType', 'owner');

        navigate('/verify-email', { 
          state: { 
            email: formData.email,
            message: 'Registration successful! Please verify your email to activate your account.',
          }
        });
        
      } else if (result.type === 'auth/ownerRegister/rejected') {
        // Handle backend validation errors
        const errorPayload = result.payload;
        
        if (errorPayload?.error?.includes('CSRF')) {
          // Retry with fresh CSRF token
          console.warn('🔄 CSRF error detected, refreshing token...');
          dispatch(setRegisterError({ 
            error: 'Security token issue. Please try again.' 
          }));
        } else if (typeof errorPayload === 'object') {
          // Handle field-specific errors from backend
          const backendErrors = {};
          Object.keys(errorPayload).forEach(key => {
            if (errorPayload[key] && Array.isArray(errorPayload[key])) {
              backendErrors[key] = errorPayload[key][0];
            }
          });
          
          if (Object.keys(backendErrors).length > 0) {
            setFieldErrors(backendErrors);
            dispatch(setRegisterError({ 
              error: 'Please fix the validation errors below.' 
            }));
          } else {
            dispatch(setRegisterError({ 
              error: errorPayload.error || errorPayload.detail  || 'Registration failed. Please try again.' 
            }));
          }
        } else {
          dispatch(setRegisterError({ 
            error: 'Registration failed. Please try again.' 
          }));
        }
      }
    } catch (error) {
      console.error('Unexpected registration error:', error);
      dispatch(setRegisterError({ 
        error: 'An unexpected error occurred. Please try again later.' 
      }));
    }
  };

  // Helper to check if field should show error
  const shouldShowError = (fieldName) => {
    return touched[fieldName] && fieldErrors[fieldName];
  };

  // Helper to get input class
  const getInputClass = (fieldName) => {
    const baseClass = `input-glass ${isFocused[fieldName] ? 'input-focused' : ''}`;
    return shouldShowError(fieldName) ? `${baseClass} input-error` : baseClass;
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
            Join <span className="brand-accent">RestaurantPro</span>
          </h1>
          <p className="brand-subtitle">
            Start your restaurant management journey with our premium platform
          </p>
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">🚀</div>
              <span>Setup in minutes</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">💳</div>
              <span>No credit card required</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🎯</div>
              <span>Free 14-day trial</span>
            </div>
          </div>
        </div>

        {/* Right Side - Registration Form */}
        <div className="form-section">
          <div 
            className={`login-glass-card ${isHovered ? 'card-hover' : ''}`}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
          >
            {/* Header */}
            <div className="form-header">
              <h2 className="form-title">Create Account</h2>
              <p className="form-subtitle">Register as a restaurant owner</p>
            </div>

            {/* Success Message */}
            {successMessage && (
              <div className="alert-glass success">
                <div className="alert-icon">✅</div>
                <div className="alert-content">
                  <div className="alert-title">Registration Successful!</div>
                  <div className="alert-message">{successMessage}</div>
                </div>
              </div>
            )}

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

            {registerError && !csrfError && (
              <div className="alert-glass warning">
                <div className="alert-icon">❌</div>
                <div className="alert-content">
                  <div className="alert-title">Registration Failed</div>
                  <div className="alert-message">
                    {registerError.error || 'Please check your information and try again.'}
                  </div>
                </div>
              </div>
            )}

            {/* Registration Form */}
            <form className="login-form" onSubmit={handleSubmit}>
              {/* Personal Information */}
              <div className="form-row">
                <div className="input-group">
                  <div className={getInputClass('firstName')}>
                    <input
                      type="text"
                      name="firstName"
                      placeholder=" "
                      value={formData.firstName}
                      onChange={handleChange}
                      onFocus={() => handleFocus('firstName')}
                      onBlur={() => handleBlur('firstName')}
                      disabled={registerLoading}
                      className="glass-input"
                      required
                    />
                    <label className="input-label">First Name</label>
                    <div className="input-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeWidth="1.5" strokeLinecap="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="input-group">
                  <div className={getInputClass('lastName')}>
                    <input
                      type="text"
                      name="lastName"
                      placeholder=" "
                      value={formData.lastName}
                      onChange={handleChange}
                      onFocus={() => handleFocus('lastName')}
                      onBlur={() => handleBlur('lastName')}
                      disabled={registerLoading}
                      className="glass-input"
                      required
                    />
                    <label className="input-label">Last Name</label>
                  </div>
                </div>
              </div>

              {/* Contact Information */}
              <div className="input-group">
                <div className={getInputClass('email')}>
                  <input
                    type="email"
                    name="email"
                    placeholder=" "
                    value={formData.email}
                    onChange={handleChange}
                    onFocus={() => handleFocus('email')}
                    onBlur={() => handleBlur('email')}
                    disabled={registerLoading}
                    className="glass-input"
                    required
                  />
                  <label className="input-label">Email Address</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div className="input-group">
                <div className={getInputClass('phoneNumber')}>
                  <input
                    type="tel"
                    name="phoneNumber"
                    placeholder=" "
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    onFocus={() => handleFocus('phoneNumber')}
                    onBlur={() => handleBlur('phoneNumber')}
                    disabled={registerLoading}
                    className="glass-input"
                  />
                  <label className="input-label">Phone Number (Optional)</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Restaurant Information */}
              <div className="input-group">
                <div className={getInputClass('restaurantName')}>
                  <input
                    type="text"
                    name="restaurantName"
                    placeholder=" "
                    value={formData.restaurantName}
                    onChange={handleChange}
                    onFocus={() => handleFocus('restaurantName')}
                    onBlur={() => handleBlur('restaurantName')}
                    disabled={registerLoading}
                    className="glass-input"
                  />
                  <label className="input-label">Restaurant Name (Optional)</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0H5m14 0h2m-2 0h-4m-6 0H3m2 0h4M7 7h.01M7 11h.01M7 15h.01"/>
                    </svg>
                  </div>
                </div>
              </div>

              {/* Account Information */}
              <div className="input-group">
                <div className={getInputClass('username')}>
                  <input
                    type="text"
                    name="username"
                    placeholder=" "
                    value={formData.username}
                    onChange={handleChange}
                    onFocus={() => handleFocus('username')}
                    onBlur={() => handleBlur('username')}
                    disabled={registerLoading}
                    className="glass-input"
                    required
                  />
                  <label className="input-label">Username</label>
                  <div className="input-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeWidth="1.5" strokeLinecap="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
                    </svg>
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="input-group">
                  <div className={getInputClass('password')}>
                    <input
                      type="password"
                      name="password"
                      placeholder=" "
                      value={formData.password}
                      onChange={handleChange}
                      onFocus={() => handleFocus('password')}
                      onBlur={() => handleBlur('password')}
                      disabled={registerLoading}
                      className="glass-input"
                      required
                      minLength="8"
                    />
                    <label className="input-label">Password</label>
                    <div className="input-icon">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeWidth="1.5" strokeLinecap="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
                      </svg>
                    </div>
                  </div>
                </div>

                <div className="input-group">
                  <div className={getInputClass('passwordConfirm')}>
                    <input
                      type="password"
                      name="passwordConfirm"
                      placeholder=" "
                      value={formData.passwordConfirm}
                      onChange={handleChange}
                      onFocus={() => handleFocus('passwordConfirm')}
                      onBlur={() => handleBlur('passwordConfirm')}
                      disabled={registerLoading}
                      className="glass-input"
                      required
                      minLength="8"
                    />
                    <label className="input-label">Confirm Password</label>
                  </div>
                </div>
              </div>

              <button 
                type="submit" 
                disabled={registerLoading}
                className={`login-button ${registerLoading ? 'loading' : ''}`}
              >
                {registerLoading ? (
                  <>
                    <div className="button-spinner"></div>
                    Creating Account...
                  </>
                ) : (
                  <>
                    <span>Create Owner Account</span>
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
                Already have an account?{' '}
                <Link to="/login" className="footer-link">
                  Sign in here
                </Link>
              </p>
              
              <div className="terms-text">
                By creating an account, you agree to our{' '}
                <a href="/terms" className="footer-link">Terms of Service</a> and{' '}
                <a href="/privacy" className="footer-link">Privacy Policy</a>
              </div>
            </div>
          </div>

          {/* Security Badge */}
          <div className="security-badge">
            <div className="badge-icon">🔒</div>
            <span>Your data is securely encrypted</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnerRegister;