// components/onboarding/RestaurantOnboarding.jsx
import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { restaurantService } from '../../services/restaurantService';
import { cuisineService } from '../../services/cuisineService';
import { fetchOwnerProfile } from '../../store/slices/ownerAuthSlice';
import { setPendingRestaurant, completeOnboarding } from '../../store/slices/authSlice';
import { 
  ChevronLeft, 
  ChevronRight, 
  MapPin, 
  Clock, 
  Utensils,
  Plus,
  Trash2,
  Building,
  Check
} from 'lucide-react';
import './RestaurantOnboarding.css';

const RestaurantOnboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cuisines, setCuisines] = useState([]);
  const [selectedCuisines, setSelectedCuisines] = useState([]);
  const [isFirstRestaurant, setIsFirstRestaurant] = useState(false);
  const [formData, setFormData] = useState({
    restaurant: {
      name: '',
      description: '',
      phone_number: '',
      website: '',
      price_range: 'medium',
      status: 'active'
    },
    branches: [
      {
        name: 'Main Branch',
        phone_number: '',
        email: '',
        address: {
          street: '',
          city: '',
          state: '',
          country: '',
          postal_code: '',
          latitude: '',
          longitude: ''
        },
        operating_hours: {
          monday: { open: '09:00', close: '22:00', closed: false },
          tuesday: { open: '09:00', close: '22:00', closed: false },
          wednesday: { open: '09:00', close: '22:00', closed: false },
          thursday: { open: '09:00', close: '22:00', closed: false },
          friday: { open: '09:00', close: '23:00', closed: false },
          saturday: { open: '10:00', close: '23:00', closed: false },
          sunday: { open: '10:00', close: '21:00', closed: false }
        }
      }
    ],
    cuisines: [],
    menu: {
      categories: [
        {
          name: 'Appetizers',
          description: 'Start your meal right',
          sort_order: 1,
          items: [
            {
              name: 'Sample Appetizer',
              description: 'A delicious starter to begin your dining experience',
              price: '8.99',
              preparation_time: 15,
              is_available: true,
              sort_order: 1,
              modifiers: []
            }
          ]
        }
      ]
    },
    special_offers: []
  });

  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { owner, restaurants } = useSelector(state => state.ownerAuth);
  const { user, hasPendingRestaurant } = useSelector(state => state.auth);

  useEffect(() => {
    if (!user?.email_verified) return;

    const userHasRestaurants = restaurants && restaurants.length > 0;
    const hasPendingRestaurant = localStorage.getItem('pendingRestaurantSetup') === 'true';

    console.log('🏪 Onboarding Access Check:', {
      userHasRestaurants,
      hasPendingRestaurant,
      restaurantsCount: restaurants?.length
    });

    // Only allow access if user has no restaurants OR has pending setup
    if (userHasRestaurants && !hasPendingRestaurant) {
      console.log('🚫 Redirecting to dashboard - user has restaurants');
      navigate('/owner/dashboard', { replace: true });
    }
  }, [user, restaurants, navigate]);

  // Load cuisines from backend
  useEffect(() => {
    const loadCuisines = async () => {
      try {
        const response = await cuisineService.getCuisines();
        if (response.data) {
          setCuisines(response.data);
        }
      } catch (error) {
        console.error('Failed to load cuisines:', error);
      }
    };
    
    loadCuisines();
  }, []);

  // Check for pending restaurant setup and existing restaurants
  useEffect(() => {
    const checkRestaurantStatus = async () => {
      try {
        const ownerRestaurants = Array.isArray(restaurants) ? restaurants : [];
        const hasExistingRestaurants = ownerRestaurants.length > 0;
        
        const pendingRestaurantData = localStorage.getItem('pendingRestaurantData');
        const hasPendingSetup = localStorage.getItem('pendingRestaurantSetup') === 'true';
        
        console.log('🏪 Restaurant Status Check:', {
          hasExistingRestaurants,
          hasPendingSetup,
          pendingRestaurantData: pendingRestaurantData ? JSON.parse(pendingRestaurantData) : null
        });

        // SCENARIO 1: User has restaurants and no pending setup - redirect to dashboard
        if (hasExistingRestaurants && !hasPendingSetup) {
          console.log('🔄 User has restaurants, redirecting to dashboard');
          navigate('/owner/dashboard', { replace: true });
          return;
        }

        // SCENARIO 2: User has no restaurants and no pending setup - this is first restaurant
        if (!hasExistingRestaurants && !hasPendingSetup) {
          setIsFirstRestaurant(true);
          // Set pending setup flag
          localStorage.setItem('pendingRestaurantSetup', 'true');
          console.log('✅ First restaurant setup initiated');
          return;
        }

        // SCENARIO 3: User has pending setup (from registration or manual creation)
        if (hasPendingSetup && pendingRestaurantData) {
          try {
            const pendingData = JSON.parse(pendingRestaurantData);
            setIsFirstRestaurant(pendingData.isFirstRestaurant || true);
            
            setFormData(prev => ({
              ...prev,
              restaurant: {
                ...prev.restaurant,
                name: pendingData.name || ''
              }
            }));

            console.log('🔄 Auto-filled pending restaurant:', pendingData.name);
          } catch (parseError) {
            console.error('Error parsing pending restaurant data:', parseError);
            localStorage.removeItem('pendingRestaurantData');
            localStorage.setItem('pendingRestaurantSetup', 'true');
          }
        }

        // SCENARIO 4: User manually navigated to onboarding to create additional restaurant
        if (hasExistingRestaurants && !hasPendingSetup && location.pathname.includes('/onboarding')) {
          setIsFirstRestaurant(false);
          console.log('✅ Additional restaurant creation initiated');
          return;
        }

      } catch (error) {
        console.error('Error checking restaurant status:', error);
      }
    };

    checkRestaurantStatus();
  }, [navigate, restaurants, location.pathname]);

  // Enhanced input handlers
  const handleInputChange = (section, field, value) => {
    setFormData(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  const handleBranchChange = (index, field, value) => {
    const updatedBranches = [...formData.branches];
    updatedBranches[index] = {
      ...updatedBranches[index],
      [field]: value
    };
    
    setFormData(prev => ({
      ...prev,
      branches: updatedBranches
    }));
  };

  const handleAddressChange = (branchIndex, field, value) => {
    const updatedBranches = [...formData.branches];
    updatedBranches[branchIndex].address = {
      ...updatedBranches[branchIndex].address,
      [field]: value
    };
    
    setFormData(prev => ({
      ...prev,
      branches: updatedBranches
    }));
  };

  const handleOperatingHoursChange = (branchIndex, day, field, value) => {
    const updatedBranches = [...formData.branches];
    updatedBranches[branchIndex].operating_hours[day] = {
      ...updatedBranches[branchIndex].operating_hours[day],
      [field]: field === 'closed' ? value : value
    };
    
    setFormData(prev => ({
      ...prev,
      branches: updatedBranches
    }));
  };

  // Menu category handlers
  const handleCategoryChange = (index, field, value) => {
    const updatedCategories = [...formData.menu.categories];
    updatedCategories[index] = {
      ...updatedCategories[index],
      [field]: value
    };
    
    setFormData(prev => ({
      ...prev,
      menu: {
        ...prev.menu,
        categories: updatedCategories
      }
    }));
  };

  const handleMenuItemChange = (categoryIndex, itemIndex, field, value) => {
    const updatedCategories = [...formData.menu.categories];
    updatedCategories[categoryIndex].items[itemIndex] = {
      ...updatedCategories[categoryIndex].items[itemIndex],
      [field]: value
    };
    
    setFormData(prev => ({
      ...prev,
      menu: {
        ...prev.menu,
        categories: updatedCategories
      }
    }));
  };

  const addCategory = () => {
    const newCategory = {
      name: '',
      description: '',
      sort_order: formData.menu.categories.length + 1,
      items: []
    };
    
    setFormData(prev => ({
      ...prev,
      menu: {
        ...prev.menu,
        categories: [...prev.menu.categories, newCategory]
      }
    }));
  };

  const addMenuItem = (categoryIndex) => {
    const newItem = {
      name: '',
      description: '',
      price: '0.00',
      preparation_time: 15,
      is_available: true,
      sort_order: formData.menu.categories[categoryIndex].items.length + 1,
      modifiers: []
    };
    
    const updatedCategories = [...formData.menu.categories];
    updatedCategories[categoryIndex].items.push(newItem);
    
    setFormData(prev => ({
      ...prev,
      menu: {
        ...prev.menu,
        categories: updatedCategories
      }
    }));
  };

  const removeCategory = (index) => {
    if (formData.menu.categories.length > 1) {
      const updatedCategories = formData.menu.categories.filter((_, i) => i !== index);
      setFormData(prev => ({
        ...prev,
        menu: {
          ...prev.menu,
          categories: updatedCategories
        }
      }));
    }
  };

  const removeMenuItem = (categoryIndex, itemIndex) => {
    const updatedCategories = [...formData.menu.categories];
    if (updatedCategories[categoryIndex].items.length > 1) {
      updatedCategories[categoryIndex].items = updatedCategories[categoryIndex].items.filter((_, i) => i !== itemIndex);
      setFormData(prev => ({
        ...prev,
        menu: {
          ...prev.menu,
          categories: updatedCategories
        }
      }));
    }
  };

  // Cuisine selection
  const toggleCuisine = (cuisineId) => {
    setSelectedCuisines(prev => {
      const newSelection = prev.includes(cuisineId)
        ? prev.filter(id => id !== cuisineId)
        : [...prev, cuisineId];
      
      // Update form data
      setFormData(prevForm => ({
        ...prevForm,
        cuisines: newSelection
      }));
      
      return newSelection;
    });
  };

  const handleRestaurantLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
        setFormData(prev => ({
        ...prev,
        restaurant: {
            ...prev.restaurant,
            logo: file
        }
        }));
    }
    };

    const handleRestaurantBannerUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
        setFormData(prev => ({
        ...prev,
        restaurant: {
            ...prev.restaurant,
            banner_image: file
        }
        }));
    }
    };

    const handleMenuItemImageUpload = (categoryIndex, itemIndex, event) => {
    const file = event.target.files[0];
    if (file) {
        const updatedCategories = [...formData.menu.categories];
        updatedCategories[categoryIndex].items[itemIndex] = {
        ...updatedCategories[categoryIndex].items[itemIndex],
        image: file
        };
        
        setFormData(prev => ({
        ...prev,
        menu: {
            ...prev.menu,
            categories: updatedCategories
        }
        }));
    }
    };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
        console.log('🚀 Starting restaurant onboarding...');

        const submitFormData = new FormData();

        // 1. Build the data structure that EXACTLY matches your backend
        const onboardingData = {
        restaurant: {
            name: formData.restaurant.name,
            description: formData.restaurant.description || '',
            phone_number: formData.restaurant.phone_number || '',
            email: formData.restaurant.email || user?.email || '',
            website: formData.restaurant.website || '',
            status: 'active',
            is_featured: false,
            // Note: 'cuisines' will be handled separately in the view
        },
        branches: formData.branches.map(branch => ({
            name: branch.name,
            phone_number: branch.phone_number || '',
            address_data: {
                street_address: branch.address.street,
                city: branch.address.city,
                state: branch.address.state,
                country: branch.address.country, 
                postal_code: branch.address.postal_code
            },
            operating_hours: branch.operating_hours,
            is_active: true,
            is_main_branch: formData.branches.length === 1 // First branch is main
        })),
        cuisines: selectedCuisines,
        menu: {
            categories: formData.menu.categories.map((category, index) => ({
            name: category.name,
            description: category.description || '',
            display_order: category.sort_order,
            is_active: true,
            items: category.items.map((item, itemIndex) => ({
                name: item.name,
                description: item.description || '',
                price: item.price,
                preparation_time: item.preparation_time,
                is_available: item.is_available,
                display_order: item.sort_order,
                item_type: 'main', // Default to 'main'
                is_vegetarian: false,
                is_vegan: false,
                is_gluten_free: false,
                is_spicy: false
            }))
            }))
        },
        is_first_restaurant: isFirstRestaurant
        };

        submitFormData.append('data', JSON.stringify(onboardingData));

        // 2. Add files
        if (formData.restaurant.logo) {
        submitFormData.append('restaurant_logo', formData.restaurant.logo);
        }
        if (formData.restaurant.banner_image) {
        submitFormData.append('restaurant_banner', formData.restaurant.banner_image);
        }

        // 3. Add menu item images
        formData.menu.categories.forEach((category, catIndex) => {
        category.items.forEach((item, itemIndex) => {
            if (item.image) {
            submitFormData.append(`menu_item_images[${catIndex}][${itemIndex}]`, item.image);
            }
        });
        });

        console.log('📦 Final data being sent:', onboardingData);
        
        const response = await restaurantService.createRestaurantOnboarding(submitFormData);
        
        if (response.data) {
          console.log('✅ Restaurant onboarding successful!');
          
          // COMPREHENSIVE CLEANUP
          localStorage.removeItem('pendingRestaurantSetup');
          localStorage.removeItem('pendingRestaurantData');
          
          // Update Redux state to clear pending flags
          dispatch(completeOnboarding());
          
          // Refresh restaurants data
          await dispatch(fetchOwnerProfile()).unwrap();
          
          // Simple navigation to dashboard
          setTimeout(() => {
            navigate('/owner/dashboard', { 
              replace: true,
              state: { 
                message: 'Restaurant setup completed successfully!',
                restaurantId: response.data.restaurant_id
              }
            });
          }, 500);
        }
    } catch (error) {
        console.error('❌ Onboarding failed:', error);
        console.error('Error details:', error.response?.data);
        
        const errorDetails = error.response?.data;
        let errorMessage = 'Failed to setup restaurant. Please check all required fields.';
        
        if (errorDetails) {
        // Show validation errors from backend
        if (errorDetails.details) {
            if (typeof errorDetails.details === 'object') {
            const errors = [];
            Object.entries(errorDetails.details).forEach(([field, fieldErrors]) => {
                if (Array.isArray(fieldErrors)) {
                errors.push(`${field}: ${fieldErrors.join(', ')}`);
                } else {
                errors.push(`${field}: ${fieldErrors}`);
                }
            });
            errorMessage = errors.join('; ');
            } else {
            errorMessage = errorDetails.details;
            }
        } else if (errorDetails.error) {
            errorMessage = errorDetails.error;
        }
        }
        
        setError(errorMessage);
    } finally {
        setLoading(false);
    }
  };

  // Add cancel handler
  const handleCancel = () => {
    if (restaurants.length === 0) {
      // If no restaurants, user must complete onboarding
      alert('You need to complete restaurant setup to use the platform.');
      return;
    }
    
    // If user has restaurants, allow cancel and clear pending flag
    dispatch(setPendingRestaurant(false));
    navigate('/owner/dashboard');
  };

  const nextStep = () => {
    if (validateCurrentStep()) {
      setCurrentStep(prev => Math.min(prev + 1, 5));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const validateCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return formData.restaurant.name.trim() !== '';
      case 2:
        return formData.branches.every(branch => 
          branch.name.trim() !== '' && 
          branch.address.street.trim() !== '' &&
          branch.address.city.trim() !== '' &&
          branch.address.postal_code.trim() !== ''
        );
      case 3:
        return selectedCuisines.length > 0;
      case 4:
        return formData.menu.categories.every(category => 
          category.name.trim() !== '' && 
          category.items.every(item => item.name.trim() !== '' && parseFloat(item.price) > 0)
        );
      default:
        return true;
    }
  };

  // Step 1: Basic Information
  const renderStep1 = () => (
    <div className="onboarding-step">
      <div className="step-header">
        <Building className="step-icon" size={24} />
        <h3>Basic Restaurant Information</h3>
      </div>
      <div className="form-grid">
        <div className="input-group">
          <label>Restaurant Name *</label>
          <input
            type="text"
            value={formData.restaurant.name}
            onChange={(e) => handleInputChange('restaurant', 'name', e.target.value)}
            placeholder="Enter your restaurant name"
            className="glass-input"
            required
          />
        </div>
        
        <div className="input-group full-width">
          <label>Description</label>
          <textarea
            value={formData.restaurant.description}
            onChange={(e) => handleInputChange('restaurant', 'description', e.target.value)}
            placeholder="Describe your restaurant's concept, ambiance, and specialties..."
            rows="4"
            className="glass-input"
          />
        </div>
        
        <div className="input-group">
          <label>Phone Number</label>
          <input
            type="tel"
            value={formData.restaurant.phone_number}
            onChange={(e) => handleInputChange('restaurant', 'phone_number', e.target.value)}
            placeholder="+1 (555) 123-4567"
            className="glass-input"
          />
        </div>
        
        <div className="input-group">
          <label>Website</label>
          <input
            type="url"
            value={formData.restaurant.website}
            onChange={(e) => handleInputChange('restaurant', 'website', e.target.value)}
            placeholder="https://yourrestaurant.com"
            className="glass-input"
          />
        </div>
        
        <div className="input-group">
          <label>Price Range</label>
          <select
            value={formData.restaurant.price_range}
            onChange={(e) => handleInputChange('restaurant', 'price_range', e.target.value)}
            className="glass-input"
          >
            <option value="low">$ - Budget Friendly</option>
            <option value="medium">$$ - Moderate</option>
            <option value="high">$$$ - Upscale</option>
            <option value="luxury">$$$$ - Fine Dining</option>
          </select>
        </div>

        <div className="input-group full-width">
        <label>Restaurant Logo</label>
        <div className="image-upload-container">
            <input
            type="file"
            accept="image/*"
            onChange={handleRestaurantLogoUpload}
            className="image-upload-input"
            id="restaurant-logo"
            />
            <label htmlFor="restaurant-logo" className="image-upload-label">
            <div className="image-upload-preview">
                {formData.restaurant.logo ? (
                <img 
                    src={URL.createObjectURL(formData.restaurant.logo)} 
                    alt="Logo preview" 
                    className="image-preview"
                />
                ) : (
                <div className="image-upload-placeholder">
                    <Plus size={24} />
                    <span>Upload Logo</span>
                </div>
                )}
            </div>
            </label>
        </div>
        </div>

        <div className="input-group full-width">
        <label>Banner Image</label>
        <div className="image-upload-container">
            <input
            type="file"
            accept="image/*"
            onChange={handleRestaurantBannerUpload}
            className="image-upload-input"
            id="restaurant-banner"
            />
            <label htmlFor="restaurant-banner" className="image-upload-label">
            <div className="image-upload-preview banner-preview">
                {formData.restaurant.banner_image ? (
                <img 
                    src={URL.createObjectURL(formData.restaurant.banner_image)} 
                    alt="Banner preview" 
                    className="image-preview"
                />
                ) : (
                <div className="image-upload-placeholder">
                    <Plus size={24} />
                    <span>Upload Banner Image</span>
                </div>
                )}
            </div>
            </label>
        </div>
        </div>
      </div>
    </div>
  );

  // Step 2: Branch Information - FIXED INPUT HANDLING
  const renderStep2 = () => (
    <div className="onboarding-step">
      <div className="step-header">
        <MapPin className="step-icon" size={24} />
        <h3>Branch Locations</h3>
      </div>
      <p className="step-description">Add your restaurant locations. You can add multiple branches.</p>
      
      {formData.branches.map((branch, index) => (
        <div key={index} className="branch-section glass-card">
          <div className="section-header">
            <h4>Branch {index + 1}</h4>
            {formData.branches.length > 1 && (
              <button 
                type="button" 
                onClick={() => {
                  const updatedBranches = formData.branches.filter((_, i) => i !== index);
                  setFormData(prev => ({ ...prev, branches: updatedBranches }));
                }}
                className="btn-danger"
              >
                <Trash2 size={16} />
                Remove
              </button>
            )}
          </div>
          
          <div className="form-grid">
            <div className="input-group">
              <label>Branch Name *</label>
              <input
                type="text"
                value={branch.name}
                onChange={(e) => handleBranchChange(index, 'name', e.target.value)}
                placeholder="Main Branch, Downtown Location, etc."
                className="glass-input"
                required
              />
            </div>
            
            <div className="input-group">
              <label>Branch Phone</label>
              <input
                type="tel"
                value={branch.phone_number}
                onChange={(e) => handleBranchChange(index, 'phone_number', e.target.value)}
                placeholder="+1 (555) 123-4567"
                className="glass-input"
              />
            </div>
            
            <div className="input-group full-width">
              <label>Street Address *</label>
              <input
                type="text"
                value={branch.address.street}
                onChange={(e) => handleAddressChange(index, 'street', e.target.value)}
                placeholder="123 Main Street"
                className="glass-input"
                required
              />
            </div>
            
            <div className="input-group">
              <label>City *</label>
              <input
                type="text"
                value={branch.address.city}
                onChange={(e) => handleAddressChange(index, 'city', e.target.value)}
                placeholder="New York"
                className="glass-input"
                required
              />
            </div>
            
            <div className="input-group">
              <label>State *</label>
              <input
                type="text"
                value={branch.address.state}
                onChange={(e) => handleAddressChange(index, 'state', e.target.value)}
                placeholder="NY"
                className="glass-input"
                required
              />
            </div>
            
            <div className="input-group">
              <label>Postal Code *</label>
              <input
                type="text"
                value={branch.address.postal_code}
                onChange={(e) => handleAddressChange(index, 'postal_code', e.target.value)}
                placeholder="10001"
                className="glass-input"
                required
              />
            </div>
            
            <div className="input-group">
              <label>Country *</label>
              <input
                type="text"
                value={branch.address.country}
                onChange={(e) => handleAddressChange(index, 'country', e.target.value)}
                placeholder="United States"
                className="glass-input"
                required
              />
            </div>
          </div>

          {/* Operating Hours */}
          <div className="operating-hours-section">
            <h5>Operating Hours</h5>
            <div className="hours-grid">
              {Object.entries(branch.operating_hours).map(([day, hours]) => (
                <div key={day} className="day-schedule">
                  <label className="day-label">
                    <input
                      type="checkbox"
                      checked={!hours.closed}
                      onChange={(e) => handleOperatingHoursChange(index, day, 'closed', !e.target.checked)}
                    />
                    <span>{day.charAt(0).toUpperCase() + day.slice(1)}</span>
                  </label>
                  {!hours.closed && (
                    <div className="time-inputs">
                      <input
                        type="time"
                        value={hours.open}
                        onChange={(e) => handleOperatingHoursChange(index, day, 'open', e.target.value)}
                        className="time-input"
                      />
                      <span>to</span>
                      <input
                        type="time"
                        value={hours.close}
                        onChange={(e) => handleOperatingHoursChange(index, day, 'close', e.target.value)}
                        className="time-input"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
      
      <button 
        type="button" 
        onClick={() => {
          setFormData(prev => ({
            ...prev,
            branches: [...prev.branches, {
              name: `Branch ${prev.branches.length + 1}`,
              phone_number: '',
              email: '',
              address: {
                street: '',
                city: '',
                state: '',
                country: '',
                postal_code: '',
                latitude: '',
                longitude: ''
              },
              operating_hours: { ...formData.branches[0].operating_hours }
            }]
          }));
        }}
        className="btn-add"
      >
        <Plus size={16} />
        Add Another Branch
      </button>
    </div>
  );

  // Step 3: Cuisine Selection with backend data
  const renderStep3 = () => (
    <div className="onboarding-step">
      <div className="step-header">
        <Utensils className="step-icon" size={24} />
        <h3>Cuisine Selection</h3>
      </div>
      <p className="step-description">Select the cuisines that best represent your restaurant's offerings</p>
      
      <div className="cuisine-grid">
        {cuisines.map(cuisine => (
          <div 
            key={cuisine.cuisine_id}
            className={`cuisine-card ${selectedCuisines.includes(cuisine.cuisine_id) ? 'selected' : ''}`}
            onClick={() => toggleCuisine(cuisine.cuisine_id)}
          >
            <div className="cuisine-icon">
              {cuisine.icon || '🍽️'}
            </div>
            <span className="cuisine-name">{cuisine.name}</span>
            {selectedCuisines.includes(cuisine.cuisine_id) && (
              <div className="selected-check">
                <Check size={16} />
              </div>
            )}
          </div>
        ))}
      </div>
      
      {selectedCuisines.length === 0 && (
        <div className="selection-hint">
          Please select at least one cuisine type
        </div>
      )}
    </div>
  );

  // Step 4: Menu Setup
  const renderStep4 = () => (
    <div className="onboarding-step">
      <div className="step-header">
        <span className="step-icon">📋</span>
        <h3>Menu Setup</h3>
      </div>
      <p className="step-description">Create your menu categories and add items. You can always add more later.</p>
      
      {formData.menu.categories.map((category, categoryIndex) => (
        <div key={categoryIndex} className="category-section glass-card">
          <div className="section-header">
            <div className="input-group">
              <label>Category Name *</label>
              <input
                type="text"
                value={category.name}
                onChange={(e) => handleCategoryChange(categoryIndex, 'name', e.target.value)}
                placeholder="Appetizers, Main Course, Desserts, etc."
                className="glass-input"
                required
              />
            </div>
            {formData.menu.categories.length > 1 && (
              <button 
                type="button" 
                onClick={() => removeCategory(categoryIndex)}
                className="btn-danger"
              >
                <Trash2 size={16} />
                Remove Category
              </button>
            )}
          </div>
          
          <div className="input-group full-width">
            <label>Description</label>
            <input
              type="text"
              value={category.description}
              onChange={(e) => handleCategoryChange(categoryIndex, 'description', e.target.value)}
              placeholder="Describe this category..."
              className="glass-input"
            />
          </div>

          <div className="menu-items-section">
            <h5>Menu Items</h5>
            {category.items.map((item, itemIndex) => (
              <div key={itemIndex} className="menu-item-card">
                <div className="item-header">
                  <h6>Item {itemIndex + 1}</h6>
                  {category.items.length > 1 && (
                    <button 
                      type="button" 
                      onClick={() => removeMenuItem(categoryIndex, itemIndex)}
                      className="btn-danger sm"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
                
                <div className="form-grid compact">
                  <div className="input-group">
                    <label>Item Name *</label>
                    <input
                      type="text"
                      value={item.name}
                      onChange={(e) => handleMenuItemChange(categoryIndex, itemIndex, 'name', e.target.value)}
                      placeholder="Item name"
                      className="glass-input"
                      required
                    />
                  </div>
                  
                  <div className="input-group">
                    <label>Price ($) *</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={item.price}
                      onChange={(e) => handleMenuItemChange(categoryIndex, itemIndex, 'price', e.target.value)}
                      placeholder="0.00"
                      className="glass-input"
                      required
                    />
                  </div>
                  
                  <div className="input-group">
                    <label>Prep Time (min)</label>
                    <input
                      type="number"
                      value={item.preparation_time}
                      onChange={(e) => handleMenuItemChange(categoryIndex, itemIndex, 'preparation_time', parseInt(e.target.value))}
                      placeholder="15"
                      className="glass-input"
                    />
                  </div>
                </div>
                
                <div className="input-group full-width">
                  <label>Description</label>
                  <textarea
                    value={item.description}
                    onChange={(e) => handleMenuItemChange(categoryIndex, itemIndex, 'description', e.target.value)}
                    placeholder="Describe this menu item..."
                    rows="2"
                    className="glass-input"
                  />
                </div>

                <div className="input-group">
                    <label>Item Image</label>
                    <div className="image-upload-container sm">
                        <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleMenuItemImageUpload(categoryIndex, itemIndex, e)}
                        className="image-upload-input"
                        id={`item-image-${categoryIndex}-${itemIndex}`}
                        />
                        <label htmlFor={`item-image-${categoryIndex}-${itemIndex}`} className="image-upload-label">
                        <div className="image-upload-preview sm">
                            {item.image ? (
                            <img 
                                src={URL.createObjectURL(item.image)} 
                                alt="Item preview" 
                                className="image-preview"
                            />
                            ) : (
                            <div className="image-upload-placeholder sm">
                                <Plus size={16} />
                                <span>Add Image</span>
                            </div>
                            )}
                        </div>
                        </label>
                    </div>
                </div>
              </div>
            ))}
            
            <button 
              type="button" 
              onClick={() => addMenuItem(categoryIndex)}
              className="btn-add sm"
            >
              <Plus size={14} />
              Add Menu Item
            </button>
          </div>
        </div>
      ))}
      
      <button 
        type="button" 
        onClick={addCategory}
        className="btn-add"
      >
        <Plus size={16} />
        Add Category
      </button>
    </div>
  );

  // Step 5: Review and Submit
  const renderStep5 = () => (
    <div className="onboarding-step">
      <div className="step-header">
        <span className="step-icon">🎉</span>
        <h3>Review & Complete</h3>
      </div>
      
      <div className="review-sections">
        <div className="review-section glass-card">
          <h4>Restaurant Details</h4>
          <div className="review-grid">
            <div className="review-item">
              <strong>Name:</strong> {formData.restaurant.name}
            </div>
            <div className="review-item">
              <strong>Description:</strong> {formData.restaurant.description || 'Not provided'}
            </div>
            <div className="review-item">
              <strong>Price Range:</strong> {formData.restaurant.price_range}
            </div>
            <div className="review-item">
              <strong>Phone:</strong> {formData.restaurant.phone_number || 'Not provided'}
            </div>
          </div>
        </div>
        
        <div className="review-section glass-card">
          <h4>Branches ({formData.branches.length})</h4>
          {formData.branches.map((branch, index) => (
            <div key={index} className="branch-review">
              <strong>{branch.name}</strong>
              <p>{branch.address.street}, {branch.address.city}, {branch.address.state} {branch.address.postal_code}</p>
            </div>
          ))}
        </div>
        
        <div className="review-section glass-card">
          <h4>Cuisines ({selectedCuisines.length})</h4>
          <div className="cuisines-review">
            {selectedCuisines.map(cuisineId => {
              const cuisine = cuisines.find(c => c.cuisine_id === cuisineId);
              return cuisine ? <span key={cuisineId} className="cuisine-tag">{cuisine.name}</span> : null;
            })}
          </div>
        </div>
        
        <div className="review-section glass-card">
          <h4>Menu Structure</h4>
          <div className="menu-review">
            <p><strong>Categories:</strong> {formData.menu.categories.length}</p>
            <p><strong>Total Items:</strong> {formData.menu.categories.reduce((total, cat) => total + cat.items.length, 0)}</p>
          </div>
        </div>
      </div>
      
      <div className="final-note success">
        <h4>Ready to Launch! 🚀</h4>
        <p>Your restaurant will be set up and ready to accept orders immediately after submission.</p>
        <p><small>You can always add more menu items, staff, and configure settings later.</small></p>
      </div>
    </div>
  );

  const stepTitles = ['Basic Info', 'Locations', 'Cuisines', 'Menu', 'Review'];

  return (
    <div className="onboarding-container">
      <div className="onboarding-glass-card">
        {/* Header */}
        <div className="onboarding-header">
          <h1>
            {isFirstRestaurant ? 'Setup Your First Restaurant' : 'Add New Restaurant'}
          </h1>
          <p>
            {isFirstRestaurant 
              ? 'Complete your restaurant setup to start managing your business' 
              : 'Add another restaurant to your portfolio'
            }
          </p>
          
          {isFirstRestaurant && (
            <div className="first-restaurant-badge">
              🎉 Welcome! Let's get your first restaurant ready for customers
            </div>
          )}
        </div>

        {/* Enhanced Progress Bar - Horizontal on all screens */}
        <div className="progress-container-enhanced">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${((currentStep - 1) / 4) * 100}%` }}
            ></div>
          </div>
          <div className="step-indicators-enhanced">
            {stepTitles.map((title, index) => (
              <div 
                key={index} 
                className={`step-indicator-enhanced ${currentStep > index + 1 ? 'completed' : ''} ${currentStep === index + 1 ? 'active' : ''}`}
                onClick={() => {
                  if (index + 1 < currentStep) {
                    setCurrentStep(index + 1);
                  }
                }}
              >
                <div className="step-number-enhanced">
                  {currentStep > index + 1 ? <Check size={14} /> : index + 1}
                </div>
                <span className="step-title-enhanced">{title}</span>
                {index < stepTitles.length - 1 && (
                  <div className="step-connector"></div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="alert-glass error">
            <div className="alert-icon">⚠️</div>
            <div className="alert-content">
              <div className="alert-title">Setup Failed</div>
              <div className="alert-message">{error}</div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
          {currentStep === 5 && renderStep5()}

          {/* Navigation Buttons */}
          <div className="onboarding-actions">
            <div className="actions-left">
              {currentStep > 1 ? (
                <button 
                  type="button" 
                  onClick={prevStep}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>
              ) : (
                <button 
                  type="button" 
                  onClick={handleCancel}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
              )}
            </div>
            
            <div className="actions-right">
              {currentStep < 5 ? (
                <button 
                  type="button" 
                  onClick={nextStep}
                  className="btn btn-primary"
                  disabled={loading || !validateCurrentStep()}
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              ) : (
                <button 
                  type="submit" 
                  className="btn btn-success"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <div className="button-spinner"></div>
                      Setting Up Restaurant...
                    </>
                  ) : (
                    <>
                      <Check size={16} />
                      Complete Setup
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </form>

        {/* Progress Info */}
        <div className="progress-info">
          <span>Step {currentStep} of 5</span>
          <span>{Math.round((currentStep / 5) * 100)}% Complete</span>
        </div>
      </div>
    </div>
  );
};

export default RestaurantOnboarding;