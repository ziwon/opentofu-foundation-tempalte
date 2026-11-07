variable "namespace" {
  description = "Lowercase namespace used in resource names and labels."
  type        = string
}

variable "name" {
  description = "Lowercase name used in resource names and labels."
  type        = string
}

variable "environment" {
  description = "Lowercase environment used in resource names and labels."
  type        = string
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

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}
