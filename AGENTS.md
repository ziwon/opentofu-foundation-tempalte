# Working in this template

- Keep executable infrastructure in `stacks/`, reusable code in `modules/`, and
  non-secret environment data in `live/`.
- Commands use an explicit `environment/cloud/group/stack` deployment ID.
  Preserve isolated working data, derived state addresses, and saved-plan checks.
- Run `python3 tools/infra.py check` and the relevant local smoke tests. Validate
  compatibility with both `tofu` and `terraform` when changing shared tooling.
- Run `tools/quality_smoke.py` for security/lint changes; keep scanner failures fatal
  and never skip the saved-plan gate in apply, including with `--yes`.
- Bootstrap uses explicit commands and independent local state. Preserve its
  deletion protection and non-secret backend outputs.
- Mocked cloud tests are plan-only. Actual cloud apply, destroy, state migration,
  and resource provisioning require the user's authorization. The disposable
  local `terraform_data` smoke test is suitable for routine verification.
- Do not commit `.infra/`, credentials, state, saved plans, or raw cloud reports.
- Update documentation and provider lock files when their behavior or versions change.
- Explain resource replacements and migration steps in infrastructure PRs.
