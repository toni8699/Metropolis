import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiGet, apiPatch, apiPost } from "../utils/api";

const AuthContext = createContext(null);

const AUTH_USER_KEY = "authUser";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("accessToken"));
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem(AUTH_USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (user) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(AUTH_USER_KEY);
    }
  }, [user]);

  useEffect(() => {
    if (token) {
      refreshMe().catch(() => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem(AUTH_USER_KEY);
        setToken(null);
        setUser(null);
      });
    }
  }, [token]);  

  const refreshMe = async () => {
    if (!localStorage.getItem("accessToken")) return null;
    const result = await apiGet("/api/me", true);
    const nextUser = result?.user || null;
    setUser(nextUser);
    return nextUser;
  };

  const login = async (email, password) => {
    const result = await apiPost("/api/auth/login", { email, password });
    const nextToken = result?.token;
    const nextUser = result?.user;
    if (!nextToken || !nextUser) {
      throw new Error("Invalid login response.");
    }
    localStorage.setItem("accessToken", nextToken);
    setToken(nextToken);
    setUser(nextUser);
    await refreshMe();
    return result;
  };

  const register = async (data) => {
    const result = await apiPost("/api/auth/register", {
      email: data.email,
      password: data.password,
      fullName: data.fullName,
      role: data.role || "user",
    });
    const nextToken = result?.token;
    const nextUser = result?.user;
    if (!nextToken || !nextUser) {
      throw new Error("Invalid register response.");
    }
    localStorage.setItem("accessToken", nextToken);
    setToken(nextToken);
    setUser(nextUser);
    await refreshMe();
    return result;
  };

  const updateProfile = async (data) => {
    const result = await apiPatch("/api/me", data, true);
    const nextUser = result?.user;
    if (!nextUser) {
      throw new Error("Invalid profile response.");
    }
    setUser(nextUser);
    return nextUser;
  };

  const googleLogin = async (idToken) => {
    const result = await apiPost("/api/auth/google", { idToken });
    const nextToken = result?.token;
    const nextUser = result?.user;
    if (!nextToken || !nextUser) {
      throw new Error("Invalid Google login response.");
    }
    localStorage.setItem("accessToken", nextToken);
    setToken(nextToken);
    setUser(nextUser);
    await refreshMe();
    return result;
  };

  const logout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem(AUTH_USER_KEY);
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({
      user,
      token,
      role: user?.role || "user",
      isAdmin: Boolean(user?.isAdmin),
      hasListings: Boolean(user?.hasListings),
      isAuthenticated: Boolean(token && user),
      refreshMe,
      login,
      register,
      updateProfile,
      googleLogin,
      logout,
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
