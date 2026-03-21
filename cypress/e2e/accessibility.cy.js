/**
 * Cypress accessibility test suite for FOSDEM Explorer.
 *
 * Uses cypress-axe (axe-core) to audit every page in both light and dark mode.
 * Failures are logged with impact level, rule ID, and affected DOM nodes.
 *
 * Run locally:   npx cypress run --spec cypress/e2e/accessibility.cy.js
 * Run all:       npx cypress run
 */

const pages = [
  { name: 'Homepage', path: '/' },
  { name: 'Tracks', path: '/tracks' },
  { name: 'Speakers', path: '/speakers' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'My Schedule', path: '/my-schedule' },
];

/**
 * Helper: inject axe-core and run the accessibility check.
 * Uses the custom checkAccessibility command from commands.js which
 * logs each violation to the Cypress command log for easy debugging.
 */
function injectAndCheck(context = null, options = {}) {
  cy.injectAxe();
  cy.checkAccessibility(context, {
    runOnly: {
      type: 'tag',
      values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'],
    },
    ...options,
  });
}

/**
 * Set theme via the same mechanism the app uses (localStorage + DOM attribute).
 */
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
  // Give the browser a tick to repaint.
  cy.wait(100); // eslint-disable-line cypress/no-unnecessary-waiting
}

// ───────────────────────────────────────────────────────────────────
// Light-mode tests
// ───────────────────────────────────────────────────────────────────
describe('Accessibility — Light Mode', () => {
  beforeEach(() => {
    cy.window().then((win) => {
      win.localStorage.setItem('fosdem_theme', 'light');
    });
  });

  pages.forEach(({ name, path }) => {
    it(`${name} (${path}) has no a11y violations`, () => {
      cy.visit(path);
      setTheme('light');
      injectAndCheck();
    });
  });
});

// ───────────────────────────────────────────────────────────────────
// Dark-mode tests
// ───────────────────────────────────────────────────────────────────
describe('Accessibility — Dark Mode', () => {
  beforeEach(() => {
    cy.window().then((win) => {
      win.localStorage.setItem('fosdem_theme', 'dark');
    });
  });

  pages.forEach(({ name, path }) => {
    it(`${name} (${path}) has no a11y violations`, () => {
      cy.visit(path);
      setTheme('dark');
      injectAndCheck();
    });
  });
});

// ───────────────────────────────────────────────────────────────────
// Dynamic pages — need data from the API first
// ───────────────────────────────────────────────────────────────────
describe('Accessibility — Dynamic pages', () => {
  let eventId;
  let speakerId;
  let day;
  let track;

  before(() => {
    // Fetch seed data from the JSON API.
    cy.request('/api/v1/events').then((res) => {
      if (res.body.length) eventId = res.body[0].id;
    });
    cy.request('/api/v1/speakers').then((res) => {
      if (res.body.length) speakerId = res.body[0].id;
    });
    cy.request('/api/v1/days').then((res) => {
      if (res.body.length) day = res.body[0];
    });
    cy.request('/api/v1/tracks').then((res) => {
      if (res.body.length) track = res.body[0].name;
    });
  });

  ['light', 'dark'].forEach((theme) => {
    describe(`${theme} mode`, () => {
      beforeEach(() => {
        cy.window().then((win) => {
          win.localStorage.setItem('fosdem_theme', theme);
        });
      });

      it('Event detail page', function () {
        if (!eventId) this.skip();
        cy.visit(`/event/${eventId}`);
        setTheme(theme);
        injectAndCheck();
      });

      it('Speaker detail page', function () {
        if (!speakerId) this.skip();
        cy.visit(`/speaker/${speakerId}`);
        setTheme(theme);
        injectAndCheck();
      });

      it('Day page', function () {
        if (!day) this.skip();
        cy.visit(`/day/${day}`);
        setTheme(theme);
        injectAndCheck();
      });

      it('Track page', function () {
        if (!track) this.skip();
        cy.visit(`/track/${encodeURIComponent(track)}`);
        setTheme(theme);
        injectAndCheck();
      });
    });
  });
});

// ───────────────────────────────────────────────────────────────────
// Colour-contrast-only audit (stricter — catches non-AA contrast)
// ───────────────────────────────────────────────────────────────────
describe('Colour contrast audit', () => {
  const contrastRules = {
    runOnly: {
      type: 'rule',
      values: ['color-contrast'],
    },
  };

  ['light', 'dark'].forEach((theme) => {
    pages.forEach(({ name, path }) => {
      it(`${name} (${theme}) passes colour-contrast`, () => {
        cy.visit(path);
        setTheme(theme);
        cy.injectAxe();
        cy.checkAccessibility(null, contrastRules);
      });
    });
  });
});
