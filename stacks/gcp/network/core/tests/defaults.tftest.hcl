mock_provider "google" {}
run "private_network" {
  command = plan
  assert {
    condition     = !google_compute_network.this.auto_create_subnetworks && google_compute_subnetwork.private.private_ip_google_access
    error_message = "Use explicit subnets and private access to Google APIs."
  }
  assert {
    condition     = one(google_compute_firewall.deny_ingress.deny).protocol == "all"
    error_message = "Unmatched inbound traffic must be denied."
  }
}
