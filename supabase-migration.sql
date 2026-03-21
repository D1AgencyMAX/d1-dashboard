-- ========================================
-- D1 Dashboard Redesign — Database Schema
-- ========================================
-- Run this migration in Supabase SQL Editor
-- ========================================

-- 1. Campaigns Table
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  platform TEXT NOT NULL CHECK (platform IN ('meta', 'google', 'tiktok')),
  name TEXT NOT NULL,
  client_id UUID, -- Optional: reference to clients table if exists
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
  spend_usd NUMERIC DEFAULT 0,
  budget_usd NUMERIC DEFAULT 0,
  impressions BIGINT DEFAULT 0,
  clicks BIGINT DEFAULT 0,
  ctr NUMERIC DEFAULT 0, -- Click-through rate (percentage)
  roas NUMERIC DEFAULT 0, -- Return on ad spend
  target_roas NUMERIC DEFAULT 5,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE campaigns;

-- Add index for performance
CREATE INDEX idx_campaigns_platform ON campaigns(platform);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- ----------------------------------------
-- 2. Lead Flow Tracking
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS lead_flow (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  new_leads INT DEFAULT 0,
  calls_booked INT DEFAULT 0,
  consultations_held INT DEFAULT 0,
  deals_closed INT DEFAULT 0
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE lead_flow;

-- Add index for time-based queries
CREATE INDEX idx_lead_flow_timestamp ON lead_flow(timestamp DESC);

-- ----------------------------------------
-- 3. Client Pipeline
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS pipeline (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_name TEXT NOT NULL, -- Simplified (no FK requirement)
  client_id UUID, -- Optional FK if clients table exists
  stage TEXT NOT NULL CHECK (stage IN ('discovery', 'qualified', 'proposal', 'won', 'lost')),
  value_usd NUMERIC DEFAULT 0,
  entered_at TIMESTAMPTZ DEFAULT NOW(),
  expected_close_date DATE,
  probability NUMERIC DEFAULT 0.5, -- 0-1 scale for weighted pipeline
  notes TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE pipeline;

-- Add indexes
CREATE INDEX idx_pipeline_stage ON pipeline(stage);
CREATE INDEX idx_pipeline_expected_close ON pipeline(expected_close_date);

-- ----------------------------------------
-- 4. Alerts
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  type TEXT NOT NULL CHECK (type IN ('urgent', 'warning', 'info')),
  title TEXT NOT NULL,
  description TEXT,
  assigned_to UUID, -- Could reference agents(id) if needed
  action_url TEXT,
  dismissed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE alerts;

-- Add index for active alerts
CREATE INDEX idx_alerts_dismissed ON alerts(dismissed, created_at DESC);

-- ----------------------------------------
-- 5. Revenue History
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS revenue_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  month DATE NOT NULL UNIQUE, -- One record per month
  revenue_usd NUMERIC NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE revenue_history;

-- Add index
CREATE INDEX idx_revenue_history_month ON revenue_history(month DESC);

-- ----------------------------------------
-- 6. Agent Capacity
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS agent_capacity (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id UUID NOT NULL, -- References agents(id)
  agent_name TEXT NOT NULL, -- Denormalized for easier queries
  date DATE NOT NULL,
  project_count INT DEFAULT 0,
  status TEXT DEFAULT 'available' CHECK (status IN ('available', 'busy', 'overloaded')),
  projects TEXT[], -- Array of project names
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(agent_id, date)
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE agent_capacity;

-- Add indexes
CREATE INDEX idx_agent_capacity_date ON agent_capacity(date DESC);
CREATE INDEX idx_agent_capacity_agent ON agent_capacity(agent_id);

-- ----------------------------------------
-- 7. Client Profits
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS client_profits (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  client_id UUID, -- Optional FK
  client_name TEXT NOT NULL,
  revenue_usd NUMERIC DEFAULT 0,
  labor_cost_usd NUMERIC DEFAULT 0,
  tools_cost_usd NUMERIC DEFAULT 0,
  ads_cost_usd NUMERIC DEFAULT 0,
  profit_usd NUMERIC GENERATED ALWAYS AS (revenue_usd - labor_cost_usd - tools_cost_usd - ads_cost_usd) STORED,
  margin_percent NUMERIC GENERATED ALWAYS AS (
    CASE 
      WHEN revenue_usd > 0 THEN ((revenue_usd - labor_cost_usd - tools_cost_usd - ads_cost_usd) / revenue_usd) * 100
      ELSE 0
    END
  ) STORED,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE client_profits;

-- Add index
CREATE INDEX idx_client_profits_margin ON client_profits(margin_percent DESC);

-- ========================================
-- Sample Data (for development/testing)
-- ========================================

-- Sample campaigns
INSERT INTO campaigns (platform, name, client_id, status, spend_usd, budget_usd, impressions, clicks, ctr, roas, target_roas)
VALUES 
  ('meta', 'Summer Sale 2026', NULL, 'active', 1240.50, 2000, 45200, 1266, 2.8, 4.2, 5.0),
  ('google', 'Brand Awareness Q1', NULL, 'active', 850.00, 1500, 32000, 960, 3.0, 3.5, 4.0),
  ('tiktok', 'Product Launch', NULL, 'paused', 420.00, 1000, 18500, 370, 2.0, 2.8, 5.0);

-- Sample lead flow (last 24 hours, hourly)
INSERT INTO lead_flow (timestamp, new_leads, calls_booked, consultations_held, deals_closed)
SELECT 
  NOW() - (n || ' hours')::INTERVAL,
  FLOOR(RANDOM() * 10 + 1)::INT,
  FLOOR(RANDOM() * 5)::INT,
  FLOOR(RANDOM() * 3)::INT,
  FLOOR(RANDOM() * 2)::INT
FROM generate_series(0, 23) n;

-- Sample pipeline
INSERT INTO pipeline (client_name, stage, value_usd, probability, expected_close_date)
VALUES
  ('Acme Corp', 'discovery', 15000, 0.3, '2026-04-15'),
  ('TechStart Inc', 'qualified', 25000, 0.5, '2026-04-10'),
  ('GrowthCo', 'proposal', 40000, 0.7, '2026-03-28'),
  ('LocalBiz', 'qualified', 8000, 0.5, '2026-04-20'),
  ('Enterprise XYZ', 'won', 60000, 1.0, '2026-03-15');

-- Sample alerts
INSERT INTO alerts (type, title, description, dismissed)
VALUES
  ('urgent', 'Campaign paused unexpectedly', 'Meta Ads campaign "Summer Sale" was paused due to payment issue.', FALSE),
  ('warning', 'Low ROAS on TikTok campaign', 'Product Launch campaign ROAS dropped below 3.0x target.', FALSE),
  ('info', 'New lead received', 'Lead from website contact form: john@example.com', TRUE);

-- Sample revenue history (last 12 months)
INSERT INTO revenue_history (month, revenue_usd)
SELECT 
  DATE_TRUNC('month', NOW() - (n || ' months')::INTERVAL)::DATE,
  FLOOR(RANDOM() * 30000 + 20000) -- Random revenue between $20K-$50K
FROM generate_series(0, 11) n;

-- Sample client profits
INSERT INTO client_profits (client_name, revenue_usd, labor_cost_usd, tools_cost_usd, ads_cost_usd)
VALUES
  ('Client A', 12500, 2000, 300, 450),
  ('Client B', 8200, 2800, 250, 350),
  ('Client C', 15000, 1800, 200, 500),
  ('Client D', 6000, 3200, 400, 700);

-- ========================================
-- Helper Functions
-- ========================================

-- Function to auto-update 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_pipeline_updated_at 
  BEFORE UPDATE ON pipeline 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_capacity_updated_at 
  BEFORE UPDATE ON agent_capacity 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_client_profits_updated_at 
  BEFORE UPDATE ON client_profits 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Row-Level Security (RLS) — Optional
-- ========================================
-- Uncomment if you want to enable RLS

-- ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE lead_flow ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE pipeline ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE revenue_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_capacity ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE client_profits ENABLE ROW LEVEL SECURITY;

-- Example policy (allow all for authenticated users)
-- CREATE POLICY "Allow all for authenticated users" ON campaigns
--   FOR ALL USING (auth.role() = 'authenticated');

-- ========================================
-- Materialized Views (Performance Boost)
-- ========================================

-- Aggregated lead flow metrics (refresh every 5 min via cron or trigger)
CREATE MATERIALIZED VIEW IF NOT EXISTS lead_flow_summary AS
SELECT
  DATE_TRUNC('day', timestamp) AS day,
  SUM(new_leads) AS total_leads,
  SUM(calls_booked) AS total_calls,
  SUM(consultations_held) AS total_consultations,
  SUM(deals_closed) AS total_closes,
  CASE 
    WHEN SUM(new_leads) > 0 THEN ROUND((SUM(calls_booked)::NUMERIC / SUM(new_leads)) * 100, 1)
    ELSE 0
  END AS lead_to_call_rate,
  CASE 
    WHEN SUM(calls_booked) > 0 THEN ROUND((SUM(consultations_held)::NUMERIC / SUM(calls_booked)) * 100, 1)
    ELSE 0
  END AS call_to_consultation_rate,
  CASE 
    WHEN SUM(consultations_held) > 0 THEN ROUND((SUM(deals_closed)::NUMERIC / SUM(consultations_held)) * 100, 1)
    ELSE 0
  END AS consultation_to_close_rate
FROM lead_flow
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', timestamp)
ORDER BY day DESC;

-- Index on materialized view
CREATE UNIQUE INDEX idx_lead_flow_summary_day ON lead_flow_summary(day);

-- Manual refresh (call periodically via cron or trigger)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY lead_flow_summary;

-- ========================================
-- Verification Queries
-- ========================================

-- Check if tables were created
SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
  'campaigns', 'lead_flow', 'pipeline', 'alerts', 
  'revenue_history', 'agent_capacity', 'client_profits'
);

-- Check sample data
SELECT COUNT(*) FROM campaigns;
SELECT COUNT(*) FROM lead_flow;
SELECT COUNT(*) FROM pipeline;
SELECT COUNT(*) FROM alerts;
SELECT COUNT(*) FROM revenue_history;
SELECT COUNT(*) FROM client_profits;

-- View lead flow summary
SELECT * FROM lead_flow_summary LIMIT 7;

-- ========================================
-- DONE ✅
-- ========================================
-- Next steps:
-- 1. Update lib/supabase.ts with new TypeScript types
-- 2. Start building dashboard components
-- 3. Set up realtime subscriptions in useRealtimeData hook
-- ========================================
