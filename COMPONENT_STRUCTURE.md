# 🏗️ Component Structure Plan
**Dashboard Redesign Implementation Guide**

---

## 📁 File Structure

```
src/
├── app/
│   ├── layout.tsx (existing)
│   ├── page.tsx (main dashboard — refactor)
│   └── globals.css (update with new utilities)
│
├── components/
│   ├── dashboard/
│   │   ├── RevenueCounter.tsx          ⭐ NEW
│   │   ├── ClientPipelineFunnel.tsx    ⭐ NEW
│   │   ├── CampaignDashboard.tsx       ⭐ NEW
│   │   ├── TeamCapacityHeatmap.tsx     ⭐ NEW
│   │   ├── ProfitMarginTracker.tsx     ⭐ NEW
│   │   ├── AIWorkerStatus.tsx          🔄 ENHANCE (existing AgentGrid)
│   │   ├── LeadFlowLive.tsx            ⭐ NEW
│   │   ├── RevenueProjection.tsx       ⭐ NEW
│   │   ├── AlertFeed.tsx               🔄 ENHANCE (existing ActivityFeed)
│   │   └── QuickActionsBar.tsx         ⭐ NEW
│   │
│   ├── charts/
│   │   ├── LineChart.tsx               ⭐ NEW (Recharts wrapper)
│   │   ├── BarChart.tsx                ⭐ NEW
│   │   ├── Sparkline.tsx               ⭐ NEW
│   │   └── FunnelChart.tsx             ⭐ NEW
│   │
│   ├── ui/
│   │   ├── GlassCard.tsx               ⭐ NEW (reusable glass component)
│   │   ├── StatusDot.tsx               ⭐ NEW
│   │   ├── TrendIndicator.tsx          ⭐ NEW
│   │   ├── AnimatedNumber.tsx          ⭐ NEW
│   │   └── LoadingSkeleton.tsx         ⭐ NEW
│   │
│   ├── StatusBar.tsx (existing — enhance)
│   ├── BusinessMetricsPanel.tsx (existing — enhance)
│   └── ... (keep other existing components)
│
├── lib/
│   ├── supabase.ts (existing — add new types)
│   ├── animations.ts                   ⭐ NEW (Framer Motion presets)
│   ├── utils.ts                        ⭐ NEW (formatters, calculations)
│   └── forecasting.ts                  ⭐ NEW (revenue projection logic)
│
└── hooks/
    ├── useRealtimeData.ts              ⭐ NEW (WebSocket hook)
    ├── useDebounce.ts                  ⭐ NEW
    └── useMediaQuery.ts                ⭐ NEW (responsive)
```

---

## 🧩 Component Breakdown

### 1. **RevenueCounter**
**Props:**
```typescript
interface RevenueCounterProps {
  value: number;           // Current revenue
  target?: number;         // Monthly target (optional)
  trend24h?: number[];     // Sparkline data
  currency?: string;       // Default: 'USD'
}
```

**Dependencies:**
- `react-countup` (number animation)
- `framer-motion` (particle effects)
- Custom `Sparkline` component

**Files:**
- `components/dashboard/RevenueCounter.tsx`
- `components/charts/Sparkline.tsx`

---

### 2. **ClientPipelineFunnel**
**Props:**
```typescript
interface PipelineStage {
  stage: 'discovery' | 'qualified' | 'proposal' | 'won';
  count: number;
  value: number;
  clients: Array<{ name: string; value: number }>;
  conversionRate?: number;
}

interface ClientPipelineFunnelProps {
  stages: PipelineStage[];
  onStageClick?: (stage: string) => void;
}
```

**Dependencies:**
- `framer-motion` (3D animations, particle flow)
- CSS 3D transforms
- Optional: `three.js` if we want camera control

**Files:**
- `components/dashboard/ClientPipelineFunnel.tsx`
- `components/ui/FunnelStage.tsx` (individual stage card)

---

