variable "tags" {
  description = "Additional tags compatible with AWS, Azure, and GCP labels. Core context keys are reserved."
  type        = map(string)
  default     = {}
  nullable    = false

  validation {
    condition = alltrue([
      for key, value in var.tags :
      can(regex("^[a-z][a-z0-9_-]{0,62}$", key)) &&
      can(regex("^[a-z0-9_-]{0,63}$", value))
    ])
    error_message = "Tag keys must start with a lowercase letter and contain 1–63 lowercase letters, digits, underscores, or hyphens; values may contain 0–63 of those characters with no first-character restriction. Null values are not allowed."
  }

  validation {
    condition     = length(setintersection(toset(keys(var.tags)), toset(["project", "environment", "managed_by"]))) == 0
    error_message = "The project, environment, and managed_by tags are owned by the context module and cannot be overridden."
  }

  validation {
    condition     = length(var.tags) <= 46
    error_message = "Use at most 46 additional tags, reserving space for three standard tags and one resource-specific Name tag."
  }
}

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
