import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";

import { api, setToken, User } from "../lib/api";

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

type RegisterPayload = {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  account_type: "admin" | "dev" | "client";
  admin_signup_code?: string;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    const current = localStorage.getItem("apex_host_token");
    if (!current) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api<User>("/auth/me"));
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    const token = await api<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    setToken(token.access_token);
    await refreshUser();
  };

  const register = async (payload: RegisterPayload) => {
    const token = await api<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    setToken(token.access_token);
    await refreshUser();
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({ user, loading, login, register, logout, refreshUser }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="grid min-h-screen place-items-center bg-apex-bg text-apex-muted">Carregando Apex Host...</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
