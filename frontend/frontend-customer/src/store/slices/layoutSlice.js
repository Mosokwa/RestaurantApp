// store/slices/layoutSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  sidebarCollapsed: true, // or false based on your default
  sidebarExpanded: false,
};

const layoutSlice = createSlice({
  name: 'layout',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    setSidebarCollapsed: (state, action) => {
      state.sidebarCollapsed = action.payload;
    },
  },
});

export const { toggleSidebar, setSidebarCollapsed } = layoutSlice.actions;
export default layoutSlice.reducer;