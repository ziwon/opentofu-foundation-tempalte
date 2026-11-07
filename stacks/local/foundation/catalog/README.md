# local/foundation/catalog

Reusable resource composition for native roots in `live/`. Pass `context` from
`modules/context` and the declared resource inputs. Provider configuration and
backend state belong to the calling root.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
