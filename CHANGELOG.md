## v2.1.0 (2026-03-21)

### Feat

- add urlencode_path filter to templates for safe URL encoding of track links
- add video URL support for events and enhance 404 error pages with context-aware back links
- add robots.txt endpoint and update HTMX script source

## v2.0.1 (2026-03-21)

### Fix

- update bump process to format SBOM and ensure proper line endings
- refresh SBOM during version bump process

## v2.0.0 (2026-03-21)

### Feat

- add cyclonedx-bom to development dependencies
- add security scan workflow with Semgrep, Trivy, and TruffleHog
- accessibility fixes
- dark mode styles for hero text, word cloud terms, and heatmap cells
- add my schedule grid feature and enhance event grid rendering
- update hero section with SVG icon and schedule transfer UI
- update roadmap with rate limiting details and update caching documentation
- implement caching for event and speaker details, and update load test parameters
- enhance caching mechanisms across services and update load testing parameters
- add speaker bios to the application, including database schema updates and UI enhancements
- implement global rate limiting with slowapi and add rate limit test cases

### Fix

- add logging for health check failures and implement tests for unhealthy status
- remove cpu/mem limit on docker
- migrate to multi-stage Docker build and optimize resource limits in docker-compose
- implement styled 404 error pages for events and speakers
- implement health check for DuckDB connections and add recovery tests
- update dependencies in pyproject.toml and improve install targets in Makefile
- specify exact versions for dependencies in pyproject.toml
- update Trivy scan configuration and remove TruffleHog job
- add SIGNING_KEY to fake_secrets.env for testing purposes
- trufflehog
- update HTMX script tag to include integrity and crossorigin attributes for improved security
- update security scan workflow to enhance output formatting and improve summary reporting for Semgrep, Trivy, and TruffleHog
- enhance security scan workflow by updating Semgrep and Trivy configurations, adding output summaries, and improving artifact uploads
- security scanning tool issues
- update security scan workflow to use SARIF format and improve report uploads
- add .catch() handler to fetch calls in My Schedule for error handling
- add security response headers to prevent clickjacking and MIME sniffing
- enhance CSV sanitization by adding HTML stripping and formula protection
- resolve CSV formula injection and ensure consistent event abstracts
- add HTML sanitization for event abstracts and include nh3 dependency

### Refactor

- web application structure by modularizing routes

## v1.1.0 (2026-03-19)

### Feat

- enhance mobile navigation with hamburger menu and improved styles
- implement PWA support with offline access, service worker, and manifest

### Fix

- unclosable install PWA box

## v1.0.0 (2026-03-19)

### Feat

- add k6 load and smoke tests with Makefile targets for performance validation
- enhance documentation and self-hosting experience with new guides and deployment instructions
- enhance keyword page with event statistics and improved layout

### Refactor

- remove unused DTOs and CSS styles for event highlighting

## v0.7.0 (2026-03-18)

### Feat

- split repository out into appropriate domains grouped by query type (e.g. speaker/event/analytics)
- add comprehensive tests for web analytics, events, health, my schedule, speakers, and tracks

## v0.6.0 (2026-03-18)

### Feat

- add schedule transfer section with export/import functionality and corresponding tests
- update navigation layout and styles for improved accessibility and responsiveness
- add keyword search page and dual-range filter for event topics
- new type aliases
- update DTOs for events and analytics, refactor API routes to use new models

## v0.5.1 (2026-03-17)

### Feat

- introduce view models for analytics and schedule results, update related services and tests
- refactor repository methods to return typed domain models and update related code
- implement EventSearchResult model and update repository methods to return structured data
- define analytics models for speakers and topics, update repository methods to return structured data
- introduce detailed event and analytics models, update repository methods, and enhance API responses
- add domain models for events and speakers

### Fix

- use python 3 in makefile

## v0.5.0 (2026-03-17)

### Feat

- enhance data models and services for speakers and events with DTOs and summaries
- add room tracks and track change markers to schedule data for improved event organization
- update color variables for improved theme consistency and styling
- update event detail layout for improved structure and styling

## v0.4.0 (2026-03-17)

### Feat

- refactor breadcrumb navigation for improved accessibility and styling
- add grid rowspans and covered cells to schedule data for improved rendering
- improve layout for speakers table with scrollable wrapper and adjust styles for better readability
- enhance health endpoint to include event count and update Dockerfile for graceful shutdown

## v0.3.1 (2026-03-17)

### Feat

- implement dark mode toggle and loading spinner in search

## v0.3.0 (2026-03-16)

### Feat

- tests in parallel
- fix linting issue
- enhance analytics caching, add keyword extraction, and update breadcrumb styles
- add analytics, schedule, scrape, and speaker services
- basic storage of events
- add CSV export functionality for events and speakers with corresponding tests
- add cache control middleware and tests for caching behavior + api

## v0.2.0 (2026-03-15)

### Feat

- implement topic statistics retrieval and display in analytics + wordcloud
- add speaker statistics retrieval and display in analytics
- add room statistics and heatmap to analytics page

## v0.1.2 (2026-03-15)

### Feat

- add contributing guidelines and open-source readiness audit
- add analytics page with event statistics and corresponding styles

## v0.1.1 (2026-03-14)

### Feat

- enhance bump command to support version increment levels
- add speaker management features with detail and listing pages

## v0.0.9 (2026-03-14)

### Feat

- implement tracks browser and track detail pages with event listing
- add grid view for schedule with day selection and event display

## v0.0.8 (2026-03-14)

## v0.0.7 (2026-03-14)

### Feat

- implement schedule page with sorting options and event grouping by day
- enhance release workflow and commit process with Commitizen integration

## v0.0.6 (2026-03-14)

## v0.0.5 (2026-03-14)

## v0.0.4 (2026-03-13)

## v0.0.3 (2026-03-13)

## v0.0.2 (2026-03-13)

## v0.0.1 (2026-03-13)
