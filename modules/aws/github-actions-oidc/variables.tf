variable "create_oidc_provider" {
  description = "Create the account's GitHub Actions OIDC provider. Set false to trust a provider that another deployment manages in the same account."
  type        = bool
  default     = true
  nullable    = false
}

variable "roles" {
  description = "IAM roles keyed by caller name. Each trusts exact GitHub Actions subjects, and optional prefix patterns, for the STS audience."
  type = map(object({
    name                 = string
    subjects             = optional(set(string), [])
    subject_patterns     = optional(set(string), [])
    managed_policy_arns  = optional(set(string), [])
    inline_policy_json   = optional(string)
    max_session_duration = optional(number, 3600)
    permissions_boundary = optional(string)
  }))
  nullable = false

  validation {
    condition     = alltrue([for role in values(var.roles) : length(role.subjects) + length(role.subject_patterns) > 0])
    error_message = "Every role needs at least one subject or subject pattern."
  }
  validation {
    condition = alltrue(flatten([for role in values(var.roles) : [
      for subject in role.subjects : can(regex("^repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:(ref:refs/(heads|tags)/|environment:)[^*?\\s]+$", subject))
    ]]))
    error_message = "Subjects must be exact, without wildcards, in the form repo:<owner>/<repo>:ref:refs/heads/<branch>, repo:<owner>/<repo>:ref:refs/tags/<tag>, or repo:<owner>/<repo>:environment:<name>."
  }
  validation {
    condition = alltrue(flatten([for role in values(var.roles) : [
      for pattern in role.subject_patterns : can(regex("^repo:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:(ref:refs/(heads|tags)/|environment:)[^*?\\s]+\\*$", pattern))
    ]]))
    error_message = "Subject patterns must name a branch, tag, or environment prefix and end in a single *, such as repo:<owner>/<repo>:ref:refs/heads/release/*."
  }
  validation {
    condition     = alltrue([for role in values(var.roles) : role.max_session_duration >= 3600 && role.max_session_duration <= 43200])
    error_message = "IAM accepts a max_session_duration from 3600 to 43200 seconds."
  }
  validation {
    condition     = alltrue([for role in values(var.roles) : can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", role.name))])
    error_message = "IAM role names have at most 64 letters, digits, or +=,.@_- characters."
  }
}
