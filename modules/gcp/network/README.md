# gcp/network

Core module that owns a regional GCP network without automatic subnets, one private
subnet with Google API access and flow logs, and a priority 65534 firewall rule that
denies and logs all ingress that no other rule allows. The subnet and rule names add `-private` and
`-deny-ingress` to `name`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
