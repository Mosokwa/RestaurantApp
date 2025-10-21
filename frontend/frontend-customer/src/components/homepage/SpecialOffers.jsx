import { Link } from 'react-router-dom';
import LoadMoreButton from '../common/LoadMoreButton';
import './Homepage.css';

const SpecialOffers = ({ offers, pagination, loading, onLoadMore, loadMoreLoading }) => {
  if (loading && (!offers || offers.length === 0)) {
    return (
      <section className="special-offers">
        <h2>Special Offers</h2>
        <div className="offers-container loading">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="offer-card skeleton"></div>
          ))}
        </div>
      </section>
    );
  }
  
  if (!offers || offers.length === 0) {
    return null;
  }
  
  return (
    <section className="special-offers">
      <h2>Special Offers</h2>
      <div className="offers-container">
        {offers.map(offer => (
          <div key={offer.offer_id} className="offer-card">
            <div className="offer-content">
              <h3>{offer.title}</h3>
              <p>{offer.description}</p>
              <div className="offer-details">
                <span className="offer-type">
                  {offer.offer_type === 'percentage' ? `${offer.discount_value}% OFF` : 
                   offer.offer_type === 'fixed' ? `$${offer.discount_value} OFF` : 
                   offer.offer_type}
                </span>
                {offer.min_order_amount > 0 && (
                  <span className="min-order">Min order: ${offer.min_order_amount}</span>
                )}
              </div>
              <Link 
                to={`/restaurant/${offer.restaurant || offer.restaurant_id}`}
                className="use-offer-btn"
              >
                Use Offer
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Load More Button for pagination */}
      {pagination?.next && onLoadMore && (
        <LoadMoreButton
          loading={loadMoreLoading}
          onClick={onLoadMore}
        />
      )}
      
      {/* Loading indicator for additional items */}
      {loading && offers.length > 0 && (
        <div className="loading-more">
          <div className="spinner"></div>
          <p>Loading more offers...</p>
        </div>
      )}
      
    </section>
  );
};

export default SpecialOffers;