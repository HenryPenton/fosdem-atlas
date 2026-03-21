/**
 * E2E smoke test suite for FOSDEM Explorer.
 *
 * Checks that every significant page loads, renders key content, and
 * that primary user journeys are functional.
 *
 * Run locally:  npx cypress run --spec 'e2e/smoke.cy.js'   (from cypress/)
 */

describe('Smoke — Static pages load', () => {
  const pages = [
    { name: 'Homepage',    path: '/',            heading: /FOSDEM/i,    selector: '.hero h1' },
    { name: 'Tracks',      path: '/tracks',      heading: /tracks/i,    selector: '.hero h1' },
    { name: 'Speakers',    path: '/speakers',    heading: /speakers/i,  selector: '.hero h1' },
    { name: 'Analytics',   path: '/analytics',   heading: /analytics/i, selector: '.hero h1' },
    { name: 'My Schedule', path: '/my-schedule', heading: /schedule/i,  selector: '.hero h1' },
    { name: 'Offline',     path: '/offline',     heading: /.+/,         selector: '.hero h1' },
  ];

  pages.forEach(({ name, path, heading, selector }) => {
    it(`${name} — returns 200 and renders heading`, () => {
      cy.visit(path);
      cy.get(selector).should('be.visible').invoke('text').should('match', heading);
    });
  });
});

describe('Smoke — Navigation', () => {
  it('nav links point to the right pages', () => {
    cy.visit('/');
    cy.get('nav a[href="/speakers"]').should('be.visible');
    cy.get('nav a[href="/tracks"]').should('be.visible');
    cy.get('nav a[href="/analytics"]').should('be.visible');
    cy.get('nav a[href="/my-schedule"]').should('be.visible');
  });

  it('clicking Tracks nav link loads the tracks page', () => {
    cy.visit('/');
    cy.get('nav a[href="/tracks"]').click();
    cy.location('pathname').should('eq', '/tracks');
    cy.get('.hero h1').should('be.visible');
  });

  it('clicking Speakers nav link loads the speakers page', () => {
    cy.visit('/');
    cy.get('nav a[href="/speakers"]').click();
    cy.location('pathname').should('eq', '/speakers');
    cy.get('.hero h1').should('be.visible');
  });
});

describe('Smoke — Dynamic pages', () => {
  let eventId;
  let speakerId;
  let day;
  let track;

  before(() => {
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

  it('Event detail page renders title and metadata', function () {
    if (!eventId) this.skip();
    cy.visit(`/event/${eventId}`);
    cy.get('.event-detail-title').should('be.visible').invoke('text').should('have.length.gt', 0);
    cy.get('.event-detail-meta').should('exist');
  });

  it('Speaker detail page renders speaker name', function () {
    if (!speakerId) this.skip();
    cy.visit(`/speaker/${speakerId}`);
    cy.get('.hero h1').should('be.visible').invoke('text').should('have.length.gt', 0);
  });

  it('Day page renders track cards', function () {
    if (!day) this.skip();
    cy.visit(`/day/${day}`);
    cy.get('.hero h1').should('be.visible');
    cy.get('.track-card').should('have.length.gt', 0);
  });

  it('Track page renders event cards', function () {
    if (!track) this.skip();
    cy.visit(`/track/${encodeURIComponent(track)}`);
    cy.get('.hero h1').should('be.visible');
    cy.get('.event-card').should('have.length.gt', 0);
  });
});

describe('Smoke — Search', () => {
  it('typing in the search box filters results', () => {
    cy.visit('/');
    cy.get('.search-input').type('linux');
    // Results update via HTMX — wait for at least one result or a no-results message
    cy.get('#search-results', { timeout: 8000 }).should('not.be.empty');
  });
});

describe('Smoke — API health', () => {
  it('/health returns ok', () => {
    cy.request('/health').then((res) => {
      expect(res.status).to.eq(200);
      expect(res.body).to.have.property('status', 'healthy');
    });
  });

  it('/api/v1/events returns an array', () => {
    cy.request('/api/v1/events').then((res) => {
      expect(res.status).to.eq(200);
      expect(res.body).to.be.an('array').and.have.length.gt(0);
    });
  });

  it('/api/v1/speakers returns an array', () => {
    cy.request('/api/v1/speakers').then((res) => {
      expect(res.status).to.eq(200);
      expect(res.body).to.be.an('array').and.have.length.gt(0);
    });
  });

  it('/api/v1/tracks returns an array', () => {
    cy.request('/api/v1/tracks').then((res) => {
      expect(res.status).to.eq(200);
      expect(res.body).to.be.an('array').and.have.length.gt(0);
    });
  });
});
