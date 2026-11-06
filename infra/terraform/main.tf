terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.25.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required Google Cloud APIs for ADK and Healthcare
resource "google_project_service" "enabled_apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtrace.googleapis.com",
    "logging.googleapis.com",
    "aiplatform.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# Artifact Registry Repository for Healthcare Agents
resource "google_artifact_registry_repository" "agent_repo" {
  location      = var.region
  repository_id = "hospital-agents"
  description   = "Docker repository for Hospital AI Agents"
  format        = "DOCKER"
  depends_on    = [google_project_service.enabled_apis]
}

# Dedicated Service Account for HIPAA compliance
resource "google_service_account" "agent_sa" {
  account_id   = "sa-onboarding-agent"
  display_name = "Service Account for Hospital Patient Onboarding Agent"
}

# Secret Manager for Gemini API Key
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.enabled_apis]
}

# Grant Service Account access to read secrets
resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.gemini_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Grant Cloud Trace Agent role for OpenTelemetry
resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
