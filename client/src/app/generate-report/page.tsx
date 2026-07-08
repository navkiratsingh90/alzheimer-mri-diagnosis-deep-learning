"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  Loader2,
  FileImage,
  Radio,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import api from "../../lib/api";

interface Prediction {
  id: number;
  image_path: string;
  result: string;
  confidence: number;
  timestamp: string;
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

const getImageUrl = (path: string) => {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base}/${path}`;
};

export default function GenerateReportPage() {
  const router = useRouter();
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        const res = await api.get("/reports/predictions");
        setPredictions(res.data);
      } catch (err) {
        console.error(err);
        setError("Failed to load predictions.");
      } finally {
        setLoading(false);
      }
    };
    fetchPredictions();
  }, []);

  const handleGenerate = async () => {
    if (!selectedId) return;
    setGenerating(true);
    setError(null);
    try {
      const res = await api.post("/reports/generate", {
        prediction_id: selectedId,
      });
      const { report_id } = res.data;
      // Redirect to reports list or directly to download
      router.push(`/reports?highlight=${report_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate report.");
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#0EA472]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFB] font-['Inter',-apple-system,sans-serif] p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/dashboard"
            className="flex items-center gap-1.5 text-sm text-[#64748B] hover:text-[#0D1B2A] transition"
          >
            <ArrowLeft size={16} />
            Back to Dashboard
          </Link>
          <h1 className="text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.5px]">
            Generate Report
          </h1>
        </div>

        {predictions.length === 0 ? (
          <div className="bg-white border border-[#E8EDF2] rounded-2xl p-12 text-center shadow-sm">
            <FileImage size={48} className="mx-auto text-[#94A3B8] mb-3" />
            <h3 className="text-lg font-semibold text-[#0D1B2A]">No scans found</h3>
            <p className="text-sm text-[#64748B] mt-1">
              You haven't uploaded any MRI scans yet.
            </p>
            <Link
              href="/dashboard"
              className="inline-block mt-4 text-sm font-semibold text-[#0EA472] hover:underline"
            >
              Upload your first scan →
            </Link>
          </div>
        ) : (
          <>
            <p className="text-sm text-[#64748B] mb-4">
              Select a scan below to generate a detailed PDF report with AI analysis.
            </p>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm flex items-center gap-2">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <div className="space-y-3">
              {predictions.map((pred) => (
                <div
                  key={pred.id}
                  className={`bg-white border rounded-2xl p-4 shadow-sm flex items-center gap-4 cursor-pointer transition hover:border-[#0EA472] ${
                    selectedId === pred.id
                      ? "border-[#0EA472] ring-2 ring-[#0EA472] ring-opacity-20"
                      : "border-[#E8EDF2]"
                  }`}
                  onClick={() => setSelectedId(pred.id)}
                >
                  <div className="flex-shrink-0">
                    <div className="relative w-16 h-16 rounded-lg overflow-hidden border border-[#E8EDF2]">
                      <Image
                        src={getImageUrl(pred.image_path) || "/placeholder.png"}
                        alt="Scan"
                        fill
                        className="object-cover"
                        unoptimized
                      />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#0D1B2A]">
                        #{pred.id}
                      </span>
                      <span className="text-sm text-[#64748B]">
                        {formatDate(pred.timestamp)}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-sm font-medium text-[#0D1B2A]">
                        {pred.result}
                      </span>
                      <span className="text-xs text-[#64748B]">
                        {(pred.confidence * 100).toFixed(1)}% confidence
                      </span>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {selectedId === pred.id ? (
                      <CheckCircle size={24} className="text-[#0EA472]" />
                    ) : (
                      <div className="w-6 h-6 rounded-full border-2 border-[#D1D5DB]" />
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={handleGenerate}
                disabled={!selectedId || generating}
                className="px-6 py-3 bg-[#0EA472] text-white font-semibold rounded-xl hover:bg-[#059669] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {generating ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate Report"
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}