/**
 * Exhaustive accessibility audit for FOSDEM Explorer.
 *
 * Discovers EVERY dynamic page via the JSON API (events, speakers, tracks,
 * days, keywords) and runs axe-core in both light and dark mode.  Also
 * expands every abstract toggle on track pages and audits the open state.
 *
 * This is intentionally slow — designed for weekly CI runs, not per-PR.
 *
 * Run locally:
 *   cd cypress && npx cypress run --spec 'e2e/a11y-long.cy.js' --config defaultCommandTimeout=15000
 */

const axeOptions = {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
  },
};

function setTheme(theme) {
  cy.window().then((win) => {
    if (theme === 'dark') {
      win.document.documentElement.setAttribute('data-theme', 'dark');
      win.localStorage.setItem('fosdem_theme', 'dark');
    } else {
      win.document.documentElement.removeAttribute('data-theme');
      win.localStorage.setItem('fosdem_theme', 'light');
    }
  });
  // eslint-disable-next-line cypress/no-unnecessary-waiting
  cy.wait(100);
}

/**
 * Visit a page, set the theme, inject axe, and audit.
 * Collects violations without failing so the full suite can finish.
 * Returns violations via the `failed` array.
 */
function auditPage(path, theme, failed) {
  cy.task('log', `  ✓ ${theme} ${path}`);
  cy.visit(path, { failOnStatusCode: false });
  setTheme(theme);
  cy.injectAxe();
  cy.checkA11y(null, axeOptions, (violations) => {
    if (violations.length) {
      failed.push({
        path,
        rules: violations.map((v) => `${v.id} (${v.impact})`),
      });
    }
  }, true); // skipFailures — collect all, report at end
}

/** Throw a single summary error listing every page that failed. */
function reportFailures(resourceType, failed) {
  if (failed.length) {
    const summary = failed
      .map((f) => `  ${f.path}: ${f.rules.join(', ')}`)
      .join('\n');
    throw new Error(
      `${failed.length} ${resourceType} page(s) had a11y violations:\n${summary}`,
    );
  }
}

// ───────────────────────────────────────────────────────────────────
describe('Full a11y audit — every page', { defaultCommandTimeout: 15000 }, () => {
  let events = [];
  let speakers = [];
  let tracks = [];
  let days = [];
  let keywords = [];

  before(() => {
    cy.request('/api/v1/events').then((res) => {
      events = res.body || [];
    });
    cy.request('/api/v1/speakers').then((res) => {
      speakers = res.body || [];
    });
    cy.request('/api/v1/tracks').then((res) => {
      tracks = res.body || [];
    });
    cy.request('/api/v1/days').then((res) => {
      days = res.body || [];
    });
    cy.request('/api/v1/analytics').then((res) => {
      const kw = res.body?.topic_stats?.keywords || [];
      // Only test keywords with meaningful occurrence counts
      keywords = kw.filter((k) => k.count >= 5).map((k) => k.term);
    });
  });

  // ── Events ─────────────────────────────────────────────────────
  ['light', 'dark'].forEach((theme) => {
    it(`audits all event pages (${theme})`, function () {
      if (!events.length) this.skip();
      const failed = [];
      cy.wrap(events, { timeout: 600000 }).each((event) => {
        auditPage(`/event/${event.id}`, theme, failed);
      }).then(() => reportFailures('event', failed));
    });
  });

  // ── Speakers ───────────────────────────────────────────────────
  ['light', 'dark'].forEach((theme) => {
    it(`audits all speaker pages (${theme})`, function () {
      if (!speakers.length) this.skip();
      const failed = [];
      cy.wrap(speakers, { timeout: 600000 }).each((speaker) => {
        auditPage(`/speaker/${speaker.id}`, theme, failed);
      }).then(() => reportFailures('speaker', failed));
    });
  });

  // ── Tracks ─────────────────────────────────────────────────────
  ['light', 'dark'].forEach((theme) => {
    it(`audits all track pages (${theme})`, function () {
      if (!tracks.length) this.skip();
      const failed = [];
      cy.wrap(tracks, { timeout: 120000 }).each((track) => {
        auditPage(`/track/${encodeURIComponent(track.name)}`, theme, failed);
      }).then(() => reportFailures('track', failed));
    });
  });

  // ── Days ───────────────────────────────────────────────────────
  ['light', 'dark'].forEach((theme) => {
    it(`audits all day pages (${theme})`, function () {
      if (!days.length) this.skip();
      const failed = [];
      cy.wrap(days, { timeout: 30000 }).each((day) => {
        auditPage(`/day/${day}`, theme, failed);
      }).then(() => reportFailures('day', failed));
    });
  });

  // ── Keywords ───────────────────────────────────────────────────
  ['light', 'dark'].forEach((theme) => {
    it(`audits all keyword pages (${theme})`, function () {
      if (!keywords.length) this.skip();
      const failed = [];
      cy.wrap(keywords, { timeout: 120000 }).each((term) => {
        auditPage(`/keyword/${encodeURIComponent(term)}`, theme, failed);
      }).then(() => reportFailures('keyword', failed));
    });
  });
});

