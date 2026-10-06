// Service Worker Pustaka Struk
// Versi: v1 — minimal & valid

const CACHE_NAME = 'pustaka-struk-v1';

// Install: skip waiting biar langsung aktif
self.addEventListener('install', function(event) {
  self.skipWaiting();
});

// Activate: klaim semua client
self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});

// Fetch: biarkan Streamlit lewat, cache yang lain
self.addEventListener('fetch', function(event) {
  // Jangan cache request ke Streamlit
  if (event.request.url.includes('streamlit.app')) {
    return;
  }
  
  event.respondWith(
    caches.match(event.request).then(function(response) {
      return response || fetch(event.request);
    })
  );
});
