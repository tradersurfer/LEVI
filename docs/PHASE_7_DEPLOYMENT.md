# Phase 7 — Release Engineering

Phase 7 packages and documents the existing application without adding features. The Python 3.11 image runs non-root and exposes `/health` and `/ready`. Local Compose includes app, workspace, and PostgreSQL; production Compose requires explicit security configuration.

Scripts provide PowerShell/shell installation, environment validation, offline secret audit, health-performance baseline, and smoke testing. CI verifies backend tests, frontend tests/lint/build, compilation, audits, and Docker construction. Release automation is gated to `v*` tags.

Local targets are startup below 5 seconds and health response below 1 second. Memory below 500 MB must be observed in hosting because portable offline accounting is unreliable across supported systems.

Release notes are draft assets only. This phase does not create a tag, publish a release, push a branch, or implement Phases 4–6.
