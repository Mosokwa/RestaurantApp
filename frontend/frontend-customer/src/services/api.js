import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

//helper function for obtaining the csrf token from the cookies
export const getCSRFToken = () => {
    const name = 'csrftoken';
    const cookiesVlaue = document.cookie.split('; ').find(row => row.startsWith(name + '=')) ?.split('=')[1];
    return cookiesVlaue || '';
};

//helper function to ensure that we have a csrf token
export const ensureCSRFToken = async () => {
    let csrfToken = getCSRFToken();

    if(!csrfToken){
        try{
            const response = await axios.get(`${import.meta.env.VITE_BASE_URL}/api/auth/csrf/`, {
                withCredentials: true
            });
            csrfToken =response.data.csrfToken;
        }
        catch (error) {
            console.warn('Failed to fetch CSRF token:', error);
        }
    }

    return csrfToken;
};

// creating an axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    withCredentials: true, //important for cookies and sessions 
    headers:{
        'Content-Type': 'application/json',
    },
});

//the Request interceptor to add auth token
api.interceptors.request.use(
    async (config) => {

        if (config.method !== 'get'){
            const csrfToken = await ensureCSRFToken();

            if (csrfToken) {
                config.headers['X-CSRFToken'] = csrfToken;
            }
        }

        const authToken = localStorage.getItem('access_token');
        if (authToken){
            config.headers.Authorization = `Bearer ${authToken}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
)

//Response interceptor to handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error)=> {
        const originalRequest = error.config;

        //handling expired CSRF tokens 
        if(error.response?.status === 403 && !originalRequest._retry){
            originalRequest._retry = true;

            try {
                const newCSRFToken = await ensureCSRFToken();

                originalRequest.headers['X-CSRFToken'] = newCSRFToken;
                return api(originalRequest);
            }
            catch (csrfError) {
                console.error('CSRF token refresh failed:', csrfError);

                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }

        //Jwt refresh 
        if (error.response?.status === 401 && !originalRequest._retry){
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken){
                    const response = await axios.post(
                        `${import.meta.env.VITE_BASE_URL}/api/auth/token/refresh/`, {refresh: refreshToken}
                    );

                    const { access } = response.data;
                    localStorage.setItem('access_token', access);

                    originalRequest.headers.Authorization = `Bearer ${access}`;

                    return api(originalRequest);

                } 
            }
            catch (refreshError) {
                    //refresh token failed, logout user
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('user');

                    window.location.href = '/login';

                    return Promise.reject(refreshError);
                }
        }
        return Promise.reject(error);
    }
);

// Helper function to extract pagination info from response
export const parsePaginatedResponse = (response) => {
    if (response.data && response.data.results !== undefined) {
        return {
            items: response.data.results,
            pagination: {
                count: response.data.count,
                next: response.data.next,
                previous: response.data.previous,
            }
        };
    }
    return {
        items: response.data,
        pagination: null
    };
};

// Helper function to build pagination parameters
export const buildPaginationParams = (page = 1, pageSize = 20) => {
    return {
        page: page,
        page_size: pageSize
    };
};

// Helper function to extract page number from URL
export const getPageNumberFromUrl = (url) => {
    if (!url) return null;
    try {
        const urlObj = new URL(url);
        return parseInt(urlObj.searchParams.get('page')) || 1;
    } catch {
        return null;
    }
};

export default api;