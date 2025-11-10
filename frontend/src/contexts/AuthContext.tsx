import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/client';
import type { User, LoginRequest, RegisterRequest } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 初期化: トークンがあればユーザー情報を取得
  useEffect(() => {
    const initAuth = async () => {
      console.log('AuthContext: Starting initialization');
      const token = localStorage.getItem('token');
      console.log('AuthContext: Token exists:', !!token);

      if (token) {
        try {
          console.log('AuthContext: Fetching user data...');
          // タイムアウト付きでユーザー情報を取得
          const timeoutPromise = new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), 5000)
          );
          const userData = await Promise.race([authAPI.me(), timeoutPromise]) as any;
          setUser(userData);
          console.log('AuthContext: User loaded successfully');
        } catch (error) {
          console.error('AuthContext: Failed to fetch user:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
      console.log('AuthContext: Initialization complete');
    };

    initAuth();
  }, []);

  const login = async (data: LoginRequest) => {
    console.log('AuthContext: Calling authAPI.login');
    const response = await authAPI.login(data);
    console.log('AuthContext: Login response received:', response);
    localStorage.setItem('token', response.access_token);
    console.log('AuthContext: Token saved to localStorage');
    setUser(response.user);
    console.log('AuthContext: User state updated');
  };

  const register = async (data: RegisterRequest) => {
    const userData = await authAPI.register(data);
    // 登録後は自動的にログイン
    await login({ email: data.email, password: data.password });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
