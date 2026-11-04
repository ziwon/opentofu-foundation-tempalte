output "id" {
  description = "Resource name shared across the deployment."
  value       = local.id
}
output "tags" {
  description = "Labels compatible with AWS, Azure, and GCP."
  value       = local.tags
}
