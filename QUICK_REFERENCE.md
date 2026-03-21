# ⚡ Quick Reference Card
**For developers implementing the D1 Dashboard redesign**

---

## 📦 Install Dependencies (Copy/Paste)

```bash
npm install framer-motion recharts lucide-react react-countup date-fns clsx zustand
```

---

## 🗄️ Run Database Migration

1. Open Supabase SQL Editor
2. Copy/paste `supabase-migration.sql`
3. Click "Run"
4. Done! ✅

---

## 🎨 Glassmorphism Template

```tsx
// components/ui/GlassCard.tsx
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
}

export default function GlassCard({ children, className = "" }: GlassCardProps) {
  return (
    <div className={`
      bg-white/5 backdrop-blur-md backdrop-saturate-[180%]
      border border-white/10 rounded-xl
      shadow-[0_8px_32px_rgba(0,0,0,0.37)]
      ${className}
    `}>
      {children}
    </div>
  );
}
```

---

## 🎬 Animation Presets (Copy/Paste)

```typescript
// lib/animations.ts
export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 }
};

export const slideUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 }
};

export const bounceIn = {
  initial: { scale: 0 },
  animate: { scale: 1 },
  transition: { type: 'spring', stiffness: 400, damping: 15 }
};

export const spring = {
  type: 'spring',
  stiffness: 300,
  damping: 30
};
```

---

## 🔢 Animated Number Component

```tsx
// components/ui/AnimatedNumber.tsx
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface AnimatedNumberProps {
  value: number;
  format?: 'currency' | 'number' | 'percent';
  decimals?: number;
}

export default function AnimatedNumber({ 
  value, 
  format = 'number',
  decimals = 0 
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    let start = displayValue;
    let end = value;
    let startTime: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / 1000, 1);
      const current = start + (end - start) * progress;
      setDisplayValue(current);
      
      if (progress < 1) requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [value]);

  const formatValue = (val: number) => {
    if (format === 'currency') return `$${val.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
    if (format === 'percent') return `${val.toFixed(decimals)}%`;
    return val.toFixed(decimals);
  };

  return (
    <motion.span
      key={value}
      initial={{ scale: 1.2, color: '#22c55e' }}
      animate={{ scale: 1, color: 'inherit' }}
      transition={{ duration: 0.3 }}
    >
      {formatValue(displayValue)}
    </motion.span>
  );
}
```

---

## 📊 Recharts Line Chart Template

```tsx
// components/charts/LineChart.tsx
import { LineChart as RechartsLine, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface LineChartProps {
  data: Array<{ label: string; value: number }>;
  color?: string;
}

export default function LineChart({ data, color = '#4f8fff' }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <RechartsLine data={data}>
        <defs>
          <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.8} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis 
          dataKey="label" 
          stroke="#8888aa" 
          fontSize={10}
        />
        <YAxis 
          stroke="#8888aa" 
          fontSize={10}
        />
        <Tooltip 
          contentStyle={{ 
            background: 'rgba(26, 26, 46, 0.9)', 
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '8px'
          }}
        />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke={color} 
          strokeWidth={2}
          fill="url(#lineGradient)"
          dot={false}
        />
      </RechartsLine>
    </ResponsiveContainer>
  );
}
```

---

## 🔴 Status Dot Component

```tsx
// components/ui/StatusDot.tsx
interface StatusDotProps {
  status: 'active' | 'idle' | 'error' | 'warning';
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function StatusDot({ status, pulse = false, size = 'md' }: StatusDotProps) {
  const colors = {
    active: 'bg-green-500',
    idle: 'bg-yellow-500',
    error: 'bg-red-500',
    warning: 'bg-orange-500'
  };

  const sizes = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  };

  return (
    <div className={`
      ${sizes[size]} 
      ${colors[status]} 
      rounded-full 
      ${pulse ? 'animate-pulse' : ''}
    `} />
  );
}
```

---

## 📈 Trend Indicator Component

```tsx
// components/ui/TrendIndicator.tsx
import { TrendingUp, TrendingDown } from 'lucide-react';

interface TrendIndicatorProps {
  value: number;
  format?: 'percent' | 'number';
}

export default function TrendIndicator({ value, format = 'percent' }: TrendIndicatorProps) {
  const isPositive = value >= 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const color = isPositive ? 'text-green-500' : 'text-red-500';
  
  const formatValue = (val: number) => {
    const abs = Math.abs(val);
    return format === 'percent' ? `${abs.toFixed(1)}%` : abs.toFixed(0);
  };

  return (
    <div className={`flex items-center gap-1 text-sm ${color}`}>
      <Icon size={14} />
      <span>{formatValue(value)}</span>
    </div>
  );
}
```

---

## 🔌 Supabase Realtime Hook

```typescript
// hooks/useRealtimeData.ts
import { useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { RealtimeChannel } from '@supabase/supabase-js';

export function useRealtimeData<T>(
  table: string,
  onUpdate: (data: T) => void
) {
  useEffect(() => {
    const channel: RealtimeChannel = supabase
      .channel(`${table}-realtime`)
      .on('postgres_changes', 
          { event: '*', schema: 'public', table },
          (payload) => onUpdate(payload.new as T)
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [table, onUpdate]);
}

// Usage:
// useRealtimeData<Campaign>('campaigns', (campaign) => {
//   setCampaigns(prev => prev.map(c => c.id === campaign.id ? campaign : c));
// });
```

---

## 🎨 Tailwind Utility Classes

Add to `globals.css`:

```css
/* Glassmorphism */
.glass {
  @apply bg-white/5 backdrop-blur-md backdrop-saturate-[180%] 
         border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.37)];
}

.glass-strong {
  @apply bg-white/8 backdrop-blur-lg backdrop-saturate-[200%] 
         border border-white/15;
}

/* Hover lift */
.hover-lift {
  @apply transition-transform hover:-translate-y-1 hover:shadow-lg;
}

/* Pulse glow */
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(79, 143, 255, 0.4); }
  50% { box-shadow: 0 0 12px 4px rgba(79, 143, 255, 0.15); }
}

.pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* Shimmer loading */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.shimmer {
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

---

## 🛠️ Utility Functions

```typescript
// lib/utils.ts
export const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0
  }).format(value);
};

export const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(1)}%`;
};

export const formatCompact = (value: number) => {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toString();
};

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    active: 'green',
    working: 'blue',
    idle: 'yellow',
    error: 'red',
    paused: 'gray'
  };
  return colors[status] || 'gray';
};

export const formatRelativeTime = (date: Date) => {
  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return 'just now';
};
```

---

## 🚀 Component Starter Template

```tsx
// components/dashboard/ExampleComponent.tsx
'use client';

import { motion } from 'framer-motion';
import GlassCard from '@/components/ui/GlassCard';
import AnimatedNumber from '@/components/ui/AnimatedNumber';
import { fadeIn } from '@/lib/animations';

interface ExampleComponentProps {
  data: any;
  loading?: boolean;
}

export default function ExampleComponent({ 
  data, 
  loading = false 
}: ExampleComponentProps) {
  if (loading) {
    return (
      <GlassCard className="p-6 animate-pulse">
        <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
        <div className="h-12 bg-white/10 rounded"></div>
      </GlassCard>
    );
  }

  return (
    <motion.div {...fadeIn}>
      <GlassCard className="p-6 hover-lift">
        <h3 className="text-sm text-gray-400 mb-2">EXAMPLE METRIC</h3>
        <div className="text-3xl font-bold">
          <AnimatedNumber value={data.value} format="currency" />
        </div>
      </GlassCard>
    </motion.div>
  );
}
```

---

## 🐛 Debugging Checklist

### Supabase Not Updating?
1. Check realtime is enabled: `ALTER PUBLICATION supabase_realtime ADD TABLE your_table;`
2. Verify subscription in browser console
3. Test manual insert in SQL Editor

### Animations Laggy?
1. Reduce particle counts (12 → 6)
2. Use CSS animations instead of Framer Motion for simple cases
3. Add `will-change: transform` to animated elements
4. Check for unnecessary re-renders (React DevTools)

### Types Not Working?
1. Ensure types match Supabase schema exactly
2. Use `.returns<YourType[]>()` on Supabase queries
3. Run `tsc --noEmit` to check for type errors

### Bundle Too Large?
1. Lazy load heavy components: `const Chart = lazy(() => import('./Chart'))`
2. Use dynamic imports for charts: `import('recharts').then(...)`
3. Tree-shake unused Lucide icons

---

## 📊 Performance Budget

| Metric | Target | Current |
|--------|--------|---------|
| Initial JS | < 200KB | TBD |
| Page Load | < 2s | TBD |
| FCP | < 1s | TBD |
| TTI | < 3s | TBD |
| Lighthouse | > 90 | TBD |

Run: `npm run build && npm run start` then Lighthouse audit

---

## 🎯 Implementation Priority

**Week 1:**
1. GlassCard ← Start here!
2. AnimatedNumber
3. StatusDot
4. RevenueCounter

**Week 2:**
1. LineChart wrapper
2. ClientPipelineFunnel
3. CampaignDashboard
4. LeadFlowLive

**Week 3:**
1. ProfitMarginTracker
2. TeamCapacityHeatmap
3. RevenueProjection
4. AlertFeed

**Week 4:**
1. QuickActionsBar
2. Responsive polish
3. Accessibility
4. Deploy 🚀

---

## 📚 Documentation Quick Links

- Full Spec: `REDESIGN_SPEC.md`
- Component Structure: `COMPONENT_STRUCTURE.md`
- Database: `supabase-migration.sql`
- Types: `TYPESCRIPT_TYPES.ts`
- Visuals: `VISUAL_MOCKUP.md`

---

## 💡 Pro Tips

1. **Build incrementally** — Don't try to do everything at once
2. **Test realtime early** — Make sure Supabase subscriptions work
3. **Use React DevTools** — Identify unnecessary re-renders
4. **Respect prefers-reduced-motion** — Not everyone wants animations
5. **Mobile first** — Design responsive from the start
6. **Ask for help** — Delegate to Atlas (code) or Aura (design) as needed

---

## 🔥 One-Liner Snippets

### Format currency
```ts
const fmt = (n: number) => `$${n.toLocaleString()}`;
```

### Debounce hook
```ts
const useDebounce = (value: any, delay: number) => {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debounced;
};
```

### Conditional class
```ts
import clsx from 'clsx';
className={clsx('base-class', { 'active': isActive, 'disabled': !enabled })}
```

---

**Keep this file open while coding. Good luck! 🚀**

*— Aura*
