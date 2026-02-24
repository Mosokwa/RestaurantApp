import './LocationPrompt.css';

const LocationPrompt = ({ isOpen, onRequestLocation, onDismiss }) => {
  if (!isOpen) return null;

  return (
    <div className="location-prompt-overlay">
      <div className="location-prompt-card glass-card">
        <div className="location-prompt-icon">📍</div>
        <h3>Enable Location Services</h3>
        <p>
          See restaurants near you, get accurate delivery estimates, 
          and discover popular spots in your area.
        </p>
        
        <div className="location-prompt-buttons">
          <button 
            className="allow-location-btn"
            onClick={onRequestLocation}
          >
            Allow Location Access
          </button>
          <button 
            className="maybe-later-btn"
            onClick={onDismiss}
          >
            Maybe Later
          </button>
        </div>

        <div className="location-privacy-note">
          <span className="privacy-icon">🔒</span>
          <span>Your location is only used to find nearby restaurants</span>
        </div>
      </div>
    </div>
  );
};

export default LocationPrompt;