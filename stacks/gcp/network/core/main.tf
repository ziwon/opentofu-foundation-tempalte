module "naming" {
  source      = "../../../../modules/naming"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
}

resource "google_compute_network" "this" {
  name                    = module.naming.id
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}
resource "google_compute_subnetwork" "private" {
  name                     = "${module.naming.id}-private"
  network                  = google_compute_network.this.id
  region                   = var.region
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
resource "google_compute_firewall" "deny_ingress" {
  name          = "${module.naming.id}-deny-ingress"
  network       = google_compute_network.this.name
  direction     = "INGRESS"
  priority      = 65534
  source_ranges = ["0.0.0.0/0"]
  deny { protocol = "all" }
  log_config { metadata = "INCLUDE_ALL_METADATA" }
}
