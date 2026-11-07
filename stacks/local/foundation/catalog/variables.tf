variable "context" {
  description = "Deployment identity and standard tags from the root context module."
  type = object({
    id   = string
    tags = map(string)
  })
  nullable = false
}

variable "description" {
  description = "A local-only catalog entry to exercise the deployment workflow."
  type        = string
}
