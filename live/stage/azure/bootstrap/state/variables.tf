variable "allowed_ip_ranges" {
  description = "Public IPv4 addresses or CIDR ranges for operators and runners using the state backend. Empty denies all public clients."
  type        = list(string)
  default     = []
}

variable "allowed_subnet_ids" {
  description = "Subnet IDs with Microsoft.Storage service endpoints allowed to reach the state backend."
  type        = list(string)
  default     = []
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

variable "location" {
  description = "Azure location."
  type        = string
}
variable "subscription_id" {
  description = "Explicit Azure subscription; no ambient default subscription is used."
  type        = string
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "Provide a subscription UUID."
  }
}

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}