### 3. **CampaignDashboard**
**Props:**
```typescript
interface Campaign {
  id: string;
  platform: 'meta' | 'google' | 'tiktok';
  name: string;
  status: 'active' | 'paused' | 'completed';
  spend: number;
  budget: number;
  impressions: number;
  clicks: number;
  ctr: number;
  roas: number;
  targetRoas: number;
  trend7d: number[];
}

interface CampaignDashboardProps {
  campaigns: Campaign[];
  onCampaignClick?: (id: string) => void;
}
```

**Dependencies:**
- `framer-motion` (card animations)
- `Sparkline` component
- `TrendIndicator` component
- Platform icons (custom SVG or emojis)

**Files:**
- `components/dashboard/CampaignDashboard.tsx`
- `components/ui/CampaignCard.tsx`

---

### 4. **TeamCapacityHeatmap**
**Props:**
```typescript
interface AgentCapacity {
  agentId: string;
  agentName: string;
  dailyCapacity: Array<{
    date: Date;
    projectCount: number;
    status: 'available' | 'busy' | 'overloaded';
    projects: string[];
  }>;
}

interface TeamCapacityHeatmapProps {
  agents: AgentCapacity[];
  weekStartDate?: Date;
}
```

**Dependencies:**
- `date-fns` (date calculations)
- `framer-motion` (cell animations)
- Tooltip component (could use Radix UI or build custom)

**Files:**
- `components/dashboard/TeamCapacityHeatmap.tsx`
- `components/ui/HeatmapCell.tsx`

---

### 5. **ProfitMarginTracker**
**Props:**
```typescript
interface ClientProfit {
  clientId: string;
  clientName: string;
  revenue: number;
  costs: {
    labor: number;
    tools: number;
    ads: number;
  };
  profit: number;
  margin: number;
}

interface ProfitMarginTrackerProps {
  clients: ClientProfit[];
  expandedClientId?: string;
  onClientClick?: (id: string) => void;
}
```

**Dependencies:**
- `framer-motion` (expand/collapse animation)
- `BarChart` component (horizontal)

**Files:**
- `components/dashboard/ProfitMarginTracker.tsx`
- `components/charts/BarChart.tsx`

---

### 6. **AIWorkerStatus** (Enhanced AgentGrid)
**Props:**
```typescript
interface Agent {
  id: string;
  name: string;
  status: 'working' | 'idle' | 'error';
  currentTask?: string;
  lastHeartbeat?: Date;
  tasksCompleted: number;
  tokensUsed: number;
  costUsd: number;
}

interface AIWorkerStatusProps {
  agents: Agent[];
  fleetHealth: number; // 0-100%
  avgLoad: number;
}
```

**Dependencies:**
- `framer-motion` (pulse animations)
- `StatusDot` component

**Files:**
- `components/dashboard/AIWorkerStatus.tsx` (replaces/enhances AgentGrid)
- `components/ui/StatusDot.tsx`

---

### 7. **LeadFlowLive**
**Props:**
```typescript
interface LeadFlowMetrics {
  leadsToday: number;
  callsToday: number;
  consultationsToday: number;
  closesToday: number;
  leadToCallRate: number;
  callToConsultationRate: number;
  consultationToCloseRate: number;
  hourlyData: Array<{
    hour: Date;
    leads: number;
    calls: number;
    consultations: number;
    closes: number;
  }>;
}

interface LeadFlowLiveProps {
  metrics: LeadFlowMetrics;
}
```

**Dependencies:**
- `recharts` (line chart)
- `framer-motion` (flow arrows, celebration on close)
- `AnimatedNumber` component

**Files:**
- `components/dashboard/LeadFlowLive.tsx`
- `components/charts/LineChart.tsx`

---

