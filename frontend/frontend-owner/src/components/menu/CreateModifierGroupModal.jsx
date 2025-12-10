import { useState, useEffect } from 'react';
import { X, Type, ListOrdered, Users, Settings } from 'lucide-react';
import './styles/ModalComponents.css';

const CreateModifierGroupModal = ({ group, onSubmit, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_required: false,
    min_selections: 0,
    max_selections: 1
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (group) {
      setFormData({
        name: group.name || '',
        description: group.description || '',
        is_required: group.is_required || false,
        min_selections: group.min_selections || 0,
        max_selections: group.max_selections || 1
      });
    }
  }, [group]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Group name is required';
    }
    
    if (formData.min_selections < 0) {
      newErrors.min_selections = 'Minimum selections cannot be negative';
    }
    
    if (formData.max_selections < 1) {
      newErrors.max_selections = 'Maximum selections must be at least 1';
    }
    
    if (formData.min_selections > formData.max_selections) {
      newErrors.min_selections = 'Minimum cannot exceed maximum selections';
      newErrors.max_selections = 'Maximum cannot be less than minimum selections';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-container glass-card">
        <div className="modal-header">
          <h2>{group ? 'Edit Modifier Group' : 'Create Modifier Group'}</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label className="form-label">
              <Type size={16} />
              Group Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`form-input ${errors.name ? 'error' : ''}`}
              placeholder="Enter group name (e.g., Size, Toppings, Extras)"
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label className="form-label">
              <ListOrdered size={16} />
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              className="form-textarea"
              placeholder="Enter group description (optional)"
              rows="3"
            />
          </div>

          <div className="form-section">
            <h4 className="section-title">
              <Settings size={16} />
              Selection Settings
            </h4>
            
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">
                  Minimum Selections
                </label>
                <input
                  type="number"
                  value={formData.min_selections}
                  onChange={(e) => handleChange('min_selections', parseInt(e.target.value) || 0)}
                  className={`form-input ${errors.min_selections ? 'error' : ''}`}
                  min="0"
                />
                {errors.min_selections && <span className="error-text">{errors.min_selections}</span>}
              </div>

              <div className="form-group">
                <label className="form-label">
                  Maximum Selections
                </label>
                <input
                  type="number"
                  value={formData.max_selections}
                  onChange={(e) => handleChange('max_selections', parseInt(e.target.value) || 1)}
                  className={`form-input ${errors.max_selections ? 'error' : ''}`}
                  min="1"
                />
                {errors.max_selections && <span className="error-text">{errors.max_selections}</span>}
              </div>
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_required}
                  onChange={(e) => handleChange('is_required', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  <Users size={14} />
                  Required Selection
                </span>
              </label>
              <p className="checkbox-help">
                Customers must select at least one modifier from this group
              </p>
            </div>
          </div>

          <div className="selection-preview">
            <h5>Selection Preview:</h5>
            <p>
              Customers can select {formData.min_selections} to {formData.max_selections} option(s)
              {formData.is_required && ' (required)'}
            </p>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {group ? 'Update Group' : 'Create Group'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateModifierGroupModal;