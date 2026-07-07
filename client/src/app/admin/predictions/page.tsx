"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  FileText,
  ArrowLeft,
  LogOut,
  Shield,
  Trash2,
  Loader2,
  AlertCircle,
  Search,
  ChevronDown,
  ChevronUp,
  Clock,
  Eye,
  Users,
  BarChart3,
} from "lucide-react";
import React from 'react'
import api from "../../../lib/api";

// ── Types ─────────────────────────────────────────────────────
interface Prediction {
  id: number;
  user_id: number;
  username: string; // populated from backend (nested)
  image_path: string;
  result: string;
  confidence: number;
  timestamp: string;
}

// ── Helper functions ─────────────────────────────────────────
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

const getStageBadge = (result: string) => {
  const map: Record<string, { bg: string; text: string }> = {
    NonDemented: { bg: "bg-[#D1FAE5]", text: "text-[#065F46]" },
    VeryMild: { bg: "bg-[#DBEAFE]", text: "text-[#1E40AF]" },
    Mild: { bg: "bg-[#FEF3C7]", text: "text-[#92400E]" },
    Moderate: { bg: "bg-[#FEE2E2]", text: "text-[#991B1B]" },
  };
  return map[result] || { bg: "bg-[#F1F5F9]", text: "text-[#64748B]" };
};

