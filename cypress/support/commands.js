/**
 * Custom Cypress command: run axe accessibility checks and log
 * every violation with its DOM targets to the Cypress command log.
 *
 * Usage:
 *   cy.checkA11y()                       — default rules, all elements
 *   cy.checkA11y(null, { runOnly: … })   — only specific rules
 *   cy.checkA11y('.selector')            — scope to element
 */
Cypress.Commands.add('checkAccessibility', (context, options) => {
  cy.checkA11y(context, options, (violations) => {
    violations.forEach((violation) => {
      const nodes = violation.nodes.map((node) => node.target.join(', ')).join('\n  ');
      Cypress.log({
        name: 'a11y',
        message: `[${violation.impact}] ${violation.id}: ${violation.description}`,
        consoleProps: () => violation,
      });
      cy.log(
        `**${violation.impact?.toUpperCase()}** — ${violation.id}\n` +
          `${violation.help}\n` +
          `Affected nodes:\n  ${nodes}`
      );
    });
  });
});
