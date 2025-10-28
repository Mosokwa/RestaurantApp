// store/slices/authSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { authService } from '../../services/authService';
import { initializeApp, getCSRFState } from '../../services/api';

// CSRF Token Management - Uses centralized initialization
export const initializeCSRF = createAsyncThunk(
  'auth/initializeCSRF',
  async (_, { rejectWithValue, getState }) => {
    try {
      const state = getState();
      
      // Check if already initialized or initializing
      if (state.auth.csrfInitialized) {
        console.log('✅ CSRF already initialized in Redux state');
        return { success: true, skipped: true };
      }

      console.log('🔄 Starting CSRF initialization via Redux...');
      const token = await initializeApp(); // Use centralized function
      
      console.log('✅ CSRF protection initialized via Redux');
      return { success: true, csrfToken: token };
    } catch (error) {
      console.warn('⚠️ CSRF initialization failed, continuing anyway:', error.message);
      // It's okay if CSRF fails - it will be retried on first API call
      return { success: false, error: error.message };
    }
  }
);

// Owner Authentication
export const ownerLogin = createAsyncThunk(
  'auth/ownerLogin',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.ownerLogin(credentials);
      
      // Ensure email_verified is properly set
      const userData = {
        ...response.user,
        email_verified: response.user.email_verified !== undefined ? response.user.email_verified : false
      };
      
      return {
        ...response,
        user: userData
      };
    } catch (error) {
      const errorData = error.response?.data || { error: error.message };
      
      if (errorData.error?.includes('not verified') || errorData.error?.includes('not activated')) {
        localStorage.setItem('pendingVerificationEmail', credentials.username);
        localStorage.setItem('pendingUserType', 'owner');
        
        return rejectWithValue({
          ...errorData,
          requiresVerification: true,
          email: credentials.username
        });
      }
      
      return rejectWithValue(errorData);
    }
  }
);


