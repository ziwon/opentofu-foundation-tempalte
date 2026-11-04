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
  description = "AWS region for this deployment."
  type        = string
}
variable "aws_account_id" {
  description = "Expected AWS account; the provider rejects credentials for another account."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "An AWS account ID contains 12 digits."
  }
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
