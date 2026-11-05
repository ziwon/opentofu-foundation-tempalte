output "id" {
  description = "Canonical deployment name: namespace-name-environment. Add resource-specific suffixes where needed."
  value       = local.id
}
output "tags" {
  description = "Standard context tags merged with additional portable tags for AWS, Azure, and GCP."
  value       = local.tags
}
