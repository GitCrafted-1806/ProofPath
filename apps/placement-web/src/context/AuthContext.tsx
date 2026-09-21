"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, formatApiError, User } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  demoLogin: () => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  const clearError = useCallback(() => setError(null), []);

  const verifyToken = useCallback(async (authToken: string) => {
    try {
      const response = await api.get<User>("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (response.data.role !== "PLACEMENT_COORDINATOR") {
        throw new Error(
          "Access denied: You are logged in as a Student. The Placement Cell Web Dashboard is strictly reserved for Placement Coordinators."
        );
      }
      setUser(response.data);
      setToken(authToken);
    } catch (err) {
      localStorage.removeItem("proofpath_coordinator_token");
      setUser(null);
      setToken(null);
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const savedToken = localStorage.getItem("proofpath_coordinator_token");
    if (savedToken) {
      verifyToken(savedToken);
    } else {
      setIsLoading(false);
    }
  }, [verifyToken]);

  // Protect coordinator routes
  useEffect(() => {
    if (!isLoading && !token && pathname !== "/login") {
      router.push("/login");
    }
  }, [isLoading, token, pathname, router]);

  const login = async (email: string, password: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const response = await api.post<{ access_token: string; role: string }>("/api/v1/auth/login", {
        email,
        password,
      });

      if (response.data.role !== "PLACEMENT_COORDINATOR") {
        throw new Error(
          "Access denied: This portal is strictly for Placement Coordinators. Please access the Student Portal for student credentials."
        );
      }

      const authToken = response.data.access_token;
      localStorage.setItem("proofpath_coordinator_token", authToken);
      setToken(authToken);

      const meResp = await api.get<User>("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(meResp.data);

      router.push("/");
    } catch (err) {
      const formatted = formatApiError(err);
      setError(formatted);
      throw new Error(formatted);
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async () => {
    return login("coordinator@college.edu", "Password123!");
  };

  const logout = () => {
    localStorage.removeItem("proofpath_coordinator_token");
    setUser(null);
    setToken(null);
    setError(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        demoLogin,
        logout,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
