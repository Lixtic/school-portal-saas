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
