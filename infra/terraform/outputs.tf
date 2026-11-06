output "artifact_registry_repo" {
  description = "The Artifact Registry Docker repository URI."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agent_repo.repository_id}"
}

output "service_account_email" {
  description = "The dedicated service account email for Cloud Run."
  value       = google_service_account.agent_sa.email
}
