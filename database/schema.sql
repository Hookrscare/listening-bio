-- Provisional PostgreSQL/PostGIS schema generated from the planning brief.
-- Replace/refine through Alembic when the original database_schema_ai_biodiversity.sql is supplied.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  external_id text UNIQUE,
  organization_type text,
  website_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email text NOT NULL UNIQUE,
  full_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role text NOT NULL DEFAULT 'owner',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_membership_org_user UNIQUE (organization_id, user_id)
);

CREATE TABLE projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  external_id text UNIQUE,
  description text,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name text NOT NULL,
  external_id text UNIQUE,
  habitat_type text,
  latitude double precision,
  longitude double precision,
  location_geom geometry(Point, 4326),
  location_geom_wkt text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audio_files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id uuid NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  uploaded_by_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  file_name text NOT NULL,
  idempotency_key text,
  storage_uri text NOT NULL,
  content_type text NOT NULL DEFAULT 'audio/wav',
  duration_seconds double precision,
  recorded_at timestamptz,
  status text NOT NULL DEFAULT 'uploaded',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_audio_file_status CHECK (status IN ('uploaded', 'queued', 'processing', 'processed', 'failed')),
  CONSTRAINT uq_audio_file_site_idempotency_key UNIQUE (site_id, idempotency_key)
);

CREATE TABLE processing_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  audio_file_id uuid NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'queued',
  job_type text NOT NULL DEFAULT 'mock_audio_analysis',
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_processing_job_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled'))
);

CREATE TABLE ai_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  version text NOT NULL,
  model_type text NOT NULL,
  provider text,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_ai_model_name_version UNIQUE (name, version)
);

CREATE TABLE species_reference (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scientific_name text NOT NULL UNIQUE,
  common_name text,
  gbif_taxon_key integer,
  taxon_rank text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_detection_type CHECK (detection_type IN ('species', 'sound_class')),
  CONSTRAINT ck_detection_review_status CHECK (review_status IN ('unreviewed', 'confirmed', 'rejected'))
);

CREATE TABLE raw_model_outputs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  processing_job_id uuid NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
  audio_file_id uuid NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
  ai_model_id uuid REFERENCES ai_models(id) ON DELETE SET NULL,
  output_format text NOT NULL DEFAULT 'mock_json',
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sound_classes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  label text NOT NULL UNIQUE,
  source text NOT NULL DEFAULT 'YAMNet',
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ck_grant_task_status CHECK (status IN ('todo', 'in_progress', 'done', 'blocked'))
);

CREATE TABLE detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  processing_job_id uuid NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
  audio_file_id uuid NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
  ai_model_id uuid REFERENCES ai_models(id) ON DELETE SET NULL,
  species_reference_id uuid REFERENCES species_reference(id) ON DELETE SET NULL,
  sound_class_id uuid REFERENCES sound_classes(id) ON DELETE SET NULL,
  detection_type text NOT NULL,
  label text NOT NULL,
  confidence double precision NOT NULL,
  start_seconds double precision NOT NULL DEFAULT 0,
  end_seconds double precision NOT NULL DEFAULT 0,
  review_status text NOT NULL DEFAULT 'unreviewed',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title text NOT NULL,
  report_type text NOT NULL DEFAULT 'prototype_summary',
  status text NOT NULL DEFAULT 'draft',
  storage_uri text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grant_opportunities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  funder_name text,
  deadline date,
  status text NOT NULL DEFAULT 'researching',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE grant_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  grant_opportunity_id uuid NOT NULL REFERENCES grant_opportunities(id) ON DELETE CASCADE,
  title text NOT NULL,
  status text NOT NULL DEFAULT 'todo',
  due_date date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE partners (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  partner_type text,
  status text NOT NULL DEFAULT 'prospect',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE partner_contacts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id uuid NOT NULL REFERENCES partners(id) ON DELETE CASCADE,
  full_name text NOT NULL,
  email text,
  role_title text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE research_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  title text NOT NULL,
  source_url text,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE outreach_messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  partner_id uuid REFERENCES partners(id) ON DELETE SET NULL,
  subject text NOT NULL,
  body text NOT NULL,
  status text NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE impact_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  snapshot_date date NOT NULL,
  species_richness integer NOT NULL DEFAULT 0,
  biodiversity_activity_score double precision NOT NULL DEFAULT 0,
  noise_score double precision NOT NULL DEFAULT 0,
  grant_readiness_score double precision NOT NULL DEFAULT 0,
  community_value_indicators jsonb NOT NULL DEFAULT '{}'::jsonb,
  metric_label text NOT NULL DEFAULT 'prototype_indicator',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE weekly_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  week_start_date date NOT NULL,
  summary text NOT NULL,
  recommended_actions jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid,
  metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE schema_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version text NOT NULL UNIQUE,
  source text NOT NULL,
  notes text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_sites_location_geom ON sites USING gist (location_geom);
CREATE INDEX idx_audio_files_site_id ON audio_files(site_id);
CREATE INDEX idx_processing_jobs_audio_file_id ON processing_jobs(audio_file_id);
CREATE INDEX idx_detections_audio_file_id ON detections(audio_file_id);
CREATE INDEX idx_detections_processing_job_id ON detections(processing_job_id);
CREATE INDEX idx_raw_model_outputs_processing_job_id ON raw_model_outputs(processing_job_id);
CREATE INDEX idx_grant_tasks_grant_opportunity_id ON grant_tasks(grant_opportunity_id);
