-- ONECALL online platform foundation (PostgreSQL 14+)
-- Architecture-only migration. Do NOT run on a public database until
-- authentication, tenant authorization, secrets and backups are configured.
-- Every table uses deny-by-default row level security; no client policies yet.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE businesses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name text NOT NULL CHECK (length(display_name) BETWEEN 2 AND 120),
  slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE business_members (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  identity_subject text NOT NULL CHECK (length(identity_subject) BETWEEN 1 AND 255),
  role text NOT NULL CHECK (role IN ('owner','manager','staff')),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id,identity_subject)
);
CREATE TABLE pricing_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  version integer NOT NULL CHECK (version > 0),
  rates jsonb NOT NULL CHECK (jsonb_typeof(rates)='object'),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id,version),
  UNIQUE (business_id,id)
);
CREATE TABLE enquiries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  customer_name text NOT NULL CHECK (length(customer_name) BETWEEN 2 AND 120),
  customer_email text,
  description text NOT NULL,
  job_details jsonb NOT NULL CHECK (jsonb_typeof(job_details)='object'),
  status text NOT NULL DEFAULT 'new' CHECK (status IN ('new','quoted','closed','cancelled')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id,id)
);
CREATE TABLE quotes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL,
  enquiry_id uuid NOT NULL,
  pricing_version_id uuid NOT NULL,
  estimate_snapshot jsonb NOT NULL CHECK (jsonb_typeof(estimate_snapshot)='object'),
  amount_pence bigint NOT NULL CHECK (amount_pence >= 0),
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','rejected','sent','accepted','expired')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (business_id,id),
  FOREIGN KEY (business_id,enquiry_id) REFERENCES enquiries(business_id,id),
  FOREIGN KEY (business_id,pricing_version_id) REFERENCES pricing_versions(business_id,id)
);
CREATE TABLE approval_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL,
  quote_id uuid NOT NULL,
  action text NOT NULL CHECK (action IN ('approve','reject','revise')),
  actor_subject text NOT NULL CHECK (length(actor_subject)>0),
  note text NOT NULL DEFAULT '',
  approved_pence bigint CHECK (approved_pence IS NULL OR approved_pence >= 0),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (business_id,quote_id) REFERENCES quotes(business_id,id)
);
CREATE TABLE booking_requests (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL,
  quote_id uuid NOT NULL,
  desired_start timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'requested'
    CHECK (status IN ('requested','confirmed','declined','cancelled')),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (business_id,quote_id) REFERENCES quotes(business_id,id)
);
CREATE TABLE photo_metadata (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id uuid NOT NULL,
  enquiry_id uuid NOT NULL,
  private_object_key text NOT NULL,
  media_type text NOT NULL CHECK (media_type IN ('image/jpeg','image/png','image/webp')),
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (business_id,enquiry_id) REFERENCES enquiries(business_id,id),
  UNIQUE (business_id,private_object_key)
);

CREATE INDEX idx_enquiries_business_created ON enquiries(business_id,created_at DESC);
CREATE INDEX idx_quotes_business_status ON quotes(business_id,status);
CREATE INDEX idx_approvals_business_quote ON approval_events(business_id,quote_id);
CREATE INDEX idx_bookings_business_start ON booking_requests(business_id,desired_start);

-- Defensive default: no exposed role can read/write these tables via RLS
-- until a deliberately reviewed identity-aware authorization layer is added.
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE photo_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE businesses FORCE ROW LEVEL SECURITY;
ALTER TABLE business_members FORCE ROW LEVEL SECURITY;
ALTER TABLE pricing_versions FORCE ROW LEVEL SECURITY;
ALTER TABLE enquiries FORCE ROW LEVEL SECURITY;
ALTER TABLE quotes FORCE ROW LEVEL SECURITY;
ALTER TABLE approval_events FORCE ROW LEVEL SECURITY;
ALTER TABLE booking_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE photo_metadata FORCE ROW LEVEL SECURITY;

-- TODO before connecting an online application:
-- 1. Select an identity provider and verify every user session server-side.
-- 2. Define audited RLS policies for each authenticated business member.
-- 3. Restrict role grants and service/database owner credentials.
-- 4. Enforce approval and booking state transitions transactionally.
-- 5. Add encrypted private object storage, retention and deletion.
-- 6. Perform tenant-isolation, abuse, authentication and backup testing.
