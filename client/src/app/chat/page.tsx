"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  MessageSquare,
  Send,
  Loader2,
  Brain,
  User,
  LogOut,
  ArrowLeft,
  Sparkles,
  Lightbulb,
  ClipboardList,
  HeartPulse,
  FileText,
  Upload,
  CheckCircle,
  Trash2,
  Paperclip,
  X,
} from "lucide-react";
import React from "react";
import api from "../../lib/api"; 
import Link from "next/link";

// ── Types ─────────────────────────────────────────────────────
interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatHistoryItem {
  id: number;
  question: string;
  answer: string;
  timestamp: string;
}

// ── Quick suggestion prompts ──────────────────────────────
const SUGGESTIONS = [
  { icon: <Lightbulb size={14} />, text: "What does 'Mild Demented' mean?" },
  { icon: <HeartPulse size={14} />, text: "What are early symptoms of Alzheimer's?" },
  { icon: <ClipboardList size={14} />, text: "Explain the MMSE test" },
  { icon: <Brain size={14} />, text: "How does MRI help in diagnosis?" },
];

// ── Main Component ──────────────────────────────────────────
export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [autoSent, setAutoSent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null); // NEW

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Auto-scroll ──────────────────────────────────────────
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ── Fetch user info ──────────────────────────────────────
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await api.get("/auth/me");
        setUser(res.data);
      } catch {
        router.push("/login");
      }
    };
    fetchUser();
  }, [router]);

  // ── Fetch chat history ──────────────────────────────────
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get("/chat/history");
        const history: ChatHistoryItem[] = res.data;

        if (history.length === 0) {
          setMessages([
            {
              id: "welcome",
              role: "assistant",
              content:
                "👋 Hello! I'm your NeuroSight AI assistant. I can help you understand Alzheimer's diagnosis, explain MRI findings, and provide context from medical literature. How can I assist you today?",
              timestamp: new Date(),
            },
          ]);
        } else {
          const msgs: Message[] = [];
          const sorted = [...history].reverse();
          for (const item of sorted) {
            msgs.push({
              id: `user-${item.id}`,
              role: "user",
              content: item.question,
              timestamp: new Date(item.timestamp),
            });
            msgs.push({
              id: `assistant-${item.id}`,
              role: "assistant",
              content: item.answer,
              timestamp: new Date(item.timestamp),
            });
          }
          setMessages(msgs);
        }
      } catch (error) {
        console.error("Failed to load chat history:", error);
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content: "👋 Hello! How can I help you today?",
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, []);

  // ── Auto-send from dashboard ────────────────────────────
  useEffect(() => {
    if (loadingHistory) return;
    const result = searchParams.get("result");
    const confidence = searchParams.get("confidence");
    if (result && confidence && !autoSent) {
      const question = `I have a prediction result of "${result}" with ${confidence}% confidence. Can you explain what this means?`;
      sendMessage(question, null); // pass null for no file
      setAutoSent(true);
      window.history.replaceState({}, "", "/chat");
    }
  }, [loadingHistory, searchParams, autoSent]);

  // ── Send message (with optional file) ────────────────────
  const sendMessage = async (content: string, file: File | null) => {
    if (!content.trim() && !file) return;

    // Build FormData
    const formData = new FormData();
    formData.append("question", content.trim());
    if (file) {
      formData.append("file", file);
    }

    // Add user message to UI (temporarily without answer)
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim() + (file ? ` 📎 ${file.name}` : ""),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setAttachedFile(null);
    setLoading(true);

    try {
      const res = await api.post("/chat", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.data.answer || "No response.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: error.response?.data?.detail || "Error sending message.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
      // reset file input
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // ── Handle file attachment ───────────────────────────────
  const handleAttachFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAttachedFile(file);
    }
    e.target.value = "";
  };

  const removeAttachedFile = () => {
    setAttachedFile(null);
  };

  // ── Handle submit ──────────────────────────────────────
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input, attachedFile);
  };

  // ── Logout ──────────────────────────────────────────────
  const handleLogout = async () => {
    await api.get("/auth/logout");
    router.push("/login");
  };

  // ── Clear history ──────────────────────────────────────
  const clearHistory = async () => {
    if (!confirm("Delete all chat history and uploaded PDFs?")) return;
    try {
      await Promise.all([
        api.delete("/chat/history"),
        api.delete("/chat/documents")
      ]);
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: "History and documents cleared. How can I help you?",
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      alert("Failed to clear history.");
    }
  };

  // ── Loading state ──────────────────────────────────────
  if (loadingHistory) {
    return (
      <div className="min-h-screen bg-[#F8FAFB] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-[#0EA472]" />
      </div>
    );
  }

  // ── Render ──────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#F8FAFB] font-['Inter',-apple-system,sans-serif] flex flex-col">
      {/* Navbar – same as before */}
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
              <MessageSquare size={16} className="text-white" />
            </div>
            <span className="text-base font-bold text-[#0D1B2A] tracking-[-0.3px]">
              Neuro<span className="text-[#0EA472]">Sight</span>
              <span className="ml-1 text-sm font-normal text-[#64748B]">
                Chat
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

      {/* ── Main chat area ── */}
      <div className="flex-1 pt-16 flex flex-col max-w-4xl mx-auto w-full px-4 sm:px-6">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto py-6 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                  msg.role === "user"
                    ? "bg-[#0D1B2A] text-white"
                    : "bg-white border border-[#E8EDF2] text-[#0D1B2A]"
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {msg.role === "assistant" && (
                    <Sparkles size={14} className="text-[#0EA472]" />
                  )}
                  <span className="text-xs font-medium opacity-70">
                    {msg.role === "user" ? "You" : "NeuroSight AI"}
                  </span>
                  <span className="text-[10px] opacity-50">
                    {msg.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-[#E8EDF2] rounded-2xl px-5 py-3 flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-[#0EA472]" />
                <span className="text-sm text-[#64748B]">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions – if few messages */}
        {messages.length <= 2 && (
          <div className="pb-4">
            <p className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider mb-3">
              Quick questions
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map(({ icon, text }) => (
                <button
                  key={text}
                  onClick={() => sendMessage(text, null)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white border border-[#E8EDF2] text-xs text-[#0D1B2A] hover:border-[#0EA472] hover:bg-[#EDF7F3] transition"
                >
                  {icon}
                  {text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="py-4 border-t border-[#E8EDF2] bg-white sticky bottom-0">
          {/* Attached file indicator */}
          {attachedFile && (
            <div className="flex items-center gap-2 mb-2 p-2 bg-[#EDF7F3] rounded-lg border border-[#A7F3D0]">
              <FileText size={16} className="text-[#0EA472]" />
              <span className="text-sm text-[#0D1B2A]">{attachedFile.name}</span>
              <button
                onClick={removeAttachedFile}
                className="ml-auto text-[#EF4444] hover:bg-[#FEE2E2] rounded p-1"
              >
                <X size={16} />
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a clinical question..."
                className="w-full px-4 py-2.5 pr-12 border border-[#E8EDF2] rounded-xl bg-[#F8FAFB] text-[#0D1B2A] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#0EA472] focus:border-transparent transition"
                disabled={loading}
              />
              <label
                htmlFor="file-attach"
                className="absolute right-3 top-1/2 -translate-y-1/2 cursor-pointer text-[#94A3B8] hover:text-[#0EA472] transition"
                title="Attach a PDF"
              >
                <Paperclip size={18} />
              </label>
              <input
                id="file-attach"
                type="file"
                accept=".pdf"
                onChange={handleAttachFile}
                className="hidden"
                ref={fileInputRef}
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              disabled={(!input.trim() && !attachedFile) || loading}
              className="bg-[#0D1B2A] text-white px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-[#1E3A5F] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <>
                  Send
                  <Send size={16} />
                </>
              )}
            </button>
          </form>

          <div className="flex justify-between items-center mt-2">
            <p className="text-[10px] text-[#94A3B8]">
              Powered by Gemini · For research purposes only
            </p>
            {messages.length > 2 && (
              <button
                onClick={clearHistory}
                className="text-xs text-[#EF4444] hover:underline flex items-center gap-1"
              >
                <Trash2 size={12} />
                Clear history
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}