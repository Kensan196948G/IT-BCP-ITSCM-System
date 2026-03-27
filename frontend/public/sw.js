const CACHE_NAME = 'bcp-itscm-v2';
const CRITICAL_ASSETS = [
  '/',
  '/plans',
  '/procedures',
  '/contacts',
  '/rto-monitor',
  '/incidents',
  '/offline',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(CRITICAL_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);

  // Skip WebSocket and API requests from caching
  if (url.pathname.startsWith('/ws') || url.pathname.startsWith('/api')) {
    return;
  }

  const isCritical = CRITICAL_ASSETS.some(
    (asset) => url.pathname === asset || url.pathname === asset + '/'
  );

  if (isCritical) {
    // Stale-while-revalidate for BCP critical resources
    event.respondWith(
      caches.match(event.request).then((cached) => {
        const fetchPromise = fetch(event.request)
          .then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, clone);
              });
            }
            return response;
          })
          .catch(() => {
            // Network failed, return cached or offline page
            return cached || caches.match('/offline');
          });

        return cached || fetchPromise;
      })
    );
  } else {
    // Network-first for other resources, fallback to offline page
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          return response;
        })
        .catch(() => {
          return caches.match(event.request).then((cached) => {
            return cached || caches.match('/offline');
          });
        })
    );
  }
});
