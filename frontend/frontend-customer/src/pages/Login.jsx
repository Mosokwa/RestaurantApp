// pages/Login.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { login, verify2FA, clearError, resetAuthState } from '../store/slices/authSlice';
import './styles/Login.css';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [totpToken, setTotpToken] = useState('');

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error, isAuthenticated, requires2FA, user } = useSelector((state) => state.auth);

  useEffect(() => {
    dispatch(resetAuthState());
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate('/');
    }
  }, [isAuthenticated, user, navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (requires2FA) {
        await dispatch(verify2FA(formData, totpToken));
      } else {
        await dispatch(login(formData));
      }
    } catch (error) {
      // Error is handled in the slice
      console.error('Authentication error:', error);
    }
  };

  const handleSocialLogin = (provider) => {
    // Implement social login logic here
    console.log(`Logging in with ${provider}`);
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>{requires2FA ? 'Two-Factor Authentication' : 'Login'}</h2>
        
        {error && (
          <div className="error-message">
            {typeof error === 'object' ? JSON.stringify(error) : error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {!requires2FA ? (
            <>
              <input
                type="text"
                name="username"
                placeholder="Username"
                value={formData.username}
                onChange={handleChange}
                required
                disabled={loading}
              />
              
              <input
                type="password"
                name="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={loading}
              />
            </>
          ) : (
            <div className="two-factor-section">
              <p>Please enter the verification code from your authenticator app</p>
              <input
                type="text"
                name="totpToken"
                placeholder="Enter 6-digit code"
                value={totpToken}
                onChange={(e) => setTotpToken(e.target.value)}
                required
                disabled={loading}
                maxLength={6}
                pattern="[0-9]{6}"
                title="Please enter a 6-digit code"
              />
            </div>
          )}

          <button type="submit" disabled={loading}>
            {loading ? 'Processing...' : requires2FA ? 'Verify' : 'Login'}
          </button>
        </form>

        {!requires2FA && (
          <>
            <div className="auth-links">
              <Link to="/forgot-password">Forgot Password?</Link>
              <span>•</span>
              <Link to="/signup">Create Account</Link>
            </div>

            <div className="social-login">
              <p>Or continue with</p>
              <div className="social-buttons">
                <button 
                  type="button" 
                  className="social-btn google"
                  onClick={() => handleSocialLogin('google')}
                  disabled={loading}
                >
                  Google
                </button>
                <button 
                  type="button" 
                  className="social-btn facebook"
                  onClick={() => handleSocialLogin('facebook')}
                  disabled={loading}
                >
                  Facebook
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Login;