variable "namespace" {
  description = "Lowercase namespace used in resource names and labels."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,15}$", var.namespace))
    error_message = "Use 1–16 lowercase letters, digits, or hyphens, beginning with a letter."
  }
}

variable "name" {
  description = "Lowercase name used in resource names and labels."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,15}$", var.name))
    error_message = "Use 1–16 lowercase letters, digits, or hyphens, beginning with a letter."
  }
}

variable "environment" {
  description = "Lowercase environment used in resource names and labels."
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,15}$", var.environment))
    error_message = "Use 1–16 lowercase letters, digits, or hyphens, beginning with a letter."
  }
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
