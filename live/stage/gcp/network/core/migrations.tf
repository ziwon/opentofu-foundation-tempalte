moved {
  from = google_compute_network.this
  to   = module.stack.google_compute_network.this
}

moved {
  from = google_compute_subnetwork.private
  to   = module.stack.google_compute_subnetwork.private
}

moved {
  from = google_compute_firewall.deny_ingress
  to   = module.stack.google_compute_firewall.deny_ingress
}
