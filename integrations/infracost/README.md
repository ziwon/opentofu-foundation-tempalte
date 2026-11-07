# Estimate costs with Infracost

This optional integration prices a saved plan with Infracost 0.10.47. The template's
checks, CI, and Atlantis workflow do not use it, and every root works without it.

Infracost looks up prices through the Infracost pricing API, so it needs network
access and an API key. Its estimates are advisory. They use list prices and assumed
usage, and they do not replace a review of the plan or your cloud bill.

## Install the pinned CLI

The pin lives in this directory's `mise.toml`, so a plain `mise install` at the
repository root does not download a tool that needs an account. The same file turns
off the Infracost update check.

```sh
mise trust integrations/infracost/mise.toml
mise -C integrations/infracost install
```

The recipe uses the 0.10 CLI's `breakdown` command on a saved plan. Check that a
newer Infracost release still supports `breakdown --path <plan.json>` before you raise the pin.

## Provide the API key

Get a key from the [Infracost dashboard](https://dashboard.infracost.io) and export it
as `INFRACOST_API_KEY`. In CI, read it from the platform's secret store. Do not
commit the key or write it to `.env` files, `mise.toml`, or tool configuration in
the repository.

## Price a saved plan

Save a plan, then run the `cost` recipe through the integration's tools:

```sh
just plan dev/aws/network/core
mise -C integrations/infracost exec -- just cost dev/aws/network/core
```

The recipe runs these native commands from the repository root:

```sh
mkdir -p .infra/cost/dev/aws/network/core
tofu -chdir=live/dev/aws/network/core show -json plan.tfplan > .infra/cost/dev/aws/network/core/plan.json
infracost breakdown --path .infra/cost/dev/aws/network/core/plan.json
```

## Keep the plan JSON private

The plan JSON holds the same values as the saved plan, including attributes marked
`sensitive`. The recipe writes it under the ignored `.infra/` directory. Delete it
when you discard the saved plan. Do not print it in CI logs or upload it as a build
artifact. Infracost parses the file locally and sends price-lookup attributes, such
as region and instance type, to its pricing API. If your Infracost organization
enables its cloud dashboard, results are uploaded too. Check that your data-handling
policy allows this before you price a production root. See [SECURITY.md](../../SECURITY.md).
