# Open-Source Readiness Audit

_Audited: 21 March 2026 (v1.1.0)_
_Previous audit: 19 March 2026 (v0.7.0)_

---

## Recommended (Not Blocking)

### 1. Add CODE_OF_CONDUCT.md

Standard for open-source projects. Establishes community norms and an
incident-reporting contact. GitHub provides a template via
**Settings > Community Standards > Code of conduct**.

### 2. Add SECURITY.md

Tells users how to responsibly disclose vulnerabilities. Suggested content:

```markdown
# Security Policy

## Reporting a Vulnerability

Please do not open a public GitHub issue for security vulnerabilities.
Email [your-email] with the subject "FOSDEM Explorer Security Report".
You can expect a response within 72 hours.
```

### 3. Add `[project.urls]` to pyproject.toml

The repository/homepage URLs are missing from the package metadata. Add:

```toml
[project.urls]
Repository = "https://github.com/<your-username>/fosdem-explorer"
```

### 4. Add security headers

The app sets no `Content-Security-Policy`, `X-Frame-Options`,
`X-Content-Type-Options`, or `Strict-Transport-Security` headers. Any page can
be iframed and content-sniffed. Add middleware in `src/adapters/web/app.py`
before public deployment.

### 5. Pin production dependencies

All 12 runtime dependencies in `pyproject.toml` have no version constraints.
A breaking release of `fastapi`, `duckdb`, or `apscheduler` (3.x → 4.x) could
silently break the app for contributors running `pip install -e .`. Add lower
bounds at minimum (e.g. `fastapi>=0.115`).

### 6. Test against Python 3.11 in CI

`requires-python = ">=3.11"` but CI (`ci.yml`) only tests 3.12. Add a matrix
entry for 3.11 to guarantee documented compatibility.

### 7. Add Docker image vulnerability scanning

No `trivy` or equivalent in the release workflow. Consider adding a scan step
before pushing the image.

---

## Clean — No Action Required

| Area                  | Status           | Notes                                                                                                                          |
| --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Secrets / credentials | ✅ Clear         | No hardcoded keys or tokens. `.env` is gitignored. Config uses `pydantic-settings` with a `FOSDEM_` prefix.                    |
| License               | ✅ Good          | MIT + CC BY 4.0 dual-licence declared in `LICENSE`, `DATA_LICENSE.md`, `pyproject.toml`, and the template footer.              |
| .gitignore            | ✅ Comprehensive | Covers `__pycache__`, `.env`, `*.duckdb`, `data/`, IDE files, build artefacts, `node_modules/`, Cypress screenshots/videos.    |
| Configuration         | ✅ Safe          | `debug` defaults to `False`. All settings come from environment variables.                                                     |
| Docker                | ✅ Good          | Non-root `app` user, no secrets, health checks defined, proper `.dockerignore`.                                                |
| SQL injection         | ✅ Safe          | All queries use parameterised statements. Dynamic WHERE clauses bind user input as params, not string interpolation.           |
| XSS                   | ✅ Acceptable    | `| safe` is used on FOSDEM abstracts in `event.html` and `partials/event_card.html` (a trusted, read-only data source). Jinja2 auto-escaping is active everywhere else. |
| Tests                 | ✅ Clean         | 249 Python tests passing (85% coverage). Fabricated fixture data, in-memory DuckDB, no real endpoints. Cypress suite (28 a11y + 18 smoke) runs in CI. k6 load/smoke tests use `localhost` by default. |
| Data files            | ✅ Gitignored    | `data/fosdem.duckdb` matches `*.duckdb` and `data/` patterns — will not be committed.                                          |
| TODOs / internal refs | ✅ Clear         | No TODO, FIXME, internal hostnames, email addresses, or private URLs found.                                                    |
| CHANGELOG / ROADMAP   | ✅ Public-ready  | No internal-only content. CHANGELOG current through v1.1.0; ROADMAP reflects all completed phases 1–5.                        |
| Cypress / npm         | ✅ Contained     | All Node artefacts live in `cypress/` subdirectory. `node_modules/`, screenshots, videos are gitignored.                       |
| Lint / type-checking  | ✅ Clean         | `ruff check`, `ruff format --check`, and `mypy` all pass with zero issues.                                                    |

---

## Corrections from v0.7.0 Audit

| Item | Previous Claim | Correction |
| ---- | -------------- | ---------- |
| XSS `| safe` locations | Listed `event.html`, `keyword.html`, `track.html` | Actually only in `event.html` and `partials/event_card.html`. `keyword.html` and `track.html` do not use `| safe`. |

---

## Optional Enhancements

- **SPDX licence headers** in `.py` files (e.g. `# SPDX-License-Identifier: MIT`) — optional but provides the strongest machine-readable licence clarity for large-scale reuse.
