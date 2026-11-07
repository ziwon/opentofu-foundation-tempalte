variable "context" {
  description = "Deployment identity and standard tags from the root context module."
  type = object({
    id   = string
    tags = map(string)
  })
  nullable = false
}

variable "create_oidc_provider" {
  description = "Create the account's GitHub Actions OIDC provider. Set false in every other deployment that shares the account."
  type        = bool
  default     = true
  nullable    = false
}

variable "roles" {
  description = "GitHub Actions roles keyed by a short name; each role is named <context.id>-<key>."
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
  description = "Exact GitHub Actions subjects that may assume <context.id>-audit, a read-only role for Prowler account scans. Empty creates no audit role."
  type        = set(string)
  default     = []
  nullable    = false
  validation {
    condition     = length(var.audit_subjects) == 0 || !contains(keys(var.roles), "audit")
    error_message = "The audit role key is reserved while audit_subjects is set."
  }
}
