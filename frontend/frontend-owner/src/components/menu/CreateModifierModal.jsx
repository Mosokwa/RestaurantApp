import { useState, useEffect } from 'react';
import { X, Type, DollarSign, ListOrdered, Eye, EyeOff } from 'lucide-react';
import './styles/ModalComponents.css';

const CreateModifierModal = ({ modifier, groups, selectedGroup, onSubmit, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price_modifier: '0.00',
    is_available: true,
    display_order: 0,
    modifier_group: ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (modifier) {
      setFormData({
        name: modifier.name || '',
        description: modifier.description || '',
        price_modifier: modifier.price_modifier || '0.00',
        is_available: modifier.is_available !== false,
        display_order: modifier.display_order || 0,
        modifier_group: modifier.modifier_group || ''
      });
    } else if (selectedGroup) {
      setFormData(prev => ({
        ...prev,
        modifier_group: selectedGroup.modifier_id
      }));
    }
  }, [modifier, selectedGroup]);

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
      newErrors.name = 'Modifier name is required';
    }
    
    if (!formData.modifier_group) {
      newErrors.modifier_group = 'Modifier group is required';
    }
    
    if (formData.price_modifier === '' || parseFloat(formData.price_modifier) < 0) {
      newErrors.price_modifier = 'Price modifier must be 0 or greater';
    }
    
    if (formData.display_order < 0) {
      newErrors.display_order = 'Display order cannot be negative';
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

  const getSelectedGroup = () => {
    return groups.find(group => group.modifier_id == formData.modifier_group);
  };

  const selectedGroupData = getSelectedGroup();

  return (
    <div className="modal-overlay">
      <div className="modal-container glass-card">
        <div className="modal-header">
          <h2>{modifier ? 'Edit Modifier' : 'Create New Modifier'}</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label className="form-label">
              Modifier Group *
            </label>
            <select
              value={formData.modifier_group}
              onChange={(e) => handleChange('modifier_group', e.target.value)}
              className={`form-select ${errors.modifier_group ? 'error' : ''}`}
              disabled={!!selectedGroup} // Disable if group is pre-selected
            >
              <option value="">Select Group</option>
              {groups.map(group => (
                <option key={group.modifier_id} value={group.modifier_id}>
                  {group.name}
                </option>
              ))}
            </select>
            {errors.modifier_group && <span className="error-text">{errors.modifier_group}</span>}
            
            {selectedGroupData && (
              <div className="group-info-preview">
                <p><strong>Group:</strong> {selectedGroupData.name}</p>
                <p><strong>Settings:</strong> {selectedGroupData.min_selections}-{selectedGroupData.max_selections} selections</p>
                {selectedGroupData.is_required && (
                  <p className="required-badge">Required</p>
                )}
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">
              <Type size={16} />
              Modifier Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`form-input ${errors.name ? 'error' : ''}`}
              placeholder="Enter modifier name (e.g., Large, Extra Cheese, Spicy)"
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
              placeholder="Enter modifier description (optional)"
              rows="2"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <DollarSign size={16} />
                Price Modifier *
              </label>
              <div className="price-input-container">
                <span className="price-prefix">
                  {parseFloat(formData.price_modifier) > 0 ? '+' : ''}$
                </span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.price_modifier}
                  onChange={(e) => handleChange('price_modifier', e.target.value)}
                  className={`form-input price-input ${errors.price_modifier ? 'error' : ''}`}
                  placeholder="0.00"
                />
              </div>
              {errors.price_modifier && <span className="error-text">{errors.price_modifier}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">
                Display Order
              </label>
              <input
                type="number"
                value={formData.display_order}
                onChange={(e) => handleChange('display_order', parseInt(e.target.value) || 0)}
                className={`form-input ${errors.display_order ? 'error' : ''}`}
                min="0"
              />
              {errors.display_order && <span className="error-text">{errors.display_order}</span>}
            </div>
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_available}
                onChange={(e) => handleChange('is_available', e.target.checked)}
                className="checkbox-input"
              />
              <span className="checkbox-custom"></span>
              <span className="checkbox-text">
                {formData.is_available ? <Eye size={14} /> : <EyeOff size={14} />}
                Available for Selection
              </span>
            </label>
          </div>

          <div className="modifier-preview">
            <h5>Modifier Preview:</h5>
            <div className="preview-card">
              <div className="preview-header">
                <span className="preview-name">{formData.name || 'Modifier Name'}</span>
                <span className="preview-price">
                  {parseFloat(formData.price_modifier) > 0 ? '+' : ''}
                  ${parseFloat(formData.price_modifier || 0).toFixed(2)}
                </span>
              </div>
              {formData.description && (
                <p className="preview-description">{formData.description}</p>
              )}
              <div className="preview-status">
                {formData.is_available ? (
                  <span className="status-available">Available</span>
                ) : (
                  <span className="status-unavailable">Unavailable</span>
                )}
              </div>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {modifier ? 'Update Modifier' : 'Create Modifier'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateModifierModal;