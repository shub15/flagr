/**
 * Application configuration
 */

export const config = {
    // Backend API base URL
    apiBaseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    googleClientId: import.meta.env.VITE_GOOGLE_CLIENT_ID || '',
    googleApiKey: import.meta.env.VITE_GOOGLE_API_KEY || '',

    // Local storage keys
    tokenKey: 'auth_token',
    userKey: 'auth_user',

    // API endpoints
    endpoints: {
        login: '/api/auth/login',
        signup: '/api/auth/signup',
        me: '/api/auth/me',
    },
} as const;
