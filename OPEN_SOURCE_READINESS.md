# Open-Source Readiness Audit

_Audited: 21 March 2026 (v2.1.0)_
_Previous audits: 21 March 2026 (v1.1.0), 19 March 2026 (v0.7.0)_

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

### 4. Add `Content-Security-Policy` and `Strict-Transport-Security` headers

`X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` are now
set (fixed since v1.1.0 audit). However, `Content-Security-Policy` and
`Strict-Transport-Security` are still absent. Add these in the
`add_security_headers` middleware in `src/adapters/web/app.py` before public
deployment.

### 5. Test against Python 3.11 in CI

`requires-python = ">=3.11"` but `.github/workflows/ci.yml` only tests 3.12.
The security workflow uses 3.11 for Trivy, but the main CI test job does not.
Add a matrix entry for 3.11 to guarantee documented compatibility.

### 6. Fix version mismatch across configuration files

`pyproject.toml` correctly shows `2.1.0` but three other locations still
contain `0.1.0`:
- `src/__init__.py` — `__version__ = "0.1.0"`
- `src/config.py` — `version: str = "0.1.0"`
- `.env.example` — `FOSDEM_VERSION=0.1.0`

The health endpoint and startup logs display the stale version. These should
be updated or, ideally, read the version dynamically from `pyproject.toml` via
`importlib.metadata`.

### 7. Replace `print()` with `logging` in `src/main.py`

Ten `print()` calls handle startup, shutdown, and scrape status messages.
Production applications should use Python's `logging` module for structured
log levels, filtering, and integration with log aggregation tools. Other
modules (e.g. `src/adapters/web/routers/health.py`) already use `logging`.

### 8. Add screenshots to README.md or remove placeholders

Seven `<!-- TODO: Add screenshot … -->` HTML comments remain in `README.md`
(lines 5, 20, 76, 78, 80, 82, 84). Either add screenshots for a polished
first impression or remove the comments.

---

## Resolved Since v1.1.0 Audit

| Item | Previous Status | Current Status |
| ---- | --------------- | -------------- |
| Pin production dependencies | ❌ All 12 deps unpinned | ✅ All deps have exact versions (e.g. `fastapi==0.135.1`) |
| Security headers | ❌ No security headers | ✅ `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` set (CSP/HSTS still missing — see item 4) |
| Docker image vulnerability scanning | ❌ No Trivy | ✅ Semgrep + Trivy in `.github/workflows/security.yml` (scans dependencies; image scan in release workflow still recommended) |
| SBOM | Not mentioned | ✅ CycloneDX SBOM generated at `docs/sbom.json` |

---

## Clean — No Action Required

| Area                  | Status           | Notes                                                                                                                          |
| --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Secrets / credentials | ✅ Clear         | No hardcoded keys or tokens. `.env` is gitignored. Config uses `pydantic-settings` with a `FOSDEM_` prefix.                    |
| License               | ✅ Good          | MIT + CC BY 4.0 dual-licence declared in `LICENSE`, `DATA_LICENSE.md`, `pyproject.toml`, and the template footer.              |
| .gitignore            | ✅ Comprehensive | Covers `__pycache__`, `.env`, `*.duckdb`, `data/`, IDE files, build artefacts, `node_modules/`, Cypress screenshots/videos.    |
| Configuration         | ✅ Safe          | `debug` defaults to `False`. All settings come from environment variables.                                                     |
| Docker                | ✅ Good          | Multi-stage build, non-root `app` user, no secrets, health checks defined, proper `.dockerignore`.                             |
| SQL injection         | ✅ Safe          | All queries use parameterised statements. Dynamic WHERE clauses bind user input as params, not string interpolation.           |
| XSS                   | ✅ Acceptable    | `| safe` is used on FOSDEM abstracts in `event.html` and `partials/event_card.html` (a trusted, read-only data source). Jinja2 auto-escaping is active everywhere else. |
| Tests                 | ✅ Clean         | 269 Python tests passing (85% coverage). Fabricated fixture data, in-memory DuckDB, no real endpoints. Cypress suite (28 a11y + 18 smoke) runs in CI. k6 load/smoke tests use `localhost` by default. |
| Data files            | ✅ Gitignored    | `data/fosdem.duckdb` matches `*.duckdb` and `data/` patterns — will not be committed.                                          |
| TODOs / internal refs | ✅ Mostly clear  | No FIXME, internal hostnames, email addresses, or private URLs. Seven screenshot TODO comments in `README.md` (HTML comments, invisible to readers). |
| CHANGELOG / ROADMAP   | ✅ Public-ready  | No internal-only content. CHANGELOG current through v2.1.0; ROADMAP reflects all completed phases 1–5.                        |
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
