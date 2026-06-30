// src/pages/restaurant/components/RealTimeAlert.jsx
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, X } from 'lucide-react';

const RealTimeAlert = ({ updates }) => {
  const [currentAlert, setCurrentAlert] = useState(null);
  
  useEffect(() => {
    if (updates && updates.length > 0 && !currentAlert) {
      setCurrentAlert(updates[0]);
      
      // Auto-dismiss after 5 seconds
      const timer = setTimeout(() => {
        setCurrentAlert(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [updates, currentAlert]);
  
  if (!currentAlert) return null;
  
  const getAlertMessage = () => {
    if (currentAlert.type === 'availability') {
      return `${currentAlert.itemName || 'An item'} is now ${currentAlert.isAvailable ? 'available' : 'unavailable'}`;
    }
    return currentAlert.message;
  };
  
  return (
    <AnimatePresence>
      {currentAlert && (
        <motion.div
          className="real-time-alert"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
        >
          <AlertCircle size={18} />
          <span>{getAlertMessage()}</span>
          <button onClick={() => setCurrentAlert(null)}>
            <X size={16} />
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default RealTimeAlert;