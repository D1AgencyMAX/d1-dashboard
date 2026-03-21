# 🎨 D1 Agency Control Center — Design Specification
**Designer:** Aura (AI/UX)  
**Date:** 2026-03-21  
**Status:** Ready for Implementation

---

## 🎯 Vision

Transform the D1 dashboard from a *static metrics display* into a **living, breathing control center** that makes you *feel* the agency's pulse. Think NASA mission control meets Cyberpunk 2077 meets Bloomberg Terminal.

### Core Principles
1. **LIVELY** — Every metric tells a story through motion
2. **INTELLIGENT** — Data visualizations that reveal insights, not just numbers
3. **CINEMATIC** — Glassmorphism, depth, and visual drama
4. **PURPOSEFUL** — Every animation has intent; no decoration without function

---

## 🧱 Component Architecture

### Layout Structure
```
┌─────────────────────────────────────────────────────┐
│  StatusBar (sticky)                                 │
│  ┌───────────────────────────────────────────────┐ │
│  │ Real-time Revenue Counter | Alert Feed        │ │
│  └───────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│  Hero KPI Grid (4 cols)                             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ MRR  │ │ Pipe │ │ Leads│ │ Margin│              │
│  └──────┘ └──────┘ └──────┘ └──────┘              │
├─────────────────────────────────────────────────────┤
│  Client Pipeline Funnel (3D visualization)          │
│  [Leads → Qualified → Proposal → Won]               │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────┬───────────────────────┐   │
│  │ Campaign Dashboard  │  Team Heatmap         │   │
│  │ (Meta/Google Ads)   │  (Capacity Grid)      │   │
│  └─────────────────────┴───────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────┬───────────────────────┐   │
│  │ AI Workers Status   │  Lead Flow Live       │   │
│  │ (14 OpenClaw nodes) │  (Real-time graph)    │   │
│  └─────────────────────┴───────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────┬───────────────────────┐   │
│  │ Profit Tracker      │  Revenue Projection   │   │
│  │ (Per-client drill)  │  (Trend + Forecast)   │   │
│  └─────────────────────┴───────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Quick Actions Command Bar (floating bottom)        │
│  [Launch Campaign][Add Client][Generate Report]     │
└─────────────────────────────────────────────────────┘
```

---

## 📦 New/Enhanced Components

### 1. **RevenueCounter** (Hero Component)
**Location:** Top-right of StatusBar  
**Visual:** Large, animated number with particle effects  

**Features:**
- Counts up in real-time using `react-countup` or custom spring animation
- Trailing particle effects when value increases (canvas or CSS particles)
- Glow effect pulses on revenue events
- Mini sparkline graph behind the number showing 24h trend
- Format: `$127,450` with fractional animation

**Animation Spec:**
```typescript
// Framer Motion spring config
const spring = {
  type: "spring",
  stiffness: 100,
  damping: 10,
  mass: 0.5
}

// Particle burst on increment
onIncrement: () => {
  // Spawn 8-12 particles
  // Color: from green-400 to transparent
  // Duration: 1.2s
  // Direction: radial outward
}
```

**Data Requirements:**
- `business_metrics.revenue_total` (live updates via Supabase realtime)
- `business_metrics.revenue_today` (for 24h sparkline)

---

### 2. **ClientPipelineFunnel** (3D Interactive Funnel)
**Location:** Full-width section below KPIs  
**Visual:** Isometric 3D funnel with glassmorphic stages  

**Design:**
```
   ┌─────────────────────┐  200 Leads
   │    DISCOVERY        │  (Dark blue glass)
   └──────────┬──────────┘
        ▼
      ┌──────────────────┐  80 Qualified
      │   QUALIFIED      │  (Blue glass)
      └────────┬─────────┘
           ▼
         ┌────────────┐  25 Proposals
         │ PROPOSAL   │  (Purple glass)
         └─────┬──────┘
            ▼
          ┌──────┐  8 Won
          │ WON  │  (Green glass)
          └──────┘
```

**Features:**
- Each stage is a glassmorphic 3D card (`transform: perspective(1000px) rotateX(20deg)`)
- Animated flow particles moving between stages
- Click stage → expand to show actual clients in that stage
- Conversion rate % shown on connecting arrows
- Color shifts based on health (green = good conversion, red = bottleneck)

**Micro-interactions:**
- Hover stage → lift up (`translateY(-8px)`) + increase glow
- Stages "breathe" with subtle scale animation (0.98 → 1.0 loop)

**Data Requirements:**
```typescript
interface PipelineData {
  stage: 'discovery' | 'qualified' | 'proposal' | 'won';
  count: number;
  value_usd: number;
  clients: Array<{
    name: string;
    entered_at: Date;
    expected_close_date?: Date;
  }>;
  conversion_rate: number; // from previous stage
}
```

**Tech:**
- CSS 3D transforms or Three.js (if we want true 3D camera control)
- Framer Motion for stage animations
- Canvas for particle flow

---

### 3. **CampaignDashboard** (Live Ad Performance)
**Location:** Left column, mid-page  
**Visual:** Grid of campaign cards with real-time metrics  

**Card Design:**
```
┌─────────────────────────────────────┐
│ 🔵 META  Summer Sale — Active       │
│ ────────────────────────────────    │
│  💰 Spend: $1,240 / $2,000          │
│  👁  Impressions: 45.2K ↑ 12%       │
│  🎯 CTR: 2.8% ↑ 0.4%                │
│  💵 ROAS: 4.2x ⚠️ (Target: 5x)      │
│ ────────────────────────────────    │
│  [View Details] [Pause] [Optimize]  │
└─────────────────────────────────────┘
```

**Features:**
- Platform badge (Meta = blue, Google = multi-color, TikTok = pink)
- Live metrics update every 5s
- Trend indicators (↑/↓ with percentage change)
- Alert badges for underperforming campaigns (⚠️ if ROAS < target)
- Mini line chart showing 7-day trend below each metric
- Glassmorphic card with colored border matching platform

**Animations:**
- Numbers count up on data update
- Trend arrows bounce in
- Alert badges pulse
- Hover → card lifts and shows detailed breakdown

**Data Requirements:**
```typescript
interface Campaign {
  id: string;
  platform: 'meta' | 'google' | 'tiktok';
  name: string;
  status: 'active' | 'paused' | 'completed';
  spend_usd: number;
  budget_usd: number;
  impressions: number;
  clicks: number;
  ctr: number;
  roas: number;
  target_roas: number;
  trend_7d: number[]; // daily ROAS for sparkline
  last_updated: Date;
}
```

---

### 4. **TeamCapacityHeatmap** (Who's Working on What)
**Location:** Right column, mid-page  
**Visual:** Calendar-style heatmap grid  

**Design:**
```
        Mon   Tue   Wed   Thu   Fri
Atlas   🟢🟢  🟡🟢  🟢🟢  🟢    🔴
Nova    🟢    🟢🟢  🟢    🟢🟢  🟢
Aura    🟡    🟢    🟢🟡  🟢    🟢🟢
Blaze   🟢🟢  🔴    🟢🟢  🟢🟢  🟢
...

Legend:
🟢 = Available (1-2 projects)
🟡 = Busy (3-4 projects)
🔴 = Overloaded (5+ projects)
```

**Features:**
- Each cell represents agent capacity for that day
- Tooltip on hover shows actual project names
- Color intensity = workload density
- Smooth gradient transitions between states
- Click agent name → filter to show their projects only
- Week navigation arrows (← prev / next →)

**Micro-interactions:**
- Cells pulse when agent picks up new task (real-time)
- Hover cell → pop up with project list
- Gradient animation flows across busy days

**Data Requirements:**
```typescript
interface AgentCapacity {
  agent_id: string;
  agent_name: string;
  date: Date;
  project_count: number;
  projects: Array<{
    name: string;
    client: string;
    deadline: Date;
  }>;
  status: 'available' | 'busy' | 'overloaded';
}
```

---

### 5. **ProfitMarginTracker** (Per-Client Breakdown)
**Location:** Left column, lower section  
**Visual:** Stacked bar chart with drill-down  

**Design:**
```
Client A  ████████████████ 78% margin ($12.5K)
Client B  ██████████       62% margin ($8.2K)
Client C  ████████████████████ 85% margin ($15K)
Client D  ████             35% margin ($2.1K) ⚠️
```

**Features:**
- Horizontal bars sorted by margin % (descending)
- Color gradient: Red (0-40%) → Yellow (40-60%) → Green (60%+)
- Click bar → expand to show cost breakdown (labor, tools, ads)
- Alert badge for margins < 40%
- Total profit shown at top

**Drill-down View:**
```
Client D — $2.1K profit (35% margin)
────────────────────────────────────
Revenue:     $6,000
Costs:       $3,900
  ├─ Labor:    $2,800 (Atlas, Nova, Aura)
  ├─ Tools:    $400 (Supabase, Vercel, APIs)
  └─ Ads:      $700 (Meta campaigns)
Profit:      $2,100
────────────────────────────────────
```

**Data Requirements:**
```typescript
interface ClientProfit {
  client_id: string;
  client_name: string;
  revenue_usd: number;
  costs: {
    labor_usd: number;
    tools_usd: number;
    ads_usd: number;
  };
  profit_usd: number;
  margin_percent: number;
}
```

---

### 6. **AIWorkerStatus** (14 OpenClaw Instances)
**Location:** Left column, above fold  
**Visual:** Grid of glowing agent nodes with live status  

**Design:**
```
┌───────────────────────────────────────┐
│  AI WORKER FLEET — 14 Active Nodes    │
│  ────────────────────────────────────  │
│  🟢 Atlas      ⚡ Building API         │
│  🟢 Nova       🎨 Designing UI         │
│  🟡 Aura       💤 Idle (2m)            │
│  🟢 Blaze      📊 Optimizing ads       │
│  🟢 Forge      🔧 DB migration         │
│  🔴 Synapse    ⚠️ Error (retrying...)  │
│  ... (+ 8 more)                        │
│  ────────────────────────────────────  │
│  Fleet Health: 85% | Avg Load: 3.2    │
└───────────────────────────────────────┘
```

**Features:**
- Real-time status updates via Socket.io
- Color-coded dots: Green (working), Yellow (idle), Red (error)
- Current task shown next to each agent
- Click agent → view detailed logs/activity
- Fleet health bar at bottom
- Particle effects around active agents

**Animations:**
- Status dots pulse at different rates based on activity
- Task text scrolls if too long (marquee effect)
- Error agents flash red
- Idle agents fade opacity to 70%

**Data Requirements:**
- Already in `agents` table! Just need live updates via Supabase realtime
- Consider adding `last_heartbeat` timestamp to show connectivity

---

### 7. **LeadFlowLive** (Real-time Lead → Close Tracker)
**Location:** Right column, mid-page  
**Visual:** Animated flow diagram + live graph  

**Design:**
```
┌──────────────────────────────────────────┐
│  LEAD FLOW — Last 24 Hours               │
│  ──────────────────────────────────────  │
│                                           │
│   📥 New Leads                            │
│      ↓ (47 today)                         │
│   ☎️ Calls Booked                         │
│      ↓ (18 today | 38% conversion)       │
│   🤝 Consultations                        │
│      ↓ (12 today | 67% show rate)        │
│   ✅ Closed Deals                         │
│      ↓ (3 today | 25% close rate)        │
│                                           │
│  ──────────────────────────────────────  │
│  📈 [Live graph showing hourly flow]     │
└──────────────────────────────────────────┘
```

**Features:**
- Animated arrows flow between stages (CSS animation or Canvas)
- Numbers count up in real-time when new leads arrive
- Conversion rate % updates dynamically
- Color shifts based on performance (green = good, yellow = okay, red = poor)
- Live line graph at bottom showing hourly lead volume (Recharts or Chart.js)
- Sparkles/particles when a deal closes

**Graph Spec:**
- X-axis: Last 24 hours (hourly buckets)
- Y-axis: Lead count
- 4 lines: Leads, Calls, Consultations, Closes
- Color gradient fill under lines
- Tooltip on hover showing exact numbers

**Data Requirements:**
```typescript
interface LeadFlow {
  timestamp: Date;
  new_leads: number;
  calls_booked: number;
  consultations_held: number;
  deals_closed: number;
}

// Aggregate for display
interface FlowMetrics {
  leads_today: number;
  calls_today: number;
  consultations_today: number;
  closes_today: number;
  lead_to_call_rate: number;
  call_to_consultation_rate: number;
  consultation_to_close_rate: number;
  hourly_data: LeadFlow[]; // last 24 hours
}
```

---

### 8. **RevenueProjection** (Trend + Forecast)
**Location:** Right column, lower section  
**Visual:** Dual-chart component (historical + forecast)  

**Design:**
```
┌─────────────────────────────────────────┐
│  REVENUE PROJECTION                     │
│  ─────────────────────────────────────  │
│                                          │
│  This Month:    $32,400 / $50K target   │
│  Projection:    $47,200 (94% likely)    │
│  Next Month:    $58,000 (forecast)      │
│                                          │
│  [Line graph: past 6 months + 2 future] │
│  ▰▰▰▰▰▰▰▰░░ (historical blue, forecast  │
│              dotted purple)              │
│                                          │
└─────────────────────────────────────────┘
```

**Features:**
- Solid line for historical data (last 6 months)
- Dotted line for forecast (next 2 months)
- Confidence interval shading around forecast
- Target line overlay (dashed horizontal at $50K)
- Color coding: blue (historical), purple (forecast), yellow (target)
- Animated path drawing on load

**Forecasting Logic:**
- Simple linear regression or moving average
- Consider seasonality (if data available)
- Confidence = based on variance in historical data

**Data Requirements:**
```typescript
interface RevenueData {
  month: Date;
  actual_revenue?: number;  // for historical
  projected_revenue?: number; // for forecast
  confidence_high?: number; // upper bound
  confidence_low?: number;  // lower bound
}
```

---

### 9. **AlertFeed** (Urgent Issues)
**Location:** Sidebar (right), top section  
**Visual:** Vertical feed with priority badges  

**Design:**
```
┌─────────────────────────────────────┐
│  🚨 ALERTS                          │
│  ─────────────────────────────────  │
│  🔴 URGENT — Client XYZ ad stopped  │
│     ↳ 2m ago | Assigned to Blaze   │
│  ─────────────────────────────────  │
│  🟡 WARNING — Low ROAS on Campaign  │
│     ↳ 15m ago | Review suggested   │
│  ─────────────────────────────────  │
│  🔵 INFO — New lead from website    │
│     ↳ 1h ago | Auto-assigned       │
└─────────────────────────────────────┘
```

**Features:**
- Priority levels: Red (urgent), Yellow (warning), Blue (info)
- Timestamp with relative time ("2m ago")
- Auto-dismisses after 24h (or manual dismiss)
- Click alert → navigate to relevant section
- Badge count on header icon
- Slide-in animation for new alerts
- Sound notification option (toggle)

**Alert Types:**
1. **Urgent:** Ad stopped, client complaint, system error
2. **Warning:** Low ROAS, approaching budget limit, missed deadline
3. **Info:** New lead, task completed, report ready

**Data Requirements:**
```typescript
interface Alert {
  id: string;
  type: 'urgent' | 'warning' | 'info';
  title: string;
  description?: string;
  created_at: Date;
  assigned_to?: string; // agent ID
  action_url?: string; // link to relevant page
  dismissed: boolean;
}
```

---

### 10. **QuickActionsBar** (Command Center)
**Location:** Fixed bottom-right (floating fab group)  
**Visual:** Circular action buttons that fan out  

**Design:**
```
Collapsed:
  🎯 (main button)

Expanded:
  ╱ 🚀 Launch Campaign
 🎯 ─ 👤 Add Client
  ╲ 📊 Generate Report
```

**Features:**
- Main button (🎯) toggles fan-out menu
- Each action button has icon + label on hover
- Glassmorphic background with blur
- Smooth spring animations (Framer Motion)
- Keyboard shortcuts (Cmd+K opens command palette)

**Actions:**
1. **Launch Campaign** → Opens campaign wizard modal
2. **Add Client** → Opens client onboarding form
3. **Generate Report** → Triggers report generation (PDF/dashboard link)
4. **Quick Search** (bonus) → Cmd+K search bar overlay

**Tech:**
- Framer Motion `AnimatePresence` for fab group
- Portal/modal for action forms
- Could integrate with cmdk library for search

---

## 🎨 Design System

### Color Palette (Enhanced)
```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: rgba(26, 26, 46, 0.6); /* glassmorphic */
  --bg-card-hover: rgba(31, 31, 53, 0.8);
  
  /* Glassmorphism */
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  
  /* Borders */
  --border: #2a2a4a;
  --border-glow: rgba(79, 143, 255, 0.3);
  
  /* Text */
  --text-primary: #e8e8f0;
  --text-secondary: #8888aa;
  --text-muted: #606080;
  
  /* Accents */
  --accent-blue: #4f8fff;
  --accent-green: #22c55e;
  --accent-red: #ef4444;
  --accent-yellow: #eab308;
  --accent-purple: #a855f7;
  --accent-cyan: #06b6d4;
  --accent-pink: #ec4899;
  
  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --gradient-success: linear-gradient(135deg, #22c55e 0%, #10b981 100%);
  --gradient-danger: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  --gradient-info: linear-gradient(135deg, #4f8fff 0%, #3b82f6 100%);
}
```

### Glassmorphism Utility Classes
```css
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(10px) saturate(180%);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
}

.glass-card-strong {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
```

### Animation Presets (Framer Motion)
```typescript
export const animations = {
  // Card entrance
  cardEntrance: {
    initial: { opacity: 0, y: 20, scale: 0.95 },
    animate: { opacity: 1, y: 0, scale: 1 },
    transition: { duration: 0.4, ease: [0.4, 0, 0.2, 1] }
  },
  
  // Slide from right
  slideRight: {
    initial: { opacity: 0, x: 100 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -100 },
    transition: { type: "spring", stiffness: 300, damping: 30 }
  },
  
  // Number counter
  counterSpring: {
    type: "spring",
    stiffness: 100,
    damping: 10,
    mass: 0.5
  },
  
  // Pulse glow
  pulseGlow: {
    scale: [1, 1.05, 1],
    opacity: [0.8, 1, 0.8],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  },
  
  // Bounce in
  bounceIn: {
    initial: { scale: 0 },
    animate: { scale: 1 },
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 15
    }
  }
};
```

### Micro-interaction Patterns

1. **Hover Lift**
   - Component: Cards, buttons
   - Effect: `translateY(-4px)` + increased shadow
   - Duration: 200ms ease-out

2. **Active Pulse**
   - Component: Status indicators, live metrics
   - Effect: Scale 0.95 → 1.0 loop + glow
   - Duration: 2s infinite

3. **Data Update Flash**
   - Component: Numbers, charts
   - Effect: Brief highlight overlay (color flash)
   - Duration: 300ms

4. **Loading Skeleton**
   - Component: All data components
   - Effect: Gradient shimmer animation
   - Pattern: `linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)`

5. **Alert Entry**
   - Component: AlertFeed items
   - Effect: Slide from right + bounce settle
   - Sound: Optional notification sound (toggle in settings)

---

## 📊 Chart Specifications

### Library Choice: **Recharts**
Why: React-native, composable, supports gradients/animations, good TypeScript support

### Alternative: **Chart.js** (if Recharts performance issues)

### Chart Types Needed

1. **Line Charts** (Revenue, Lead Flow)
   - Gradient fills
   - Smooth curves (`monotone` interpolation)
   - Animated path drawing on load
   - Tooltip with custom styling

2. **Bar Charts** (Profit Margin, Team Capacity)
   - Horizontal orientation
   - Gradient fills based on value
   - Click handlers for drill-down

3. **Funnel Chart** (Client Pipeline)
   - Custom SVG or CSS 3D transforms
   - Animated flow particles (Canvas)

4. **Sparklines** (Inline trends)
   - Tiny (30px height)
   - No axes, just curve
   - Color-coded by trend direction

---

## 🔌 Data Integration

### Real-time Updates

**Primary:** Supabase Realtime (WebSocket)
- Already implemented ✅
- Subscribe to all relevant tables
- Push updates to React state

**Fallback:** Polling (5s interval)
- Already implemented ✅
- Ensures data freshness if WebSocket drops

**Optimization:**
- Debounce rapid updates (e.g., revenue counter shouldn't flicker)
- Use React `useMemo` for expensive calculations
- Consider virtual scrolling for long lists (react-window)

### New Supabase Tables Needed

```sql
-- Campaign performance
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  platform TEXT NOT NULL, -- 'meta' | 'google' | 'tiktok'
  name TEXT NOT NULL,
  client_id UUID REFERENCES clients(id),
  status TEXT DEFAULT 'active',
  spend_usd NUMERIC DEFAULT 0,
  budget_usd NUMERIC DEFAULT 0,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  ctr NUMERIC DEFAULT 0,
  roas NUMERIC DEFAULT 0,
  target_roas NUMERIC DEFAULT 5,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead flow tracking
CREATE TABLE lead_flow (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  new_leads INT DEFAULT 0,
  calls_booked INT DEFAULT 0,
  consultations_held INT DEFAULT 0,
  deals_closed INT DEFAULT 0
);

-- Client pipeline
CREATE TABLE pipeline (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID REFERENCES clients(id),
  stage TEXT NOT NULL, -- 'discovery' | 'qualified' | 'proposal' | 'won'
  value_usd NUMERIC DEFAULT 0,
  entered_at TIMESTAMPTZ DEFAULT NOW(),
  expected_close_date DATE,
  notes TEXT
);

-- Alerts
CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL, -- 'urgent' | 'warning' | 'info'
  title TEXT NOT NULL,
  description TEXT,
  assigned_to UUID REFERENCES agents(id),
  action_url TEXT,
  dismissed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Revenue history (for projections)
CREATE TABLE revenue_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  month DATE NOT NULL,
  revenue_usd NUMERIC NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team capacity
CREATE TABLE agent_capacity (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID REFERENCES agents(id),
  date DATE NOT NULL,
  project_count INT DEFAULT 0,
  status TEXT DEFAULT 'available', -- 'available' | 'busy' | 'overloaded'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(agent_id, date)
);

-- Client profit breakdown
CREATE TABLE client_profits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID REFERENCES clients(id),
  revenue_usd NUMERIC DEFAULT 0,
  labor_cost_usd NUMERIC DEFAULT 0,
  tools_cost_usd NUMERIC DEFAULT 0,
  ads_cost_usd NUMERIC DEFAULT 0,
  profit_usd NUMERIC DEFAULT 0,
  margin_percent NUMERIC DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🛠️ Tech Stack Recommendations

### Current Stack (Keep)
- ✅ Next.js 16.2
- ✅ React 19
- ✅ TypeScript
- ✅ Tailwind CSS 4
- ✅ Supabase

### Add These Libraries

```json
{
  "dependencies": {
    "framer-motion": "^11.0.0",        // Animations
    "recharts": "^2.12.0",              // Charts
    "lucide-react": "^0.344.0",         // Icons
    "react-countup": "^6.5.0",          // Number animations
    "date-fns": "^3.3.0",               // Date formatting
    "clsx": "^2.1.0",                   // Conditional classes
    "zustand": "^4.5.0"                 // State management (optional)
  },
  "devDependencies": {
    "@types/recharts": "^1.8.29"
  }
}
```

**Why Framer Motion?**
- Industry standard for React animations
- Declarative API (perfect for component-based design)
- Great TypeScript support
- Built-in gesture support (drag, hover, tap)
- Layout animations (auto-animate on layout changes)

**Why Recharts?**
- Composable (build charts from primitives)
- React-native (no D3 learning curve)
- Responsive by default
- Good animation support

**Alternative to Zustand:** Could use React Context + useReducer for global state, but Zustand is cleaner for things like alert dismissal, quick actions state, etc.

---

## 📐 Responsive Design

### Breakpoints
```css
/* Mobile: < 640px */
- Stack all cards vertically
- Collapse StatusBar to hamburger menu
- Hide sparklines, show numbers only
- Simplify funnel to vertical list

/* Tablet: 640px - 1024px */
- 2-column grid
- Condense charts (smaller height)
- Keep animations but reduce particle counts

/* Desktop: 1024px+ */
- Full 3-4 column grid
- All animations enabled
- Expand StatusBar to full width

/* Ultra-wide: 1600px+ */
- Consider 4-column layout for some sections
- Add more whitespace
```

### Mobile-Specific Optimizations
- Disable heavy animations (particles, 3D transforms)
- Use CSS animations instead of JS where possible
- Lazy load charts (only render when in viewport)
- Reduce polling frequency on mobile (10s instead of 5s)

---

## 🚀 Performance Optimizations

### Critical
1. **Code Splitting**
   - Lazy load heavy components (charts, 3D funnel)
   - Use `React.lazy()` and `Suspense`

2. **Virtualization**
   - If agent list > 50, use `react-window`
   - Same for activity feed

3. **Memoization**
   - Wrap chart data calculations in `useMemo`
   - Use `React.memo` for components that receive stable props

4. **Debouncing**
   - Debounce real-time updates (especially counters)
   - Throttle scroll events if using scroll-based animations

5. **Image Optimization**
   - Use Next.js `<Image>` component
   - Serve icons as SVG (Lucide React)

### Nice-to-Have
- Prefetch data for next likely view (e.g., if hovering on campaign card, prefetch detailed stats)
- Service worker for offline indicator
- Web vitals monitoring (Vercel Analytics)

---

## 🎭 Accessibility

### Must-Haves
1. **Keyboard Navigation**
   - All interactive elements must be keyboard accessible
   - Focus indicators (visible outline on focus)
   - Skip links ("Skip to main content")

2. **Screen Readers**
   - ARIA labels for all icons
   - Live regions for real-time updates (`aria-live="polite"`)
   - Semantic HTML (`<nav>`, `<main>`, `<article>`)

3. **Color Contrast**
   - All text must meet WCAG AA standards (4.5:1 for normal text)
   - Don't rely solely on color to convey information (use icons + text)

4. **Motion Preferences**
   - Respect `prefers-reduced-motion`
   - Disable animations if user has motion sensitivity

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 🧪 Testing Strategy

### Unit Tests
- Component rendering (Vitest + Testing Library)
- Data calculations (profit margins, conversion rates)

### Integration Tests
- Supabase queries return correct data
- Real-time updates trigger re-renders

### Visual Regression
- Percy or Chromatic for screenshot testing
- Ensure animations don't break layout

### Performance Testing
- Lighthouse audits (target: 90+ performance score)
- Bundle size monitoring (ideally < 200KB initial JS)

---

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Install dependencies (Framer Motion, Recharts, Lucide)
- [ ] Set up new Supabase tables
- [ ] Create glassmorphism utility classes
- [ ] Build animation preset library
- [ ] Implement RevenueCounter component

### Phase 2: Core Components (Week 2)
- [ ] ClientPipelineFunnel (3D visualization)
- [ ] CampaignDashboard (live ad metrics)
- [ ] TeamCapacityHeatmap
- [ ] AIWorkerStatus (enhanced with real-time)
- [ ] LeadFlowLive (graph + flow diagram)

### Phase 3: Analytics (Week 3)
- [ ] ProfitMarginTracker
- [ ] RevenueProjection (with forecasting)
- [ ] AlertFeed
- [ ] QuickActionsBar

### Phase 4: Polish (Week 4)
- [ ] Responsive design (mobile, tablet)
- [ ] Accessibility audit (keyboard, screen readers)
- [ ] Performance optimization (lazy loading, memoization)
- [ ] Animation polish (timing, easing)
- [ ] User testing + feedback iteration

---

## 🎬 Bonus: "Wow" Features

### 1. **Command Palette** (Cmd+K)
Like Linear/GitHub — quick search/actions overlay

### 2. **Voice Alerts**
"Atlas has completed the API" — optional text-to-speech for critical alerts

### 3. **Dark/Light Mode Toggle**
(Though dark is primary, some clients may want light mode)

### 4. **Export to PDF**
One-click dashboard export for client reports

### 5. **Time-Travel Mode**
Scrub through historical data with timeline slider

### 6. **AI Insights Panel**
"Based on current trends, you're likely to hit $50K by March 28"

---

## 🏁 Success Metrics

**Before:**
- Static, boring, no animations
- Data updates every 5s but not obvious
- No visual hierarchy
- Hard to spot problems

**After:**
- Feels alive — particles, pulses, real-time counters
- Instantly obvious when something needs attention (alerts, red indicators)
- Beautiful enough to show clients in sales calls
- Actually *fun* to look at

**Quantifiable:**
- Page load < 2s (Lighthouse)
- First contentful paint < 1s
- Smooth 60fps animations (no janky scrolling)
- Zero accessibility violations (WAVE audit)

---

## 🎨 Final Thoughts

This dashboard should make Ken feel like Tony Stark looking at JARVIS's UI. Every number, every graph, every animation should serve a purpose: **helping him run a world-class agency at a glance.**

The design balances aesthetics with function — it's not just pretty, it's *useful*. And critically, it scales: as the agency grows from 3 clients to 30, the dashboard adapts.

Let's build something spectacular. 🚀

---

**Next Steps:**
1. Review this spec with Max
2. Get approval on design direction
3. Create Supabase tables
4. Start building Phase 1 components
5. Iterate based on real data + feedback

*— Aura*
