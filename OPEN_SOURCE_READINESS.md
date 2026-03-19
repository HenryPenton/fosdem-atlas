# Open-Source Readiness Audit

_Audited: 19 March 2026 (v0.7.0)_

---

## Recommended (Not Blocking)

### 3. Add CODE_OF_CONDUCT.md

Standard for open-source projects. Establishes community norms and an incident-reporting contact. GitHub provides a template via **Settings > Community Standards > Code of conduct**.

### 4. Add SECURITY.md

Tells users how to responsibly disclose vulnerabilities. Suggested content:

```markdown
# Security Policy

## Reporting a Vulnerability

Please do not open a public GitHub issue for security vulnerabilities.
Email [your-email] with the subject "FOSDEM Explorer Security Report".
You can expect a response within 72 hours.
```

### 5. Add `[project.urls]` to pyproject.toml

The repository/homepage URLs are missing from the package metadata. Add:

```toml
[project.urls]
Repository = "https://github.com/<your-username>/fosdem-explorer"
```

---

## Clean — No Action Required

| Area                  | Status           | Notes                                                                                                                          |
| --------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Secrets / credentials | ✅ Clear         | No hardcoded keys or tokens. `.env` is gitignored. Config uses `pydantic-settings` with a `FOSDEM_` prefix.                    |
| License               | ✅ Good          | MIT + CC BY 4.0 dual-licence declared in `LICENSE`, `DATA_LICENSE.md`, `pyproject.toml`, and the template footer.              |
| .gitignore            | ✅ Comprehensive | Covers `__pycache__`, `.env`, `*.duckdb`, `data/`, IDE files, build artefacts, test cache.                                     |
| Configuration         | ✅ Safe          | `debug` defaults to `False`. All settings come from environment variables.                                                     |
| Docker                | ✅ Good          | Non-root `app` user, no secrets, health checks defined, proper `.dockerignore`.                                                |
| SQL injection         | ✅ Safe          | All queries use parameterised statements. Dynamic WHERE clauses bind user input as params, not string interpolation.           |
| XSS                   | ✅ Acceptable    | `\| safe` is used only on FOSDEM abstracts in `event.html`, `keyword.html`, and `track.html` (a trusted, read-only data source). Jinja2 auto-escaping is active everywhere else. |
| Tests                 | ✅ Clean         | Fabricated fixture data, in-memory DuckDB, no real endpoints. k6 load/smoke tests use `localhost` by default with an env-var override — no internal hostnames. |
| Data files            | ✅ Gitignored    | `data/fosdem.duckdb` matches `*.duckdb` and `data/` patterns — will not be committed.                                          |
| TODOs / internal refs | ✅ Clear         | No TODO, FIXME, internal hostnames, email addresses, or private URLs found.                                                    |
| CHANGELOG / ROADMAP   | ✅ Public-ready  | No internal-only content. CHANGELOG current through v0.7.0; ROADMAP reflects all completed phases 1–5.                        |

---

## Optional Enhancements

- **SPDX licence headers** in `.py` files (e.g. `# SPDX-License-Identifier: MIT`) — optional but provides the strongest machine-readable licence clarity for large-scale reuse.
