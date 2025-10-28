// store/slices/logoutActions.js
import { logout as authLogout } from './authSlice';
import { logoutOwner } from './ownerAuthSlice';

export const performLogout = () => async (dispatch) => {
  try {
    // Dispatch both logout actions to clear all states
    await dispatch(authLogout()).unwrap();
    dispatch(logoutOwner());
  } catch (error) {
    // Even if API call fails, clear local state
    dispatch(authLogout());
    dispatch(logoutOwner());
  }
};