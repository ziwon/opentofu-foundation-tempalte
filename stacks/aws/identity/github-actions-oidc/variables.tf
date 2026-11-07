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
