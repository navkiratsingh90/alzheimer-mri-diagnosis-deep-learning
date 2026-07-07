"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Upload,
  FileImage,
  Activity,
  Clock,
  ArrowRight,
  Brain,
  AlertCircle,
  Loader2,
  LogOut,
  MessageSquare,
  FileText,
  Scan,
} from "lucide-react";
import Image from "next/image";
import React from 'react'
import { AuthProvider, useAuth } from "../../lib/authContext";

// ── Types ─────────────────────────────────────────────────────
interface Prediction {
  id: number;
  image_path: string;
  result: string;
  confidence: number;
  timestamp: string;
}

interface User {
  id: number;
  username: string;
  role: string;
}

const MOCK_PREDICTIONS: Prediction[] = [
  {
    id: 101,
    image_path: "/mock/mri-1.jpg", // this will fail, but we have fallback
    result: "Mild",
    confidence: 0.784,
    timestamp: new Date(Date.now() - 3600000 * 2).toISOString(), // 2 hours ago
  },
  {
    id: 102,
    image_path: "/mock/mri-2.jpg",
    result: "NonDemented",
    confidence: 0.923,
    timestamp: new Date(Date.now() - 3600000 * 24 * 3).toISOString(), // 3 days ago
  },
  {
    id: 103,
    image_path: "/mock/mri-3.jpg",
    result: "VeryMild",
    confidence: 0.651,
    timestamp: new Date(Date.now() - 3600000 * 24 * 7).toISOString(), // 7 days ago
  },
  {
    id: 104,
    image_path: "/mock/mri-4.jpg",
    result: "Moderate",
    confidence: 0.892,
    timestamp: new Date(Date.now() - 3600000 * 24 * 14).toISOString(), // 14 days ago
  },
];

