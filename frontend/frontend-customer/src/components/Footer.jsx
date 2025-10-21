// components/Footer.jsx
import { useSelector } from 'react-redux';
import { Link, useLocation } from 'react-router-dom';
import LogoutButton from './LogoutButton';
import { authService } from '../services/auth';
import './Footer.css';

const Footer = () => {
  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const user = useSelector(state => state.auth.user);
  const location = useLocation();

  const isRestaurantPage = location.pathname.includes('/restaurant/');
  const currentYear = new Date().getFullYear();


  // Restaurant page footer content
  const restaurantFooter = {
    contact: {
      title: "Contact Us",
      content: (
        <>
          <p>📍 123 Restaurant Street</p>
          <p>🍽️ Food District, City 10001</p>
          <p>📞 (555) 123-4567</p>
          <p>✉️ info@restaurant.com</p>
        </>
      )
    },
    about: {
      title: "About Our Restaurant",
      content: (
        <>
          <p>Experience the finest dining with our carefully crafted menu featuring locally sourced ingredients and authentic flavors.</p>
          <p>Open daily from 11AM to 11PM</p>
          <p>Reservations recommended</p>
        </>
      )
    },
    links: {
      title: "Quick Links",
      content: (
        <div className="footer-links">
          <a href="#home">Home</a>
          <a href="#menu">Menu</a>
          <a href="#about">About</a>
          <a href="#reservation">Reservations</a>
          <a href="#reviews">Reviews</a>
        </div>
      )
    }
  };

  // General footer content
  const generalFooter = {
    contact: {
      title: "Contact Us",
      content: (
        <>
          <p>📞 Customer Support: (555) 123-4567</p>
          <p>✉️ support@tastybites.com</p>
          <p>📍 123 Main Street, Food City</p>
          <p>⏰ Mon-Sun: 9AM-9PM</p>
        </>
      )
    },
    about: {
      title: "About TastyBites",
      content: (
        <>
          <p>Discover the best restaurants in your area. Order food online, make reservations, and explore culinary experiences.</p>
          <p>Join our food community today!</p>
        </>
      )
    },
    links: {
      title: "Quick Links",
      content: (
        <div className="footer-links">
          <Link to="/">Home</Link>
          <Link to="/restaurants">Restaurants</Link>
          <Link to="/explore">Explore</Link>
          {isAuthenticated ? (
            <>
              <Link to="/profile">Profile</Link>
              <LogoutButton className='footer-logout'>
                Logout
                </LogoutButton>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/signup">Sign Up</Link>
            </>
          )}
        </div>
      )
    }
  };

  const footerContent = isRestaurantPage ? restaurantFooter : generalFooter;

  return (
    <footer className="footer">
      {/* Main Footer Content */}
      <div className="footer-main">
        <div className="footer-container">
          {/* Contact Column */}
          <div className="footer-column">
            <h3 className="footer-title">{footerContent.contact.title}</h3>
            <div className="footer-content">
              {footerContent.contact.content}
            </div>
          </div>

          {/* About Column */}
          <div className="footer-column">
            <h3 className="footer-title">{footerContent.about.title}</h3>
            <div className="footer-content">
              {footerContent.about.content}
            </div>
          </div>

          {/* Links Column */}
          <div className="footer-column">
            <h3 className="footer-title">{footerContent.links.title}</h3>
            <div className="footer-content">
              {footerContent.links.content}
            </div>
          </div>
        </div>
      </div>

      {/* Copyright Row */}
      <div className="footer-bottom">
        <div className="footer-container">
          <div className="copyright">
            <p>&copy; {currentYear} TastyBites. All rights reserved.</p>
            <div className="footer-bottom-links">
              <Link to="/privacy">Privacy Policy</Link>
              <Link to="/terms">Terms of Service</Link>
              <Link to="/contact">Contact</Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;