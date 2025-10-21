import api, { getCSRFToken } from "./api";

export const csrfService = {
    getToken: async () => {
        try {
            const response = await api.get('/auth/csrf/');

            return response.data.csrfToken;
        }
        catch (error){
            console.error('Failed to fetch CSRF token:', error);
            throw error;
        }
    },

    ensureToken: async () => {
        const tokenFromCookie = getCSRFTokenFromCookie();
        if (tokenFromCookie) {
            return tokenFromCookie;
        }

        return await csrfService.getToken();
    },

    setToken: (token) => {
        document.cookie = `csrftoken= ${token}; path=/; samesite=lax`;
    }
};

const getCSRFTokenFromCookie = () => {
    const name = 'csrftoken';
    const cookieValue = document.cookie.split('; ').find(row => row.startsWith(name + '=')) ?.split('=')[1];

    return cookieValue || null;
};

export default csrfService;