# Release Checklist

## Pre-release

1. Ensure branch is up to date with `main`.
2. Run `make lint` and `make test`.
3. Verify `.env.example` matches current required env vars.
4. Confirm docs updates for any public interface changes.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Version cut

1. Bump `API_VERSION` in `.env.example` and deployment env if needed.
2. Move `[Unreleased]` notes to a dated version section in `CHANGELOG.md`.
3. Tag release:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`

## Post-release

1. Publish GitHub release notes from `CHANGELOG.md`.
2. Smoke test:
   - `GET /healthz`
   - `GET /readyz`
   - one `memory.query` + one `memory.save` flow
3. Archive exported snapshot fixture for rollback testing.
