variable "name_base" {
  description = "Hyphenated deployment ID that the account name derives from, such as module.context.id."
  type        = string
}
variable "subscription_id" {
  description = "Subscription ID hashed into the account name suffix."
  type        = string
}
variable "resource_group_name" {
  description = "Resource group that holds the account."
  type        = string
}
variable "location" {
  description = "Azure location."
  type        = string
}
variable "replication_type" {
  description = "Account replication type, such as LRS or ZRS."
  type        = string
}
variable "delete_retention_days" {
  description = "Days that deleted blobs and deleted containers are retained."
  type        = number
}
variable "container_name" {
  description = "Name of the private Blob container."
  type        = string
}
variable "allowed_ip_ranges" {
  description = "Public IPv4 addresses or CIDR ranges allowed through the account firewall. Empty denies all public clients."
  type        = list(string)
}
variable "allowed_subnet_ids" {
  description = "Subnet IDs with Microsoft.Storage service endpoints allowed through the account firewall."
  type        = list(string)
}
variable "tags" {
  description = "Tags applied to the account."
  type        = map(string)
  nullable    = false
}
