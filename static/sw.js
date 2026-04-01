const SW_VERSION = 'v10';
const STATIC_CACHE = `school-static-${SW_VERSION}`;
const RUNTIME_CACHE = `school-runtime-${SW_VERSION}`;

const OFFLINE_URL = '/offline/';
const SYNC_TAG = 'aura-form-sync';
const PRECACHE_URLS = [
  '/',
  OFFLINE_URL,
  '/static/img/logo.png',
  '/static/js/offline-store.js',
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
      if (response && response.ok && !response.redirected) {
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
    // Never cache redirected responses — a 302→login followed by fetch
    // produces a 200 login page that would be stored under the original URL.
    if (response && response.ok && !response.redirected) {
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


// Check if a navigation URL is a tenant page (not auth/login/signup).
function isTenantAppPage(url) {
  const path = url.pathname;
  // Tenant paths look like /{schema_name}/... with at least two segments
  const segments = path.split('/').filter(Boolean);
  if (segments.length < 2) return false;
  // Exclude auth-related pages that must always be fresh
  const authPaths = ['login', 'logout', 'signup', 'password_reset', 'register'];
  if (authPaths.includes(segments[1])) return false;
  // Exclude public/admin paths
  if (['admin', 'public', '__debug__'].includes(segments[0])) return false;
  return true;
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (!request.url.startsWith('http')) {
    return;
  }

  // ── Handle POST requests: queue for background sync when offline ──────
  if (request.method === 'POST') {
    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;
    // Only queue tenant form submissions (not API calls, not login)
    if (!isTenantAppPage(url)) return;

    event.respondWith(
      fetch(request.clone()).catch(async () => {
        // Network failed — store in IDB queue for later sync
        try {
          const formData = await request.clone().formData();
          const serialized = {};
          for (const [key, value] of formData.entries()) {
            if (typeof value === 'string') {
              serialized[key] = value;
            }
          }
          const db = await openSyncDB();
          const tx = db.transaction('sync-queue', 'readwrite');
          tx.objectStore('sync-queue').add({
            url: request.url,
            method: 'POST',
            data: serialized,
            timestamp: Date.now(),
          });
          await new Promise((resolve, reject) => {
            tx.oncomplete = resolve;
            tx.onerror = reject;
          });
          db.close();

          // Request background sync if available
          if (self.registration.sync) {
            await self.registration.sync.register(SYNC_TAG);
          }

          // Notify the client that submission was queued
          const clients = await self.clients.matchAll({ type: 'window' });
          for (const client of clients) {
            client.postMessage({ type: 'FORM_QUEUED', url: request.url });
          }
        } catch (err) {
          // Could not queue — nothing we can do
        }

        // Return a synthetic response so the page doesn't crash
        return new Response(
          JSON.stringify({ queued: true, message: 'Saved offline. Will sync when connected.' }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      })
    );
    return;
  }

  if (request.method !== 'GET') {
    return;
  }

  if (request.mode === 'navigate') {
    // PWA launch endpoint must always hit the network (it's a pure redirect)
    // — never serve a cached response for it.
    if (url.pathname === '/pwa-launch/') {
      event.respondWith(fetch(request).catch(() => Response.redirect('/', 302)));
      return;
    }
    // All navigation uses network-first so CSRF tokens, session cookies,
    // and server-side messages are always fresh.  Cached pages still serve
    // as offline fallback inside networkFirst().
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

  // Never cache AJAX / API calls — these return JSON and must always
  // hit the live server so authentication & tenant schema are correct.
  // Detecting by Accept header, X-Requested-With, or known API path segments.
  const isApiCall = (
    url.pathname.includes('/get-class-students/') ||
    url.pathname.includes('/api/') ||
    request.headers.get('Accept') === 'application/json' ||
    request.headers.get('X-Requested-With') === 'XMLHttpRequest'
  );
  if (isApiCall) {
    return; // Let the browser handle it directly — no SW interception
  }

  event.respondWith(networkFirst(request));
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  // Client can request sync replay
  if (event.data && event.data.type === 'REPLAY_QUEUE') {
    replaySyncQueue().then((result) => {
      event.source.postMessage({ type: 'QUEUE_REPLAYED', ...result });
    });
  }
  // Client can request cached page list
  if (event.data && event.data.type === 'GET_CACHED_PAGES') {
    getCachedPageList().then((pages) => {
      event.source.postMessage({ type: 'CACHED_PAGES', pages });
    });
  }
});

// ── IndexedDB for Background Sync Queue ────────────────────────────────

function openSyncDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('aura-sync', 1);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('sync-queue')) {
        db.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function replaySyncQueue() {
  let sent = 0;
  let failed = 0;

  try {
    const db = await openSyncDB();
    const tx = db.transaction('sync-queue', 'readonly');
    const store = tx.objectStore('sync-queue');
    const items = await new Promise((resolve) => {
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });

    for (const item of items) {
      try {
        const fd = new FormData();
        for (const [k, v] of Object.entries(item.data)) {
          fd.append(k, v);
        }

        const resp = await fetch(item.url, {
          method: item.method || 'POST',
          body: fd,
          credentials: 'same-origin',
        });

        if (resp.ok || resp.status === 302) {
          const delTx = db.transaction('sync-queue', 'readwrite');
          delTx.objectStore('sync-queue').delete(item.id);
          await new Promise((r) => { delTx.oncomplete = r; });
          sent++;
        } else {
          failed++;
        }
      } catch (err) {
        failed++;
      }
    }

    db.close();
  } catch (err) {
    // DB inaccessible
  }

  // Notify all clients
  const clients = await self.clients.matchAll({ type: 'window' });
  for (const client of clients) {
    client.postMessage({ type: 'QUEUE_SYNCED', sent, failed });
  }

  return { sent, failed };
}

// ── Background Sync Handler ────────────────────────────────────────────

self.addEventListener('sync', (event) => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(replaySyncQueue());
  }
});

// ── Periodic Background Sync (if available) ────────────────────────────
// Auto-refresh cached pages in the background so offline data stays fresh

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'aura-refresh-cache') {
    event.waitUntil(refreshCachedPages());
  }
});

async function refreshCachedPages() {
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const keys = await cache.keys();
    // Re-fetch up to 10 cached pages to keep them fresh
    const toRefresh = keys.filter(r => r.mode === 'navigate').slice(0, 10);
    await Promise.allSettled(
      toRefresh.map(async (request) => {
        try {
          const response = await fetch(request, { credentials: 'same-origin' });
          if (response && response.ok && !response.redirected) {
            await cache.put(request, response);
          }
        } catch (err) {
          // Skip pages that fail to refresh
        }
      })
    );
  } catch (err) {
    // Cache inaccessible
  }
}

// ── Get list of cached navigation pages ────────────────────────────────

async function getCachedPageList() {
  const pages = [];
  try {
    const cache = await caches.open(RUNTIME_CACHE);
    const keys = await cache.keys();
    for (const request of keys) {
      const url = new URL(request.url);
      // Only include HTML navigation pages, not static assets or API calls
      if (url.origin !== self.location.origin) continue;
      if (url.pathname.startsWith('/static/')) continue;
      pages.push({
        url: url.pathname,
        fullUrl: request.url,
      });
    }
  } catch (err) {
    // ignore
  }
  return pages;
}
// ── Web Push Handlers ──────────────────────────────────────────────────────

self.addEventListener('push', (event) => {
  let data = { title: 'Portals', body: 'You have a new notification.', url: '/' };
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