/**
 * k6 smoke test — verifies all key pages and API endpoints are reachable
 * and respond within 2 seconds using a single VU.
 *
 * Usage:
 *   k6 run tests/load/smoke.js
 *   BASE_URL=https://example.com k6 run tests/load/smoke.js
 */

import http from 'k6/http';
import { check, group } from 'k6';

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: {
    http_req_failed: ['rate==0'],
    http_req_duration: ['p(95)<2000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

function encodePath(s) {
  return s
    .split('/')
    .map((seg) => encodeURIComponent(seg))
    .join('/');
}

export function setup() {
  const events = http.get(`${BASE_URL}/api/v1/events`).json();
  const speakers = http.get(`${BASE_URL}/api/v1/speakers`).json();
  const days = http.get(`${BASE_URL}/api/v1/days`).json();
  const tracks = http.get(`${BASE_URL}/api/v1/tracks`).json();

  return {
    eventId: Array.isArray(events) && events.length ? events[0].id : null,
    speakerId: Array.isArray(speakers) && speakers.length ? speakers[0].id : null,
    day: Array.isArray(days) && days.length ? days[0] : null,
    track: Array.isArray(tracks) && tracks.length ? tracks[0].name : null,
  };
}

export default function ({ eventId, speakerId, day, track }) {
  group('health', () => {
    check(http.get(`${BASE_URL}/health`), {
      'health: status 200': (r) => r.status === 200,
      'health: body healthy': (r) => r.json('status') === 'healthy',
    });
  });

  group('HTML pages', () => {
    const pages = [
      ['/', 'homepage'],
      ['/tracks', 'tracks'],
      ['/speakers', 'speakers'],
      ['/analytics', 'analytics'],
      ['/my-schedule', 'my-schedule'],
    ];
    if (day) pages.push([`/day/${day}`, 'day']);
    if (eventId) pages.push([`/event/${eventId}`, 'event detail']);
    if (speakerId) pages.push([`/speaker/${speakerId}`, 'speaker detail']);
    if (track) pages.push([`/track/${encodePath(track)}`, 'track detail']);

    for (const [path, label] of pages) {
      check(http.get(`${BASE_URL}${path}`), {
        [`${label}: status 200`]: (r) => r.status === 200,
      });
    }
  });

  group('HTML partials', () => {
    check(http.get(`${BASE_URL}/api/events`), {
      'events partial: status 200': (r) => r.status === 200,
    });
    check(http.get(`${BASE_URL}/api/events/search?q=linux`), {
      'search partial: status 200': (r) => r.status === 200,
    });
  });

  group('JSON API', () => {
    const endpoints = [
      ['/api/v1/events', 'events list'],
      ['/api/v1/events/search?q=python', 'events search'],
      ['/api/v1/days', 'days'],
      ['/api/v1/tracks', 'tracks'],
      ['/api/v1/speakers', 'speakers'],
      ['/api/v1/analytics', 'analytics'],
      ['/api/v1/rooms', 'rooms'],
    ];
    if (eventId) endpoints.push([`/api/v1/events/${eventId}`, 'event detail']);
    if (speakerId) endpoints.push([`/api/v1/speakers/${speakerId}`, 'speaker detail']);
    if (day) endpoints.push([`/api/v1/days/${day}`, 'day detail']);
    if (track) endpoints.push([`/api/v1/tracks/${encodePath(track)}`, 'track detail']);

    for (const [path, label] of endpoints) {
      check(http.get(`${BASE_URL}${path}`), {
        [`API ${label}: status 200`]: (r) => r.status === 200,
      });
    }
  });
}
