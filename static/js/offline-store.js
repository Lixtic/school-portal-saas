/**
 * SchoolPadi Offline Store — IndexedDB-backed offline data layer
 *
 * Stores page snapshots, queued form submissions, and key data
 * so the app remains usable without network connectivity.
 */
(function () {
  'use strict';

  const DB_NAME = 'padi-offline';
  const DB_VERSION = 1;
  const STORES = {
    pages: 'offline-pages',       // cached page snapshots (title, url, html excerpt, timestamp)
    queue: 'offline-queue',       // queued form submissions for background sync
    data:  'offline-data',        // key-value data cache (timetable, grades, announcements)
  };

  let _db = null;

  // ── IndexedDB Setup ──────────────────────────────────────────────────────

  function openDB() {
    if (_db) return Promise.resolve(_db);
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(STORES.pages)) {
          const ps = db.createObjectStore(STORES.pages, { keyPath: 'url' });
          ps.createIndex('timestamp', 'timestamp', { unique: false });
        }
        if (!db.objectStoreNames.contains(STORES.queue)) {
          db.createObjectStore(STORES.queue, { keyPath: 'id', autoIncrement: true });
        }
        if (!db.objectStoreNames.contains(STORES.data)) {
          db.createObjectStore(STORES.data, { keyPath: 'key' });
        }
      };
      req.onsuccess = () => { _db = req.result; resolve(_db); };
      req.onerror = () => reject(req.error);
    });
  }

  function tx(storeName, mode) {
    return openDB().then((db) => {
      const t = db.transaction(storeName, mode || 'readonly');
      return t.objectStore(storeName);
    });
  }

  // ── Page Snapshots ───────────────────────────────────────────────────────
  // Saves a lightweight snapshot of each visited page so users can
  // browse previously-visited pages while offline.

  function extractPageData() {
    const mainContent = document.querySelector('.main-content, main, [role="main"], .content-wrapper');
    if (!mainContent) return null;

    // Extract readable text tables and key data
    const tables = [];
    mainContent.querySelectorAll('table').forEach((table) => {
      const rows = [];
      table.querySelectorAll('tr').forEach((tr) => {
        const cells = [];
        tr.querySelectorAll('th, td').forEach((cell) => {
          cells.push(cell.textContent.trim());
        });
        if (cells.length) rows.push(cells);
      });
      if (rows.length) tables.push(rows);
    });

    // Extract card content
    const cards = [];
    mainContent.querySelectorAll('.card').forEach((card) => {
      const title = card.querySelector('.card-title, .card-header')?.textContent?.trim() || '';
      const body = card.querySelector('.card-body')?.textContent?.trim()?.slice(0, 300) || '';
      if (title || body) cards.push({ title, body });
    });

    // Extract stat values
    const stats = [];
    mainContent.querySelectorAll('.stat-value, .display-6, .display-5, h2.fw-bold, .h2.fw-bold').forEach((el) => {
      const label = el.closest('.card, .stat-card')?.querySelector('.stat-label, .text-muted, small')?.textContent?.trim() || '';
      stats.push({ value: el.textContent.trim(), label });
    });

    return { tables, cards, stats };
  }

  async function savePageSnapshot() {
    try {
      const url = location.pathname + location.search;
      if (url.startsWith('/offline') || url.startsWith('/admin')) return;

      const title = document.title || '';
      const pageData = extractPageData();
      const mainEl = document.querySelector('.main-content, main, [role="main"], .content-wrapper');
      const htmlSnapshot = mainEl ? mainEl.innerHTML : '';

      // Determine page type from URL segments
      const segments = url.split('/').filter(Boolean);
      let pageType = 'page';
      const typeMap = {
        'dashboard': 'dashboard', 'timetable': 'timetable', 'grades': 'grades',
        'attendance': 'attendance', 'announcements': 'announcements', 'fees': 'fees',
        'students': 'students', 'teachers': 'teachers', 'subjects': 'subjects',
        'my-children': 'children', 'report-card': 'report', 'lesson-plans': 'lessons',
      };
      for (const seg of segments) {
        if (typeMap[seg]) { pageType = typeMap[seg]; break; }
      }

      // Detect tenant from URL
      const tenant = segments.length >= 2 ? segments[0] : null;

      const store = await tx(STORES.pages, 'readwrite');
      store.put({
        url,
        title,
        tenant,
        pageType,
        data: pageData,
        html: htmlSnapshot,
        timestamp: Date.now(),
      });
    } catch (err) {
      // Silently ignore — offline store is best-effort
    }
  }

  async function getPageSnapshot(url) {
    try {
      const store = await tx(STORES.pages);
      return new Promise((resolve) => {
        const req = store.get(url);
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      });
    } catch (err) {
      return null;
    }
  }

  async function getAllPages(tenant) {
    try {
      const store = await tx(STORES.pages);
      return new Promise((resolve) => {
        const req = store.getAll();
        req.onsuccess = () => {
          let pages = req.result || [];
          if (tenant) pages = pages.filter((p) => p.tenant === tenant);
          // Sort by most recent
          pages.sort((a, b) => b.timestamp - a.timestamp);
          resolve(pages);
        };
        req.onerror = () => resolve([]);
      });
    } catch (err) {
      return [];
    }
  }

  // ── Offline Form Queue ───────────────────────────────────────────────────
  // When network is down, form submissions are serialized and queued.
  // The service worker replays them via Background Sync when online.

  async function queueFormSubmission(formData, action, method) {
    try {
      const store = await tx(STORES.queue, 'readwrite');
      const entry = {
        action,
        method: method.toUpperCase(),
        data: formData, // serialized as object
        timestamp: Date.now(),
        status: 'pending',
        retries: 0,
      };
      return new Promise((resolve) => {
        const req = store.add(entry);
        req.onsuccess = () => resolve(req.result); // returns auto-incremented id
        req.onerror = () => resolve(null);
      });
    } catch (err) {
      return null;
    }
  }

  async function getQueuedSubmissions() {
    try {
      const store = await tx(STORES.queue);
      return new Promise((resolve) => {
        const req = store.getAll();
        req.onsuccess = () => {
          const items = (req.result || []).filter((i) => i.status === 'pending');
          resolve(items);
        };
        req.onerror = () => resolve([]);
      });
    } catch (err) {
      return [];
    }
  }

  async function removeQueuedItem(id) {
    try {
      const store = await tx(STORES.queue, 'readwrite');
      store.delete(id);
    } catch (err) {
      // ignore
    }
  }

  async function markQueuedItem(id, status) {
    try {
      const store = await tx(STORES.queue, 'readwrite');
      return new Promise((resolve) => {
        const getReq = store.get(id);
        getReq.onsuccess = () => {
          const item = getReq.result;
          if (item) {
            item.status = status;
            item.retries = (item.retries || 0) + 1;
            store.put(item);
          }
          resolve();
        };
        getReq.onerror = () => resolve();
      });
    } catch (err) {
      // ignore
    }
  }

  // ── Key-Value Data Cache ─────────────────────────────────────────────────

  async function saveData(key, value) {
    try {
      const store = await tx(STORES.data, 'readwrite');
      store.put({ key, value, timestamp: Date.now() });
    } catch (err) {
      // ignore
    }
  }

  async function getData(key) {
    try {
      const store = await tx(STORES.data);
      return new Promise((resolve) => {
        const req = store.get(key);
        req.onsuccess = () => resolve(req.result ? req.result.value : null);
        req.onerror = () => resolve(null);
      });
    } catch (err) {
      return null;
    }
  }

  // ── Replay Queue (foreground fallback when Background Sync unavailable) ─

  async function replayQueue() {
    const items = await getQueuedSubmissions();
    if (!items.length) return { sent: 0, failed: 0 };

    let sent = 0;
    let failed = 0;

    for (const item of items) {
      if (!navigator.onLine) break;
      try {
        // Rebuild FormData
        const fd = new FormData();
        for (const [k, v] of Object.entries(item.data)) {
          fd.append(k, v);
        }

        const resp = await fetch(item.action, {
          method: item.method,
          body: fd,
          credentials: 'same-origin',
        });

        if (resp.ok || resp.status === 302 || resp.status === 301) {
          await removeQueuedItem(item.id);
          sent++;
        } else {
          await markQueuedItem(item.id, 'pending');
          failed++;
        }
      } catch (err) {
        await markQueuedItem(item.id, 'pending');
        failed++;
      }
    }

    return { sent, failed };
  }

  // ── Pre-fetch linked pages ───────────────────────────────────────────────
  // After current page loads, quietly fetch and cache linked tenant pages
  // so they're available offline. Only fetches same-tenant links.

  function prefetchLinkedPages() {
    if (!navigator.onLine) return;

    const current = location.pathname;
    const segments = current.split('/').filter(Boolean);
    if (segments.length < 2) return;
    const tenant = segments[0];

    const links = new Set();
    document.querySelectorAll('a[href]').forEach((a) => {
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
      // Only same-tenant internal links
      if (href.startsWith('/' + tenant + '/')) {
        // Skip logout/delete/action links
        if (/logout|delete|remove|revoke/i.test(href)) return;
        links.add(href.split('?')[0]); // normalize
      }
    });

    // Limit to 6 prefetches per page load to conserve bandwidth
    let count = 0;
    for (const href of links) {
      if (count >= 6) break;
      // Use link prefetch if supported, otherwise low-priority fetch
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = href;
      link.as = 'document';
      document.head.appendChild(link);
      count++;
    }
  }

  // ── Sync data APIs (timetable, announcements) ────────────────────────────
  // Proactively fetches structured JSON data and stores in the data cache
  // so key screens can render offline from cached data.

  async function syncOfflineData() {
    if (!navigator.onLine) return;

    var current = location.pathname;
    var segments = current.split('/').filter(Boolean);
    if (segments.length < 2) return;
    var tenant = segments[0];
    // Skip non-tenant paths (landlord area, public pages)
    if (['tenants', 'admin', 'accounts', 'static', 'media'].indexOf(tenant) !== -1) return;

    var apis = [
      { key: tenant + ':timetable', url: '/' + tenant + '/academics/api/offline/timetable/' },
      { key: tenant + ':announcements', url: '/' + tenant + '/announcements/api/offline/' },
    ];

    for (var i = 0; i < apis.length; i++) {
      try {
        var resp = await fetch(apis[i].url, { credentials: 'same-origin' });
        if (resp.ok) {
          var json = await resp.json();
          await saveData(apis[i].key, json);
        }
      } catch (err) {
        // Silently skip — data will be fetched next time
      }
    }
  }

  // ── Auto-save on page load ───────────────────────────────────────────────

  function init() {
    // Save page snapshot after content renders
    if (document.readyState === 'complete') {
      setTimeout(savePageSnapshot, 800);
      setTimeout(prefetchLinkedPages, 2000);
      setTimeout(syncOfflineData, 3000);
    } else {
      window.addEventListener('load', () => {
        setTimeout(savePageSnapshot, 800);
        setTimeout(prefetchLinkedPages, 2000);
        setTimeout(syncOfflineData, 3000);
      });
    }

    // Replay queued submissions when coming back online
    window.addEventListener('online', async () => {
      const result = await replayQueue();
      if (result.sent > 0) {
        window.dispatchEvent(new CustomEvent('padi:queue-synced', { detail: result }));
      }
    });

    // Expose count for UI badge updates
    window.addEventListener('padi:queue-changed', async () => {
      const items = await getQueuedSubmissions();
      const badge = document.getElementById('offlineQueueBadge');
      if (badge) {
        badge.textContent = items.length;
        badge.style.display = items.length > 0 ? 'inline-flex' : 'none';
      }
    });
  }

  // ── Public API ───────────────────────────────────────────────────────────

  window.PadiOffline = {
    savePageSnapshot,
    getPageSnapshot,
    getAllPages,
    queueFormSubmission,
    getQueuedSubmissions,
    removeQueuedItem,
    replayQueue,
    saveData,
    getData,
    prefetchLinkedPages,
    syncOfflineData,
    init,
  };

  // Auto-init
  init();
})();
