/**
 * Authentication service
 */

import api from './api';
import { config } from '../config';

export interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    created_at: string;
}

export interface LoginResponse {
    access_token: string;
    token_type: string;
}

export interface SignupData {
    username: string;
    email: string;
    password: string;
}

class AuthService {
    /**
     * Login with email and password
     */
    async login(email: string, password: string): Promise<LoginResponse> {
        // FastAPI's OAuth2PasswordRequestForm expects form data, not JSON
        const formData = new URLSearchParams();
        formData.append('username', email); // OAuth2 spec uses 'username' field
        formData.append('password', password);

        const response = await api.post<LoginResponse>(
            config.endpoints.login,
            formData,
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            }
        );

        return response.data;
    }

    /**
     * Signup new user
     */
    async signup(data: SignupData): Promise<User> {
        const response = await api.post<User>(config.endpoints.signup, data);
        return response.data;
    }

    /**
     * Smart authentication: Try login first, fallback to signup
     */
    async smartAuth(name: string, email: string, password: string): Promise<{ token: string; user: User }> {
        // Validate required fields only
        if (!email || !email.includes('@')) {
            throw new Error('Please enter a valid email address');
        }
        if (!password || password.length < 6) {
            throw new Error('Password must be at least 6 characters long');
        }

        try {
            // Try to login first
            const loginResponse = await this.login(email, password);
            this.setToken(loginResponse.access_token);

            // Fetch user info
            const user = await this.getCurrentUser();

            return { token: loginResponse.access_token, user };
        } catch (loginError: any) {
            // If login fails with 401 (user doesn't exist or wrong password)
            // Try to create a new account
            if (loginError.response?.status === 401) {
                try {
                    // If name is not provided or too short, use email prefix as username
                    const username = name && name.trim().length >= 3
                        ? name.trim()
                        : email.split('@')[0];

                    const signupData = {
                        username,
                        email: email.trim().toLowerCase(),
                        password,
                    };

                    console.log('Attempting signup with:', {
                        username: signupData.username,
                        email: signupData.email,
                        passwordLength: password.length
                    });

                    const user = await this.signup(signupData);

                    // Now login with the new account
                    const loginResponse = await this.login(email, password);
                    this.setToken(loginResponse.access_token);

                    return { token: loginResponse.access_token, user };
                } catch (signupError: any) {
                    console.error('Signup error details:', signupError.response?.data);

                    // Extract meaningful error message
                    const errorDetail = signupError.response?.data?.detail;
                    if (typeof errorDetail === 'string') {
                        throw new Error(errorDetail);
                    } else if (Array.isArray(errorDetail)) {
                        // FastAPI validation errors are arrays
                        const messages = errorDetail.map((err: any) =>
                            `${err.loc?.join(' → ') || 'Field'}: ${err.msg}`
                        ).join('; ');
                        throw new Error(`Validation failed: ${messages}`);
                    }

                    throw signupError;
                }
            }

            // For other errors, throw the original login error
            throw loginError;
        }
    }

    /**
     * Get current user info using stored token
     */
    async getCurrentUser(): Promise<User> {
        const response = await api.get<User>(config.endpoints.me);
        this.setUser(response.data);
        return response.data;
    }

    /**
     * Logout user
     */
    logout(): void {
        this.removeToken();
        this.removeUser();
    }

    /**
     * Token management
     */
    setToken(token: string): void {
        localStorage.setItem(config.tokenKey, token);
    }

    getToken(): string | null {
        return localStorage.getItem(config.tokenKey);
    }

    removeToken(): void {
        localStorage.removeItem(config.tokenKey);
    }

    /**
     * User data management
     */
    setUser(user: User): void {
        localStorage.setItem(config.userKey, JSON.stringify(user));
    }

    getUser(): User | null {
        const userStr = localStorage.getItem(config.userKey);
        return userStr ? JSON.parse(userStr) : null;
    }

    removeUser(): void {
        localStorage.removeItem(config.userKey);
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated(): boolean {
        return !!this.getToken();
    }
}

export default new AuthService();