// ── Main Component ──────────────────────────────────────────
export default function AdminPredictionsPage() {
  const router = useRouter();
  const [predictions, setPredictions] = useState<Prediction[]>([{
	id: 1,
  user_id: 2,
  username: "navkirat",// populated from backend (nested)
  image_path: "img.png",
  result: "Mild Demented",
  confidence: 0.5,
  timestamp: "26 aug, 2026",
  }]);
  const [filtered, setFiltered] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<{ username: string; role: string } | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<"timestamp" | "result" | "confidence" | "username">(
    "timestamp"
  );
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // ── Fetch data ─────────────────────────────────────────────
  useEffect(() => {
    const fetchData = async () => {
    //   try {
    //     // Verify admin
    //     const meRes = await api.get("/auth/me");
    //     const user = meRes.data;
    //     setCurrentUser(user);
    //     if (user.role !== "admin") {
    //       router.push("/dashboard");
    //       return;
    //     }

    //     // Fetch all predictions (admin endpoint)
    //     const predRes = await api.get("/admin/predictions");
    //     // Assuming the backend returns array with username attached
    //     // or we can fetch users separately and join, but simpler: backend includes username
    //     setPredictions(predRes.data);
    //     setFiltered(predRes.data);
    //   } catch (err) {
    //     setError("Failed to load predictions. Please try again.");
    //   } finally {
    //     setLoading(false);
    //   }
    };
    fetchData();
  }, [router]);

  // ── Search & sort ──────────────────────────────────────────
  useEffect(() => {
    const term = searchTerm.toLowerCase();
    let list = predictions.filter(
      (p) =>
        p.result.toLowerCase().includes(term) ||
        (p.username && p.username.toLowerCase().includes(term)) ||
        formatDate(p.timestamp).toLowerCase().includes(term) ||
        (p.confidence * 100).toFixed(1).includes(term)
    );
    // Sort
    list.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];
      if (sortField === "timestamp") {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      } else if (sortField === "username") {
        aVal = a.username || "";
        bVal = b.username || "";
      }
      if (sortDirection === "asc") return aVal > bVal ? 1 : -1;
      else return aVal < bVal ? 1 : -1;
    });
    setFiltered(list);
  }, [searchTerm, sortField, sortDirection, predictions]);

  // ── Delete prediction ──────────────────────────────────────
  const deletePrediction = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this prediction?")) return;
    setActionLoading(id);
    setError(null);
    // try {
    //   await api.delete(`/admin/predictions/${id}`);
    //   setPredictions((prev) => prev.filter((p) => p.id !== id));
    //   // Filtered will update via useEffect
    // } catch (err: any) {
    //   setError(err.response?.data?.detail || "Failed to delete prediction.");
    // } finally {
    //   setActionLoading(null);
    // }
  };

  // ── Logout ──────────────────────────────────────────────────
  const handleLogout = async () => {
    // await api.get("/auth/logout");
    // router.push("/login");
  };

  // ── Loading ─────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#0EA472]" />
      </div>
    );
  }

  // ── Stats ──────────────────────────────────────────────────
  const stageCounts = predictions.reduce((acc, p) => {
    acc[p.result] = (acc[p.result] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // ── Render ──────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#F8FAFB] font-['Inter',-apple-system,sans-serif]">
      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-[#E8EDF2] px-8 h-16 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-sm text-[#64748B] hover:text-[#0D1B2A] transition"
          >
            <ArrowLeft size={16} />
            <span className="hidden sm:inline">Dashboard</span>
          </Link>
          <div className="w-px h-6 bg-[#E8EDF2]" />
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0EA472] to-[#059669] flex items-center justify-center">
              <FileText size={16} className="text-white" />
            </div>
            <span className="text-base font-bold text-[#0D1B2A] tracking-[-0.3px]">
              Neuro<span className="text-[#0EA472]">Sight</span>
              <span className="ml-1 text-sm font-normal text-[#64748B]">
                Admin · Predictions
              </span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-[#0D1B2A] font-medium hidden sm:inline">
            {currentUser?.username} (Admin)
          </span>
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
      <div className="pt-20 px-8 pb-12 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h1 className="text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.5px]">
              All Predictions
            </h1>
            <p className="text-sm text-[#64748B] mt-1">
              {predictions.length} total scan{predictions.length !== 1 ? "s" : ""} across all users
            </p>
          </div>
          <div className="flex gap-3 mt-4 sm:mt-0">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-[#EDF7F3] text-[#0EA472] rounded-full">
              <Shield size={14} />
              Admin Access
            </span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 text-sm text-[#EF4444] bg-[#FEF2F2] border border-[#FECACA] rounded-xl px-4 py-2.5 flex items-center gap-2">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {Object.entries(stageCounts).map(([stage, count]) => {
            const { bg, text } = getStageBadge(stage);
            return (
              <div
                key={stage}
                className={`${bg} border border-[#E8EDF2] rounded-xl p-3 text-center`}
              >
                <span className={`text-xs font-medium ${text}`}>{stage}</span>
                <p className="text-xl font-bold text-[#0D1B2A] mt-1">{count}</p>
              </div>
            );
          })}
        </div>

        {/* Search & sort */}
        <div className="bg-white border border-[#E8EDF2] rounded-2xl p-4 shadow-sm mb-6 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
            <input
              type="text"
              placeholder="Search by user, stage, date, or confidence..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#0EA472] focus:border-transparent transition"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value as any)}
              className="px-3 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] text-sm focus:outline-none focus:ring-2 focus:ring-[#0EA472]"
            >
              <option value="timestamp">Date</option>
              <option value="username">User</option>
              <option value="result">Stage</option>
              <option value="confidence">Confidence</option>
            </select>
            <button
              onClick={() => setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"))}
              className="px-3 py-2.5 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] hover:bg-[#F1F5F9] transition"
            >
              {sortDirection === "asc" ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
          </div>
        </div>

        {/* Table */}
        {filtered.length === 0 ? (
          <div className="bg-white border border-[#E8EDF2] rounded-2xl p-12 text-center shadow-sm">
            <BarChart3 size={48} className="mx-auto text-[#94A3B8] mb-3" />
            <h3 className="text-lg font-semibold text-[#0D1B2A]">No predictions found</h3>
            <p className="text-sm text-[#64748B] mt-1">
              {predictions.length === 0
                ? "No scans have been uploaded by any user yet."
                : "Try adjusting your search filters."}
            </p>
          </div>
        ) : (
          <div className="bg-white border border-[#E8EDF2] rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F8FAFB] border-b border-[#E8EDF2]">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider">
                      ID
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => setSortField("username")}
                    >
                      <span className="flex items-center gap-1">
                        User
                        {sortField === "username" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => setSortField("result")}
                    >
                      <span className="flex items-center gap-1">
                        Stage
                        {sortField === "result" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => setSortField("confidence")}
                    >
                      <span className="flex items-center gap-1">
                        Confidence
                        {sortField === "confidence" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => setSortField("timestamp")}
                    >
                      <span className="flex items-center gap-1">
                        Date
                        {sortField === "timestamp" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-[#64748B] uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((pred) => {
                    const { bg, text } = getStageBadge(pred.result);
                    return (
                      <tr
                        key={pred.id}
                        className="border-b border-[#F1F5F9] last:border-0 hover:bg-[#F8FAFB] transition"
                      >
                        <td className="px-4 py-3 text-[#64748B] text-xs">#{pred.id}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <Users size={14} className="text-[#94A3B8]" />
                            <span className="font-medium text-[#0D1B2A]">
                              {pred.username || "Unknown"}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${bg} ${text}`}>
                            {pred.result}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 max-w-[80px] h-1.5 rounded-full bg-[#F1F5F9]">
                              <div
                                className="h-1.5 rounded-full bg-[#0EA472]"
                                style={{ width: `${pred.confidence * 100}%` }}
                              />
                            </div>
                            <span className="text-xs font-semibold text-[#0D1B2A]">
                              {(pred.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-[#64748B] text-xs">
                          <div className="flex items-center gap-1.5">
                            <Clock size={14} />
                            {formatDate(pred.timestamp)}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Link
                              href={`/dashboard?scan=${pred.id}`}
                              className="p-1.5 rounded-lg hover:bg-[#F1F5F9] transition text-[#64748B] hover:text-[#0D1B2A]"
                              title="View in dashboard"
                            >
                              <Eye size={16} />
                            </Link>
                            <button
                              onClick={() => deletePrediction(pred.id)}
                              disabled={actionLoading === pred.id}
                              className="p-1.5 rounded-lg text-[#EF4444] hover:bg-[#FEF2F2] transition disabled:opacity-50"
                            >
                              {actionLoading === pred.id ? (
                                <Loader2 size={16} className="animate-spin" />
                              ) : (
                                <Trash2 size={16} />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer count */}
        {filtered.length > 0 && (
          <div className="mt-4 text-sm text-[#64748B] text-center">
            Showing {filtered.length} of {predictions.length} predictions
          </div>
        )}
      </div>
    </div>
  );
}