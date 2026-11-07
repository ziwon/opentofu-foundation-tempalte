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
}
variable "subnet_cidr" {
  description = "Private subnet IPv4 CIDR within the network range."
  type        = string
}

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}
