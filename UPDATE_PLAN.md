# Update Plan

The project was created roughly 7–8 months ago. This is a numbered list of work to bring it up to date. Versions below come from `pip list --outdated`, `pnpm outdated` and `npm outdated` as of 2026-11-24. Completed items have been removed.

---

1. **Set up Dependabot or Renovate.** This is an open ROADMAP item and there is no `.github/dependabot.yml`. Cover uv/pip, npm (`scripts/site` and `cypress`), docker and github-actions. The Dockerfile base images are pinned by digest, so the docker ecosystem is needed to keep those digests current.

2. **Extend the CI test matrix** with more Python versions. This is an open ROADMAP item.

3. **Run the security checks and triage the findings.** Run `make audit` (pip-audit), the Trivy image scan, gitleaks and the ZAP baseline scan. Fix what they find and regenerate `docs/sbom.json` with `make sbom`.

4. **Refresh stale docs and reports.**
    - `BUG_REPORT.md` was generated on 21 March 2026 for v2.1.0. The project is now at 2.2.3.
    - `OPEN_SOURCE_READINESS.md`
    - `reports/`
    - Version references in `README.md` and `SELF_HOSTING.md`

    Optionally re-run the bugs, security and tidy sweeps.

5. **Verify the scraper against upstream FOSDEM.** Confirm the schedule XML URL and format still match. Check for the upcoming edition's data, and update any year-specific config, defaults and test fixtures.

6. **Clean up the repo.** Remove the stale `src/fosdem_atlas.egg-info` (git-ignored, but still on disk).

7. **Clear the open ROADMAP items**, or decide to defer them.
    - Fix the heatmap colour-scale tooltip when all event counts are zero.
    - Public roadmap page.
    - i18n support.

8. **Final verification and release.**
    - Run `make lint`, `make test`, `make test-js` and `make cy-run`.
    - Build and run the Docker image, then do a manual smoke test.
    - Run `make bump` to version, update the changelog and tag.

---

## Suggested order

1, 2 → 3–7 → 8
