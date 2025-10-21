// pages/EmailVerification.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { 
  verifyEmailWithCode, 
  resendVerification, 
  clearError 
} from '../store/slices/authSlice';
import './styles/Login.css';

const EmailVerification = () => {
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [isResent, setIsResent] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, error } = useSelector((state) => state.auth);

  const { email = '', username = '', emailSent = false } = location.state || {};

  useEffect(() => {
    if (!email || !username) {
      navigate('/signup');
    }
  }, [email, username, navigate]);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    } else {
      setCanResend(true);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

  const handleCodeChange = (index, value) => {
    if (!/^\d?$/.test(value)) return;
    
    const newCode = [...verificationCode];
    newCode[index] = value;
    setVerificationCode(newCode);
    
    // Auto-focus to next input
    if (value && index < 5) {
      document.getElementById(`code-${index + 1}`).focus();
    }
    
    // Auto-submit when all digits are entered
    if (newCode.every(digit => digit !== '') && index === 5) {
      handleSubmit();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !verificationCode[index] && index > 0) {
      document.getElementById(`code-${index - 1}`).focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    if (/^\d{6}$/.test(pastedData)) {
      const digits = pastedData.split('');
      setVerificationCode(digits);
      document.getElementById('code-5').focus();
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    
    const code = verificationCode.join('');
    if (code.length !== 6) return;
    
    try {
      const result = await dispatch(verifyEmailWithCode({ email: email, code: code }));

      if (result && (result.message === 'Email verified successfully' || result.success )){
        navigate('/login', { 
        state: { 
          message: 'Email verified successfully! Please login.',
          type: 'success'
        } 
      });
      }

      
    } catch (error) {
      console.error('Verification error:', error);
    }
  };

  const handleResendVerification = async () => {
    try {
      const result = await dispatch(resendVerification(email)).unwrap();
      
      if (result.resend) { // Now checking for 'resend' flag instead of 'email_sent'
        setIsResent(true);
        setEmailStatus('sent');
        setCanResend(false);
        setCountdown(60);
        setTimeout(() => setIsResent(false), 5000);
      } else {
        setEmailStatus('failed');
      }
    } catch (error) {
      console.error('Resend error:', error);
      setEmailStatus('failed');
    }
  };


  if (!email || !username) {
    return null;
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Verify Your Email</h2>
        
        <div className="verification-info">
          <p>We've sent a 6-digit verification code to:</p>
          <p className="email-display">{email}</p>
          <p>Enter the code below to verify your email address.</p>
        </div>

        {error && (
          <div className="error-message">
            {typeof error === 'object' ? JSON.stringify(error) : error}
          </div>
        )}

        {isResent && (
          <div className="success-message">
            New verification code has been sent!
          </div>
        )}

        <form onSubmit={handleSubmit} className="verification-form">
          <div className="code-inputs">
            {verificationCode.map((digit, index) => (
              <input
                key={index}
                id={`code-${index}`}
                type="text"
                maxLength="1"
                value={digit}
                onChange={(e) => handleCodeChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={index === 0 ? handlePaste : undefined}
                disabled={loading}
                className="code-input"
                autoFocus={index === 0}
              />
            ))}
          </div>
          
          <button 
            type="submit" 
            disabled={loading || verificationCode.some(digit => digit === '')}
            className="verify-button"
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </button>
        </form>

        <div className="verification-actions">
          <p>Didn't receive the code?</p>
          <button 
            type="button" 
            onClick={handleResendVerification}
            disabled={loading || !canResend}
            className="resend-button"
          >
            {canResend ? 'Resend Code' : `Resend in ${countdown}s`}
          </button>
        </div>

        <div className="auth-links">
          <Link to="/login">Back to Login</Link>
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;