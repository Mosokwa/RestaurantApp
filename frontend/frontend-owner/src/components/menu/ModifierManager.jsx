import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  ChevronDown,
  Search,
  Filter,
  Tag,
  Layers
} from 'lucide-react';
import { 
  fetchModifierGroups,
  createModifierGroup,
  updateModifierGroup,
  deleteModifierGroup,
  createModifier,
  updateModifier,
  deleteModifier,
  fetchMenuItems
} from '../../store/slices/menuSlice';
import './styles/ModifierManager.css';

const ModifierManager = () => {
  const dispatch = useDispatch();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { 
    modifierGroups, 
    menuItems, 
    loading 
  } = useSelector(state => state.menu);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showGroupForm, setShowGroupForm] = useState(false);
  const [showModifierForm, setShowModifierForm] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [editingModifier, setEditingModifier] = useState(null);
  const [expandedGroups, setExpandedGroups] = useState(new Set());

  // Form states
  const [groupForm, setGroupForm] = useState({
    name: '',
    description: '',
    is_required: false,
    min_selections: 0,
    max_selections: 1
  });

  const [modifierForm, setModifierForm] = useState({
    name: '',
    description: '',
    price_modifier: 0,
    is_available: true
  });

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchModifierGroups());
      dispatch(fetchMenuItems({ restaurantId: currentRestaurant.restaurant_id }));
    }
  }, [dispatch, currentRestaurant]);

  // Filter modifier groups
  const filteredGroups = modifierGroups.filter(group => 
    group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateGroup = () => {
    setEditingGroup(null);
    setGroupForm({
      name: '',
      description: '',
      is_required: false,
      min_selections: 0,
      max_selections: 1
    });
    setShowGroupForm(true);
  };

  const handleEditGroup = (group) => {
    setEditingGroup(group);
    setGroupForm({
      name: group.name,
      description: group.description || '',
      is_required: group.is_required,
      min_selections: group.min_selections,
      max_selections: group.max_selections
    });
    setShowGroupForm(true);
  };

  const handleSaveGroup = () => {
    if (!groupForm.name.trim()) {
      alert('Group name is required');
      return;
    }

    if (editingGroup) {
      dispatch(updateModifierGroup({
        id: editingGroup.modifier_id,
        groupData: groupForm
      }));
    } else {
      dispatch(createModifierGroup(groupForm));
    }

    setShowGroupForm(false);
    setEditingGroup(null);
  };

  const handleDeleteGroup = (groupId) => {
    if (window.confirm('Are you sure you want to delete this modifier group? This will remove all associated modifiers.')) {
      dispatch(deleteModifierGroup(groupId));
    }
  };

  const handleCreateModifier = (group) => {
    setSelectedGroup(group);
    setEditingModifier(null);
    setModifierForm({
      name: '',
      description: '',
      price_modifier: 0,
      is_available: true
    });
    setShowModifierForm(true);
  };

  const handleEditModifier = (modifier, group) => {
    setSelectedGroup(group);
    setEditingModifier(modifier);
    setModifierForm({
      name: modifier.name,
      description: modifier.description || '',
      price_modifier: parseFloat(modifier.price_modifier),
      is_available: modifier.is_available
    });
    setShowModifierForm(true);
  };

  const handleSaveModifier = () => {
    if (!modifierForm.name.trim()) {
      alert('Modifier name is required');
      return;
    }

    const modifierData = {
      ...modifierForm,
      modifier_group: selectedGroup.modifier_id
    };

    if (editingModifier) {
      dispatch(updateModifier({
        id: editingModifier.item_modifier_id,
        modifierData: modifierData
      }));
    } else {
      dispatch(createModifier(modifierData));
    }

    setShowModifierForm(false);
    setEditingModifier(null);
    setSelectedGroup(null);
  };

  const handleDeleteModifier = (modifierId) => {
    if (window.confirm('Are you sure you want to delete this modifier?')) {
      dispatch(deleteModifier(modifierId));
    }
  };

  const toggleGroupExpansion = (groupId) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupId)) {
      newExpanded.delete(groupId);
    } else {
      newExpanded.add(groupId);
    }
    setExpandedGroups(newExpanded);
  };

  const getModifiersCount = (group) => {
    return group.modifiers?.length || 0;
  };

  const getMenuItemsCount = (group) => {
    // This would need to be implemented based on your data structure
    return group.menu_items_count || 0;
  };

  if (!currentRestaurant) {
    return (
      <div className="modifier-manager">
        <div className="no-restaurant-glass">
          <Layers size={48} className="icon-muted" />
          <h2>No Restaurant Selected</h2>
          <p>Please select a restaurant to manage modifiers</p>
        </div>
      </div>
    );
  }

  return (
    <div className="modifier-manager">
      {/* Header */}
      <div className="modifier-header">
        <div className="header-content">
          <div className="header-info">
            <Tag className="header-icon" />
            <div>
              <h2>Modifier Management</h2>
              <p>Manage modifier groups and options for your menu items</p>
            </div>
          </div>
          <button 
            className="btn-primary"
            onClick={handleCreateGroup}
          >
            <Plus size={18} />
            Add Modifier Group
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="modifier-filters-glass">
        <div className="filters-content">
          <div className="search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search modifier groups..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="filter-actions">
            <button className="btn-secondary">
              <Filter size={16} />
              Filter
            </button>
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="modifier-stats-glass">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon total">
              <Layers size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Groups</h3>
              <p className="stat-value">{modifierGroups.length}</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon active">
              <Tag size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Modifiers</h3>
              <p className="stat-value">
                {modifierGroups.reduce((total, group) => total + getModifiersCount(group), 0)}
              </p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon items">
              <Tag size={20} />
            </div>
            <div className="stat-content">
              <h3>Active Modifiers</h3>
              <p className="stat-value">
                {modifierGroups.reduce((total, group) => 
                  total + (group.modifiers?.filter(m => m.is_available).length || 0), 0
                )}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modifier Groups List */}
      <div className="modifier-groups-glass">
        <div className="groups-header">
          <h3>Modifier Groups ({filteredGroups.length})</h3>
          <span className="groups-count">
            Showing {filteredGroups.length} of {modifierGroups.length} groups
          </span>
        </div>

        <div className="groups-list">
          {filteredGroups.map(group => (
            <div key={group.modifier_id} className="modifier-group-card">
              <div className="group-header">
                <div className="group-info">
                  <div className="group-main">
                    <h4 className="group-name">{group.name}</h4>
                    {group.description && (
                      <p className="group-description">{group.description}</p>
                    )}
                    <div className="group-meta">
                      <span className="meta-badge">
                        {getModifiersCount(group)} modifiers
                      </span>
                      <span className="meta-badge">
                        {group.min_selections}-{group.max_selections} selections
                      </span>
                      {group.is_required && (
                        <span className="meta-badge required">Required</span>
                      )}
                    </div>
                  </div>
                  <div className="group-actions">
                    <button 
                      className="action-btn"
                      onClick={() => handleCreateModifier(group)}
                    >
                      <Plus size={16} />
                      Add Modifier
                    </button>
                    <button 
                      className="action-btn"
                      onClick={() => handleEditGroup(group)}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="action-btn danger"
                      onClick={() => handleDeleteGroup(group.modifier_id)}
                    >
                      <Trash2 size={16} />
                    </button>
                    <button 
                      className="expand-btn"
                      onClick={() => toggleGroupExpansion(group.modifier_id)}
                    >
                      <ChevronDown 
                        size={16} 
                        className={expandedGroups.has(group.modifier_id) ? 'expanded' : ''}
                      />
                    </button>
                  </div>
                </div>
              </div>

              {/* Modifiers List */}
              {expandedGroups.has(group.modifier_id) && (
                <div className="modifiers-list">
                  {group.modifiers?.length > 0 ? (
                    group.modifiers.map(modifier => (
                      <div key={modifier.item_modifier_id} className="modifier-item">
                        <div className="modifier-info">
                          <div className="modifier-main">
                            <h5 className="modifier-name">{modifier.name}</h5>
                            {modifier.description && (
                              <p className="modifier-description">{modifier.description}</p>
                            )}
                          </div>
                          <div className="modifier-details">
                            <span className="modifier-price">
                              {parseFloat(modifier.price_modifier) > 0 ? `+$${parseFloat(modifier.price_modifier).toFixed(2)}` : 'No extra cost'}
                            </span>
                            {!modifier.is_available && (
                              <span className="availability-badge">Unavailable</span>
                            )}
                          </div>
                        </div>
                        <div className="modifier-actions">
                          <button 
                            className="action-btn"
                            onClick={() => handleEditModifier(modifier, group)}
                          >
                            <Edit size={14} />
                          </button>
                          <button 
                            className="action-btn danger"
                            onClick={() => handleDeleteModifier(modifier.item_modifier_id)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-modifiers">
                      <Tag size={24} />
                      <p>No modifiers in this group</p>
                      <button 
                        className="btn-secondary"
                        onClick={() => handleCreateModifier(group)}
                      >
                        <Plus size={14} />
                        Add First Modifier
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {filteredGroups.length === 0 && (
            <div className="empty-state">
              <Layers size={48} className="empty-icon" />
              <h3>No Modifier Groups Found</h3>
              <p>
                {searchTerm 
                  ? 'Try adjusting your search terms'
                  : 'Create your first modifier group to get started'
                }
              </p>
              {!searchTerm && (
                <button 
                  className="btn-primary"
                  onClick={handleCreateGroup}
                >
                  <Plus size={18} />
                  Create Modifier Group
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modifier Group Form Modal */}
      {showGroupForm && (
        <div className="modal-overlay" onClick={() => setShowGroupForm(false)}>
          <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingGroup ? 'Edit Modifier Group' : 'Create Modifier Group'}</h3>
              <button 
                className="close-btn"
                onClick={() => setShowGroupForm(false)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="form-group">
                <label>Group Name *</label>
                <input
                  type="text"
                  value={groupForm.name}
                  onChange={(e) => setGroupForm({...groupForm, name: e.target.value})}
                  placeholder="e.g., Size Options, Toppings, etc."
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={groupForm.description}
                  onChange={(e) => setGroupForm({...groupForm, description: e.target.value})}
                  placeholder="Optional description for this modifier group"
                  rows="3"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Minimum Selections</label>
                  <input
                    type="number"
                    min="0"
                    value={groupForm.min_selections}
                    onChange={(e) => setGroupForm({...groupForm, min_selections: parseInt(e.target.value) || 0})}
                  />
                </div>

                <div className="form-group">
                  <label>Maximum Selections</label>
                  <input
                    type="number"
                    min="1"
                    value={groupForm.max_selections}
                    onChange={(e) => setGroupForm({...groupForm, max_selections: parseInt(e.target.value) || 1})}
                  />
                </div>
              </div>

              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={groupForm.is_required}
                    onChange={(e) => setGroupForm({...groupForm, is_required: e.target.checked})}
                  />
                  <span className="checkmark"></span>
                  Required selection
                </label>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowGroupForm(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={handleSaveGroup}
              >
                <Save size={16} />
                {editingGroup ? 'Update Group' : 'Create Group'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modifier Form Modal */}
      {showModifierForm && selectedGroup && (
        <div className="modal-overlay" onClick={() => setShowModifierForm(false)}>
          <div className="modal-glass" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingModifier ? 'Edit Modifier' : 'Create Modifier'}</h3>
              <button 
                className="close-btn"
                onClick={() => setShowModifierForm(false)}
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-content">
              <div className="form-group">
                <label>Modifier Name *</label>
                <input
                  type="text"
                  value={modifierForm.name}
                  onChange={(e) => setModifierForm({...modifierForm, name: e.target.value})}
                  placeholder="e.g., Large, Extra Cheese, etc."
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={modifierForm.description}
                  onChange={(e) => setModifierForm({...modifierForm, description: e.target.value})}
                  placeholder="Optional description for this modifier"
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Price Modifier</label>
                <div className="price-input">
                  <span className="currency-symbol">$</span>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={modifierForm.price_modifier}
                    onChange={(e) => setModifierForm({...modifierForm, price_modifier: parseFloat(e.target.value) || 0})}
                    placeholder="0.00"
                  />
                </div>
                <small>Additional cost when this modifier is selected</small>
              </div>

              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={modifierForm.is_available}
                    onChange={(e) => setModifierForm({...modifierForm, is_available: e.target.checked})}
                  />
                  <span className="checkmark"></span>
                  Available for selection
                </label>
              </div>
            </div>

            <div className="modal-actions">
              <button 
                className="btn-secondary"
                onClick={() => setShowModifierForm(false)}
              >
                Cancel
              </button>
              <button 
                className="btn-primary"
                onClick={handleSaveModifier}
              >
                <Save size={16} />
                {editingModifier ? 'Update Modifier' : 'Create Modifier'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModifierManager;