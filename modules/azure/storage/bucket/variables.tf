variable "context" {
  description = "Deployment identity and standard tags from the root context module."
  type = object({
    id   = string
    tags = map(string)
  })
  nullable = false
}

variable "allowed_ip_ranges" {
  description = "Public IPv4 addresses or CIDR ranges allowed to reach blobs. Empty denies all public clients."
  type        = list(string)
  default     = []
}
variable "allowed_subnet_ids" {
  description = "Subnet IDs with Microsoft.Storage service endpoints allowed to reach blobs."
  type        = list(string)
  default     = []
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
