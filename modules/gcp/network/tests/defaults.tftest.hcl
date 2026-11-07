variables {
  name        = "starter-fixture-dev"
  region      = "us-central1"
  subnet_cidr = "10.10.1.0/24"
}

mock_provider "google" {}
run "private_network" {
  command = plan
  assert {
    condition     = google_compute_network.this.name == "starter-fixture-dev" && !google_compute_network.this.auto_create_subnetworks && google_compute_network.this.routing_mode == "REGIONAL"
    error_message = "Create a regional network with explicit subnets, named after the deployment."
  }
  assert {
    condition     = google_compute_subnetwork.private.name == "starter-fixture-dev-private" && google_compute_subnetwork.private.region == "us-central1" && google_compute_subnetwork.private.ip_cidr_range == "10.10.1.0/24" && google_compute_subnetwork.private.private_ip_google_access
    error_message = "Create the private subnet in the given region and range with private access to Google APIs."
  }
  assert {
    condition     = one(google_compute_subnetwork.private.log_config).metadata == "INCLUDE_ALL_METADATA" && one(google_compute_subnetwork.private.log_config).flow_sampling == 0.5
    error_message = "Record subnet flow logs with all metadata."
  }
  assert {
    condition     = google_compute_firewall.deny_ingress.name == "starter-fixture-dev-deny-ingress" && google_compute_firewall.deny_ingress.direction == "INGRESS" && google_compute_firewall.deny_ingress.priority == 65534 && google_compute_firewall.deny_ingress.source_ranges == toset(["0.0.0.0/0"]) && one(google_compute_firewall.deny_ingress.deny).protocol == "all"
    error_message = "Unmatched inbound traffic must be denied."
  }
  assert {
    condition     = output.network_id == google_compute_network.this.id && output.network_name == google_compute_network.this.name && output.subnetwork_id == google_compute_subnetwork.private.id
    error_message = "Export the network and subnet identifiers."
  }
}
