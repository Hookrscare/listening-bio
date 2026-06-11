from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    organization_type: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    name: str
    description: str | None = None
    status: str


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    habitat_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class AudioFileCreate(BaseModel):
    site_id: str
    file_name: str
    idempotency_key: str | None = None
    storage_uri: str
    content_type: str = "audio/wav"
    duration_seconds: float | None = Field(default=None, ge=0)
    recorded_at: datetime | None = None
    uploaded_by_user_id: str | None = None


class AudioFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    site_id: str
    file_name: str
    idempotency_key: str | None = None
    storage_uri: str
    content_type: str
    duration_seconds: float | None = None
    status: str


class ProcessingJobCreate(BaseModel):
    audio_file_id: str
    job_type: str = "mock_audio_analysis"


class ProcessingJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    audio_file_id: str
    status: str
    job_type: str
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class DetectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    processing_job_id: str
    audio_file_id: str
    detection_type: str
    label: str
    confidence: float
    start_seconds: float
    end_seconds: float
    review_status: str


class RawModelOutputRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    processing_job_id: str
    audio_file_id: str
    ai_model_id: str | None = None
    output_format: str
    payload: dict[str, Any]


class ReportCreate(BaseModel):
    project_id: str
    title: str
    report_type: str = "prototype_summary"
    status: str = "draft"
    storage_uri: str | None = None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    report_type: str
    status: str
    storage_uri: str | None = None


class ProjectSummary(BaseModel):
    project_id: str
    project_name: str
    site_count: int
    audio_file_count: int
    detection_count: int
    species_richness: int
    biodiversity_activity_score: float
    noise_score: float
    metric_label: str = "prototype_indicator"
