variable "context" {
  description = "Deployment identity and standard tags from the root context module."
  type = object({
    id   = string
    tags = map(string)
  })
  nullable = false
}

variable "network_cidr" {
  description = "Private network IPv4 CIDR."
  type        = string
  validation {
    condition     = can(cidrnetmask(var.network_cidr))
    error_message = "Use an IPv4 CIDR."
  }
}
variable "subnet_cidr" {
  description = "Private subnet IPv4 CIDR within the network range."
  type        = string
  validation {
    condition     = can(cidrnetmask(var.subnet_cidr))
    error_message = "Use an IPv4 CIDR."
  }
}
