from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    external_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    organization_type: Mapped[str | None] = mapped_column(String(80))
    website_url: Mapped[str | None] = mapped_column(String(500))

    projects: Mapped[list["Project"]] = relationship(back_populates="organization")
    api_keys: Mapped[list["APIKey"]] = relationship(back_populates="organization")


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="owner")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")

    organization: Mapped[Organization] = relationship(back_populates="projects")
    sites: Mapped[list["Site"]] = relationship(back_populates="project")


class Site(TimestampMixin, Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    habitat_type: Mapped[str | None] = mapped_column(String(120))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    location_geom_wkt: Mapped[str | None] = mapped_column(Text)

    project: Mapped[Project] = relationship(back_populates="sites")
    audio_files: Mapped[list["AudioFile"]] = relationship(back_populates="site")


class AudioFile(TimestampMixin, Base):
    __tablename__ = "audio_files"
    __table_args__ = (
        UniqueConstraint("site_id", "idempotency_key", name="uq_audio_file_site_idempotency_key"),
        CheckConstraint("status in ('uploaded', 'queued', 'processing', 'processed', 'failed')", name="ck_audio_file_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(120))
    storage_uri: Mapped[str] = mapped_column(String(800), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False, default="audio/wav")
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")

    site: Mapped[Site] = relationship(back_populates="audio_files")
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(back_populates="audio_file")


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        CheckConstraint("status in ('queued', 'running', 'completed', 'failed', 'cancelled')", name="ck_processing_job_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    audio_file_id: Mapped[str] = mapped_column(ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    job_type: Mapped[str] = mapped_column(String(80), nullable=False, default="mock_audio_analysis")
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    audio_file: Mapped[AudioFile] = relationship(back_populates="processing_jobs")
    detections: Mapped[list["Detection"]] = relationship(back_populates="processing_job")


class AIModel(TimestampMixin, Base):
    __tablename__ = "ai_models"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_ai_model_name_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    version: Mapped[str] = mapped_column(String(80), nullable=False)
    model_type: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SpeciesReference(TimestampMixin, Base):
    __tablename__ = "species_reference"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    scientific_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    common_name: Mapped[str | None] = mapped_column(String(255))
    gbif_taxon_key: Mapped[int | None] = mapped_column(Integer)
    taxon_rank: Mapped[str | None] = mapped_column(String(80))


class SoundClass(TimestampMixin, Base):
    __tablename__ = "sound_classes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    label: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="YAMNet")
    description: Mapped[str | None] = mapped_column(Text)


class Detection(TimestampMixin, Base):
    __tablename__ = "detections"
    __table_args__ = (
        CheckConstraint("detection_type in ('species', 'sound_class')", name="ck_detection_type"),
        CheckConstraint("review_status in ('unreviewed', 'confirmed', 'rejected')", name="ck_detection_review_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    processing_job_id: Mapped[str] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    audio_file_id: Mapped[str] = mapped_column(ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    ai_model_id: Mapped[str | None] = mapped_column(ForeignKey("ai_models.id", ondelete="SET NULL"))
    species_reference_id: Mapped[str | None] = mapped_column(ForeignKey("species_reference.id", ondelete="SET NULL"))
    sound_class_id: Mapped[str | None] = mapped_column(ForeignKey("sound_classes.id", ondelete="SET NULL"))
    detection_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unreviewed")

    processing_job: Mapped[ProcessingJob] = relationship(back_populates="detections")
    review_events: Mapped[list["ReviewEvent"]] = relationship(back_populates="detection")


class APIKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization: Mapped[Organization] = relationship(back_populates="api_keys")


class ReviewEvent(Base):
    __tablename__ = "review_events"
    __table_args__ = (
        CheckConstraint("previous_status in ('unreviewed', 'confirmed', 'rejected')", name="ck_review_event_previous_status"),
        CheckConstraint("new_status in ('unreviewed', 'confirmed', 'rejected')", name="ck_review_event_new_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    detection_id: Mapped[str] = mapped_column(ForeignKey("detections.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    previous_status: Mapped[str] = mapped_column(String(50), nullable=False)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    detection: Mapped[Detection] = relationship(back_populates="review_events")


class UsageEvent(Base):
    __tablename__ = "usage_events"
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_usage_event_quantity_nonnegative"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class RawModelOutput(TimestampMixin, Base):
    __tablename__ = "raw_model_outputs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    processing_job_id: Mapped[str] = mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False)
    audio_file_id: Mapped[str] = mapped_column(ForeignKey("audio_files.id", ondelete="CASCADE"), nullable=False)
    ai_model_id: Mapped[str | None] = mapped_column(ForeignKey("ai_models.id", ondelete="SET NULL"))
    output_format: Mapped[str] = mapped_column(String(80), nullable=False, default="mock_json")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class Report(TimestampMixin, Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(80), nullable=False, default="prototype_summary")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    storage_uri: Mapped[str | None] = mapped_column(String(800))


class GrantOpportunity(TimestampMixin, Base):
    __tablename__ = "grant_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    funder_name: Mapped[str | None] = mapped_column(String(255))
    deadline: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="researching")


class GrantTask(TimestampMixin, Base):
    __tablename__ = "grant_tasks"
    __table_args__ = (
        CheckConstraint("status in ('todo', 'in_progress', 'done', 'blocked')", name="ck_grant_task_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    grant_opportunity_id: Mapped[str] = mapped_column(ForeignKey("grant_opportunities.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="todo")
    due_date: Mapped[date | None] = mapped_column(Date)


class Partner(TimestampMixin, Base):
    __tablename__ = "partners"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="prospect")


class PartnerContact(TimestampMixin, Base):
    __tablename__ = "partner_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    partner_id: Mapped[str] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    role_title: Mapped[str | None] = mapped_column(String(200))


class ResearchItem(TimestampMixin, Base):
    __tablename__ = "research_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(800))
    notes: Mapped[str | None] = mapped_column(Text)


class OutreachMessage(TimestampMixin, Base):
    __tablename__ = "outreach_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    partner_id: Mapped[str | None] = mapped_column(ForeignKey("partners.id", ondelete="SET NULL"))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")


class ImpactSnapshot(TimestampMixin, Base):
    __tablename__ = "impact_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    species_richness: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    biodiversity_activity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    noise_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    grant_readiness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    community_value_indicators: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    metric_label: Mapped[str] = mapped_column(String(120), nullable=False, default="prototype_indicator")


class WeeklyReview(TimestampMixin, Base):
    __tablename__ = "weekly_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_actions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class SchemaVersion(TimestampMixin, Base):
    __tablename__ = "schema_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    version: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
