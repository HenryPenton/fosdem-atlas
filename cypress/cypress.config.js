const { defineConfig } = require('cypress');

module.exports = defineConfig({
  e2e: {
    baseUrl: 'http://localhost:8000',
    supportFile: 'support/e2e.js',
    specPattern: 'e2e/**/*.cy.js',
    screenshotsFolder: 'screenshots',
    videosFolder: 'videos',
    downloadsFolder: 'downloads',
    video: false,
    screenshotOnRunFailure: true,
    allowCypressEnv: false,
    defaultCommandTimeout: 10000,
    viewportWidth: 1280,
    viewportHeight: 800,
    setupNodeEvents(on) {
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
      });
    },
  },
});
