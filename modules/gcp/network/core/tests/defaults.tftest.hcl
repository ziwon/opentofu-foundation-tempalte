variables {
  region      = "us-central1"
  subnet_cidr = "10.10.1.0/24"
  context     = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

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