export const ownerRegister = createAsyncThunk(
  'auth/ownerRegister',
  async (ownerData, { rejectWithValue }) => {
    try {
      const response = await authService.ownerRegister(ownerData);
      localStorage.setItem('pendingVerificationEmail', ownerData.email);
      localStorage.setItem('pendingUserType', 'owner');
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const loadUserFromToken = createAsyncThunk(
  'auth/loadUserFromToken',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No token found');
      }
      
      // Get fresh user data from backend
      const response = await authService.getCurrentOwner();
      
      console.log('🔍 User data from API:', response);
      
      // FIX: Ensure we have the actual user object, not wrapped response
      const userData = response.data || response;
      
      // FIX: Proper verification logic
      const verifiedStatus = userData.email_verified !== undefined ?userData.email_verified : true; // Assume verified for existing tokens
      
      return {
        ...userData,
        email_verified: verifiedStatus
      };
    } catch (error) {
      console.error('Token load error:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Email Verification Actions
export const verifyEmailCode = createAsyncThunk(
  'auth/verifyEmailCode',
  async ({ email, code }, { rejectWithValue }) => {
    try {
      const response = await authService.verifyEmailCode({ email, code });
      localStorage.removeItem('pendingVerificationEmail');
      localStorage.removeItem('pendingUserType');
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const resendVerificationEmail = createAsyncThunk(
  'auth/resendVerificationEmail',
  async (email, { rejectWithValue }) => {
    try {
      const response = await authService.resendVerificationEmail(email);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Owner-specific Verification Actions
export const ownerVerifyEmail = createAsyncThunk(
  'auth/ownerVerifyEmail',
  async (email, { rejectWithValue }) => {
    try {
      const response = await authService.ownerVerifyEmail(email);
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const ownerVerifyCode = createAsyncThunk(
  'auth/ownerVerifyCode',
  async ({ email, code }, { rejectWithValue }) => {
    try {
      const response = await authService.ownerVerifyCode(email, code);
      localStorage.removeItem('pendingVerificationEmail');
      localStorage.removeItem('pendingUserType');
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// 2FA Actions
export const verify2FACode = createAsyncThunk(
  'auth/verify2FACode',
  async ({ code, rememberDevice, ...loginData }, { rejectWithValue }) => {
    try {
      const response = await authService.login({
        ...loginData,
        totp_token: code
      });
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Social Login Actions
export const socialLogin = createAsyncThunk(
  'auth/socialLogin',
  async ({ provider, token }, { rejectWithValue }) => {
    try {
      let response;
      if (provider === 'google') {
        response = await authService.googleLogin({ token });
      } else if (provider === 'facebook') {
        response = await authService.facebookLogin({ token });
      } else {
        throw new Error(`Unsupported provider: ${provider}`);
      }
      
      if (response.tokens?.access) {
        localStorage.setItem('token', response.tokens.access);
        localStorage.setItem('refreshToken', response.tokens.refresh);
      }
      
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || { error: `${provider} authentication failed` });
    }
  }
);

// General Auth Actions
export const login = createAsyncThunk(
  'auth/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials);
      
      if (response.tokens?.access) {
        localStorage.setItem('token', response.tokens.access);
        localStorage.setItem('refreshToken', response.tokens.refresh);
      }
      
      return response;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue, dispatch }) => {
    try {
      const response = await authService.logout();
      dispatch(clearAuth());
      return response;
    } catch (error) {
      dispatch(clearAuth());
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Initial state
const initialState = {
  // User data
  user: null,
  owner: null,
  restaurants: [],
  staff: [],
  
  // Authentication state
  token: localStorage.getItem('token'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('token'),
  isOwner: false,
  
  // Special states
  requires2FA: false,
  tempLoginData: null,
  
  // Loading states
  loading: false,
  loginLoading: false,
  registerLoading: false,
  staffLoading: false,
  verificationLoading: false,
  
  // CSRF state
  csrfInitialized: false,
  csrfLoading: false,
  csrfError: null,
  
  // Errors
  error: null,
  loginError: null,
  registerError: null,
  staffError: null,
  verificationError: null,
  
  // Success messages
  successMessage: null
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.csrfError = null;
      state.loginError = null;
      state.registerError = null;
      state.staffError = null;
      state.verificationError = null;
      state.successMessage = null;
    },
    
    setLoginError: (state, action) => {
      state.loginError = action.payload;
    },
    
    setRegisterError: (state, action) => {
      state.registerError = action.payload;
    },
    
    clearAuth: (state) => {
      state.user = null;
      state.owner = null;
      state.restaurants = [];
      state.staff = [];
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.isOwner = false;
      state.requires2FA = false;
      state.tempLoginData = null;
      state.error = null;
      state.loginError = null;
      state.registerError = null;
      state.staffError = null;
      state.verificationError = null;
      state.successMessage = null;
      
      // Clear all localStorage items
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('csrfToken');
      localStorage.removeItem('pendingVerificationEmail');
      localStorage.removeItem('pendingUserType');
    },
    
    clearVerificationData: (state) => {
      localStorage.removeItem('pendingVerificationEmail');
      localStorage.removeItem('pendingUserType');
    },
    
    set2FARequired: (state, action) => {
      state.requires2FA = true;
      state.tempLoginData = action.payload;
    },
    
    clear2FA: (state) => {
      state.requires2FA = false;
      state.tempLoginData = null;
    },

    setEmailVerified: (state, action) => {
      if (state.user) {
        state.user.email_verified = action.payload;
      }
      if (state.owner) {
        state.owner.email_verified = action.payload;
      }
    },
    
    // ADD THIS to debug the current state
    debugAuthState: (state) => {
      console.log('🔍 AUTH STATE DEBUG:', {
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        emailVerified: state.user?.email_verified,
        token: !!state.token
      });
    }
  },
  extraReducers: (builder) => {
    builder
      // CSRF Initialization
      .addCase(initializeCSRF.pending, (state) => {
        state.csrfLoading = true;
        state.csrfError = null;
      })
      .addCase(initializeCSRF.fulfilled, (state) => {
        state.csrfLoading = false;
        state.csrfInitialized = true;
      })
      .addCase(initializeCSRF.rejected, (state, action) => {
        state.csrfLoading = false;
        state.csrfError = action.payload;
        state.csrfInitialized = true;
      })
      
      // Owner Login
      .addCase(ownerLogin.pending, (state) => {
        state.loginLoading = true;
        state.loginError = null;
      })
      .addCase(ownerLogin.fulfilled, (state, action) => {
        state.loginLoading = false;
        
        if (action.payload.requires_2fa) {
          state.requires2FA = true;
          state.tempLoginData = action.meta.arg;
          return;
        }

        const userData = {
          ...action.payload.user,
          email_verified: action.payload.user.email_verified !== undefined ? action.payload.user.email_verified : true // Assume verified if not provided
        };
        
        state.user = userData;
        state.owner = userData;
        state.token = action.payload.tokens.access;
        state.refreshToken = action.payload.tokens.refresh;
        state.isAuthenticated = true;
        state.isOwner = true;
        state.successMessage = 'Login successful';
        
        localStorage.setItem('token', action.payload.tokens.access);
        localStorage.setItem('refreshToken', action.payload.tokens.refresh);
        localStorage.removeItem('pendingVerificationEmail');
        localStorage.removeItem('pendingUserType');
        
        console.log('✅ Login successful:', {
          email: userData.email,
        });
      })
      .addCase(ownerLogin.rejected, (state, action) => {
        state.loginLoading = false;
        state.loginError = action.payload;
        
        if (action.payload?.requiresVerification) {
          state.loginError = { 
            error: 'Please verify your email to activate your account.',
            requiresVerification: true 
          };
        }
      })
      
      // Owner Register
      .addCase(ownerRegister.pending, (state) => {
        state.registerLoading = true;
        state.registerError = null;
      })
      .addCase(ownerRegister.fulfilled, (state, action) => {
        state.registerLoading = false;
        state.successMessage = action.payload.message || 'Registration successful! Please check your email for verification.';
      })
      .addCase(ownerRegister.rejected, (state, action) => {
        state.registerLoading = false;
        state.registerError = action.payload;
      })
      
      // Load User from Token
      .addCase(loadUserFromToken.pending, (state) => {
        state.loading = true;
      })
      .addCase(loadUserFromToken.fulfilled, (state, action) => {
        state.loading = false;

        let userData = action.payload;

        // Handle nested data structure if present
        if (userData && userData.data) {
          userData = userData.data;
        }

        // Ensure email_verified is properly set
        const verifiedUserData = {
          ...userData,
          email_verified: userData.email_verified !== undefined ? userData.email_verified : true
        };
  
        console.log('✅ Setting user state from token:', {
          email: verifiedUserData.email,
          email_verified: verifiedUserData.email_verified
        });

        state.user = verifiedUserData;
        state.owner = verifiedUserData;
        state.isAuthenticated = true;
        state.isOwner = verifiedUserData.user_type === 'owner';
        
        console.log('✅ User loaded from token:', userData.email);
      })
      .addCase(loadUserFromToken.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.owner = null;
      })
      
      // Email Verification
      .addCase(verifyEmailCode.pending, (state) => {
        state.verificationLoading = true;
        state.verificationError = null;
      })
      .addCase(verifyEmailCode.fulfilled, (state, action) => {
        state.verificationLoading = false;
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.successMessage = 'Email verified successfully!';
      })
      .addCase(verifyEmailCode.rejected, (state, action) => {
        state.verificationLoading = false;
        state.verificationError = action.payload;
      })
      
      // Resend Verification Email
      .addCase(resendVerificationEmail.pending, (state) => {
        state.verificationLoading = true;
        state.verificationError = null;
      })
      .addCase(resendVerificationEmail.fulfilled, (state, action) => {
        state.verificationLoading = false;
        state.successMessage = 'Verification code sent successfully!';
      })
      .addCase(resendVerificationEmail.rejected, (state, action) => {
        state.verificationLoading = false;
        state.verificationError = action.payload;
      })
      
      // Owner Email Verification
      .addCase(ownerVerifyEmail.pending, (state) => {
        state.verificationLoading = true;
        state.verificationError = null;
      })
      .addCase(ownerVerifyEmail.fulfilled, (state, action) => {
        state.verificationLoading = false;
        state.successMessage = action.payload.message || 'Verification email sent successfully!';
      })
      .addCase(ownerVerifyEmail.rejected, (state, action) => {
        state.verificationLoading = false;
        state.verificationError = action.payload;
      })
      
      // Owner Verify Code
      .addCase(ownerVerifyCode.pending, (state) => {
        state.verificationLoading = true;
        state.verificationError = null;
      })
      .addCase(ownerVerifyCode.fulfilled, (state, action) => {
        state.verificationLoading = false;
        state.successMessage = action.payload.message || 'Email verified successfully! You can now log in.';
      })
      .addCase(ownerVerifyCode.rejected, (state, action) => {
        state.verificationLoading = false;
        state.verificationError = action.payload;
      })
      
      // 2FA Verification
      .addCase(verify2FACode.pending, (state) => {
        state.verificationLoading = true;
        state.verificationError = null;
      })
      .addCase(verify2FACode.fulfilled, (state, action) => {
        state.verificationLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.tokens.access;
        state.refreshToken = action.payload.tokens.refresh;
        state.isAuthenticated = true;
        state.isOwner = action.payload.user?.user_type === 'owner';
        state.requires2FA = false;
        state.tempLoginData = null;
        state.successMessage = 'Login successful';
        
        localStorage.setItem('token', action.payload.tokens.access);
        localStorage.setItem('refreshToken', action.payload.tokens.refresh);
      })
      .addCase(verify2FACode.rejected, (state, action) => {
        state.verificationLoading = false;
        state.verificationError = action.payload;
      })
      
      // Social Login
      .addCase(socialLogin.fulfilled, (state, action) => {
        state.user = action.payload.user;
        state.token = action.payload.tokens?.access;
        state.refreshToken = action.payload.tokens?.refresh;
        state.isAuthenticated = true;
        state.isOwner = action.payload.user?.user_type === 'owner';
        state.successMessage = 'Login successful';
      })
      .addCase(socialLogin.rejected, (state, action) => {
        state.loginError = action.payload;
      });
  }
});

export const { 
  clearError,
  setLoginError,
  setRegisterError, 
  clearAuth, 
  clearVerificationData,
  set2FARequired,
  clear2FA,
  setEmailVerified,
  debugAuthState
} = authSlice.actions;

export default authSlice.reducer;