import { useState, useEffect } from 'react';
import { 
  X, 
  Type, 
  DollarSign, 
  Clock, 
  Image, 
  Utensils,
  Flame,
  Leaf,
  Wheat,
  Sparkles,
  Eye,
  EyeOff
} from 'lucide-react';
import './styles/ModalComponents.css';

const CreateItemModal = ({ item, categories, onSubmit, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    price: '',
    category: '',
    item_type: 'main',
    preparation_time: 15,
    calories: '',
    is_vegetarian: false,
    is_vegan: false,
    is_gluten_free: false,
    is_spicy: false,
    is_featured: false,
    is_available: true,
    image: null
  });
  const [errors, setErrors] = useState({});
  const [imagePreview, setImagePreview] = useState(null);

  useEffect(() => {
    if (item) {
      setFormData({
        name: item.name || '',
        description: item.description || '',
        price: item.price || '',
        category: item.category?.category_id || '',
        item_type: item.item_type || 'main',
        preparation_time: item.preparation_time || 15,
        calories: item.calories || '',
        is_vegetarian: item.is_vegetarian || false,
        is_vegan: item.is_vegan || false,
        is_gluten_free: item.is_gluten_free || false,
        is_spicy: item.is_spicy || false,
        is_featured: item.is_featured || false,
        is_available: item.is_available !== false,
        image: null
      });
      
      if (item.image) {
        setImagePreview(item.image);
      }
    }
  }, [item]);

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

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setErrors(prev => ({ ...prev, image: 'Image size must be less than 5MB' }));
        return;
      }
      
      if (!file.type.startsWith('image/')) {
        setErrors(prev => ({ ...prev, image: 'Please select an image file' }));
        return;
      }
      
      handleChange('image', file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Item name is required';
    }
    
    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Valid price is required';
    }
    
    if (!formData.category) {
      newErrors.category = 'Category is required';
    }
    
    if (!formData.preparation_time || formData.preparation_time < 1) {
      newErrors.preparation_time = 'Preparation time must be at least 1 minute';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    // Create FormData for file upload
    const submitData = new FormData();
    
    Object.keys(formData).forEach(key => {
      if (key === 'image' && formData[key]) {
        submitData.append(key, formData[key]);
      } else if (formData[key] !== null && formData[key] !== undefined) {
        submitData.append(key, formData[key]);
      }
    });
    
    onSubmit(submitData);
  };

  const itemTypes = [
    { value: 'main', label: 'Main Dish', icon: Utensils },
    { value: 'beverage', label: 'Beverage', icon: '🥤' },
    { value: 'dessert', label: 'Dessert', icon: '🍰' },
    { value: 'side', label: 'Side Dish', icon: '🍟' },
    { value: 'combo', label: 'Combo Meal', icon: '🍱' }
  ];

  return (
    <div className="modal-overlay">
      <div className="modal-container large glass-card">
        <div className="modal-header">
          <h2>{item ? 'Edit Menu Item' : 'Create New Menu Item'}</h2>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {/* Image Upload */}
          <div className="form-group">
            <label className="form-label">
              <Image size={16} />
              Item Image
            </label>
            <div className="image-upload">
              <div className="image-preview">
                {imagePreview ? (
                  <img src={imagePreview} alt="Preview" />
                ) : (
                  <div className="image-placeholder">
                    <Image size={32} />
                    <span>Click to upload image</span>
                  </div>
                )}
              </div>
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="image-input"
              />
              {errors.image && <span className="error-text">{errors.image}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <Type size={16} />
                Item Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className={`form-input ${errors.name ? 'error' : ''}`}
                placeholder="Enter item name"
              />
              {errors.name && <span className="error-text">{errors.name}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">
                <DollarSign size={16} />
                Price *
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.price}
                onChange={(e) => handleChange('price', e.target.value)}
                className={`form-input ${errors.price ? 'error' : ''}`}
                placeholder="0.00"
              />
              {errors.price && <span className="error-text">{errors.price}</span>}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              className="form-textarea"
              placeholder="Enter item description"
              rows="3"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                Category *
              </label>
              <select
                value={formData.category}
                onChange={(e) => handleChange('category', e.target.value)}
                className={`form-select ${errors.category ? 'error' : ''}`}
              >
                <option value="">Select Category</option>
                {categories.map(cat => (
                  <option key={cat.category_id} value={cat.category_id}>
                    {cat.name}
                  </option>
                ))}
              </select>
              {errors.category && <span className="error-text">{errors.category}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">
                Item Type
              </label>
              <select
                value={formData.item_type}
                onChange={(e) => handleChange('item_type', e.target.value)}
                className="form-select"
              >
                {itemTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                <Clock size={16} />
                Preparation Time (minutes) *
              </label>
              <input
                type="number"
                min="1"
                value={formData.preparation_time}
                onChange={(e) => handleChange('preparation_time', parseInt(e.target.value) || 1)}
                className={`form-input ${errors.preparation_time ? 'error' : ''}`}
              />
              {errors.preparation_time && <span className="error-text">{errors.preparation_time}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">
                Calories
              </label>
              <input
                type="number"
                min="0"
                value={formData.calories}
                onChange={(e) => handleChange('calories', e.target.value)}
                className="form-input"
                placeholder="Optional"
              />
            </div>
          </div>

          {/* Dietary Preferences */}
          <div className="form-section">
            <h4 className="section-title">Dietary & Preferences</h4>
            <div className="checkbox-grid">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_vegetarian}
                  onChange={(e) => handleChange('is_vegetarian', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  <Leaf size={14} />
                  Vegetarian
                </span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_vegan}
                  onChange={(e) => handleChange('is_vegan', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  <Wheat size={14} />
                  Vegan
                </span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_gluten_free}
                  onChange={(e) => handleChange('is_gluten_free', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  Gluten Free
                </span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_spicy}
                  onChange={(e) => handleChange('is_spicy', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  <Flame size={14} />
                  Spicy
                </span>
              </label>
            </div>
          </div>

          {/* Item Settings */}
          <div className="form-section">
            <h4 className="section-title">Item Settings</h4>
            <div className="checkbox-grid">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.is_featured}
                  onChange={(e) => handleChange('is_featured', e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-custom"></span>
                <span className="checkbox-text">
                  <Sparkles size={14} />
                  Featured Item
                </span>
              </label>

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
                  Available for Order
                </span>
              </label>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              {item ? 'Update Item' : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateItemModal;