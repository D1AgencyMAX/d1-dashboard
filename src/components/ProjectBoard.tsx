"use client";

import { useState } from "react";

const sections = [
  {
    title: "1. The Trust Hero",
    description: "High-empathy search interface. Large typography: 'Care you can trust, right in your neighborhood.' Background: Warm, inclusive photography. Simple Category + Postcode input.",
    status: "Drafted",
    color: "border-l-blue-500"
  },
  {
    title: "2. Verification Badges",
    description: "Row of trust icons: 'NDIS Registered', 'ABN Verified', 'WWCC Checked'. Clicking each opens an explanation modal to build participant confidence.",
    status: "Components Ready",
    color: "border-l-green-500"
  },
  {
    title: "3. Smart Category Grid",
    description: "Icon-driven navigation for core NDIS services: Plan Management, Support Coordination, Allied Health, Community Access. High contrast for accessibility.",
    status: "Wireframed",
    color: "border-l-purple-500"
  },
  {
    title: "4. Featured Providers",
    description: "Premium horizontal cards showing: Provider Name, Rating, Capacity Status ('Taking Clients' badge), and primary service area.",
    status: "In Progress",
    color: "border-l-amber-500"
  },
  {
    title: "5. The Provider Profile",
    description: "Dual-column layout. Left: High-level stats, contact form, pricing guide. Right: Detailed service descriptions, experience, and verified reviews.",
    status: "Finalizing",
    color: "border-l-pink-500"
  }
];

export default function ProjectBoard() {
  const [activeTab, setActiveTab] = useState("Home");

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] bg-[var(--bg-secondary)]/30 flex items-center justify-between">
        <h2 className="text-sm font-bold text-[var(--text-primary)] font-mono flex items-center gap-2">
          <span className="text-blue-500">📐</span> PROJECT_PREVIEW: NDIS_CONNECT
        </h2>
        <div className="flex gap-2">
          {["Home", "Profile", "Mobile"].map(tab => (
            <button 
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`text-[9px] px-2 py-0.5 rounded border ${activeTab === tab ? 'bg-blue-500/20 border-blue-500 text-blue-400' : 'border-[var(--border)] text-[var(--text-secondary)]'}`}
            >
              {tab.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <div className="p-4 space-y-4">
        <p className="text-[10px] text-[var(--text-secondary)] font-mono uppercase tracking-widest">Aura's Design Pipeline:</p>
        <div className="space-y-3">
          {sections.map((s) => (
            <div key={s.title} className={`p-3 rounded-lg bg-[var(--bg-primary)]/40 border-l-4 ${s.color} border border-y-[var(--border)] border-r-[var(--border)]`}>
              <div className="flex justify-between items-start mb-1">
                <h3 className="text-xs font-bold text-[var(--text-primary)]">{s.title}</h3>
                <span className="text-[8px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">{s.status}</span>
              </div>
              <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">{s.description}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="p-4 border-t border-[var(--border)] bg-[var(--bg-secondary)]/10">
        <a 
          href="https://ndis-preview.vercel.app" 
          target="_blank"
          className="aspect-video bg-[#0a0a1a] rounded border border-[var(--border)] flex items-center justify-center flex-col gap-2 group cursor-pointer hover:border-blue-500/50 transition-all"
        >
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">🔗</div>
          <span className="text-[10px] font-mono text-blue-400 group-hover:underline uppercase">View Live Design Prototype</span>
        </a>
      </div>
    </div>
  );
}
