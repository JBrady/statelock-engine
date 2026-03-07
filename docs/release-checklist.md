# Release Checklist

## Pre-release

1. Ensure branch is up to date with `main`.
1. Run `make lint` and `make test`.
1. Run `make web-check` when `apps/web` is present.
1. Verify `.env.example` matches current required env vars.
1. Confirm docs updates for any public interface changes.
1. Update `CHANGELOG.md` under `[Unreleased]`.

## Version cut

1. Bump `API_VERSION` in `.env.example` and deployment env if needed.
1. Move `[Unreleased]` notes to a dated version section in `CHANGELOG.md`.
1. Tag release:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`

## Post-release

1. Publish GitHub release notes from `CHANGELOG.md`.
1. Smoke test:
   - `GET /healthz`
   - `GET /readyz`
   - one `memory.query` + one `memory.save` flow
1. Smoke test the unified web UI when `apps/web` ships in the release.
1. Archive exported snapshot fixture for rollback testing.
