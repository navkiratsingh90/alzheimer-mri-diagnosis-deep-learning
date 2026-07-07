"use client";
import Link from 'next/link';
import React from 'react'
import { Mail, Brain, Activity, MessageSquare } from 'lucide-react';
const quickLinks = [
  { name: 'Home', href: '/' },
  { name: 'Upload MRI', href: '/upload' },
  { name: 'Clinical Chat', href: '/chat' },
  { name: 'About', href: '/about' },
];

const techStack = [
  'TensorFlow',
  'FastAPI',
  'Next.js',
  'LangChain',
  'Grad-CAM',
  'OASIS Dataset',
];

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gradient-to-r from-slate-900 to-slate-800 text-white">
      {/* Main footer content */}
      <div className="max-w-7xl mx-auto px-6 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10">
          {/* Brand column */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-blue-500 p-1.5 rounded-lg">
                <Brain className="w-5 h-5 text-white" />
			
              </div>
              <span className="font-bold text-xl">NeuroSight</span>
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              AI-powered Alzheimer's staging from MRI scans. Transparent, fast, and clinically relevant.
            </p>
            <div className="flex gap-3 mt-6">
              <a
                href="https://github.com/yourusername/neurosight"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-slate-700 hover:bg-slate-600 p-2 rounded-full transition-colors"
                aria-label="GitHub"
              >
                {/* <Github className="w-4 h-4" /> */}
              </a>
              <a
                href="#"
                className="bg-slate-700 hover:bg-slate-600 p-2 rounded-full transition-colors"
                aria-label="Twitter"
              >
                {/* <Twitter className="w-4 h-4" /> */}
              </a>
              <a
                href="#"
                className="bg-slate-700 hover:bg-slate-600 p-2 rounded-full transition-colors"
                aria-label="LinkedIn"
              >
                {/* <Linkedin className="w-4 h-4" /> */}
              </a>
              <a
                href="mailto:your.email@example.com"
                className="bg-slate-700 hover:bg-slate-600 p-2 rounded-full transition-colors"
                aria-label="Email"
              >
                <Mail className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              Quick Links
            </h3>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-slate-300 hover:text-white text-sm transition-colors"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Tech Stack */}
          <div>
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-400" />
              Tech Stack
            </h3>
            <div className="flex flex-wrap gap-2">
              {techStack.map((tech) => (
                <span
                  key={tech}
                  className="bg-slate-700/50 text-slate-300 text-xs px-2 py-1 rounded-md"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* CTA / Newsletter (optional) */}
          <div>
            <h3 className="font-semibold text-lg mb-4">Stay Updated</h3>
            <p className="text-slate-300 text-sm mb-3">
              Star on GitHub for latest releases.
            </p>
            <a
              href="https://github.com/yourusername/neurosight"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {/* <Github className="w-4 h-4" /> */}
              GitHub Repository
            </a>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700 mt-10 pt-6 text-center text-slate-400 text-sm">
          <p>© {currentYear} NeuroSight. Built for clinical AI research.</p>
          <p className="mt-1">
            OASIS dataset | EfficientNet-B4 | Grad-CAM | LangChain RAG
          </p>
        </div>
      </div>
    </footer>
  );
}