// ───────────────────────────────────────────────────────────────────
describe('Full a11y audit — expanded abstracts', { defaultCommandTimeout: 15000 }, () => {
  let tracks = [];

  before(() => {
    cy.request('/api/v1/tracks').then((res) => {
      tracks = res.body || [];
    });
  });

  ['light', 'dark'].forEach((theme) => {
    it(`audits every track page with all abstracts expanded (${theme})`, function () {
      if (!tracks.length) this.skip();
      const failed = [];

      cy.wrap(tracks, { timeout: 300000 }).each((track) => {
        const path = `/track/${encodeURIComponent(track.name)}`;
        cy.task('log', `  ✓ ${theme} ${path} (abstracts open)`);
        cy.visit(path, { failOnStatusCode: false });
        setTheme(theme);

        // Expand every abstract toggle on this page
        cy.get('body').then(($body) => {
          const toggles = $body.find('.abstract-toggle:not([open])');
          if (toggles.length) {
            cy.wrap(toggles).each(($toggle) => {
              cy.wrap($toggle).find('summary').click({ force: true });
            });
          }
        });

        cy.injectAxe();
        cy.checkA11y(null, axeOptions, (violations) => {
          if (violations.length) {
            failed.push({
              path,
              rules: violations.map((v) => `${v.id} (${v.impact})`),
            });
          }
        }, true);
      }).then(() => reportFailures('track (abstracts open)', failed));
    });
  });
});

// ───────────────────────────────────────────────────────────────────
describe('Full a11y audit — My Schedule with conflicts', { defaultCommandTimeout: 15000 }, () => {
  const conflictEvents = [
    {
      id: 'c1',
      title: 'Talk One',
      start_time: '2026-02-01T10:00:00',
      duration_minutes: 60,
      room: 'Room A',
      day: '2026-02-01',
    },
    {
      id: 'c2',
      title: 'Talk Two',
      start_time: '2026-02-01T10:30:00',
      duration_minutes: 60,
      room: 'Room B',
      day: '2026-02-01',
    },
  ];

  ['light', 'dark'].forEach((theme) => {
    it(`has no a11y violations (${theme})`, () => {
      cy.intercept('GET', '/api/v1/events/by-ids*', { body: conflictEvents });
      cy.intercept('GET', '/my-schedule/grid*', { body: '<p>Schedule grid</p>' });
      cy.visit('/my-schedule', {
        onBeforeLoad(win) {
          win.localStorage.setItem('fosdem_my_schedule', JSON.stringify(['c1', 'c2']));
        },
      });
      setTheme(theme);
      cy.get('#schedule-conflicts').should('be.visible');
      cy.injectAxe();
      const failed = [];
      cy.checkA11y(null, axeOptions, (violations) => {
        if (violations.length) {
          failed.push({
            path: '/my-schedule (with conflicts)',
            rules: violations.map((v) => `${v.id} (${v.impact})`),
          });
        }
      }, true);
      cy.then(() => reportFailures('my-schedule-with-conflicts', failed));
    });
  });
});
