import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { menuService } from '../../services/menuService';

// ==================== ASYNC THUNKS ====================

export const fetchCategories = createAsyncThunk(
  'menu/fetchCategories',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await menuService.getCategories(restaurantId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const createCategory = createAsyncThunk(
  'menu/createCategory',
  async (categoryData, { rejectWithValue }) => {
    try {
      const response = await menuService.createCategory(categoryData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const updateCategory = createAsyncThunk(
  'menu/updateCategory',
  async ({ id, categoryData }, { rejectWithValue }) => {
    try {
      const response = await menuService.updateCategory(id, categoryData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const deleteCategory = createAsyncThunk(
  'menu/deleteCategory',
  async (id, { rejectWithValue }) => {
    try {
      await menuService.deleteCategory(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchMenuItems = createAsyncThunk(
  'menu/fetchMenuItems',
  async ({ restaurantId, categoryId = null }, { rejectWithValue }) => {
    try {
      const response = await menuService.getMenuItems(restaurantId, categoryId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const createMenuItem = createAsyncThunk(
  'menu/createMenuItem',
  async (itemData, { rejectWithValue }) => {
    try {
      const response = await menuService.createMenuItem(itemData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const updateMenuItem = createAsyncThunk(
  'menu/updateMenuItem',
  async ({ id, itemData }, { rejectWithValue }) => {
    try {
      const response = await menuService.updateMenuItem(id, itemData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const deleteMenuItem = createAsyncThunk(
  'menu/deleteMenuItem',
  async (id, { rejectWithValue }) => {
    try {
      await menuService.deleteMenuItem(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchMenuAnalytics = createAsyncThunk(
  'menu/fetchMenuAnalytics',
  async ({ restaurantId, days = 30 }, { rejectWithValue }) => {
    try {
      const response = await menuService.getMenuAnalytics(restaurantId, days);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchCategoryAnalytics = createAsyncThunk(
  'menu/fetchCategoryAnalytics',
  async (restaurantId, { rejectWithValue }) => {
    try {
      const response = await menuService.getCategoryAnalytics(restaurantId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchItemAssociations = createAsyncThunk(
  'menu/fetchItemAssociations',
  async (itemId, { rejectWithValue }) => {
    try {
      const response = await menuService.getItemAssociations(itemId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const bulkUpdateMenuItems = createAsyncThunk(
  'menu/bulkUpdateMenuItems',
  async (updates, { rejectWithValue }) => {
    try {
      const response = await menuService.bulkUpdateMenuItems(updates);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const fetchModifierGroups = createAsyncThunk(
  'menu/fetchModifierGroups',
  async (_, { rejectWithValue }) => {
    try {
      const response = await menuService.getModifierGroups();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const createModifierGroup = createAsyncThunk(
  'menu/createModifierGroup',
  async (groupData, { rejectWithValue }) => {
    try {
      const response = await menuService.createModifierGroup(groupData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const updateModifierGroup = createAsyncThunk(
  'menu/updateModifierGroup',
  async ({ id, groupData }, { rejectWithValue }) => {
    try {
      const response = await menuService.updateModifierGroup(id, groupData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const deleteModifierGroup = createAsyncThunk(
  'menu/deleteModifierGroup',
  async (id, { rejectWithValue }) => {
    try {
      await menuService.deleteModifierGroup(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const createModifier = createAsyncThunk(
  'menu/createModifier',
  async (modifierData, { rejectWithValue }) => {
    try {
      const response = await menuService.createModifier(modifierData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const updateModifier = createAsyncThunk(
  'menu/updateModifier',
  async ({ id, modifierData }, { rejectWithValue }) => {
    try {
      const response = await menuService.updateModifier(id, modifierData);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const deleteModifier = createAsyncThunk(
  'menu/deleteModifier',
  async (id, { rejectWithValue }) => {
    try {
      await menuService.deleteModifier(id);
      return id;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);


// ==================== SLICE DEFINITION ====================

const menuSlice = createSlice({
  name: 'menu',
  initialState: {
    // Core menu data
    categories: [],
    menuItems: [],
    
    // Analytics data
    analytics: null,
    categoryAnalytics: null,
    itemAssociations: {},
    
    // UI state
    loading: false,
    error: null,
    successMessage: null,
    
    // Real-time data
    realTimeMetrics: null,
    
    // Selection state
    selectedCategory: null,
    selectedItems: []
  },
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.successMessage = null;
    },
    clearMenuData: (state) => {
      state.categories = [];
      state.menuItems = [];
      state.analytics = null;
      state.categoryAnalytics = null;
      state.itemAssociations = {};
    },
    setSelectedCategory: (state, action) => {
      state.selectedCategory = action.payload;
    },
    setSelectedItems: (state, action) => {
      state.selectedItems = action.payload;
    },
    updateRealTimeMetrics: (state, action) => {
      state.realTimeMetrics = action.payload;
    }
  },
  extraReducers: (builder) => {
    builder
      // Categories
      .addCase(fetchCategories.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCategories.fulfilled, (state, action) => {
        state.loading = false;
        state.categories = action.payload;
      })
      .addCase(fetchCategories.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
      // Menu Items
      .addCase(fetchMenuItems.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchMenuItems.fulfilled, (state, action) => {
        state.loading = false;
        state.menuItems = action.payload;
      })
      .addCase(fetchMenuItems.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
      // Analytics
      .addCase(fetchMenuAnalytics.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMenuAnalytics.fulfilled, (state, action) => {
        state.loading = false;
        state.analytics = action.payload;
      })
      .addCase(fetchMenuAnalytics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      
      .addCase(fetchCategoryAnalytics.fulfilled, (state, action) => {
        state.categoryAnalytics = action.payload;
      })
      
      // Item Associations
      .addCase(fetchItemAssociations.fulfilled, (state, action) => {
        if (action.meta.arg) {
          state.itemAssociations[action.meta.arg] = action.payload;
        }
      })
      
      // Success messages
      .addCase(createCategory.fulfilled, (state) => {
        state.successMessage = 'Category created successfully';
      })
      .addCase(updateCategory.fulfilled, (state) => {
        state.successMessage = 'Category updated successfully';
      })
      .addCase(createMenuItem.fulfilled, (state) => {
        state.successMessage = 'Menu item created successfully';
      })
      .addCase(updateMenuItem.fulfilled, (state) => {
        state.successMessage = 'Menu item updated successfully';
      })
      
      // Error handling for mutations
      .addCase(createCategory.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(updateCategory.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(createMenuItem.rejected, (state, action) => {
        state.error = action.payload;
      })
      .addCase(updateMenuItem.rejected, (state, action) => {
        state.error = action.payload;
      });
  }
});

export const { 
  clearError, 
  clearMenuData, 
  setSelectedCategory, 
  setSelectedItems,
  updateRealTimeMetrics 
} = menuSlice.actions;

export default menuSlice.reducer;