### 8. **RevenueProjection**
**Props:**
```typescript
interface RevenueDataPoint {
  month: Date;
  actual?: number;
  projected?: number;
  confidenceHigh?: number;
  confidenceLow?: number;
}

interface RevenueProjectionProps {
  data: RevenueDataPoint[];
  target?: number;
  thisMonthRevenue: number;
  thisMonthProjection: number;
  nextMonthProjection: number;
}
```

**Dependencies:**
- `recharts` (area chart with confidence bands)
- `date-fns` (date formatting)
- `lib/forecasting.ts` (projection logic)

**Files:**
- `components/dashboard/RevenueProjection.tsx`
- `lib/forecasting.ts`

---

### 9. **AlertFeed** (Enhanced ActivityFeed)
**Props:**
```typescript
interface Alert {
  id: string;
  type: 'urgent' | 'warning' | 'info';
  title: string;
  description?: string;
  createdAt: Date;
  assignedTo?: string;
  actionUrl?: string;
  dismissed: boolean;
}

interface AlertFeedProps {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
  onAlertClick?: (alert: Alert) => void;
}
```

**Dependencies:**
- `framer-motion` (slide-in animations)
- Optional: browser Notification API for sound

**Files:**
- `components/dashboard/AlertFeed.tsx` (enhance existing ActivityFeed)
- `components/ui/AlertItem.tsx`

---

### 10. **QuickActionsBar**
**Props:**
```typescript
interface Action {
  id: string;
  label: string;
  icon: ReactNode;
  onClick: () => void;
  shortcut?: string;
}

interface QuickActionsBarProps {
  actions: Action[];
  position?: 'bottom-right' | 'bottom-left';
}
```

**Dependencies:**
- `framer-motion` (fab fan-out animation)
- `lucide-react` (icons)
- Portal/Modal component for action forms

**Files:**
- `components/dashboard/QuickActionsBar.tsx`
- `components/modals/CampaignWizard.tsx` (for "Launch Campaign" action)
- `components/modals/AddClientForm.tsx`

---

## 🎨 Reusable UI Components

### **GlassCard**
```typescript
interface GlassCardProps {
  children: ReactNode;
  variant?: 'default' | 'strong';
  hover?: boolean;
  className?: string;
}
```
Glassmorphic card with backdrop blur

---

### **StatusDot**
```typescript
interface StatusDotProps {
  status: 'active' | 'idle' | 'error' | 'warning';
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}
```
Colored dot with optional pulse animation

---

### **TrendIndicator**
```typescript
interface TrendIndicatorProps {
  value: number;
  format?: 'percent' | 'number';
  showIcon?: boolean;
}
```
Arrow + percentage (↑ 12% or ↓ 5%)

---

### **AnimatedNumber**
```typescript
interface AnimatedNumberProps {
  value: number;
  format?: 'currency' | 'number' | 'percent';
  decimals?: number;
  duration?: number;
}
```
Uses react-countup + Framer Motion for smooth number transitions

---

### **LoadingSkeleton**
```typescript
interface LoadingSkeletonProps {
  variant: 'card' | 'text' | 'chart';
  count?: number;
}
```
Shimmer loading state

---

## 🔄 Data Flow

### Supabase → React State
```
Supabase Realtime (WebSocket)
    ↓
useRealtimeData hook
    ↓
React state (via useState/useReducer)
    ↓
Components
```

### Example: `useRealtimeData` Hook
```typescript
function useRealtimeData<T>(
  table: string,
  onUpdate: (data: T) => void
) {
  useEffect(() => {
    const channel = supabase
      .channel(`${table}-realtime`)
      .on('postgres_changes', 
          { event: '*', schema: 'public', table },
          (payload) => onUpdate(payload.new as T)
      )
      .subscribe();
    
    return () => supabase.removeChannel(channel);
  }, [table, onUpdate]);
}
```

---

## 🎬 Animation Library

