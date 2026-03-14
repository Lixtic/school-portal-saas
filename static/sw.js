const SW_VERSION = 'v3';
const STATIC_CACHE = `school-static-${SW_VERSION}`;
const RUNTIME_CACHE = `school-runtime-${SW_VERSION}`;
const OFFLINE_URL = '/offline/';
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/static/img/logo.png',
  '/static/css/admin-variables.css',
  '/static/css/admin-components.css',
  '/static/css/admin-utilities.css',
  '/static/css/admin-mobile-optimization.css',
  '/static/css/admin-mobile-utilities.css',
  '/static/css/loader.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) =>
      cache.addAll(PRECACHE_URLS).catch(() => {
        // Optional assets can fail depending on network/CDN availability.
      })
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key.startsWith('school-') && ![STATIC_CACHE, RUNTIME_CACHE].includes(key))
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

async function staleWhileRevalidate(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cached = await cache.match(request);
  const networkPromise = fetch(request)
    .then((response) => {
      if (response && response.ok) {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch(() => cached);

  return cached || networkPromise;
}

async function networkFirst(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  try {
    const response = await fetch(request);
    if (response && response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }

    if (request.mode === 'navigate') {
      const offline = await caches.match(OFFLINE_URL);
      if (offline) {
        return offline;
      }
    }

    throw err;
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') {
    return;
  }

  if (!request.url.startsWith('http')) {
    return;
  }

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request));
    return;
  }

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isStatic = url.pathname.startsWith('/static/');
  const isCdn = url.hostname.includes('cdn.jsdelivr.net') || url.hostname.includes('cdnjs.cloudflare.com');

  if ((isSameOrigin && isStatic) || isCdn) {
    event.respondWith(staleWhileRevalidate(request));
    return;
  }

  if (!isSameOrigin) {
    return;
  }

  event.respondWith(networkFirst(request));
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
// ── Web Push Handlers ──────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
  let data = { title: 'School Portal', body: 'You have a new notification.', url: '/' };
  if (event.data) {
    try {
      data = Object.assign(data, JSON.parse(event.data.text()));
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: '/static/img/logo.png',
    badge: '/static/img/logo.png',
    data: { url: data.url || '/' },
    vibrate: [150, 80, 150],
    requireInteraction: false,
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Focus existing tab if found
      for (const client of clientList) {
        if (client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      // Otherwise open a new tab
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});