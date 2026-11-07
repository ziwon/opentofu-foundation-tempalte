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
}

variable "name" {
  description = "Lowercase name used in resource names and labels."
  type        = string
}

variable "environment" {
  description = "Lowercase environment used in resource names and labels."
  type        = string
}

variable "location" {
  description = "Azure location."
  type        = string
}
variable "subscription_id" {
  description = "Explicit Azure subscription; no ambient default subscription is used."
  type        = string
}

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}
