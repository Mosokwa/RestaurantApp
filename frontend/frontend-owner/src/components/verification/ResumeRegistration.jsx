// components/ResumeRegistration.jsx
import { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { ownerVerifyEmail, clearError } from '../../store/slices/authSlice';
import './styles/ResumeRegistration.css';

const ResumeRegistration = () => {
  const [email, setEmail] = useState('');
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState('');
  
  const dispatch = useDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    // Check if there's a pending verification in localStorage
    const pendingEmail = localStorage.getItem('pendingVerificationEmail');
    if (pendingEmail) {
      setEmail(pendingEmail);
    }
  }, []);

  const handleResumeRegistration = async (e) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    setIsChecking(true);
    setError('');
    dispatch(clearError());

    try {
      // Try to resend verification code
      const result = await dispatch(ownerVerifyEmail(email));
      
      if (result.type === 'auth/ownerVerifyEmail/fulfilled') {
        // Store email for verification flow
        localStorage.setItem('pendingVerificationEmail', email);
        localStorage.setItem('pendingUserType', 'owner');
        
        // Redirect to verification page
        navigate('/verify-email', { 
          state: { 
            email: email,
            message: 'Verification code sent! Please check your email.'
          }
        });
      } else if (result.type === 'auth/ownerVerifyEmail/rejected') {
        const errorMsg = result.payload?.error || 'Failed to resend verification code';
        
        if (errorMsg.includes('already verified')) {
          // User already verified - redirect to login
          localStorage.removeItem('pendingVerificationEmail');
          navigate('/owner/login', {
            state: {
              message: 'Your email is already verified. Please log in.'
            }
          });
        } else if (errorMsg.includes('not found')) {
          setError('No registration found with this email address. Please register again.');
          localStorage.removeItem('pendingVerificationEmail');
        } else {
          setError(errorMsg);
        }
      }
    } catch (error) {
      console.error('Resume registration error:', error);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setIsChecking(false);
    }
  };

  const handleNewRegistration = () => {
    // Clear any pending data and go to registration
    localStorage.removeItem('pendingVerificationEmail');
    localStorage.removeItem('pendingUserType');
    navigate('/register');
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
              <h2 className="form-title">Complete Your Registration</h2>
              <p className="form-subtitle">
                It looks like you started registering but didn't verify your email.
              </p>
            </div>

            {error && (
              <div className="alert-glass error">
                <div className="alert-icon">⚠️</div>
                <div className="alert-content">
                  <div className="alert-title">Registration Issue</div>
                  <div className="alert-message">{error}</div>
                </div>
              </div>
            )}

            <form onSubmit={handleResumeRegistration} className="login-form">
              <div className="input-group">
                <div className="input-glass">
                  <input
                    type="email"
                    placeholder=" "
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
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

              <button 
                type="submit" 
                disabled={isChecking || !email.trim()}
                className={`login-button ${isChecking ? 'loading' : ''}`}
              >
                {isChecking ? (
                  <>
                    <div className="button-spinner"></div>
                    Checking...
                  </>
                ) : (
                  'Resend Verification Code'
                )}
              </button>
            </form>

            <div className="form-footer">
              <p className="footer-text">
                Want to start over?{' '}
                <button 
                  onClick={handleNewRegistration}
                  className="footer-link"
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    cursor: 'pointer',
                    color: '#2563eb',
                    textDecoration: 'underline'
                  }}
                >
                  Register with a different email
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeRegistration;