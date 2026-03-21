# 🎨 D1 Dashboard — Visual Mockup
**ASCII Wireframe Reference**

---

## Full Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ STATUS BAR (sticky, full-width)                                                         │
│ ─────────────────────────────────────────────────────────────────────────────────────── │
│ 🔵 D1 AGENCY | COMMAND CENTER v3.0          ⚡ 14 AGENTS ACTIVE | 🔴 2 URGENT ALERTS   │
│ [Admin Mode ✓ | Client View ]                         💵 $127,450 ↑ $2,340 TODAY ✨    │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ HERO KPI GRID (4 columns, glassmorphic cards)                                          │
├─────────────────────┬─────────────────────┬─────────────────────┬─────────────────────┤
│ 💰 MRR              │ 📊 PIPELINE         │ 📥 LEADS TODAY      │ 💹 PROFIT MARGIN    │
│ $32,400 / $50K      │ $128,000            │ 47                  │ 68.5%               │
│ ▰▰▰▰▰▰▰░░░ (65%)   │ Weighted: $89,600   │ ↑ 12% vs yesterday  │ Target: 60%+ ✅     │
│ On track for $47K   │ 8 opportunities     │ [▂▃▅▇▅▃▂] 24h trend │ ↑ 3.2% this week    │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 🎯 CLIENT PIPELINE FUNNEL (3D isometric visualization)                                 │
│ ─────────────────────────────────────────────────────────────────────────────────────── │
│                                                                                         │
│        ┌────────────────────────────────────┐                                          │
│        │     DISCOVERY — 47 LEADS           │  $128K total value                       │
│        │     (Dark blue glassmorphic)       │  ✨ ✨ ✨ (particles flowing)            │
│        └────────────┬───────────────────────┘                                          │
│                     ↓ 38% conversion                                                    │
│              ┌──────────────────────┐                                                   │
│              │  QUALIFIED — 18      │  $89K weighted                                    │
│              │  (Blue glass)        │  💧 💧 (flow animation)                          │
│              └───────────┬──────────┘                                                   │
│                          ↓ 67% conversion                                               │
│                    ┌──────────┐                                                         │
│                    │ PROPOSAL │  $45K value                                             │
│                    │    12    │  (Purple glass)                                         │
│                    └─────┬────┘                                                         │
│                          ↓ 75% close rate                                               │
│                       ┌─────┐                                                           │
│                       │ WON │  $28K this month                                          │
│                       │  9  │  (Green glass) 🎉                                        │
│                       └─────┘                                                           │
│                                                                                         │
│ [Click any stage to expand client list]                                                │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────┬──────────────────────────────────────────┐
│ 📺 CAMPAIGN DASHBOARD (2/3 width)            │ 🔥 TEAM CAPACITY (1/3 width)             │
├──────────────────────────────────────────────┤                                          │
│ ┌──────────────────────────────────────────┐ │       Mon  Tue  Wed  Thu  Fri            │
│ │ 🔵 META | Summer Sale — ACTIVE          │ │ Atlas  🟢🟢 🟡🟢 🟢🟢 🟢   🔴            │
│ │ ────────────────────────────────────────│ │ Nova   🟢   🟢🟢 🟢   🟢🟢 🟢            │
│ │ 💰 Spend: $1,240 / $2,000 (62%)         │ │ Aura   🟡   🟢   🟢🟡 🟢   🟢🟢            │
│ │ 👁  Impressions: 45.2K ↑ 12%            │ │ Blaze  🟢🟢 🔴   🟢🟢 🟢🟢 🟢            │
│ │ 🎯 CTR: 2.8% ↑ 0.4%                     │ │ Forge  🟢🟢 🟢   🟢🟡 🟢   🟢            │
│ │ 💵 ROAS: 4.2x ⚠️  (Target: 5.0x)        │ │ ...                                      │
│ │ [▂▃▅▇▆▄▃] 7-day trend                   │ │                                          │
│ │ [Details] [Pause] [Optimize 🤖]         │ │ 🟢 Available (1-2 projects)              │
│ └──────────────────────────────────────────┘ │ 🟡 Busy (3-4)                            │
│                                              │ 🔴 Overloaded (5+)                       │
│ ┌──────────────────────────────────────────┐ │                                          │
│ │ 🌈 GOOGLE | Brand Awareness — ACTIVE    │ │ [Hover cell for project details]         │
│ │ ────────────────────────────────────────│ │                                          │
│ │ 💰 Spend: $850 / $1,500 (57%)           │ │                                          │
│ │ 👁  Impressions: 32K ↑ 8%               │ │                                          │
│ │ 🎯 CTR: 3.0% → (no change)              │ │                                          │
│ │ 💵 ROAS: 3.5x ✅ (Target: 4.0x)         │ │                                          │
│ └──────────────────────────────────────────┘ │                                          │
│                                              │                                          │
│ [+ Add Campaign]                             │                                          │
└──────────────────────────────────────────────┴──────────────────────────────────────────┘

┌──────────────────────────────────────────────┬──────────────────────────────────────────┐
│ 🤖 AI WORKER STATUS (2/3 width)              │ 📈 LEAD FLOW LIVE (1/3 width)            │
├──────────────────────────────────────────────┤                                          │
│ 🟢 Atlas       ⚡ Building client API        │  📥 New Leads        47                  │
│ 🟢 Nova        🎨 Designing landing page     │      ↓ (38% conversion)                  │
│ 🟡 Aura        💤 Idle (2m)                  │  ☎️  Calls Booked     18                  │
│ 🟢 Blaze       📊 Optimizing Meta ads        │      ↓ (67% show rate)                   │
│ 🟢 Forge       🔧 Database migration         │  🤝 Consultations     12                  │
│ 🔴 Synapse     ⚠️  Error (retrying...)       │      ↓ (25% close rate)                  │
│ 🟢 Logic       🔁 Automating client flow     │  ✅ Closed Deals      3                   │
│ 🟢 Vector      📊 Building analytics         │                                          │
│ 🟢 Ledger      💰 Processing invoices        │ ─────────────────────────────────        │
│ ... (+5 more)                                │ Live Graph (Last 24h):                   │
│                                              │          ╱╲                              │
│ Fleet Health: ▰▰▰▰▰▰▰▰░░ 85%                │     ╱╲  ╱  ╲  ╱╲                        │
│ Avg Load: 3.2 tasks/agent                   │ ╱╲ ╱  ╲╱    ╲╱  ╲                       │
│                                              │ ────────────────────────                 │
│ [View Detailed Logs]                         │ 00:00   06:00   12:00   18:00            │
└──────────────────────────────────────────────┴──────────────────────────────────────────┘

┌──────────────────────────────────────────────┬──────────────────────────────────────────┐
│ 💹 PROFIT MARGIN TRACKER (2/3 width)         │ 📊 REVENUE PROJECTION (1/3 width)        │
├──────────────────────────────────────────────┤                                          │
│ Client A  ████████████████ 78% ($12.5K) ✅  │ This Month:  $32.4K / $50K               │
│ Client B  ██████████       62% ($8.2K)  ✅  │ Projection:  $47.2K (94% likely)         │
│ Client C  ████████████████████ 85% ($15K) ✅│ Next Month:  $58K (forecast)             │
│ Client D  ████             35% ($2.1K)  ⚠️   │                                          │
│                                              │ ─────────────────────────────────        │
│ [Click bar to expand cost breakdown]        │         ╱                                │
│                                              │        ╱ ┈┈┈┈ (forecast)                │
│ ┌──────────────────────────────────────────┐│       ╱                                  │
│ │ Client D — $2.1K profit (35% margin)     ││  ────╱ (historical)                      │
│ │ ──────────────────────────────────────── ││     ╱                                    │
│ │ Revenue:     $6,000                      ││ Jan  Mar  May  Jul  Sep  Nov             │
│ │ Costs:       $3,900                      ││                                          │
│ │   ├─ Labor:    $2,800 (Atlas/Nova/Aura) ││ ─── Target: $50K/mo                      │
│ │   ├─ Tools:    $400 (Supabase, Vercel)  ││                                          │
│ │   └─ Ads:      $700 (Meta campaigns)    ││                                          │
│ │ Profit:      $2,100                      ││                                          │
│ └──────────────────────────────────────────┘│                                          │
└──────────────────────────────────────────────┴──────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 🚨 ALERT FEED (full width, sticky sidebar or bottom panel)                             │
│ ─────────────────────────────────────────────────────────────────────────────────────── │
│ 🔴 URGENT — Client XYZ ad campaign paused unexpectedly (2m ago) [Assigned: Blaze]      │
│ 🟡 WARNING — Low ROAS on TikTok "Product Launch" campaign (15m ago) [Review]           │
│ 🔵 INFO — New lead from website: john@example.com (1h ago) [Auto-assigned: Hunter]     │
│ 🔵 INFO — Report ready for Client A (2h ago) [Download PDF]                            │
│                                                                                         │
│ [View All Alerts (12)]                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ ⚡ QUICK ACTIONS BAR (floating bottom-right)                                            │
│                                                                                         │
│                                              ╱ 🚀 Launch Campaign                       │
│                                             🎯 ─ 👤 Add Client                          │
│                                              ╲ 📊 Generate Report                       │
│                                                                                         │
│ [Cmd+K for command palette]                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Individual Component Mockups

### 1. Revenue Counter (Hero Component)

```
┌───────────────────────────────────────┐
│  💵 TOTAL REVENUE                     │
│                                       │
│      $127,450  ✨ ✨               │
│      ▂▃▅▇▅▃▂ (24h trend)            │
│                                       │
│  ↑ $2,340 today                       │
│  Target: $150K/mo (85% there)         │
└───────────────────────────────────────┘
```

**Animations:**
- Number counts up with spring animation
- Particles emit when value increases
- Sparkline draws from left to right
- Glow pulses on increment

---

### 2. Pipeline Funnel Stage (Expanded)

```
┌─────────────────────────────────────────────┐
│ QUALIFIED STAGE — 18 Opportunities          │
│ Total Value: $89,000 (weighted)             │
│ Avg Close Probability: 50%                  │
│ ───────────────────────────────────────────│
│ 1. TechStart Inc       $25K  ⚡ 70%  4/15   │
│ 2. Acme Corp           $15K  ⚡ 50%  4/20   │
│ 3. GrowthCo            $12K  ⚡ 60%  4/18   │
│ 4. LocalBiz            $8K   ⚡ 40%  4/25   │
│ ... (+14 more)                              │
│                                             │
│ [Close] [Move to Proposal]                  │
└─────────────────────────────────────────────┘
```

---

### 3. Campaign Card (Detail View)

```
┌────────────────────────────────────────────┐
│ 🔵 META | Summer Sale 2026                 │
│ Status: ACTIVE ● Since: Mar 15             │
│ ──────────────────────────────────────────│
│                                            │
│ 💰 Budget                                  │
│    $1,240 / $2,000 ▰▰▰▰▰▰░░░░ 62%        │
│                                            │
│ 📊 Performance (Last 7 Days)               │
│    Impressions:  45,200  ↑ 12%            │
│    Clicks:       1,266   ↑ 15%            │
│    CTR:          2.8%    ↑ 0.4%           │
│    ROAS:         4.2x    ⚠️  (Target: 5x)  │
│                                            │
│ 📈 ROAS Trend:                             │
│    ╱╲                                      │
│   ╱  ╲  ╱╲                                │
│  ╱    ╲╱  ╲                               │
│ ─────────────                              │
│ Mon Tue Wed Thu Fri Sat Sun                │
│                                            │
│ ──────────────────────────────────────────│
│ [View Details] [Pause] [Optimize 🤖]       │
└────────────────────────────────────────────┘
```

---

### 4. Team Capacity Heatmap Cell (Tooltip)

```
┌───────────────────────────────────┐
│ Atlas — Wednesday, Mar 21         │
│ Status: BUSY 🟡                   │
│ ─────────────────────────────────│
│ Working on:                       │
│  • Client A API Integration       │
│  • Database migration for Client B│
│  • Code review for Nova           │
│                                   │
│ Capacity: 3/5 projects            │
│ Expected free: Thursday AM        │
└───────────────────────────────────┘
```

---

### 5. Profit Breakdown (Expanded Client)

```
┌──────────────────────────────────────────┐
│ Client D — Profit Analysis               │
│ ────────────────────────────────────────│
│                                          │
│ Revenue          $6,000                  │
│                  ████████████████████    │
│                                          │
│ Labor Cost       $2,800 (47%)            │
│  ├─ Atlas        $1,200 (15h)            │
│  ├─ Nova         $900 (12h)              │
│  └─ Aura         $700 (9h)               │
│                                          │
│ Tools Cost       $400 (7%)               │
│  ├─ Supabase     $150                    │
│  ├─ Vercel       $100                    │
│  └─ APIs         $150                    │
│                                          │
│ Ads Cost         $700 (12%)              │
│  └─ Meta Ads     $700                    │
│                                          │
│ ────────────────────────────────────────│
│ PROFIT           $2,100 (35% margin) ⚠️  │
│                                          │
│ Recommendation:                          │
│ • Reduce labor hours (currently 36h)    │
│ • Increase pricing or scope              │
│ • Target margin: 60%+                    │
│                                          │
│ [Close] [Adjust Pricing]                 │
└──────────────────────────────────────────┘
```

---

### 6. Lead Flow Graph (Live Update)

```
┌─────────────────────────────────────────┐
│ LEAD FLOW — Last 24 Hours               │
│ ───────────────────────────────────────│
│                                         │
│      60│                                │
│        │     ╱╲                         │
│      40│    ╱  ╲  ╱╲                   │
│        │   ╱    ╲╱  ╲  ╱╲              │
│      20│  ╱          ╲╱  ╲             │
│        │ ╱                 ╲           │
│       0├─────────────────────────────   │
│        0h   6h   12h   18h   24h        │
│                                         │
│ Legend:                                 │
│ ─── Leads (47 today)                    │
│ ─·─ Calls (18)                          │
│ ··· Consultations (12)                  │
│ ─ ─ Closes (3)                          │
│                                         │
│ ✨ New lead just arrived! (2s ago)      │
└─────────────────────────────────────────┘
```

---

### 7. Revenue Projection Chart

```
┌─────────────────────────────────────────┐
│ REVENUE PROJECTION                      │
│ ───────────────────────────────────────│
│                                         │
│  $60K│                ╱┈┈┈┈┈            │
│      │               ╱ (forecast)       │
│  $50K│─ ─ ─ ─ ─ ─ ─╱─ ─ (target)       │
│      │             ╱                    │
│  $40K│           ╱                      │
│      │         ╱                        │
│  $30K│       ╱                          │
│      │     ╱                            │
│  $20K│   ╱                              │
│      │ ╱                                │
│     0├────────────────────────────────  │
│      Oct Nov Dec Jan Feb Mar Apr May    │
│                      ↑                  │
│                    today                │
│                                         │
│ This Month:    $32.4K / $50K (65%)      │
│ Projection:    $47.2K (94% confidence)  │
│ Next Month:    $58K (forecast)          │
│                                         │
│ On track to hit $50K by March 28! 🎯    │
└─────────────────────────────────────────┘
```

---

### 8. Quick Actions (Expanded)

