const CACHE_NAME = 'school-app-v1';
const ASSETS_TO_CACHE = [
  '/static/css/style.css', // Assuming main css
  '/static/img/logo.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css',
  'https://manrope.fontsource.org' // Or google fonts if possible
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
          console.log('Cache addAll failed, skipping optional assets', err);
      });
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Simple cache-first strategy for static assets, network-first for pages
  if (event.request.url.includes('/static/') || event.request.url.includes('cdn.')) {
      event.respondWith(
        caches.match(event.request).then((response) => {
          return response || fetch(event.request);
        })
      );
  } else {
      // For navigation (pages), try network, fall back to nothing (or offline page if we had one)
      event.respondWith(fetch(event.request));
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