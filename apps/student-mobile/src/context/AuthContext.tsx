import React, { createContext, useContext, useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { UserResponse } from "../types";
import { loginStudent, registerStudent, getCurrentUser } from "../api/auth";
import { saveAuthToken, getAuthToken, clearAuthSession } from "../utils/storage";
import { setUnauthorizedHandler } from "../api/client";

interface AuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserResponse | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: any) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = async () => {
    try {
      await clearAuthSession();
    } finally {
      queryClient.clear();
      setToken(null);
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      await logout();
    }
  };

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
    });

    const initAuth = async () => {
      try {
        const storedToken = await getAuthToken();
        if (storedToken) {
          setToken(storedToken);
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        }
      } catch (err) {
        await clearAuthSession();
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    queryClient.clear();
    const tokenResp = await loginStudent(email, password);
    await saveAuthToken(tokenResp.access_token, tokenResp.user_id);
    setToken(tokenResp.access_token);
    const currentUser = await getCurrentUser();
    setUser(currentUser);
  };

  const register = async (payload: any) => {
    await registerStudent(payload);
    // After register, automatically log in
    await login(payload.email, payload.password);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token && !!user,
        isLoading,
        user,
        token,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
