variable "id" {
  description = "Deployment identifier; the bucket is named <id>-<project_id>."
  type        = string
}

variable "project_id" {
  description = "GCP project ID appended to the bucket name."
  type        = string
}

variable "location" {
  description = "GCS location for the bucket."
  type        = string
}

variable "labels" {
  description = "Labels set on the bucket."
  type        = map(string)
  nullable    = false
}

variable "soft_delete_retention_seconds" {
  description = "Soft delete retention in seconds; null leaves the policy to the provider."
  type        = number
  default     = null
}
