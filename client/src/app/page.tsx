"use client";

import Link from "next/link";
import {
  Brain,
  Upload,
  MessageSquare,
  FileText,
  Shield,
  ArrowRight,
  Check,
  Scan,
  Users,
  Clock,
  Activity,
  BarChart3,
} from "lucide-react";
import { useAuth } from "@/lib/authContext";
import { useRouter } from "next/navigation";

// ── Types ──────────────────────────────────────────────────
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

interface StatProps {
  value: string;
  label: string;
}
interface StepProps {
  number: string;
  title: string;
  description: string;
}
const Step = ({ number, title, description }: StepProps) => (
  <div className="flex gap-5 items-start">
    <div className="w-9 h-9 rounded-xl bg-[#0EA472] text-white flex items-center justify-center text-[13px] font-bold flex-shrink-0">
      {number}
    </div>
    <div>
      <h4 className="m-0 mb-1 text-[15px] font-semibold text-[#0D1B2A]">{title}</h4>
      <p className="m-0 text-[13.5px] text-[#64748B] leading-relaxed">{description}</p>
    </div>
  </div>
);
const ResultCard = () => (
  <div className="bg-white border border-[#E8EDF2] rounded-[20px] p-5 w-[260px] shadow-lg absolute right-0 top-1/2 -translate-y-1/2">
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-9 h-9 rounded-xl bg-[#FFF7ED] flex items-center justify-center">
        <BarChart3 size={18} className="text-[#F59E0B]" />
      </div>
      <div>
        <p className="m-0 text-[11px] text-[#94A3B8]">MRI Scan · Axial</p>
        <p className="m-0 text-xs font-semibold text-[#0D1B2A]">Patient #A-2047</p>
      </div>
    </div>

    <div className="bg-[#FFF7ED] border border-[#FED7AA] rounded-xl p-2.5 px-3.5 mb-3.5">
      <p className="m-0 mb-0.5 text-[10px] text-[#92400E] font-medium">PREDICTION</p>
      <p className="m-0 text-[15px] font-bold text-[#92400E]">Mild Demented</p>
    </div>

    {[
      { label: "NonDemented", pct: 4, color: "#0EA472" },
      { label: "Very Mild", pct: 12, color: "#3B82F6" },
      { label: "Mild", pct: 78, color: "#F59E0B" },
      { label: "Moderate", pct: 6, color: "#EF4444" },
    ].map(({ label, pct, color }) => (
      <div key={label} className="mb-2">
        <div className="flex justify-between mb-1">
          <span className="text-[11px] text-[#64748B]">{label}</span>
          <span className="text-[11px] font-semibold text-[#0D1B2A]">{pct}%</span>
        </div>
        <div className="h-1 rounded-[2px] bg-[#F1F5F9]">
          <div className="h-1 rounded-[2px]" style={{ background: color, width: `${pct}%` }} />
        </div>
      </div>
    ))}

    <div className="mt-3.5 pt-3 border-t border-[#F1F5F9] flex justify-between items-center">
      <span className="text-[11px] text-[#94A3B8]">Confidence</span>
      <span className="text-[13px] font-bold text-[#0EA472]">78.4%</span>
    </div>
  </div>
); 
// ── Sub‑components ────────────────────────────────────────
const FeatureCard = ({ icon, title, description }: FeatureCardProps) => (
  <div className="bg-white border border-[#E8EDF2] rounded-2xl p-6 flex flex-col gap-3.5">
    <div className="w-11 h-11 rounded-xl bg-[#EDF7F3] flex items-center justify-center text-[#0EA472]">
      {icon}
    </div>
    <div>
      <h3 className="m-0 mb-1.5 text-[15px] font-semibold text-[#0D1B2A]">{title}</h3>
      <p className="m-0 text-[13.5px] text-[#64748B] leading-relaxed">{description}</p>
    </div>
  </div>
);

const Stat = ({ value, label }: StatProps) => (
  <div className="flex flex-col gap-0.5">
    <span className="text-[22px] font-bold text-[#0D1B2A] tracking-[-0.5px]">{value}</span>
    <span className="text-xs text-[#64748B] font-normal">{label}</span>
  </div>
);

// ── Main Page ─────────────────────────────────────────────
export default function HomePage() {
  const router = useRouter()
  const user = useAuth()
  if (!user) router.push('/login')
  return (
    <div className="font-['Inter',-apple-system,BlinkMacSystemFont,sans-serif] bg-[#F8FAFB] min-h-screen">

      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[rgba(248,250,251,0.92)] backdrop-blur-md border-b border-[#E8EDF2] px-6 md:px-12 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0EA472] to-[#059669] flex items-center justify-center">
            <Brain size={16} className="text-white" />
          </div>
          <span className="text-base font-bold text-[#0D1B2A] tracking-[-0.3px]">
            Neuro<span className="text-[#0EA472]">Sight</span>
          </span>
        </div>

        <div className="flex items-center gap-6">
          <Link href="/login" className="text-sm text-[#64748B] font-medium hover:text-[#0D1B2A] transition">
            Login
          </Link>
          <Link
            href="/register"
            className="text-sm font-semibold text-white bg-[#0D1B2A] rounded-xl py-2 px-5 hover:bg-[#1E3A5F] transition"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="pt-32 pb-24 px-12 max-w-[1200px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-16 items-center relative">
        <div>
          <div className="inline-flex items-center gap-1.5 bg-[#EDF7F3] border border-[#A7F3D0] rounded-full py-1.5 px-3 mb-6">
            <div className="w-1.5 h-1.5 rounded-full bg-[#0EA472]" />
            <span className="text-xs font-medium text-[#047857]">
              AI-POWERED ALZHEIMER'S DETECTION
            </span>
          </div>

          <h1 className="m-0 mb-5 text-[52px] font-extrabold text-[#0D1B2A] leading-tight tracking-[-1.5px]">
            Detect Alzheimer's<br />
            <span className="text-[#0EA472]">Early.</span> Act Fast.
          </h1>

          <p className="m-0 mb-9 text-base text-[#64748B] leading-relaxed max-w-[420px]">
            Upload an MRI scan and get instant AI-powered classification across
            4 Alzheimer's stages — with visual explainability and a clinical AI
            assistant to guide next steps.
          </p>

          <div className="flex gap-3 mb-12">
            <Link href="/dashboard" className="inline-flex items-center gap-2 bg-[#0D1B2A] text-white no-underline py-3.5 px-6 rounded-xl text-sm font-semibold hover:bg-[#1E3A5F] transition">
              Analyse a Scan
              <ArrowRight size={16} />
            </Link>
            <Link href="/dashboard" className="inline-flex items-center gap-2 bg-white text-[#0D1B2A] no-underline py-3.5 px-6 rounded-xl text-sm font-medium border border-[#E8EDF2] hover:bg-[#F8FAFB] transition">
              View Dashboard
            </Link>
          </div>

          <div className="flex gap-8 pt-8 border-t border-[#E8EDF2]">
            <Stat value="93.2%" label="Classification accuracy" />
            <div className="w-px bg-[#E8EDF2]" />
            <Stat value="4 Stages" label="Alzheimer's classes" />
            <div className="w-px bg-[#E8EDF2]" />
            <Stat value="&lt; 2s" label="Inference time" />
          </div>
        </div>

        <div className="relative h-[440px]">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-60 h-60 rounded-full bg-gradient-to-br from-[#EDF7F3] to-[#DBEAFE] flex items-center justify-center">
            <div className="w-40 h-40 rounded-full bg-gradient-to-br from-[#A7F3D0] to-[#BAE6FD] flex items-center justify-center">
              <Brain size={72} className="text-[#0EA472] opacity-60" />
            </div>
          </div>
          <ResultCard />
          {/* <DoctorBadge /> */}
          <div className="absolute top-5 left-5 bg-white border border-[#E8EDF2] rounded-xl py-2.5 px-3.5 shadow-md flex items-center gap-2">
            <Activity size={14} className="text-[#0EA472]" />
            {/* <span className="text-xs font-medium text-[#0D1B2A]">Grad‑CAM active</span> */}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-16 px-6 md:px-12 max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <p className="m-0 mb-2 text-xs font-semibold text-[#0EA472] tracking-[0.08em]">
            FEATURES
          </p>
          <h2 className="m-0 text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.6px]">
            Everything you need in one place
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <FeatureCard
            icon={<Upload size={22} />}
            title="Upload MRI"
            description="Upload any brain MRI image (JPG/PNG) and get instant classification."
          />
          <FeatureCard
            icon={<Brain size={22} />}
            title="4‑Stage Classification"
            description="NonDemented, Very Mild, Mild, or Moderate – with confidence scores."
          />
          <FeatureCard
            icon={<MessageSquare size={22} />}
            title="AI Chat Assistant"
            description="Ask questions about your results and get helpful, context‑aware answers."
          />
          <FeatureCard
            icon={<FileText size={22} />}
            title="History & Reports"
            description="View all your past scans, track progression, and export data."
          />
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="bg-white border-y border-[#E8EDF2] py-24 px-12">
        <div className="max-w-[1200px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
          <div>
            <p className="m-0 mb-2 text-xs font-semibold text-[#0EA472] tracking-[0.08em]">
              HOW IT WORKS
            </p>
            <h2 className="m-0 mb-10 text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.6px]">
              Diagnosis in three steps
            </h2>
            <div className="flex flex-col gap-7">
              <Step number="01" title="Upload the MRI scan" description="Drag and drop any axial brain MRI image — JPG or PNG. The system accepts both clinical and research‑grade scans." />
              <Step number="02" title="AI analyses the scan" description="EfficientNetV2B0 classifies the scan across 4 stages in under 2 seconds. Grad‑CAM highlights the critical brain regions." />
              <Step number="03" title="Review with AI assistant" description="Chat with the LangChain agent to understand the result, get treatment context, and generate a clinical PDF report." />
            </div>
          </div>

          <div className="bg-[#F8FAFB] border border-[#E8EDF2] rounded-[20px] p-8">
            <p className="m-0 mb-5 text-[13px] font-semibold text-[#0D1B2A]">
              Sample output
            </p>
            <div className="mb-6">
              <p className="m-0 mb-3 text-[11px] text-[#94A3B8] font-medium">ALZHEIMER'S STAGE</p>
              <div className="flex gap-1.5">
                {[
                  { label: "Non", color: "#0EA472", active: false },
                  { label: "Very Mild", color: "#3B82F6", active: false },
                  { label: "Mild", color: "#F59E0B", active: true },
                  { label: "Moderate", color: "#EF4444", active: false },
                ].map(({ label, color, active }) => (
                  <div
                    key={label}
                    className={`flex-1 py-2 px-1.5 rounded-lg text-center transition ${
                      active
                        ? `bg-[${color}] border-[1.5px] border-[${color}]`
                        : "bg-[#F1F5F9] border-[1.5px] border-transparent"
                    }`}
                  >
                    <span className={`text-[10px] font-${active ? 'bold' : 'medium'} ${active ? 'text-white' : 'text-[#94A3B8]'}`}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <div className="flex justify-between mb-2">
                <span className="text-xs text-[#64748B]">Model confidence</span>
                <span className="text-xs font-bold text-[#0D1B2A]">78.4%</span>
              </div>
              <div className="h-1.5 rounded-[3px] bg-[#E8EDF2]">
                <div className="h-1.5 rounded-[3px] bg-[#F59E0B] w-[78.4%]" />
              </div>
            </div>

            <div className="bg-[#EDF7F3] rounded-xl p-3.5 px-4">
              <div className="flex gap-2 items-start">
                <div className="w-6 h-6 rounded-lg bg-[#0EA472] text-white flex items-center justify-center text-[10px] font-bold flex-shrink-0">AI</div>
                <p className="m-0 text-[12.5px] text-[#064E3B] leading-relaxed">
                  This result indicates <strong>Mild Cognitive Impairment</strong>. I recommend scheduling an MMSE test and PET scan. Would you like to see relevant treatment options from PubMed?
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats / Problem ── */}
      <section className="py-16 px-6 md:px-12 max-w-6xl mx-auto">
        <div className="bg-gradient-to-br from-[#0D1B2A] to-[#1E3A5F] rounded-3xl p-10 md:p-14 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
          <div>
            <p className="m-0 mb-2 text-xs font-semibold text-[#0EA472] tracking-[0.08em]">
              THE CHALLENGE
            </p>
            <h2 className="m-0 mb-4 text-2xl md:text-3xl font-extrabold text-white tracking-[-0.6px] leading-tight">
              Early detection saves lives
            </h2>
            <p className="m-0 mb-6 text-sm text-[#94A3B8] leading-relaxed">
              Alzheimer's affects millions worldwide, yet early diagnosis remains difficult.
              Our AI‑powered tool helps clinicians and researchers detect subtle changes
              in brain MRI scans, enabling timely intervention.
            </p>
            <div className="flex flex-col gap-2">
              {[
                "Instant classification with 93% accuracy",
                "Accessible from any device with a browser",
                "Secure and private – your data stays with you",
              ].map((point) => (
                <div key={point} className="flex items-start gap-2.5">
                  <div className="w-5 h-5 rounded-md bg-[#0EA472] flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check size={14} className="text-white" />
                  </div>
                  <span className="text-sm text-[#CBD5E1]">{point}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center">
              <p className="m-0 text-3xl font-extrabold text-[#0EA472]">55M+</p>
              <p className="m-0 text-xs text-[#94A3B8]">People affected globally</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center">
              <p className="m-0 text-3xl font-extrabold text-[#3B82F6]">10M</p>
              <p className="m-0 text-xs text-[#94A3B8]">New cases annually</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center">
              <p className="m-0 text-3xl font-extrabold text-[#F59E0B]">153M</p>
              <p className="m-0 text-xs text-[#94A3B8]">Projected by 2050</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 text-center">
              <p className="m-0 text-3xl font-extrabold text-[#EF4444]">$1T+</p>
              <p className="m-0 text-xs text-[#94A3B8]">Annual global cost</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="px-6 md:px-12 pb-16 max-w-4xl mx-auto text-center">
        <div className="bg-[#EDF7F3] border border-[#A7F3D0] rounded-3xl py-12 px-6">
          <div className="inline-flex items-center gap-1.5 mb-4">
            <Shield size={16} className="text-[#047857]" />
            <span className="text-xs font-semibold text-[#047857]">RESEARCH TOOL</span>
          </div>
          <h2 className="m-0 mb-3 text-3xl font-extrabold text-[#0D1B2A] tracking-[-0.6px]">
            Ready to get started?
          </h2>
          <p className="m-0 mx-auto mb-8 text-sm text-[#64748B] max-w-md">
            Create your free account and start analysing MRI scans in seconds.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-[#0D1B2A] text-white no-underline py-3 px-7 rounded-xl text-sm font-semibold hover:bg-[#1E3A5F] transition"
          >
            Create Account
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-[#E8EDF2] bg-white py-6 px-6 md:px-12 flex flex-wrap items-center justify-between gap-4 text-xs text-[#94A3B8]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-[7px] bg-gradient-to-br from-[#0EA472] to-[#059669] flex items-center justify-center">
            <Brain size={14} className="text-white" />
          </div>
          <span className="font-bold text-[#0D1B2A]">
            Neuro<span className="text-[#0EA472]">Sight</span>
          </span>
        </div>
        <p className="m-0">Built with TensorFlow · FastAPI · Next.js</p>
        <p className="m-0">For research purposes only · Not a certified medical device</p>
      </footer>
    </div>
  );
}