// ── Helper to format date ────────────────────────────────────
const formatDate = (dateStr: string) => {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// ── Main Component ───────────────────────────────────────────
export default function DashboardPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── State with mock data as initial values ─────────────────
  const { user } = useAuth();
  // const [user, setUser] = useState<User | null>(MOCK_USER);
  const [predictions, setPredictions] = useState<Prediction[]>(MOCK_PREDICTIONS);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [latestResult, setLatestResult] = useState<Prediction | null>(
    MOCK_PREDICTIONS[0] || null
  );

  // ── Simulate loading (optional) ────────────────────────────
  useEffect(() => {
    // You can uncomment this to simulate a loading state
    // setLoading(true);
    // setTimeout(() => setLoading(false), 800);
  }, []);

  // ── Handle file selection ──────────────────────────────────
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setUploadError(null);
  };

  // ── Handle upload (simulated) ──────────────────────────────
  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadError(null);

    // Simulate upload and add mock prediction
    const newPred: Prediction = {
      id: Date.now(),
      image_path: previewUrl || "",
      result: ["NonDemented", "VeryMild", "Mild", "Moderate"][
        Math.floor(Math.random() * 4)
      ],
      confidence: 0.7 + Math.random() * 0.25,
      timestamp: new Date().toISOString(),
    };

    // Add to list and update latest
    setPredictions((prev) => [newPred, ...prev]);
    setLatestResult(newPred);

    // Reset file input
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";

    setUploading(false);
  };

  // ── Logout (simulated) ──────────────────────────────────────
  const handleLogout = async () => {
    // Simulate logout
    router.push("/login");
  };

  // ── Loading state ──────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#0EA472]" />
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#F8FAFB] font-['Inter',-apple-system,sans-serif]">
      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-[#E8EDF2] px-8 h-16 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0EA472] to-[#059669] flex items-center justify-center">
            <Brain size={16} className="text-white" />
          </div>
          <span className="text-base font-bold text-[#0D1B2A] tracking-[-0.3px]">
            Neuro<span className="text-[#0EA472]">Sight</span>
          </span>
        </div>

        <div className="flex items-center gap-6">
          <span className="text-sm text-[#64748B] hidden sm:inline">
            {user?.username} {user?.role === "admin" && "(Admin)"}
          </span>
          {user?.role === "admin" && (
            <Link
              href="/admin/users"
              className="text-sm text-[#0EA472] font-medium hover:underline"
            >
              Admin Panel
            </Link>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-[#64748B] hover:text-[#0D1B2A] transition"
          >
            <LogOut size={16} />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </nav>

      {/* ── Main content ── */}
      <div className="pt-20 px-8 pb-12 max-w-[1200px] mx-auto">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.5px]">
            Welcome back, {user?.username || "User"} 👋
          </h1>
          <p className="text-[#64748B] text-sm mt-1">
            Upload a new MRI scan or review your recent predictions.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ── Upload & Result Column (2/3) ── */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload Card */}
            <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-[#0D1B2A] mb-4 flex items-center gap-2">
                <Upload size={20} className="text-[#0EA472]" />
                Upload MRI Scan
              </h2>

              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
                  previewUrl
                    ? "border-[#0EA472] bg-[#EDF7F3]"
                    : "border-[#E8EDF2] hover:border-[#0EA472] bg-[#F8FAFB]"
                }`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const file = e.dataTransfer.files?.[0];
                  if (file) {
                    setSelectedFile(file);
                    setPreviewUrl(URL.createObjectURL(file));
                  }
                }}
              >
                {previewUrl ? (
                  <div className="space-y-3">
                    <div className="relative w-48 h-48 mx-auto rounded-lg overflow-hidden border border-[#E8EDF2]">
                      <Image
                        src={previewUrl}
                        alt="Preview"
                        fill
                        className="object-contain"
                        unoptimized
                      />
                    </div>
                    <p className="text-sm font-medium text-[#0D1B2A]">
                      {selectedFile?.name}
                    </p>
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        setPreviewUrl(null);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      className="text-xs text-[#EF4444] hover:underline"
                    >
                      Remove
                    </button>
                  </div>
                ) : (
                  <>
                    <Scan size={48} className="mx-auto text-[#94A3B8] mb-3" />
                    <p className="text-[#64748B] text-sm">
                      Drag & drop an MRI image here, or{" "}
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="text-[#0EA472] font-semibold hover:underline"
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-xs text-[#94A3B8] mt-1">
                      Supports JPG, PNG (max 10MB)
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </>
                )}
              </div>

              {uploadError && (
                <div className="mt-3 text-sm text-[#EF4444] bg-[#FEF2F2] border border-[#FECACA] rounded-xl px-3 py-2 flex items-center gap-2">
                  <AlertCircle size={16} />
                  {uploadError}
                </div>
              )}

              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="mt-4 w-full bg-[#0D1B2A] text-white py-2.5 rounded-xl font-semibold text-sm hover:bg-[#1E3A5F] transition disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <>
                    <Upload size={18} />
                    Analyse Scan
                  </>
                )}
              </button>
            </div>

            {/* Latest Result */}
            {latestResult && (
              <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-[#0D1B2A] mb-4 flex items-center gap-2">
                  <Activity size={20} className="text-[#0EA472]" />
                  Latest Prediction
                </h2>
                <div className="flex flex-col sm:flex-row gap-6 items-start">
                  <div className="relative w-40 h-40 rounded-lg overflow-hidden border border-[#E8EDF2] flex-shrink-0 bg-[#F1F5F9] flex items-center justify-center">
                    {latestResult.image_path ? (
                      <Image
                        src={latestResult.image_path}
                        alt="Latest scan"
                        fill
                        className="object-cover"
                        onError={(e) => {
                          // Fallback if image fails to load
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    ) : (
                      <FileImage size={32} className="text-[#94A3B8]" />
                    )}
                    {/* Fallback icon if image fails */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <FileImage size={32} className="text-[#94A3B8] opacity-50" />
                    </div>
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-[#64748B]">Result:</span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          latestResult.result === "NonDemented"
                            ? "bg-[#D1FAE5] text-[#065F46]"
                            : latestResult.result === "VeryMild"
                            ? "bg-[#DBEAFE] text-[#1E40AF]"
                            : latestResult.result === "Mild"
                            ? "bg-[#FEF3C7] text-[#92400E]"
                            : "bg-[#FEE2E2] text-[#991B1B]"
                        }`}
                      >
                        {latestResult.result}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-[#64748B]">Confidence:</span>
                      <span className="text-sm font-bold text-[#0D1B2A]">
                        {(latestResult.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-[#64748B]">Date:</span>
                      <span className="text-sm text-[#0D1B2A]">
                        {formatDate(latestResult.timestamp)}
                      </span>
                    </div>
                    <Link
                      href={{
                        pathname: "/chat",
                        query: {
                          result: latestResult.result,
                          confidence: latestResult.confidence,
                        },
                      }}
                      className="inline-flex items-center gap-1.5 text-sm text-[#0EA472] font-semibold hover:underline mt-2"
                    >
                      Ask AI about this result
                      <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── Sidebar ── */}
          <div className="space-y-6">
            {/* Quick actions */}
            <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-[#64748B] uppercase tracking-wider mb-4">
                Quick Actions
              </h3>
              <div className="space-y-3">
                <Link
                  href="/chat"
                  className="flex items-center gap-3 p-3 rounded-xl bg-[#F8FAFB] hover:bg-[#EDF7F3] transition group"
                >
                  <MessageSquare size={18} className="text-[#0EA472]" />
                  <span className="text-sm font-medium text-[#0D1B2A] group-hover:text-[#0EA472] transition">
                    AI Clinical Chat
                  </span>
                </Link>
                <Link
                  href="/reports"
                  className="flex items-center gap-3 p-3 rounded-xl bg-[#F8FAFB] hover:bg-[#EDF7F3] transition group"
                >
                  <FileText size={18} className="text-[#0EA472]" />
                  <span className="text-sm font-medium text-[#0D1B2A] group-hover:text-[#0EA472] transition">
                    View All Reports
                  </span>
                </Link>
              </div>
            </div>

            {/* Stats */}
            <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-[#64748B] uppercase tracking-wider mb-4">
                Your Activity
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#64748B]">Total Scans</span>
                  <span className="text-lg font-bold text-[#0D1B2A]">
                    {predictions.length}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#64748B]">Latest Stage</span>
                  <span className="text-sm font-semibold text-[#0D1B2A]">
                    {latestResult ? latestResult.result : "—"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[#64748B]">Last Scan</span>
                  <span className="text-sm text-[#0D1B2A]">
                    {latestResult ? formatDate(latestResult.timestamp) : "No scans"}
                  </span>
                </div>
              </div>
            </div>

            {/* Recent predictions */}
            <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-[#64748B] uppercase tracking-wider mb-4">
                Recent Scans
              </h3>
              {predictions.slice(0, 5).map((pred) => (
                <div
                  key={pred.id}
                  className="flex items-center gap-3 py-2 border-b border-[#F1F5F9] last:border-0"
                >
                  <div className="w-8 h-8 rounded-md bg-[#F1F5F9] flex items-center justify-center">
                    <FileImage size={14} className="text-[#64748B]" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-[#0D1B2A]">
                        {pred.result}
                      </span>
                      <span className="text-[10px] text-[#94A3B8]">
                        {(pred.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-[10px] text-[#94A3B8]">
                      {formatDate(pred.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
              {predictions.length === 0 && (
                <p className="text-sm text-[#94A3B8] text-center py-4">
                  No scans uploaded yet.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}