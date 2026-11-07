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

variable "description" {
  description = "A local-only catalog entry to exercise the deployment workflow."
  type        = string
}

variable "tags" {
  description = "Additional portable tags or labels; standard context tags are reserved."
  type        = map(string)
  default     = {}
  nullable    = false
}
