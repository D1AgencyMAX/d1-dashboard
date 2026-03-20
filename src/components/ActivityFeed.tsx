"use client";

import { ActivityItem } from "@/lib/supabase";
import { useEffect, useRef } from "react";

export default function ActivityFeed({ activities }: { activities: ActivityItem[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [activities]);

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[#05050a] overflow-hidden flex flex-col h-[400px]">
      <div className="p-3 border-b border-[var(--border)] bg-[var(--bg-card)] flex items-center justify-between">
        <h2 className="text-xs font-bold text-[var(--text-primary)] font-mono flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          AGENT_ACTIVITY_STREAM
        </h2>
        <span className="text-[10px] font-mono text-[var(--text-secondary)]">LIVE_FEED</span>
      </div>
      
      <div 
        ref={scrollRef}
        className="flex-1 p-4 font-mono text-[11px] overflow-y-auto space-y-1.5"
      >
        {activities.length === 0 ? (
          <div className="text-gray-600 animate-pulse">Initializing data stream...</div>
        ) : (
          activities.map((item) => (
            <div key={item.id} className="flex gap-3 leading-relaxed group">
              <span className="text-gray-600 shrink-0">
                [{new Date(item.created_at).toLocaleTimeString([], { hour12: false })}]
              </span>
              <div className="flex-1">
                <span className="text-blue-400 font-bold mr-2 uppercase">
                  {item.event_type.replace('_', ' ')}:
                </span>
                <span className="text-gray-300 group-hover:text-white transition-colors">
                  {item.title}
                </span>
                {item.description && (
                  <span className="text-gray-500 ml-2 italic">— {item.description}</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
      
      <div className="p-1.5 bg-[var(--bg-secondary)] border-t border-[var(--border)] text-[9px] font-mono text-gray-500 flex justify-between px-3">
        <span>STRM_ACTIVE: {activities.length} EVTS</span>
        <span className="animate-pulse">_CURSOR</span>
      </div>
    </div>
  );
}