```
                    ╱ 🚀 Launch Campaign
                   │
                   │  👤 Add Client
              🎯 ──┤
                   │  📊 Generate Report
                   │
                    ╲ 🔍 Search (Cmd+K)
```

**Interaction:**
- Click 🎯 → Menu fans out with spring animation
- Hover action → Label appears with glassmorphic background
- Click action → Modal/wizard opens
- Press Escape → Menu collapses

---

## Color Reference

```
Status Colors:
🟢 Green   — Active, Healthy, Available    (#22c55e)
🟡 Yellow  — Warning, Busy, Attention      (#eab308)
🔴 Red     — Error, Urgent, Overloaded     (#ef4444)
🔵 Blue    — Info, Working, Processing     (#4f8fff)
🟣 Purple  — Premium, Pipeline, Forecast   (#a855f7)

Platform Colors:
🔵 Meta     — Blue (#4267B2)
🌈 Google   — Multi-color (red/yellow/green/blue)
💗 TikTok   — Pink/Cyan (#fe2c55 / #00f2ea)

Glassmorphism:
Background: rgba(255, 255, 255, 0.05)
Border: rgba(255, 255, 255, 0.1)
Backdrop: blur(10px) saturate(180%)
Shadow: 0 8px 32px rgba(0, 0, 0, 0.37)
```

---

## Animation Examples (Pseudo-Code)

### Revenue Counter Increment
```typescript
// When revenue updates
onRevenueUpdate(newValue) {
  // Animate number
  countUp(currentValue, newValue, { duration: 1000, easing: 'spring' });
  
  // Emit particles
  emitParticles({
    count: 12,
    color: 'green',
    direction: 'radial',
    duration: 1200
  });
  
  // Glow pulse
  glowPulse({ color: 'green', intensity: 0.8, duration: 500 });
}
```

### Pipeline Stage Hover
```typescript
// Framer Motion
<motion.div
  whileHover={{
    translateY: -8,
    scale: 1.02,
    boxShadow: '0 12px 40px rgba(79, 143, 255, 0.3)'
  }}
  transition={{ type: 'spring', stiffness: 300, damping: 20 }}
>
  {/* Stage content */}
</motion.div>
```

### Alert Slide-In
```typescript
// Framer Motion
<AnimatePresence>
  {alerts.map(alert => (
    <motion.div
      key={alert.id}
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -100 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
    >
      <AlertItem alert={alert} />
    </motion.div>
  ))}
</AnimatePresence>
```

---

## Responsive Breakpoints

### Mobile (< 640px)
```
┌─────────────────────┐
│ StatusBar (compact) │
├─────────────────────┤
│ KPI Cards (stacked) │
├─────────────────────┤
│ Pipeline (vertical) │
├─────────────────────┤
│ Campaigns (list)    │
├─────────────────────┤
│ Workers (list)      │
└─────────────────────┘
```

### Tablet (640px - 1024px)
```
┌───────────────────────────────┐
│ StatusBar                     │
├───────────────┬───────────────┤
│ KPI 1 + 2     │ KPI 3 + 4     │
├───────────────┴───────────────┤
│ Pipeline (2D funnel)          │
├───────────────┬───────────────┤
│ Campaigns     │ Team Heatmap  │
├───────────────┴───────────────┤
│ Workers + Alerts              │
└───────────────────────────────┘
```

### Desktop (1024px+)
```
Full 3-4 column grid (as shown in main mockup)
```

---

## Final Notes

**This mockup shows:**
- ✅ Real-time data updates (animated numbers, live graphs)
- ✅ Visual hierarchy (important metrics larger/higher)
- ✅ Interactive elements (click to expand, hover for details)
- ✅ Alert system (color-coded urgency)
- ✅ Glassmorphic design (blur, transparency, depth)
- ✅ Micro-interactions (pulses, glows, particles)
- ✅ Responsive layout (mobile, tablet, desktop)

**Ready to code? Let's build it! 🚀**

*— Aura*
