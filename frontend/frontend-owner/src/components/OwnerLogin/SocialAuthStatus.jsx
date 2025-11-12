// components/OwnerLogin/SocialAuthStatus.jsx
const SocialAuthStatus = ({ isInitialized, errors }) => {
  if (isInitialized.google && isInitialized.apple) {
    return null; // Don't show status if everything is working
  }

  const getStatusMessage = () => {
    const issues = [];
    
    if (!isInitialized.google) {
      issues.push(`Google Sign-In: ${errors.google || 'Not available'}`);
    }
    
    if (!isInitialized.apple) {
      issues.push(`Apple Sign-In: ${errors.apple || 'Not available'}`);
    }
    
    if (issues.length === 0) return null;
    
    return (
      <div className="social-status-alert">
        <div className="alert-glass info">
          <div className="alert-icon">ℹ️</div>
          <div className="alert-content">
            <div className="alert-title">Limited Authentication Options</div>
            <div className="alert-message">
              {issues.join(' • ')}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return getStatusMessage();
};

export default SocialAuthStatus;