"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  FileText,
  ArrowLeft,
  LogOut,
  Loader2,
  Download,
  Calendar,
  FileImage,
  CheckCircle,
} from "lucide-react";
import api from "../../lib/api";

interface Report {
  id: number;
  title: string;
  summary: string;
  file_path: string;
  created_at: string;
}

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

export default function ReportsListPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<number | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await api.get("/reports/list");
        setReports(res.data);
      } catch (error) {
        console.error("Failed to fetch reports:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  // ── Download handler ──────────────────────────────────────────
  const handleDownload = async (reportId: number) => {
    setDownloading(reportId);
    try {
      const response = await api.get(`/reports/download/${reportId}`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Failed to download report. Please try again.");
    } finally {
      setDownloading(null);
    }
  };

  const handleLogout = async () => {
    try {
      await api.get("/auth/logout");
    } catch (e) {
      // ignore
    }
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#0EA472]" />
      </div>
    );
  }

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
        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 text-sm text-[#64748B] hover:text-[#0D1B2A] transition"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </nav>

      {/* ── Main ── */}
      <div className="pt-20 px-8 pb-12 max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.5px]">
            My Reports
          </h1>
          <Link
            href="/generate-report"
            className="text-sm text-[#0EA472] font-semibold hover:underline"
          >
            + Generate new report
          </Link>
        </div>

        {reports.length === 0 ? (
          <div className="bg-white border border-[#E8EDF2] rounded-2xl p-12 text-center shadow-sm">
            <FileImage size={48} className="mx-auto text-[#94A3B8] mb-3" />
            <h3 className="text-lg font-semibold text-[#0D1B2A]">No reports yet</h3>
            <p className="text-sm text-[#64748B] mt-1">
              Generate your first report from a scan.
            </p>
            <Link
              href="/generate-report"
              className="inline-block mt-4 text-sm font-semibold text-[#0EA472] hover:underline"
            >
              Go to Generate Report →
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className="bg-white border border-[#E8EDF2] rounded-2xl p-5 shadow-sm hover:shadow-md transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-[#0D1B2A]">
                      {report.title}
                    </h2>
                    <p className="text-sm text-[#64748B] mt-1 line-clamp-2">
                      {report.summary}
                    </p>
                    <div className="flex items-center gap-2 mt-2 text-xs text-[#94A3B8]">
                      <Calendar size={14} />
                      {formatDate(report.created_at)}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownload(report.id)}
                    disabled={downloading === report.id}
                    className="flex items-center gap-1.5 px-4 py-2 bg-[#0EA472] text-white rounded-xl text-sm font-medium hover:bg-[#059669] transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {downloading === report.id ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Download size={16} />
                    )}
                    {downloading === report.id ? "Downloading..." : "Download PDF"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}