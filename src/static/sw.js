/**
 * FOSDEM Explorer Service Worker
 *
 * Strategy:
 *  - App shell (top-level pages, CSS, JS, icons, manifest): Cache-First with
 *    network fallback so the app loads instantly and works offline.
 *  - API & HTMX partials (/api/*): Network-First with a short-lived cache so
 *    stale data is shown when offline rather than an error.
 *  - All other fetches: Cache-First with network fallback (falls back to the
 *    offline page if both miss).
 */

const VERSION = 'v3';
const SHELL_CACHE = `fosdem-shell-${VERSION}`;
const DATA_CACHE = `fosdem-data-${VERSION}`;
const OFFLINE_URL = '/offline';

// Resources to pre-cache on install (app shell + top-level pages).
const SHELL_ASSETS = [
  '/',
  '/tracks',
  '/speakers',
  '/analytics',
  '/my-schedule',
  '/offline',
  '/static/css/style.css',
  '/static/js/my-schedule.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

// ── Install ───────────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(SHELL_CACHE)
      .then((cache) => cache.addAll(SHELL_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

// ── Activate — purge old caches ───────────────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== SHELL_CACHE && k !== DATA_CACHE)
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin GET requests.
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  // API / partials → Network-First (fall back to data cache, then offline page).
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithCache(request, DATA_CACHE));
    return;
  }

  // Everything else (pages, CSS, JS, icons) → Cache-First.
  event.respondWith(cacheFirstWithNetwork(request));
});

// ── Helpers ───────────────────────────────────────────────────────────────────
async function cacheFirstWithNetwork(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(SHELL_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    const offline = await caches.match(OFFLINE_URL);
    return offline || new Response('Offline', { status: 503 });
  }
}

async function networkFirstWithCache(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    const offline = await caches.match(OFFLINE_URL);
    return offline || new Response('Offline', { status: 503 });
  }
}
