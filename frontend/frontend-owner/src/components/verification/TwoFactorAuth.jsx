// components/verification/TwoFactorAuth.jsx
import { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import { verify2FACode, clearError, setLoginError, clear2FA } from '../../store/slices/authSlice';
import './styles/TwoFactorAuth.css';

const TwoFactorAuth = () => {
  const [code, setCode] = useState('');
  const [rememberDevice, setRememberDevice] = useState(false);
  
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { loading, error, tempLoginData } = useSelector(state => state.auth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    dispatch(clearError());

    if (code.length !== 6 || !/^\d+$/.test(code)) {
      dispatch(setLoginError({ error: 'Please enter a valid 6-digit code' }));
      return;
    }

    try {
      const result = await dispatch(verify2FACode({ 
        code, 
        rememberDevice,
        ...tempLoginData 
      }));
      
      if (result.type === 'auth/verify2FA/fulfilled') {
        dispatch(clear2FA());
        
        if (result.payload.user && !result.payload.user.email_verified) {
          navigate('/verify-email', { 
            state: { email: result.payload.user.email }
          });
        } else {
          navigate(location.state?.returnUrl || '/owner/dashboard');
        }
      }
    } catch (error) {
      console.error('2FA verification error:', error);
      setCode('');
    }
  };

  return (
    <div className="twofa-container">
      <div className="twofa-card">
        <div className="twofa-header">
          <h2>Two-Factor Authentication</h2>
          <p>Enter the 6-digit code from your authenticator app</p>
        </div>

        <form onSubmit={handleSubmit} className="twofa-form">
          <div className="input-group">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="twofa-input"
              disabled={loading}
              maxLength="6"
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="remember-device">
            <label>
              <input
                type="checkbox"
                checked={rememberDevice}
                onChange={(e) => setRememberDevice(e.target.checked)}
              />
              Remember this device for 30 days
            </label>
          </div>

          <button 
            type="submit" 
            disabled={loading || code.length !== 6}
            className="verify-button"
          >
            {loading ? 'Verifying...' : 'Verify'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TwoFactorAuth;