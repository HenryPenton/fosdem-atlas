# Update Plan

The project was created roughly 7–8 months ago. This is a numbered list of work to bring it up to date. Versions below come from `pip list --outdated`, `pnpm outdated` and `npm outdated` as of 2026-11-24. Completed items have been removed.

---

1. **Finish the Docker updates.** `docker/Dockerfile` is already on `node:24-slim` and a uv-managed Python 3.14. `docker-compose.yml` only builds the local Dockerfile and has no images of its own. Still to do: consider pinning the Dockerfile base images (`node:24-slim`, `ghcr.io/astral-sh/uv:0.13.9-debian-slim`) by digest.

2. **Set up Dependabot or Renovate.** This is an open ROADMAP item and there is no `.github/dependabot.yml`. Cover uv/pip, npm (`scripts/site` and `cypress`), docker and github-actions.

3. **Extend the CI test matrix** with more Python versions. This is an open ROADMAP item.

4. **Run the security checks and triage the findings.** Run `make audit` (pip-audit), the Trivy image scan, gitleaks and the ZAP baseline scan. Fix what they find and regenerate `docs/sbom.json` with `make sbom`.

5. **Refresh stale docs and reports.**
    - `BUG_REPORT.md` was generated on 21 March 2026 for v2.1.0. The project is now at 2.2.3.
    - `OPEN_SOURCE_READINESS.md`
    - `reports/`
    - Version references in `README.md` and `SELF_HOSTING.md`

    Optionally re-run the bugs, security and tidy sweeps.

6. **Verify the scraper against upstream FOSDEM.** Confirm the schedule XML URL and format still match. Check for the upcoming edition's data, and update any year-specific config, defaults and test fixtures.

7. **Clean up the repo.** Remove the stale `src/fosdem_atlas.egg-info` (git-ignored, but still on disk).

8. **Clear the open ROADMAP items**, or decide to defer them.
    - Fix the heatmap colour-scale tooltip when all event counts are zero.
    - Public roadmap page.
    - i18n support.

9. **Final verification and release.**
    - Run `make lint`, `make test`, `make test-js` and `make cy-run`.
    - Build and run the Docker image, then do a manual smoke test.
    - Run `make bump` to version, update the changelog and tag.

---

## Suggested order

1 → 2, 3 → 4–8 → 9
