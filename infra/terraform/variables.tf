variable "project_id" {
  type        = string
  description = "The GCP Project ID to deploy the patient onboarding agent."
  default     = "healthcare-agent-demo"
}

variable "region" {
  type        = string
  description = "GCP region for Cloud Run and Artifact Registry."
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Environment tier: development, staging, or production."
  default     = "production"
}
