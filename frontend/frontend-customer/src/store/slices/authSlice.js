// store/authSlice.js
import { createSlice } from '@reduxjs/toolkit';
import { authService } from '../../services/auth';

const initialState = {
  user: authService.getCurrentUser(),
  isAuthenticated: authService.isAuthenticated(),
  loading: false,
  error: null,
  requires2FA: false,
  registrationSuccess: false,
  verificationEmailSent: false,
  hasRestaurants: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
    },
    loginSuccess: (state, action) => {
      state.user = action.payload.user;
      state.isAuthenticated = true;
      state.loading = false;
      state.error = null;
      state.requires2FA = false;
      if (action.payload.user && action.payload.user.user_type) {
        state.userType = action.payload.user.user_type;
      }
    },
    logoutSuccess: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.loading = false;
      state.error = null;
      state.requires2FA = false;
    },
    clearError: (state) => {
      state.error = null;
    },
    updateUser: (state, action) => {
      state.user = { ...state.user, ...action.payload };
    },
    setRequires2FA: (state, action) => {
      state.requires2FA = action.payload;
    },
    setRegistrationSuccess: (state, action) => {
      state.registrationSuccess = action.payload;
    },
    setVerificationEmailSent: (state, action) => {
      state.verificationEmailSent = action.payload;
    },
    resetAuthState: (state) => {
      state.loading = false;
      state.error = null;
      state.requires2FA = false;
      state.registrationSuccess = false;
      state.verificationEmailSent = false;
    },
    setHasRestaurants: (state, action) => {
      state.hasRestaurants = action.payload;
    }
  },
});

export const {
  setLoading,
  setError,
  loginSuccess,
  logoutSuccess,
  clearError,
  updateUser,
  setRequires2FA,
  setRegistrationSuccess,
  setVerificationEmailSent,
  resetAuthState,
  setHasRestaurants,
} = authSlice.actions;

// Async actions
export const login = (credentials) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.login(credentials);
    
    if (response.requires_2fa) {
      dispatch(setRequires2FA(true));
    } else {
      dispatch(loginSuccess(response));
    }
    
    return response;
  } catch (error) {
    const errorMessage = error.response?.data?.error || error.message || 'Login failed';
    dispatch(setError(errorMessage));
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};

export const verify2FA = (credentials, token) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.login({
      ...credentials,
      totp_token: token
    });
    
    dispatch(loginSuccess(response));
    dispatch(setRequires2FA(false));
    
    return response;
  } catch (error) {
    const errorMessage = error.response?.data?.error || error.message || '2FA verification failed';
    dispatch(setError(errorMessage));
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};

export const register = (userData) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.register(userData);
    dispatch(setRegistrationSuccess(true));
    
    return response;
  } catch (error) {
    const errorMessage = error.response?.data || 'Registration failed';
    dispatch(setError(errorMessage));
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};

export const logout = () => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    await authService.logout();
    dispatch(logoutSuccess());
  } catch (error) {
    console.error('Logout error:', error);
    dispatch(logoutSuccess());
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};

export const verifyEmail = (verificationData) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.verifyEmail(verificationData);
    return response;
  } catch (error) {
    const errorMessage = error.response?.data || 'Email verification failed';
    dispatch(setError(errorMessage));
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};

export const verifyEmailWithCode = (verificationData) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.verifyEmailWithCode(verificationData);
    
    return response;

  } catch (error) {
    const errorMessage = error.response?.data?.error || error.message || 'Email verification failed';
    
    const serializableError = new Error(errorMessage);
    if (error.response) {
      serializableError.status = error.response.status;
      serializableError.data = error.response.data;
    }

    dispatch(setError(errorMessage));
    throw serializableError;

  } finally {
    dispatch(setLoading(false));
  }
};

export const resendVerification = (email) => async (dispatch) => {
  try {
    dispatch(setLoading(true));
    dispatch(clearError());
    
    const response = await authService.resendVerification(email);
    dispatch(setVerificationEmailSent(true));
    
    return response;
  } catch (error) {
    const errorMessage = error.response?.data?.error || error.message || 'Failed to resend verification email';
    dispatch(setError(errorMessage));
    throw error;
  } finally {
    dispatch(setLoading(false));
  }
};


export default authSlice.reducer;
