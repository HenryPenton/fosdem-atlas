/**
 * k6 rate-limit test — fires more than 200 requests in one minute from a
 * single VU and asserts that the server starts returning 429 responses with
 * a Retry-After header once the limit is hit.
 *
 * Usage:
 *   k6 run tests/load/rate_limit.js
 *   BASE_URL=https://example.com k6 run tests/load/rate_limit.js
 *
 * Expected outcome:
 *   - At least one 429 is received (limit triggered)
 *   - Every 429 response carries a Retry-After header
 *   - No 5xx errors are returned
 */

import http from 'k6/http';
import { check, group } from 'k6';
import { Counter } from 'k6/metrics';

const ok_count   = new Counter('rate_limit_ok');
const limit_count = new Counter('rate_limit_429');

// 250 tight iterations from 1 VU — well above the 200/min cap.
export const options = {
  vus: 1,
  iterations: 250,
  thresholds: {
    // At least one 429 must have been returned.
    rate_limit_429: ['count>0'],
    // No server errors.
    http_req_failed: ['rate==0'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  group('rate limit check', () => {
    const res = http.get(`${BASE_URL}/`);

    if (res.status === 429) {
      limit_count.add(1);
      check(res, {
        '429 has Retry-After header': (r) => r.headers['Retry-After'] !== undefined,
        '429 body has error field':   (r) => {
          try { return r.json('error') !== undefined; } catch { return false; }
        },
      });
    } else {
      ok_count.add(1);
      check(res, {
        '2xx response': (r) => r.status >= 200 && r.status < 300,
      });
    }
  });
}
