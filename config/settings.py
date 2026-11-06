"""Configuration and environment settings for Hospital Patient Onboarding."""

import os
from pathlib import Path
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Hospital Onboarding Application Configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Gemini & GCP Configuration
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "mock-api-key"))
    google_cloud_project: str = Field(default="healthcare-agent-demo")
    google_cloud_region: str = Field(default="us-central1")
    google_genai_use_vertex: bool = Field(default=False)

    # Models
    onboarding_model_name: str = Field(default="gemini-3.8-flash")
    triage_model_name: str = Field(default="gemini-4-argon")

    # Hospital Domain Config
    hospital_name: str = Field(default="St. Jude Memorial Health System")
    hospital_id: str = Field(default="HOSP-NY-0924")
    default_timezone: str = Field(default="America/New_York")
    hipaa_audit_log_enabled: bool = Field(default=True)
    pii_redaction_enabled: bool = Field(default=True)

    # Storage & Sessions
    session_backend: Literal["memory", "sqlite", "firestore"] = Field(default="sqlite")
    sqlite_db_path: str = Field(default="/tmp/patient_onboarding_sessions.db")
    firestore_collection: str = Field(default="patient_onboarding_sessions")

    # EHR & FHIR Integration (Local HAPI FHIR container or mock)
    fhir_base_url: str = Field(default="http://localhost:8081/fhir")
    fhir_auth_token: str = Field(default="mock-token-xyz")
    enable_mock_ehr: bool = Field(default=True)
    consent_mode: str = Field(default="CONVERSATIONAL_VERBAL")

    # Observability & Tracing
    otel_service_name: str = Field(default="hospital-patient-onboarding-agent")
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317")
    enable_console_tracing: bool = Field(default=True)

    # Human-In-The-Loop Guards
    require_insurance_confirmation: bool = Field(default=True)
    require_clinical_risk_override: bool = Field(default=True)
    auto_approve_low_risk_registrations: bool = Field(default=True)


settings = Settings()
