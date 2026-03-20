"use client";

import { ProviderBalance } from "@/lib/supabase";

export default function FinancialMonitor({ balances }: { balances: ProviderBalance[] }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden">
      <div className="p-4 border-b border-[var(--border)] flex items-center justify-between bg-[var(--bg-secondary)]/30">
        <h2 className="text-sm font-bold text-[var(--text-primary)] font-mono flex items-center gap-2">
          <span className="text-yellow-500">💰</span> PROVIDER_WALLETS
        </h2>
        <span className="text-[9px] font-mono text-[var(--text-secondary)]">AUTO_REFRESH</span>
      </div>
      <div className="p-4 space-y-3">
        {balances.map((b) => {
          const isLow = b.balance_usd <= b.alert_threshold && b.id !== 'google';
          return (
            <div key={b.id} className="space-y-1">
              <div className="flex items-center justify-between text-[11px] font-mono">
                <span className="text-[var(--text-secondary)]">{b.provider_name}</span>
                <span className={`font-bold ${isLow ? 'text-red-400 animate-pulse' : 'text-green-400'}`}>
                  ${Number(b.balance_usd).toFixed(2)}
                </span>
              </div>
              <div className="w-full h-1 bg-[var(--bg-primary)] rounded-full overflow-hidden border border-[var(--border)]">
                <div 
                  className={`h-full transition-all duration-1000 ${isLow ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'bg-green-500'}`}
                  style={{ width: b.id === 'google' ? '100%' : `${Math.min((Number(b.balance_usd) / (b.alert_threshold * 5)) * 100, 100)}%` }}
                />
              </div>
              {isLow && (
                <p className="text-[9px] text-red-500 font-bold tracking-tighter uppercase">⚠️ ACTION_REQUIRED: BALANCE_CRITICAL</p>
              )}
            </div>
          );
        })}
      </div>
      <div className="px-4 py-2 border-t border-[var(--border)] bg-[var(--bg-secondary)]/20 text-[9px] text-[var(--text-secondary)] font-mono flex justify-between">
        <span>LAST_CHECK: {balances.length > 0 ? new Date(balances[0].last_updated).toLocaleTimeString() : '--'}</span>
        <span>STATUS: MONITORING</span>
      </div>
    </div>
  );
}
