import { useState, useEffect } from 'react';
import { X, Palette, Type, ListOrdered, Eye, EyeOff } from 'lucide-react';
import './styles/ModalComponents.css';

const CreateCategoryModal = ({ category, onSubmit, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    display_order: 0,
    display_color: '#667eea',
    is_active: true,
    is_featured: false
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (category) {
      setFormData({
        name: category.name || '',
        description: category.description || '',
        display_order: category.display_order || 0,
        display_color: category.display_color || '#667eea',
        is_active: category.is_active !== false,
        is_featured: category.is_featured || false
      });
    }
  }, [category]);

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
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
      newErrors.name = 'Category name is required';
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

  const colorOptions = [
    '#667eea', '#764ba2', '#f093fb', '#f5576c',
    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
    '#fa709a', '#fee140', '#a8edea', '#fed6e3'
  ];

  return (
    <div className="modal-overlay">
      <div className="modal-container glass-card">
        <div className="modal-header">
          <h2>{category ? 'Edit Category' : 'Create New Category'}</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label className="form-label">
              <Type size={16} />
              Category Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`form-input ${errors.name ? 'error' : ''}`}
              placeholder="Enter category name"
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
              placeholder="Enter category description (optional)"
              rows="3"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <ListOrdered size={16} />
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

            <div className="form-group">
              <label className="form-label">
                <Palette size={16} />
                Display Color
              </label>
              <div className="color-selection">
                <div 
                  className="color-preview"
                  style={{ backgroundColor: formData.display_color }}
                />
                <input
                  type="color"
                  value={formData.display_color}
                  onChange={(e) => handleChange('display_color', e.target.value)}
                  className="color-input"
                />
              </div>
            </div>
          </div>

          <div className="color-options">
            {colorOptions.map(color => (
              <button
                key={color}
                type="button"
                className="color-option"
                style={{ backgroundColor: color }}
                onClick={() => handleChange('display_color', color)}
              />
            ))}
          </div>

          <div className="form-row">
            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => handleChange('is_active', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  {formData.is_active ? <Eye size={14} /> : <EyeOff size={14} />}
                  Active Category
                </span>
              </label>
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => handleChange('is_featured', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  Featured Category
                </span>
              </label>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {category ? 'Update Category' : 'Create Category'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCategoryModal;