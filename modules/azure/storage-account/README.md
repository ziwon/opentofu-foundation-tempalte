# azure/storage-account

Core module that owns one Azure storage account and its private Blob container.
`stacks/azure/bootstrap/state` and `stacks/azure/storage/bucket` call it as
`module "storage_account"` and keep their resource groups themselves.

The account denies network access by default, disables shared keys and anonymous
access, requires TLS 1.2 and HTTPS, and keeps blob versions. Callers choose the
replication type, the blob and container soft-delete days, the container name, the
allowed IP ranges and subnets, and the tags. The account and the container always
use `prevent_destroy`.

The module derives the account name from `name_base` and `subscription_id`. It
removes hyphens and keeps the first 18 characters, then appends 6 characters of a
SHA-1 suffix. The suffix hashes only the subscription ID when nothing was truncated,
and the subscription ID and full `name_base` otherwise. See [names and tags](../../../docs/context.md).

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
