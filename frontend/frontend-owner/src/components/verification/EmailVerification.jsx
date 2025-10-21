// components/EmailVerification.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  verifyEmailCode, 
  resendVerificationEmail,
  ownerVerifyCode,
  clearError,
  setLoginError 
} from '../../store/slices/authSlice';
import './styles/EmailVerification.css';

const EmailVerification = () => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [email, setEmail] = useState('');
  const [userType, setUserType] = useState('customer'); // 'customer' or 'owner'
  const [isResending, setIsResending] = useState(false);
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, loading, error } = useSelector(state => state.auth);

  useEffect(() => {
    // Get email and user type from location state or localStorage
    const locationEmail = location.state?.email;
    const storedEmail = localStorage.getItem('pendingVerificationEmail');
    const storedUserType = localStorage.getItem('pendingUserType') || 'customer';
    
    if (locationEmail) {
      setEmail(locationEmail);
      localStorage.setItem('pendingVerificationEmail', locationEmail);
    } else if (storedEmail) {
      setEmail(storedEmail);
    }
    
    setUserType(storedUserType);

    // Clear previous errors
    dispatch(clearError());
  }, [dispatch, location]);

  const handleCodeChange = (index, value) => {
    if (value.length <= 1 && /^\d*$/.test(value)) {
      const newCode = [...code];
      newCode[index] = value;
      setCode(newCode);

      // Auto-focus next input
      if (value && index < 5) {
        const nextInput = document.getElementById(`code-${index + 1}`);
        if (nextInput) nextInput.focus();
      }
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      const prevInput = document.getElementById(`code-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous errors
    dispatch(clearError());

    const verificationCode = code.join('');
    
    // Validation
    if (verificationCode.length !== 6 || !/^\d+$/.test(verificationCode)) {
        dispatch(setLoginError({ error: 'Please enter a valid 6-digit verification code' }));
        return;
    }

    try {
        let result;
        
        // Use appropriate verification based on user type
        if (userType === 'owner') {
            result = await dispatch(ownerVerifyCode({ email, code: verificationCode }));
        } else {
            result = await dispatch(verifyEmailCode({ email, code: verificationCode }));
        }
        
        if (result.type.endsWith('/fulfilled')) {
            // Clear stored data on success
            localStorage.removeItem('pendingVerificationEmail');
            localStorage.removeItem('pendingUserType');
            
            // Determine redirect path based on user type
            const redirectPath = '/login';
            const successMessage = userType === 'owner' 
                ? 'Owner email verified successfully! You can now login to your owner account.'
                : 'Email verified successfully! Please log in to continue.';
            
            navigate(redirectPath, { 
                state: { 
                    message: successMessage,
                    verifiedEmail: email
                }
            });
        } else if (result.type.endsWith('/rejected')) {
            // Error is automatically handled by the slice
            console.error('Email verification failed:', result.error);
            
            // Clear the code on error
            if (result.payload?.error?.includes('Invalid') || result.payload?.error?.includes('expired')) {
                setCode(['', '', '', '', '', '']);
                const firstInput = document.getElementById('code-0');
                if (firstInput) firstInput.focus();
            }
        }
    } catch (error) {
        console.error('Unexpected verification error:', error);
        dispatch(setLoginError({ 
            error: 'An unexpected error occurred during verification. Please try again.' 
        }));
    }
  };

  const handleResendCode = async () => {
    // Clear previous errors
    dispatch(clearError());

    if (!email) {
        dispatch(setLoginError({ error: 'Email not found. Please try the registration process again.' }));
        return;
    }

    try {
        setIsResending(true);
        let result;
        
        // Use appropriate resend based on user type
        if (userType === 'owner') {
            result = await dispatch(verifyEmailCode(email));
        } else {
            result = await dispatch(resendVerificationEmail(email));
        }
        
        if (result.type.endsWith('/fulfilled')) {
            // Success message is handled in the slice
            console.log('Verification code resent successfully');
            
            // Reset code inputs
            setCode(['', '', '', '', '', '']);
            // Focus first input
            const firstInput = document.getElementById('code-0');
            if (firstInput) firstInput.focus();
        } else if (result.type.endsWith('/rejected')) {
            console.error('Failed to resend verification code:', result.error);
        }
    } catch (error) {
        console.error('Unexpected resend error:', error);
        dispatch(setLoginError({ 
            error: 'Failed to resend verification code. Please try again.' 
        }));
    } finally {
        setIsResending(false);
    }
  };

  const getPageTitle = () => {
    return userType === 'owner' ? 'Verify Owner Account' : 'Verify Your Email';
  };

  const getPageSubtitle = () => {
    return userType === 'owner' 
        ? `We sent a 6-digit code to ${email} to verify your owner account`
        : `We sent a 6-digit code to ${email}`;
  };

  const getButtonText = () => {
    return userType === 'owner' ? 'Verify Owner Account' : 'Verify Email';
  };

  return (
    <div className="login-container">
      <div className="floating-orbs">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
        <div className="orb orb-4"></div>
      </div>

      <div className="login-content">
        <div className="form-section">
          <div className="login-glass-card">
            <div className="form-header">
              <h2 className="form-title">{getPageTitle()}</h2>
              <p className="form-subtitle">{getPageSubtitle()}</p>
            </div>

            <form onSubmit={handleSubmit} className="login-form">
              <div className="code-inputs">
                {code.map((digit, index) => (
                  <input
                    key={index}
                    id={`code-${index}`}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength="1"
                    value={digit}
                    onChange={(e) => handleCodeChange(index, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(index, e)}
                    className="code-input"
                    disabled={loading}
                    autoFocus={index === 0}
                  />
                ))}
              </div>

              {error && (
                <div className="alert-glass error">
                  <div className="alert-icon">⚠️</div>
                  <div className="alert-content">
                    <div className="alert-title">Verification Failed</div>
                    <div className="alert-message">{error.error || error}</div>
                  </div>
                </div>
              )}

              <button 
                type="submit" 
                disabled={loading || code.join('').length !== 6}
                className={`login-button ${loading ? 'loading' : ''}`}
              >
                {loading ? (
                  <>
                    <div className="button-spinner"></div>
                    Verifying...
                  </>
                ) : (
                  getButtonText()
                )}
              </button>
            </form>

            <div className="form-footer">
              <p className="footer-text">
                Didn't receive the code?
              </p>
              <button 
                onClick={handleResendCode}
                disabled={isResending}
                className="footer-link"
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  cursor: isResending ? 'not-allowed' : 'pointer',
                  color: isResending ? '#6b7280' : '#2563eb',
                  textDecoration: 'underline'
                }}
              >
                {isResending ? 'Sending...' : 'Resend Code'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;