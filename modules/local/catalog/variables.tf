variable "name" {
  description = "Catalog entry name."
  type        = string
}

variable "tags" {
  description = "Tags recorded with the catalog entry."
  type        = map(string)
  nullable    = false
}

variable "description" {
  description = "Catalog entry description."
  type        = string
}
