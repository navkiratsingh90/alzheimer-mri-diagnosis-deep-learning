"use client";

import { useState } from "react";
import React from 'react'
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, Lock, Eye, EyeOff, Loader2, ArrowRight, Shield } from "lucide-react";
import api from "../../../lib/api";
// import api from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      console.log(username , password);
      
      const {data} = await api.post("/auth/register", formData, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      console.log(data);
      
      router.push("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center px-4 py-12 font-['Inter',-apple-system,sans-serif]">
      <div className="w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0EA472] to-[#059669] flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <span className="text-2xl font-bold text-[#0D1B2A] tracking-[-0.5px]">
              Neuro<span className="text-[#0EA472]">Sight</span>
            </span>
          </div>
          <p className="mt-2 text-sm text-[#64748B]">Create your account</p>
        </div>

        {/* Card */}
        <div className="bg-white border border-[#E8EDF2] rounded-2xl p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-[#0D1B2A] mb-1.5">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#94A3B8]">
                  <User size={18} />
                </div>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full pl-10 pr-3 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#0EA472] focus:border-transparent transition"
                  placeholder="Choose a username"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[#0D1B2A] mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#94A3B8]">
                  <Lock size={18} />
                </div>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-10 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#0EA472] focus:border-transparent transition"
                  placeholder="Min 6 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#94A3B8] hover:text-[#0D1B2A] transition"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[#0D1B2A] mb-1.5">
                Confirm Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#94A3B8]">
                  <Shield size={18} />
                </div>
                <input
                  id="confirmPassword"
                  type={showConfirm ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full pl-10 pr-10 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#0EA472] focus:border-transparent transition"
                  placeholder="Re-enter password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#94A3B8] hover:text-[#0D1B2A] transition"
                >
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-[#EF4444] bg-[#FEF2F2] border border-[#FECACA] rounded-xl px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0D1B2A] text-white py-2.5 rounded-xl font-semibold text-sm hover:bg-[#1E3A5F] transition disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : "Create Account"}
              {!loading && <ArrowRight size={18} />}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-[#64748B]">
            Already have an account?{" "}
            <Link href="/login" className="text-[#0EA472] font-semibold hover:underline">
              Sign in
            </Link>
          </div>
        </div>

        {/* Footer note */}
        <p className="mt-6 text-xs text-center text-[#94A3B8]">
          For research purposes only · Not a certified medical device
        </p>
      </div>
    </div>
  );
}