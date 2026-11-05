variable "context" {
  description = "Deployment identity and standard tags from the root context module."
  type = object({
    id   = string
    tags = map(string)
  })
  nullable = false
}

variable "region" {
  description = "GCP region for this deployment."
  type        = string
}
variable "project_id" {
  description = "Explicit GCP project; credentials must have access to it."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Provide a valid GCP project ID."
  }
}
