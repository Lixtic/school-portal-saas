/**
 * Aura Offline Content — save structured tool content for offline access.
 *
 * Uses IndexedDB (`aura-content`, v1) with one object store keyed by
 * "{type}:{id}" (e.g. "lesson:42", "deck:7", "paper:15").
 *
 * Depends on nothing — fully self-contained.
 */
(function () {
  'use strict';

  const DB_NAME = 'aura-content';
  const DB_VERSION = 1;
  const STORE = 'items';

  let _db = null;

  function open() {
    if (_db) return Promise.resolve(_db);
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains(STORE)) {
          var s = db.createObjectStore(STORE, { keyPath: 'key' });
          s.createIndex('type', 'type', { unique: false });
          s.createIndex('saved_at', 'saved_at', { unique: false });
        }
      };
      req.onsuccess = function () { _db = req.result; resolve(_db); };
      req.onerror = function () { reject(req.error); };
    });
  }

  function store(mode) {
    return open().then(function (db) {
      return db.transaction(STORE, mode || 'readonly').objectStore(STORE);
    });
  }

  /* ── Public API ──────────────────────────────────────────────── */

  /**
   * Save content for offline access.
   * @param {string} type  - 'lesson' | 'deck' | 'paper' | 'question'
   * @param {number} id    - PK of the object
   * @param {object} data  - Full serialised content from the API
   * @returns {Promise<string>} The composite key
   */
  function save(type, id, data) {
    var key = type + ':' + id;
    return store('readwrite').then(function (s) {
      return new Promise(function (resolve) {
        var req = s.put({
          key: key,
          type: type,
          id: Number(id),
          data: data,
          saved_at: Date.now(),
        });
        req.onsuccess = function () { resolve(key); };
        req.onerror = function () { resolve(null); };
      });
    });
  }

  /**
   * Retrieve a single saved item.
   */
  function get(type, id) {
    var key = type + ':' + id;
    return store().then(function (s) {
      return new Promise(function (resolve) {
        var req = s.get(key);
        req.onsuccess = function () { resolve(req.result || null); };
        req.onerror = function () { resolve(null); };
      });
    });
  }

  /**
   * Remove saved content.
   */
  function remove(type, id) {
    var key = type + ':' + id;
    return store('readwrite').then(function (s) {
      return new Promise(function (resolve) {
        var req = s.delete(key);
        req.onsuccess = function () { resolve(true); };
        req.onerror = function () { resolve(false); };
      });
    });
  }

  /**
   * Check if content is saved.
   */
  function has(type, id) {
    return get(type, id).then(function (item) { return !!item; });
  }

  /**
   * List all saved items, optionally filtered by type.
   * @param {string} [type] - Filter by content type
   * @returns {Promise<Array>}
   */
  function list(type) {
    return store().then(function (s) {
      return new Promise(function (resolve) {
        var req;
        if (type) {
          var idx = s.index('type');
          req = idx.getAll(type);
        } else {
          req = s.getAll();
        }
        req.onsuccess = function () {
          var items = req.result || [];
          items.sort(function (a, b) { return b.saved_at - a.saved_at; });
          resolve(items);
        };
        req.onerror = function () { resolve([]); };
      });
    });
  }

  /**
   * Get total number of saved items and approximate storage size.
   */
  function stats() {
    return list().then(function (items) {
      var size = 0;
      items.forEach(function (item) {
        size += JSON.stringify(item.data || {}).length;
      });
      return { count: items.length, bytes: size };
    });
  }

  /**
   * Remove all saved content.
   */
  function clear() {
    return store('readwrite').then(function (s) {
      return new Promise(function (resolve) {
        var req = s.clear();
        req.onsuccess = function () { resolve(true); };
        req.onerror = function () { resolve(false); };
      });
    });
  }

  /**
   * Fetch from offline API and save to IDB. Shows progress via callback.
   * @param {string} type       - 'lesson' | 'deck' | 'paper'
   * @param {number} id         - PK
   * @param {string} apiUrl     - API endpoint URL
   * @param {function} [onDone] - Callback(success, data)
   */
  function download(type, id, apiUrl, onDone) {
    fetch(apiUrl, { credentials: 'same-origin' })
      .then(function (resp) {
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return resp.json();
      })
      .then(function (json) {
        return save(type, id, json).then(function () {
          if (onDone) onDone(true, json);
          window.dispatchEvent(new CustomEvent('aura:offline-changed'));
        });
      })
      .catch(function () {
        if (onDone) onDone(false, null);
      });
  }

  /* ── Expose ──────────────────────────────────────────────────── */
  window.AuraContent = {
    save: save,
    get: get,
    remove: remove,
    has: has,
    list: list,
    stats: stats,
    clear: clear,
    download: download,
  };
})();
