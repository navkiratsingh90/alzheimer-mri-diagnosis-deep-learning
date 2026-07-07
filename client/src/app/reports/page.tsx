"use client";

import { useState, useEffect } from "react";
import React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  FileText,
  Calendar,
  Activity,
  BarChart3,
  ArrowLeft,
  LogOut,
  Search,
  Download,
  ChevronDown,
  ChevronUp,
  Loader2,
  FileImage,
  AlertCircle,
  CheckCircle,
  Clock,
  File,
} from "lucide-react";
import api from "../../lib/api"; // ✅ Import API client

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

const daysAgo = (days: number) => {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString();
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
export default function ReportsPage() {
  const router = useRouter();
  const [predictions, setPredictions] = useState<Prediction[]>([ /* ... your mock data ... */ ]);
  const [filtered, setFiltered] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<"timestamp" | "result" | "confidence">("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  const [generatingReport, setGeneratingReport] = useState(false); // ✅ New state

  // ── Fetch data ─────────────────────────────────────────────
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userRes, predRes] = await Promise.all([
          api.get("/auth/me"),
          api.get("/reports/predictions"),
        ]);
        setUser(userRes.data);
        setPredictions(predRes.data);
        setFiltered(predRes.data);
      } catch (error) {
        // If API fails, use mock data (already set)
        console.warn("Using mock data due to API error");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [router]);

  // ── Search & filter ────────────────────────────────────────
  useEffect(() => {
    const term = searchTerm.toLowerCase();
    let filteredList = predictions.filter(
      (p) =>
        p.result.toLowerCase().includes(term) ||
        formatDate(p.timestamp).toLowerCase().includes(term) ||
        (p.confidence * 100).toFixed(1).includes(term)
    );
    filteredList.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];
      if (sortField === "timestamp") {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }
      if (sortDirection === "asc") return aVal > bVal ? 1 : -1;
      else return aVal < bVal ? 1 : -1;
    });
    setFiltered(filteredList);
  }, [searchTerm, sortField, sortDirection, predictions]);

  // ── Toggle sort ────────────────────────────────────────────
  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  // ── Toggle row expansion ──────────────────────────────────
  const toggleRow = (id: number) => {
    setExpandedRows((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(id)) newSet.delete(id);
      else newSet.add(id);
      return newSet;
    });
  };

  // ── Generate PDF Report ────────────────────────────────────
  const generateReport = async () => {
    if (predictions.length === 0) {
      alert("No predictions to generate a report from.");
      return;
    }
    setGeneratingReport(true);
    try {
      const ids = predictions.map(p => p.id).join(",");
      const response = await api.post("/reports/generate", {
        prediction_ids: ids,
        title: `Report – ${new Date().toLocaleDateString()}`,
      });
      const { report_id } = response.data;
      // Open the download endpoint in a new tab
      window.open(`/api/reports/download/${report_id}`, "_blank");
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert("Failed to generate report. Please try again.");
    } finally {
      setGeneratingReport(false);
    }
  };

  // ── Logout ──────────────────────────────────────────────────
  const handleLogout = async () => {
    try {
      await api.get("/auth/logout");
    } catch (e) {
      // ignore
    }
    router.push("/login");
  };

  // ── Loading ─────────────────────────────────────────────────
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
                Reports
              </span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-[#64748B] hidden sm:inline">
            {user?.username || "User"}
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
      <div className="pt-20 px-8 pb-12 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6">
          <div>
            <h1 className="text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.5px]">
              Your Reports
            </h1>
            <p className="text-sm text-[#64748B] mt-1">
              {predictions.length} scan{predictions.length !== 1 ? "s" : ""} analysed
            </p>
          </div>
          <div className="flex gap-3 mt-4 sm:mt-0">
            {/* ✅ New Generate Report Button */}
            <button
              onClick={generateReport}
              disabled={generatingReport || predictions.length === 0}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-[#0EA472] border border-[#0EA472] rounded-xl hover:bg-[#059669] transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generatingReport ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <File size={16} />
              )}
              {generatingReport ? "Generating..." : "Generate PDF Report"}
            </button>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-[#0D1B2A] bg-white border border-[#E8EDF2] rounded-xl hover:bg-[#F8FAFB] transition"
            >
              <Download size={16} />
              Export (CSV)
            </button>
          </div>
        </div>
        {/* Search & filter bar */}
        <div className="bg-white border border-[#E8EDF2] rounded-2xl p-4 shadow-sm mb-6 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
            <input
              type="text"
              placeholder="Search by stage, date, or confidence..."
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
            <FileImage size={48} className="mx-auto text-[#94A3B8] mb-3" />
            <h3 className="text-lg font-semibold text-[#0D1B2A]">No scans found</h3>
            <p className="text-sm text-[#64748B] mt-1">
              {predictions.length === 0
                ? "You haven't uploaded any MRI scans yet."
                : "Try adjusting your search filters."}
            </p>
            {predictions.length === 0 && (
              <Link
                href="/dashboard"
                className="inline-block mt-4 text-sm font-semibold text-[#0EA472] hover:underline"
              >
                Upload your first scan →
              </Link>
            )}
          </div>
        ) : (
          <div className="bg-white border border-[#E8EDF2] rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[#F8FAFB] border-b border-[#E8EDF2]">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider">
                      Scan
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => handleSort("result")}
                    >
                      <span className="flex items-center gap-1">
                        Stage
                        {sortField === "result" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => handleSort("confidence")}
                    >
                      <span className="flex items-center gap-1">
                        Confidence
                        {sortField === "confidence" &&
                          (sortDirection === "asc" ? <ChevronUp size={14} /> : <ChevronDown size={14} />)}
                      </span>
                    </th>
                    <th
                      className="px-4 py-3 text-left text-xs font-semibold text-[#64748B] uppercase tracking-wider cursor-pointer hover:text-[#0D1B2A]"
                      onClick={() => handleSort("timestamp")}
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
                    const isExpanded = expandedRows.has(pred.id);
                    return (
                      <tr
                        key={pred.id}
                        className="border-b border-[#F1F5F9] last:border-0 hover:bg-[#F8FAFB] transition"
                      >
                        {/* Scan thumbnail */}
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="relative w-10 h-10 rounded-lg overflow-hidden border border-[#E8EDF2] flex-shrink-0">
                              <Image
                                src={pred.image_path}
                                alt="Scan thumbnail"
                                fill
                                className="object-cover"
                              />
                            </div>
                            <span className="text-xs text-[#94A3B8]">#{pred.id}</span>
                          </div>
                        </td>

                        {/* Stage */}
                        <td className="px-4 py-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${bg} ${text}`}>
                            {pred.result}
                          </span>
                        </td>

                        {/* Confidence */}
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

                        {/* Date */}
                        <td className="px-4 py-3 text-[#64748B] text-xs">
                          <div className="flex items-center gap-1.5">
                            <Clock size={14} />
                            {formatDate(pred.timestamp)}
                          </div>
                        </td>

                        {/* Actions */}
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => toggleRow(pred.id)}
                            className="text-[#0EA472] hover:underline text-xs font-medium"
                          >
                            {isExpanded ? "Hide" : "Details"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Pagination (simplified) */}
        {filtered.length > 0 && (
          <div className="mt-6 flex items-center justify-between text-sm text-[#64748B]">
            <span>
              Showing {filtered.length} of {predictions.length} reports
            </span>
            {/* Could add pagination controls here if needed */}
          </div>
        )}

        {/* Export options */}
        {filtered.length > 0 && (
          <div className="mt-4 p-4 bg-white border border-[#E8EDF2] rounded-2xl shadow-sm flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm text-[#64748B]">
              <BarChart3 size={16} className="inline mr-1.5" />
              Summary: {predictions.filter((p) => p.result === "NonDemented").length} NonDemented,{" "}
              {predictions.filter((p) => p.result === "VeryMild").length} Very Mild,{" "}
              {predictions.filter((p) => p.result === "Mild").length} Mild,{" "}
              {predictions.filter((p) => p.result === "Moderate").length} Moderate
            </span>
            <button className="text-sm text-[#0EA472] font-semibold hover:underline">
              Download full report (CSV)
            </button>
          </div>
        )}
      </div>
    </div>
  );
}