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

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "create_oidc_provider" {
  description = "Create the account's GitHub Actions OIDC provider. Exactly one deployment per AWS account sets true."
  type        = bool
  nullable    = false
}

variable "roles" {
  description = "GitHub Actions roles keyed by a short name; each role is named <deployment name>-<key>."
  type = map(object({
    subjects             = optional(set(string), [])
    subject_patterns     = optional(set(string), [])
    managed_policy_arns  = optional(set(string), [])
    inline_policy_json   = optional(string)
    max_session_duration = optional(number, 3600)
    permissions_boundary = optional(string)
  }))
  nullable = false
}

variable "audit_subjects" {
  description = "Exact GitHub Actions subjects that may assume <deployment name>-audit, a read-only role for Prowler account scans. Empty creates no audit role."
  type        = set(string)
  nullable    = false
}
