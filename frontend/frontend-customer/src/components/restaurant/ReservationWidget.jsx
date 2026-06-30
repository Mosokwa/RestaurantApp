// src/pages/restaurant/components/ReservationWidget.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, 
  Clock, 
  Users, 
  CreditCard,
  Check,
  X,
  AlertCircle,
  Phone,
  Mail,
  MessageSquare,
  Gift
} from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { toast } from 'react-hot-toast';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import {
  createReservation,
  checkTableAvailability,
  toggleReservationModal,
  setReservationField
} from '../../store/slices/restaurantHomepageSlice';
import { authService } from '../../services/authService';

const ReservationWidget = ({ restaurantId, restaurant, reservationInfo }) => {
  const dispatch = useDispatch();
  const { reservation, availability, reservationSuccess, loading } = useSelector(
    (state) => state.restaurantHomepage
  );
  
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [availableTimeSlots, setAvailableTimeSlots] = useState([]);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState(null);
  const [customerInfo, setCustomerInfo] = useState({
    name: '',
    email: '',
    phone: ''
  });
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [step, setStep] = useState(1); // 1: details, 2: customer info, 3: confirmation
  
  const currentUser = authService.getCurrentUser();
  
  // Pre-fill customer info if logged in
  useEffect(() => {
    if (currentUser) {
      setCustomerInfo({
        name: currentUser.full_name || '',
        email: currentUser.email || '',
        phone: currentUser.phone_number || ''
      });
    }
  }, [currentUser]);
  
  // Fetch available time slots when date changes
  useEffect(() => {
    if (selectedDate && reservation.partySize) {
      fetchAvailableTimeSlots();
    }
  }, [selectedDate, reservation.partySize]);
  
  const fetchAvailableTimeSlots = async () => {
    try {
      const response = await dispatch(checkTableAvailability({
        restaurantId,
        date: selectedDate.toISOString().split('T')[0],
        time: null,
        partySize: reservation.partySize
      })).unwrap();
      
      setAvailableTimeSlots(response.available_slots || []);
    } catch (error) {
      console.error('Failed to fetch time slots:', error);
      toast.error('Unable to fetch available times');
    }
  };
  
  const handleDateChange = (date) => {
    setSelectedDate(date);
    setSelectedTimeSlot(null);
    dispatch(setReservationField({ field: 'date', value: date.toISOString().split('T')[0] }));
  };
  
  const handleTimeSlotSelect = (slot) => {
    setSelectedTimeSlot(slot);
    dispatch(setReservationField({ field: 'time', value: slot.time }));
  };
  
  const handlePartySizeChange = (delta) => {
    const newSize = reservation.partySize + delta;
    if (newSize >= (restaurantInfo?.min_party_size || 1) && 
        newSize <= (restaurantInfo?.max_party_size || 20)) {
      dispatch(setReservationField({ field: 'partySize', value: newSize }));
      setSelectedTimeSlot(null);
    }
  };
  
  const handleOccasionChange = (e) => {
    dispatch(setReservationField({ field: 'occasion', value: e.target.value }));
  };
  
  const handleSpecialRequestsChange = (e) => {
    dispatch(setReservationField({ field: 'specialRequests', value: e.target.value }));
  };
  
  const handleCustomerInfoChange = (field, value) => {
    setCustomerInfo(prev => ({ ...prev, [field]: value }));
  };
  
  const handleNextStep = () => {
    if (step === 1) {
      if (!selectedTimeSlot) {
        toast.error('Please select a time slot');
        return;
      }
      if (!reservation.partySize) {
        toast.error('Please select party size');
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (!customerInfo.name || !customerInfo.email || !customerInfo.phone) {
        toast.error('Please fill in all customer information');
        return;
      }
      if (!customerInfo.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
        toast.error('Please enter a valid email address');
        return;
      }
      setStep(3);
    }
  };
  
  const handlePreviousStep = () => {
    setStep(step - 1);
  };
  
  const handleSubmitReservation = async () => {
    const reservationData = {
      restaurant: restaurantId,
      branch: restaurantInfo?.branches?.[0]?.branch_id, // Use first branch or allow selection
      reservation_date: selectedDate.toISOString().split('T')[0],
      reservation_time: selectedTimeSlot.time,
      party_size: reservation.partySize,
      special_occasion: reservation.occasion !== 'none' ? reservation.occasion : null,
      special_requests: reservation.specialRequests,
      customer: {
        name: customerInfo.name,
        email: customerInfo.email,
        phone: customerInfo.phone
      }
    };
    
    try {
      const result = await dispatch(createReservation(reservationData)).unwrap();
      setShowConfirmation(true);
      toast.success('Reservation confirmed! Check your email for details.');
      
      // Reset after 3 seconds
      setTimeout(() => {
        setShowConfirmation(false);
        dispatch(toggleReservationModal(false));
        setStep(1);
        setSelectedTimeSlot(null);
      }, 3000);
    } catch (error) {
      toast.error(error.message || 'Failed to create reservation');
    }
  };
  
  const occasions = [
    { value: 'none', label: 'No special occasion' },
    { value: 'birthday', label: '🎂 Birthday' },
    { value: 'anniversary', label: '💝 Anniversary' },
    { value: 'business', label: '💼 Business Meeting' },
    { value: 'date', label: '💕 Romantic Date' },
    { value: 'family', label: '👨‍👩‍👧‍👦 Family Gathering' },
    { value: 'celebration', label: '🎉 Celebration' }
  ];
  
  const generateTimeSlots = () => {
    const slots = [];
    const startHour = 11; // 11 AM
    const endHour = 22; // 10 PM
    const interval = 30; // 30 minutes
    
    for (let hour = startHour; hour <= endHour; hour++) {
      for (let minute = 0; minute < 60; minute += interval) {
        if (hour === endHour && minute > 0) continue;
        const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        slots.push({ time, available: availableTimeSlots.includes(time) });
      }
    }
    
    return slots;
  };
  
  const timeSlots = generateTimeSlots();
  
  return (
    <div className="reservation-widget">
      <div className="widget-header">
        <h3>Make a Reservation</h3>
        <p>Secure your table at {restaurant?.name}</p>
      </div>
      
      <AnimatePresence mode="wait">
        {!showConfirmation ? (
          <motion.div
            key="form"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="reservation-form"
          >
            {/* Step 1: Date, Time, Party Size */}
            {step === 1 && (
              <div className="form-step">
                {/* Date Picker */}
                <div className="form-group">
                  <label>
                    <Calendar size={18} />
                    Select Date
                  </label>
                  <DatePicker
                    selected={selectedDate}
                    onChange={handleDateChange}
                    minDate={new Date()}
                    maxDate={new Date(Date.now() + (restaurantInfo?.reservation_max_days_ahead || 30) * 24 * 60 * 60 * 1000)}
                    dateFormat="MMMM d, yyyy"
                    className="date-picker-input"
                    wrapperClassName="date-picker-wrapper"
                  />
                </div>
                
                {/* Party Size */}
                <div className="form-group">
                  <label>
                    <Users size={18} />
                    Party Size
                  </label>
                  <div className="party-size-control">
                    <button 
                      onClick={() => handlePartySizeChange(-1)}
                      disabled={reservation.partySize <= (restaurantInfo?.min_party_size || 1)}
                    >
                      <Minus size={18} />
                    </button>
                    <span className="party-size-value">{reservation.partySize} {reservation.partySize === 1 ? 'Guest' : 'Guests'}</span>
                    <button 
                      onClick={() => handlePartySizeChange(1)}
                      disabled={reservation.partySize >= (restaurantInfo?.max_party_size || 20)}
                    >
                      <Plus size={18} />
                    </button>
                  </div>
                </div>
                
                {/* Time Slots */}
                <div className="form-group">
                  <label>
                    <Clock size={18} />
                    Select Time
                  </label>
                  <div className="time-slots-grid">
                    {timeSlots.map((slot) => (
                      <button
                        key={slot.time}
                        className={`time-slot ${selectedTimeSlot?.time === slot.time ? 'selected' : ''} ${!slot.available ? 'unavailable' : ''}`}
                        onClick={() => slot.available && handleTimeSlotSelect(slot)}
                        disabled={!slot.available}
                      >
                        {slot.time}
                        {!slot.available && <span className="unavailable-badge">Booked</span>}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Occasion */}
                <div className="form-group">
                  <label>
                    <Gift size={18} />
                    Special Occasion
                  </label>
                  <select value={reservation.occasion} onChange={handleOccasionChange} className="occasion-select">
                    {occasions.map(occasion => (
                      <option key={occasion.value} value={occasion.value}>
                        {occasion.label}
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Special Requests */}
                <div className="form-group">
                  <label>
                    <MessageSquare size={18} />
                    Special Requests
                  </label>
                  <textarea
                    placeholder="Any special requests? (allergies, preferences, etc.)"
                    value={reservation.specialRequests}
                    onChange={handleSpecialRequestsChange}
                    rows={3}
                    className="special-requests-input"
                  />
                </div>
              </div>
            )}
            
            {/* Step 2: Customer Information */}
            {step === 2 && (
              <div className="form-step">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input
                    type="text"
                    value={customerInfo.name}
                    onChange={(e) => handleCustomerInfoChange('name', e.target.value)}
                    placeholder="Enter your full name"
                    className="customer-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Email Address *</label>
                  <input
                    type="email"
                    value={customerInfo.email}
                    onChange={(e) => handleCustomerInfoChange('email', e.target.value)}
                    placeholder="your@email.com"
                    className="customer-input"
                  />
                </div>
                
                <div className="form-group">
                  <label>Phone Number *</label>
                  <input
                    type="tel"
                    value={customerInfo.phone}
                    onChange={(e) => handleCustomerInfoChange('phone', e.target.value)}
                    placeholder="(555) 555-5555"
                    className="customer-input"
                  />
                </div>
                
                {reservationInfo?.deposit_required && (
                  <div className="deposit-info">
                    <AlertCircle size={16} />
                    <span>A deposit of ${reservationInfo.deposit_amount} is required to secure your reservation</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Step 3: Review & Confirm */}
            {step === 3 && (
              <div className="form-step review-step">
                <h4>Review Your Reservation</h4>
                
                <div className="review-card">
                  <div className="review-item">
                    <Calendar size={18} />
                    <div>
                      <strong>Date & Time</strong>
                      <p>{selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })} at {selectedTimeSlot?.time}</p>
                    </div>
                  </div>
                  
                  <div className="review-item">
                    <Users size={18} />
                    <div>
                      <strong>Party Size</strong>
                      <p>{reservation.partySize} {reservation.partySize === 1 ? 'Guest' : 'Guests'}</p>
                    </div>
                  </div>
                  
                  {reservation.occasion !== 'none' && (
                    <div className="review-item">
                      <Gift size={18} />
                      <div>
                        <strong>Occasion</strong>
                        <p>{occasions.find(o => o.value === reservation.occasion)?.label}</p>
                      </div>
                    </div>
                  )}
                  
                  {reservation.specialRequests && (
                    <div className="review-item">
                      <MessageSquare size={18} />
                      <div>
                        <strong>Special Requests</strong>
                        <p>{reservation.specialRequests}</p>
                      </div>
                    </div>
                  )}
                  
                  <div className="review-item">
                    <div>
                      <strong>Contact Information</strong>
                      <p>{customerInfo.name}</p>
                      <p>{customerInfo.email}</p>
                      <p>{customerInfo.phone}</p>
                    </div>
                  </div>
                </div>
                
                {reservationInfo?.requires_confirmation && (
                  <div className="confirmation-note">
                    <AlertCircle size={16} />
                    <span>This reservation requires confirmation from the restaurant. You will receive an email once confirmed.</span>
                  </div>
                )}
              </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="form-navigation">
              {step > 1 && (
                <button onClick={handlePreviousStep} className="btn-secondary">
                  Back
                </button>
              )}
              {step < 3 ? (
                <button onClick={handleNextStep} className="btn-primary">
                  Continue
                </button>
              ) : (
                <button 
                  onClick={handleSubmitReservation} 
                  className="btn-primary"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <div className="spinner-small"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      {reservationInfo?.deposit_required ? `Pay Deposit & Confirm` : 'Confirm Reservation'}
                    </>
                  )}
                </button>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="confirmation"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="confirmation-message"
          >
            <div className="success-icon">
              <Check size={48} />
            </div>
            <h3>Reservation Confirmed!</h3>
            <p>Your table has been reserved for {selectedDate.toLocaleDateString()} at {selectedTimeSlot?.time}</p>
            <p className="confirmation-detail">A confirmation has been sent to {customerInfo.email}</p>
            <div className="confirmation-code">
              <span>Reservation Code: </span>
              <strong>{reservationSuccess?.reservation_code}</strong>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Restaurant Policies */}
      <div className="reservation-policies">
        <h4>Reservation Policies</h4>
        <ul>
          <li>Please arrive 5-10 minutes before your reservation time</li>
          <li>We hold tables for 15 minutes past reservation time</li>
          <li>Cancellations must be made at least {restaurantInfo?.cancellation_policy_hours || 24} hours in advance</li>
          {reservationInfo?.deposit_required && (
            <li>Deposit is non-refundable for no-shows or late cancellations</li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default ReservationWidget;