import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  fetchModifierGroups,
  createModifierGroup,
  updateModifierGroup,
  deleteModifierGroup,
  createModifier,
  updateModifier,
  deleteModifier
} from '../store/slices/menuSlice';
import { 
  Plus, 
  Tags, 
  Filter,
  Search,
  DollarSign,
  Settings,
  Users,
  Edit,
  Trash2,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import CreateModifierGroupModal from '../components/menu/CreateModifierGroupModal';
import CreateModifierModal from '../components/menu/CreateModifierModal';
import './styles/ModifiersPage.css';

const ModifiersPage = () => {
  const dispatch = useDispatch();
  const { currentRestaurant } = useSelector(state => state.ownerAuth);
  const { 
    modifierGroups,
    loading 
  } = useSelector(state => state.menu);
  
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showModifierModal, setShowModifierModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [editingModifier, setEditingModifier] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedGroups, setExpandedGroups] = useState(new Set());

  useEffect(() => {
    if (currentRestaurant) {
      dispatch(fetchModifierGroups());
    }
  }, [dispatch, currentRestaurant]);

  const handleCreateGroup = (groupData) => {
    dispatch(createModifierGroup(groupData)).then(() => {
      setShowGroupModal(false);
    });
  };

  const handleUpdateGroup = (groupData) => {
    dispatch(updateModifierGroup({
      id: editingGroup.modifier_id,
      groupData
    })).then(() => {
      setShowGroupModal(false);
      setEditingGroup(null);
    });
  };

  const handleDeleteGroup = (groupId) => {
    if (window.confirm('Are you sure you want to delete this modifier group? This will remove all modifiers in this group.')) {
      dispatch(deleteModifierGroup(groupId));
    }
  };

  const handleCreateModifier = (modifierData) => {
    dispatch(createModifier({
      ...modifierData,
      modifier_group: selectedGroup.modifier_id
    })).then(() => {
      setShowModifierModal(false);
      setSelectedGroup(null);
    });
  };

  const handleUpdateModifier = (modifierData) => {
    dispatch(updateModifier({
      id: editingModifier.item_modifier_id,
      modifierData
    })).then(() => {
      setShowModifierModal(false);
      setEditingModifier(null);
      setSelectedGroup(null);
    });
  };

  const handleDeleteModifier = (modifierId) => {
    if (window.confirm('Are you sure you want to delete this modifier?')) {
      dispatch(deleteModifier(modifierId));
    }
  };

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(groupId)) {
        newExpanded.delete(groupId);
      } else {
        newExpanded.add(groupId);
      }
      return newExpanded;
    });
  };

  const filteredGroups = modifierGroups.filter(group =>
    group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    group.modifiers?.some(modifier => 
      modifier.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const getModifierStats = (group) => {
    const totalModifiers = group.modifiers?.length || 0;
    const availableModifiers = group.modifiers?.filter(m => m.is_available).length || 0;
    const averagePrice = group.modifiers?.reduce((sum, m) => sum + parseFloat(m.price_modifier), 0) / totalModifiers || 0;
    
    return { totalModifiers, availableModifiers, averagePrice };
  };

  if (!currentRestaurant) {
    return (
      <div className="modifiers-container">
        <div className="no-restaurant-glass">
          <Tags size={48} className="icon-muted" />
          <h2>No Restaurant Selected</h2>
          <p>Please select a restaurant to manage modifiers</p>
        </div>
      </div>
    );
  }

  return (
    <div className="modifiers-container">
      {/* Header */}
      <div className="modifiers-header-glass">
        <div className="header-content">
          <div className="header-title">
            <Tags className="header-icon" />
            <div>
              <h1>Menu Modifiers</h1>
              <p>Manage modifiers and customization options</p>
            </div>
          </div>
          
          <div className="header-actions">
            <button 
              className="btn-secondary"
              onClick={() => setShowModifierModal(true)}
            >
              <Plus size={18} />
              Add Modifier
            </button>
            <button 
              className="btn-primary"
              onClick={() => setShowGroupModal(true)}
            >
              <Plus size={18} />
              Add Group
            </button>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="search-glass">
        <div className="search-content">
          <div className="search-box">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search modifier groups or modifiers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="modifiers-stats-glass">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon groups">
              <Tags size={20} />
            </div>
            <div className="stat-content">
              <h3>Modifier Groups</h3>
              <p className="stat-value">{modifierGroups.length}</p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon modifiers">
              <Settings size={20} />
            </div>
            <div className="stat-content">
              <h3>Total Modifiers</h3>
              <p className="stat-value">
                {modifierGroups.reduce((sum, group) => 
                  sum + (group.modifiers?.length || 0), 0
                )}
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon required">
              <Users size={20} />
            </div>
            <div className="stat-content">
              <h3>Required Groups</h3>
              <p className="stat-value">
                {modifierGroups.filter(group => group.is_required).length}
              </p>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon price">
              <DollarSign size={20} />
            </div>
            <div className="stat-content">
              <h3>Avg Price Modifier</h3>
              <p className="stat-value">
                $
                {modifierGroups.length ? 
                  (modifierGroups.reduce((sum, group) => {
                    const groupModifiers = group.modifiers || [];
                    const groupAvg = groupModifiers.reduce((s, m) => s + parseFloat(m.price_modifier), 0) / groupModifiers.length || 0;
                    return sum + groupAvg;
                  }, 0) / modifierGroups.length).toFixed(2)
                  : '0.00'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modifier Groups List */}
      <div className="modifiers-list-glass">
        <div className="list-header">
          <h3>Modifier Groups</h3>
          <span className="groups-count">
            {filteredGroups.length} groups
          </span>
        </div>
        
        <div className="groups-list">
          {filteredGroups.map(group => {
            const stats = getModifierStats(group);
            const isExpanded = expandedGroups.has(group.modifier_id);
            
            return (
              <div key={group.modifier_id} className="group-card">
                <div className="group-header">
                  <button 
                    className="expand-btn"
                    onClick={() => toggleGroup(group.modifier_id)}
                  >
                    {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  </button>
                  
                  <div className="group-info">
                    <h4 className="group-name">{group.name}</h4>
                    <p className="group-description">{group.description}</p>
                    <div className="group-meta">
                      <span className={`requirement-badge ${group.is_required ? 'required' : 'optional'}`}>
                        {group.is_required ? 'Required' : 'Optional'}
                      </span>
                      <span className="selections-info">
                        {group.min_selections}-{group.max_selections} selections
                      </span>
                      <span className="modifiers-count">
                        {stats.totalModifiers} modifiers
                      </span>
                    </div>
                  </div>
                  
                  <div className="group-actions">
                    <button 
                      className="action-btn"
                      onClick={() => {
                        setSelectedGroup(group);
                        setShowModifierModal(true);
                      }}
                    >
                      <Plus size={16} />
                      Add Modifier
                    </button>
                    <button 
                      className="action-btn"
                      onClick={() => {
                        setEditingGroup(group);
                        setShowGroupModal(true);
                      }}
                    >
                      <Edit size={16} />
                    </button>
                    <button 
                      className="action-btn danger"
                      onClick={() => handleDeleteGroup(group.modifier_id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                {isExpanded && (
                  <div className="modifiers-list">
                    {group.modifiers?.map(modifier => (
                      <div key={modifier.item_modifier_id} className="modifier-item">
                        <div className="modifier-info">
                          <h5 className="modifier-name">{modifier.name}</h5>
                          <p className="modifier-description">{modifier.description}</p>
                        </div>
                        
                        <div className="modifier-details">
                          <span className={`availability-badge ${modifier.is_available ? 'available' : 'unavailable'}`}>
                            {modifier.is_available ? 'Available' : 'Unavailable'}
                          </span>
                          <span className="modifier-price">
                            {parseFloat(modifier.price_modifier) > 0 ? '+' : ''}
                            ${parseFloat(modifier.price_modifier).toFixed(2)}
                          </span>
                        </div>
                        
                        <div className="modifier-actions">
                          <button 
                            className="action-btn small"
                            onClick={() => {
                              setEditingModifier(modifier);
                              setSelectedGroup(group);
                              setShowModifierModal(true);
                            }}
                          >
                            <Edit size={14} />
                          </button>
                          <button 
                            className="action-btn small danger"
                            onClick={() => handleDeleteModifier(modifier.item_modifier_id)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                    ))}
                    
                    {(!group.modifiers || group.modifiers.length === 0) && (
                      <div className="empty-modifiers">
                        <p>No modifiers in this group yet</p>
                        <button 
                          className="btn-text"
                          onClick={() => {
                            setSelectedGroup(group);
                            setShowModifierModal(true);
                          }}
                        >
                          <Plus size={14} />
                          Add First Modifier
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {filteredGroups.length === 0 && (
          <div className="empty-state">
            <Tags size={48} className="empty-icon" />
            <h3>No Modifier Groups Found</h3>
            <p>
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Create your first modifier group to get started'
              }
            </p>
            {searchTerm ? (
              <button 
                className="btn-secondary"
                onClick={() => setSearchTerm('')}
              >
                Clear Search
              </button>
            ) : (
              <button 
                className="btn-primary"
                onClick={() => setShowGroupModal(true)}
              >
                <Plus size={18} />
                Create Group
              </button>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showGroupModal && (
        <CreateModifierGroupModal
          group={editingGroup}
          onSubmit={editingGroup ? handleUpdateGroup : handleCreateGroup}
          onClose={() => {
            setShowGroupModal(false);
            setEditingGroup(null);
          }}
        />
      )}

      {showModifierModal && (
        <CreateModifierModal
          modifier={editingModifier}
          groups={modifierGroups}
          selectedGroup={selectedGroup}
          onSubmit={editingModifier ? handleUpdateModifier : handleCreateModifier}
          onClose={() => {
            setShowModifierModal(false);
            setEditingModifier(null);
            setSelectedGroup(null);
          }}
        />
      )}
    </div>
  );
};

export default ModifiersPage;