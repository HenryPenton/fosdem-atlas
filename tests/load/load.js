/**
 * k6 load test — simulates 2000 users each performing 2–3 browsing actions.
 * Runs as shared iterations across 50 VUs with a 3-minute safety cap.
 *
 * Usage:
 *   k6 run tests/load/load.js
 *   BASE_URL=https://example.com k6 run tests/load/load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    load: {
      executor: 'shared-iterations',
      vus: 500,                // concurrent virtual users
      iterations: 10000,       // one iteration per simulated user
      maxDuration: '3m',      // safety cap
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8001';

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

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
    eventIds: Array.isArray(events) ? events.slice(0, 50).map((e) => e.id) : [],
    speakerIds: Array.isArray(speakers) ? speakers.slice(0, 50).map((s) => s.id) : [],
    days: Array.isArray(days) ? days : [],
    tracks: Array.isArray(tracks) ? tracks.slice(0, 50).map((t) => t.name) : [],
  };
}

// Weighted browsing scenarios — each entry is [weight, fn(data)].
// Higher-weight scenarios are appended more times so pick() selects them proportionally.
const scenarios = [
  // Homepage (most frequent)
  (data) => {
    check(http.get(`${BASE_URL}/`), { 'homepage 200': (r) => r.status === 200 });
  },
  (data) => {
    check(http.get(`${BASE_URL}/`), { 'homepage 200': (r) => r.status === 200 });
  },

  // Search (HTMX partial)
  (data) => {
    const terms = ['linux', 'python', 'rust', 'kubernetes', 'security', 'open source', 'fpga'];
    check(http.get(`${BASE_URL}/api/events/search?q=${encodeURIComponent(pick(terms))}`), {
      'search partial 200': (r) => r.status === 200,
    });
  },

  // JSON API search
  (data) => {
    const terms = ['linux', 'python', 'rust', 'kernel', 'network'];
    check(http.get(`${BASE_URL}/api/v1/events/search?q=${encodeURIComponent(pick(terms))}`), {
      'API search 200': (r) => r.status === 200,
    });
  },

  // Tracks list then a random track detail
  (data) => {
    check(http.get(`${BASE_URL}/tracks`), { 'tracks list 200': (r) => r.status === 200 });
    if (data.tracks.length) {
      sleep(0.5);
      check(http.get(`${BASE_URL}/track/${encodePath(pick(data.tracks))}`), {
        'track detail 200': (r) => r.status === 200,
      });
    }
  },

  // Speakers list then a random speaker
  (data) => {
    check(http.get(`${BASE_URL}/speakers`), { 'speakers list 200': (r) => r.status === 200 });
    if (data.speakerIds.length) {
      sleep(0.5);
      check(http.get(`${BASE_URL}/speaker/${pick(data.speakerIds)}`), {
        'speaker detail 200': (r) => r.status === 200,
      });
    }
  },

  // Event detail
  (data) => {
    if (data.eventIds.length) {
      check(http.get(`${BASE_URL}/event/${pick(data.eventIds)}`), {
        'event detail 200': (r) => r.status === 200,
      });
    }
  },

  // Day view
  (data) => {
    if (data.days.length) {
      check(http.get(`${BASE_URL}/day/${pick(data.days)}`), {
        'day view 200': (r) => r.status === 200,
      });
    }
  },

  // Analytics page
  (data) => {
    check(http.get(`${BASE_URL}/analytics`), { 'analytics 200': (r) => r.status === 200 });
  },

  // My schedule page
  (data) => {
    check(http.get(`${BASE_URL}/my-schedule`), { 'my-schedule 200': (r) => r.status === 200 });
  },

  // JSON API — analytics
  (data) => {
    check(http.get(`${BASE_URL}/api/v1/analytics`), {
      'API analytics 200': (r) => r.status === 200,
    });
  },

  // JSON API — days
  (data) => {
    check(http.get(`${BASE_URL}/api/v1/days`), { 'API days 200': (r) => r.status === 200 });
    if (data.days.length) {
      sleep(0.3);
      check(http.get(`${BASE_URL}/api/v1/days/${pick(data.days)}`), {
        'API day detail 200': (r) => r.status === 200,
      });
    }
  },
];

export default function (data) {
  const count = 2 + Math.floor(Math.random() * 2); // 2 or 3 actions per user
  for (let i = 0; i < count; i++) {
    pick(scenarios)(data);
    sleep(0.5 + Math.random() * 1); // 0.5–1.5 s think time
  }
}
