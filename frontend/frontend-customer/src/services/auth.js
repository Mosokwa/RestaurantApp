import api from "./api";
import csrfService from "./csrf";

export const authService = {
    // Login
    login: async (credentials) => {
        try {

            await csrfService.ensureToken();

            const response = await api.post('/auth/login/', credentials);
            const { tokens, user } = response.data;

            //store tokens and user data
            localStorage.setItem('access_token', tokens.access);
            localStorage.setItem('refresh_token', tokens.refresh);
            localStorage.setItem('user', JSON.stringify(user));

            return response.data;
        }
        catch (error) {
            if (error.response?.status === 403){
                await csrfService.getToken();
                throw new Error('please try logging in again');
            }

            throw error;
        }
    },

    // Register
    register: async (userData) => {
        await csrfService.ensureToken();
        const response = await api.post('/auth/signup/', userData);
        return response.data;
    },

    // Logout 
    logout: async () => {
        try{
            const refreshToken = localStorage.getItem('refresh_token');

            if(refreshToken){
                await csrfService.ensureToken();
                await api.post('/auth/logout/', {refresh: refreshToken});
            }
            
        }
        catch (error) {
            console.warn('Logout API call failed, but proceeding with client cleanup:', error);
        }
        finally{
            //Clear local storage
            authService.clearAuthData();
        }
    },

    // Email verification
    // verifyEmail: async (data) => {
    //     await csrfService.ensureToken();
    //     const response = await api.post('/auth/verify-email/', data);
    //     return response.data;
    // },

    verifyEmailWithCode: async (verificationData) => {
        await csrfService.ensureToken();

        const {email, code} = verificationData
        const response = await api.post('/auth/verify-code/', { email: email, code: code });
        return response.data;
    },
    
    // Get verification status
    // getVerificationStatus: async (email) => {
    //     await csrfService.ensureToken();
    //     const response = await api.get(`/auth/verification-status/?email=${email}`);
    //     return response.data;
    // },

    // Resend verification email
    resendVerification: async (email) => {
        await csrfService.ensureToken();
        const response = await api.post('/auth/verify-email/', {email});
        return response.data;
    },

    clearAuthData: () =>{
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');

        //clear any other auth related storage
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++){
            const cookie = cookies[i];
            const eqPos = cookie.indexOf('=');
            const name = eqPos > -1 ? cookie.slice(0, eqPos).trim() : cookie;

            //clear auth-related cookies
            if(name.includes('session') || name.includes('auth')){
                document.cookie = name + '=; expires=thu, 01 Jan 1970 00:00:00 GMT; path=/';
            }
        }
    },

    // Get current user 
    getCurrentUser: () => {
        const user = localStorage.getItem('user');

        return user ? JSON.parse(user): null;
    },

    //check if user is authenticated
    isAuthenticated: () => {
        return !!localStorage.getItem('access_token');
    },

    // Password reset 
    requestPasswordReset: async (email) => {
        await csrfService.ensureToken();
        const response = await api.post('/auth/password/reset/', {email});
        return response.data;
    },

    //confirm password reset
    confirmPasswordReset: async (data) =>{
        await csrfService.ensureToken();
        const response = await api.post('/auth/password/reset/confirm/', data);

        return response.data;
    },
};