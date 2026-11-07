output "catalog" {
  description = "Local catalog entry; no cloud resources are created."
  value       = terraform_data.catalog.output
}
