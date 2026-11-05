# Working in this template

- Keep executable OpenTofu roots in `live/<environment>/<cloud>/<group>/<stack>`.
  Keep reusable resources in `modules/<cloud>/<group>/<stack>` and shared naming in `modules/context`.
- Roots own backends, provider configuration, inputs, outputs, and provider locks.
  Modules declare provider requirements but never configure providers or backends.
- Keep each root directly usable with native `tofu` commands. Python may check,
  generate examples, or inspect scanner reports. It must not orchestrate ordinary deployments.
- Preserve explicit backend identities and the default workspace. Local and bootstrap
  state belongs at `.infra/state/<deployment>/terraform.tfstate`.
- Run `python3 tools/check.py` and relevant local fixture tests. Support OpenTofu only.
- Run `python3 tools/quality_smoke.py` for security or lint changes. Scanner errors,
  unrecognized reports, and unsafe saved plans must fail trusted automation.
- Native local commands do not enforce repository fingerprints or approval prompts.
  Keep approval requirements and source/saved-plan scans in trusted deployment automation.
- Bootstrap uses independent local state and is excluded from Atlantis workloads.
  Preserve deletion protection and non-secret backend outputs.
- Cloud tests stay plan-only. Cloud apply, destroy, state migration, and provisioning
  require the user's authorization. Disposable local `terraform_data` fixtures are suitable for routine verification.
- Do not commit `.infra/`, credentials, state, saved plans, or raw cloud reports.
- Update documentation and provider locks when their behavior or versions change.
  Explain address changes, replacements, and migration steps in infrastructure PRs.
