# Frozen legacy local catalog

These files are byte-for-byte copies from commit
`657f324df43b4b203a759011af9792a7a450cf57`, before the native-root migration.
They contain the [shared local catalog](stacks/local/foundation/catalog/), the
[context module](modules/context/), and the [dev](live/dev/local/foundation/catalog/terraform.tfvars.json)
and [prod](live/prod/local/foundation/catalog/terraform.tfvars.json) inputs needed
to create the old local states.

The [migration check](../../../tools/migration_smoke.py) creates those states
before loading the current native roots with the same frozen inputs. This committed fixture lets the check
run in template-generated repositories and source archives without Git history.
Keep this baseline frozen when changing current roots so the check can detect
changes to resource values, IDs, output values, and output types.
