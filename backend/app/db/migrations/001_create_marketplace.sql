-- Listings (products for sale)
CREATE TABLE IF NOT EXISTS listings (
  id                SERIAL PRIMARY KEY,
  sku               TEXT UNIQUE NOT NULL,
  title             TEXT NOT NULL,
  description       TEXT,
  category          TEXT,
  image_url         TEXT,
  price_cents       INTEGER NOT NULL DEFAULT 0,
  currency          TEXT NOT NULL DEFAULT 'USD',
  seller_id         TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'active',  -- active|paused|banned
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compliance results (scan snapshots)
CREATE TABLE IF NOT EXISTS compliance_results (
  id                BIGSERIAL PRIMARY KEY,
  listing_id        INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  severity          TEXT NOT NULL,  -- none|low|medium|high|critical
  issues_json       JSONB NOT NULL DEFAULT '[]',
  model_version     TEXT,
  scanned_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compliance_listing_time ON compliance_results (listing_id, scanned_at DESC);

-- Flags ( surfaced high/critical issues to console )
CREATE TABLE IF NOT EXISTS flags (
  id                BIGSERIAL PRIMARY KEY,
  listing_id        INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  result_id         BIGINT  NOT NULL REFERENCES compliance_results(id) ON DELETE CASCADE,
  severity          TEXT NOT NULL,
  reason            TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolved_at       TIMESTAMPTZ,
  resolved_by       TEXT
);
CREATE INDEX IF NOT EXISTS idx_flags_open ON flags (resolved_at NULLS FIRST, severity);

-- Bans (moderation actions)
CREATE TABLE IF NOT EXISTS bans (
  id                BIGSERIAL PRIMARY KEY,
  listing_id        INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  reason            TEXT NOT NULL,
  actor             TEXT NOT NULL,   -- officer id
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  lifted_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_bans_listing ON bans (listing_id, created_at DESC);

-- Appeals (seller requests to reverse actions)
CREATE TABLE IF NOT EXISTS appeals (
  id                BIGSERIAL PRIMARY KEY,
  listing_id        INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
  flag_id           BIGINT REFERENCES flags(id) ON DELETE SET NULL,
  status            TEXT NOT NULL DEFAULT 'open', -- open|approved|rejected
  message           TEXT NOT NULL,
  decision_message  TEXT,
  created_by        TEXT NOT NULL,  -- seller id
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  decided_at        TIMESTAMPTZ,
  decided_by        TEXT
);
CREATE INDEX IF NOT EXISTS idx_appeals_status ON appeals (status, created_at DESC);

-- View: latest status per listing (UI speed-up)
CREATE OR REPLACE VIEW v_listings_latest AS
SELECT
  l.*,
  cr.severity AS latest_severity,
  cr.scanned_at AS last_checked_at
FROM listings l
LEFT JOIN LATERAL (
  SELECT severity, scanned_at
  FROM compliance_results c
  WHERE c.listing_id = l.id
  ORDER BY scanned_at DESC
  LIMIT 1
) cr ON TRUE;
