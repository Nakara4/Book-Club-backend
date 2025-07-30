// src/context/AuthContext.js
// This file shows how to properly manage user authentication state in React

import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api'; // Your API service

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check for existing token on app load
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        try {
          // Set the token in API headers
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Fetch user profile to get current user data including admin status
          const response = await api.get('/api/auth/profile/');
          setUser(response.data);
        } catch (error) {
          console.error('Token validation failed:', error);
          // Token is invalid, remove it
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          delete api.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await api.post('/api/auth/login/', { email, password });
      const { user: userData, tokens } = response.data;

      // Store tokens
      localStorage.setItem('accessToken', tokens.access);
      localStorage.setItem('refreshToken', tokens.refresh);

      // Set authorization header for future requests
      api.defaults.headers.common['Authorization'] = `Bearer ${tokens.access}`;

      // Store the COMPLETE user object (including is_staff, is_superuser)
      setUser(userData);

      console.log('Login successful. User is staff:', userData.is_staff);
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        await api.post('/api/auth/logout/', { refresh: refreshToken });
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear all auth data regardless of API call success
      setUser(null);
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      delete api.defaults.headers.common['Authorization'];
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  // Computed values
  const isAuthenticated = !!user;
  const isAdmin = user?.is_staff || user?.is_superuser;
  const isSuperUser = user?.is_superuser;

  const value = {
    user,
    setUser,
    login,
    logout,
    updateUser,
    isAuthenticated,
    isAdmin,
    isSuperUser,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