### `lib/animations.ts`
```typescript
import { Variants } from 'framer-motion';

export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },
  
  scaleIn: {
    initial: { scale: 0.8, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0.8, opacity: 0 }
  },
  
  staggerChildren: {
    animate: {
      transition: {
        staggerChildren: 0.1
      }
    }
  }
};

export const springs = {
  smooth: { type: 'spring', stiffness: 300, damping: 30 },
  bouncy: { type: 'spring', stiffness: 400, damping: 15 },
  slow: { type: 'spring', stiffness: 100, damping: 10 }
};
```

---

## 🛠️ Utilities

### `lib/utils.ts`
```typescript
// Number formatting
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

export const formatPercent = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`;
};

export const formatCompact = (value: number): string => {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toString();
};

// Color utilities
export const getStatusColor = (status: string): string => {
  const colors = {
    active: 'green',
    working: 'blue',
    idle: 'yellow',
    error: 'red',
    paused: 'gray'
  };
  return colors[status] || 'gray';
};

export const getMarginColor = (margin: number): string => {
  if (margin >= 0.6) return 'green';
  if (margin >= 0.4) return 'yellow';
  return 'red';
};

// Date utilities
import { formatDistanceToNow, format } from 'date-fns';

export const formatRelativeTime = (date: Date): string => {
  return formatDistanceToNow(date, { addSuffix: true });
};

export const formatShortDate = (date: Date): string => {
  return format(date, 'MMM d');
};
```

---

## 📋 Implementation Priority

### **Week 1: Foundation**
1. Install dependencies
2. Create Supabase tables
3. Build UI primitives (GlassCard, StatusDot, AnimatedNumber)
4. Set up animation library
5. Build RevenueCounter (flagship component)

### **Week 2: Core Visualizations**
1. ClientPipelineFunnel
2. CampaignDashboard
3. LeadFlowLive
4. AIWorkerStatus (enhance existing)

### **Week 3: Analytics & Insights**
1. ProfitMarginTracker
2. RevenueProjection (with forecasting)
3. TeamCapacityHeatmap
4. AlertFeed (enhance existing)

### **Week 4: Polish & Launch**
1. QuickActionsBar
2. Responsive design
3. Accessibility audit
4. Performance optimization
5. User testing

---

## 🧪 Testing Checklist

### Unit Tests (Vitest)
- [ ] `formatCurrency` handles edge cases
- [ ] `getMarginColor` returns correct colors
- [ ] Animation configs are valid
- [ ] Chart data transformations work

### Component Tests (Testing Library)
- [ ] RevenueCounter counts up correctly
- [ ] PipelineFunnel expands on click
- [ ] AlertFeed dismisses items
- [ ] QuickActionsBar toggles open/closed

### Integration Tests
- [ ] Supabase realtime updates trigger re-renders
- [ ] Campaign data fetches correctly
- [ ] Revenue projections calculate accurately

### Visual Tests (Chromatic)
- [ ] Components match design spec
- [ ] Animations don't break layout
- [ ] Responsive breakpoints work

### Accessibility Tests (Axe)
- [ ] No ARIA violations
- [ ] Keyboard navigation works
- [ ] Color contrast passes

---

## 🚀 Deployment

### Pre-Deploy Checklist
- [ ] All TypeScript errors resolved
- [ ] No console warnings in production
- [ ] Bundle size < 200KB (initial)
- [ ] Lighthouse score > 90
- [ ] All Supabase tables created
- [ ] Environment variables set

### Vercel Deploy
```bash
# Install dependencies
npm install

# Build
npm run build

# Deploy
vercel --prod
```

---

## 🎯 Success Criteria

**User Experience:**
- Dashboard loads in < 2 seconds
- Animations run at 60fps
- Real-time updates feel instant
- No layout shift during load

**Developer Experience:**
- Components are reusable
- TypeScript types are strict
- Code is well-documented
- Easy to add new metrics

**Business Impact:**
- Ken uses dashboard daily
- Clients are impressed in demos
- Issues are spotted faster
- Team capacity is clearer

---

**Ready to build? Let's go! 🚀**

*— Aura*
