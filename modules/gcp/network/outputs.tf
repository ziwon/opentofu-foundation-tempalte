output "network_id" {
  description = "Network identifier."
  value       = google_compute_network.this.id
}

output "network_name" {
  description = "Network name."
  value       = google_compute_network.this.name
}

output "subnetwork_id" {
  description = "Private subnet identifier."
  value       = google_compute_subnetwork.private.id
}

output "subnet_cidr" {
  description = "Private subnet IPv4 CIDR."
  value       = google_compute_subnetwork.private.ip_cidr_range
}
