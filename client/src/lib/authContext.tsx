"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import api from "./api";
import { User, AuthContextType } from "./types";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // ── Fetch current user – but NOT on public pages ──
  useEffect(() => {
    console.log(pathname);
    
    const publicPaths = ["/login", "/register"];
    if (publicPaths.includes(pathname)) {
      setLoading(false);
      return;
    }

    const fetchUser = async () => {
      setLoading(true);
      try {
        const res = await api.get("/auth/me");
        console.log(res.data);
        
        setUser(res.data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, [pathname]);

  // ── Login ──
  const login = async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      await api.post("/auth/login", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      const res = await api.get("/auth/me");
      setUser(res.data);
      router.replace("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  };

  // ── Register ──
  const register = async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      await api.post("/auth/register", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      router.replace("/login");
    } catch (error) {
      console.error("Registration error:", error);
      throw error;
    }
  };

  // ── Logout ──
  const logout = async () => {
    try {
      await api.get("/auth/logout");
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      setUser(null);
      // router.replace("/login");
    }
  };

  const isAdmin = user?.role === "admin";

  // ── Redirect unauthenticated users from protected pages ──
  useEffect(() => {
    if (loading) return;
    const publicPaths = ["/login", "/register", "/"];
    if (!user && !publicPaths.includes(pathname)) {
      router.replace("/login");
    }
  }, [loading, user, router, pathname]);

  // ── Loading spinner ──
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0EA472]"></div>
      </div>
    );
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, isAdmin }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}