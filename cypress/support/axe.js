/**
 * Minimal axe-core integration for Cypress.
 *
 *   cy.injectAxe()                              — load axe-core into the page under test
 *   cy.checkA11y(context, options, onViolations) — run axe and fail on any violation
 *
 * `context` is an optional axe context (selector or element); `options` is passed
 * straight to axe.run(); `onViolations` is called with the violations before the
 * assertion so callers can log details.
 */
Cypress.Commands.add('injectAxe', () => {
  cy.readFile('node_modules/axe-core/axe.min.js', { log: false }).then((source) => {
    cy.window({ log: false }).then((win) => {
      win.eval(source);
    });
  });
});

Cypress.Commands.add('checkA11y', (context, options, onViolations) => {
  cy.window({ log: false })
    .then((win) => win.axe.run(context || win.document, options || {}))
    .then(({ violations }) => {
      if (violations.length) {
        if (onViolations) onViolations(violations);
        violations.forEach((v) => {
          const selectors = v.nodes.flatMap((node) => node.target).join(', ');
          Cypress.log({
            $el: Cypress.$(selectors),
            name: 'a11y error!',
            consoleProps: () => v,
            message: `${v.id} on ${v.nodes.length} node${v.nodes.length === 1 ? '' : 's'}`,
          });
        });
      }
      const n = violations.length;
      assert.equal(
        n,
        0,
        `${n} accessibility violation${n === 1 ? '' : 's'} ${n === 1 ? 'was' : 'were'} detected`
      );
    });
});
