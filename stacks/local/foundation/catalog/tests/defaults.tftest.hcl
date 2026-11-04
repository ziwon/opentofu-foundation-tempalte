run "environment_namespacing" {
  command = plan
  assert {
    condition     = output.deployment_name == "${var.namespace}-${var.name}-${var.environment}"
    error_message = "Names must include the selected environment."
  }
}
