/**
 * Authentication Context
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import authService, { type User } from '../services/authService';

interface AuthContextType {
    user: User | null;
    loading: boolean;
    login: (name: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Validate token and load user on mount
    useEffect(() => {
        const initAuth = async () => {
            const token = authService.getToken();

            if (token) {
                try {
                    // Validate token by fetching current user
                    const currentUser = await authService.getCurrentUser();
                    setUser(currentUser);
                } catch (error) {
                    // Token is invalid, clear it
                    authService.logout();
                    setUser(null);
                }
            }

            setLoading(false);
        };

        initAuth();
    }, []);

    const login = async (name: string, email: string, password: string) => {
        setLoading(true);
        try {
            const { user: loggedInUser } = await authService.smartAuth(name, email, password);
            setUser(loggedInUser);
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
    };

    const value: AuthContextType = {
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
