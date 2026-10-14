const CACHE = 'khujand-museum-v1';
const SHELL = [
  '/', '/index.html', '/css/style.css', '/js/main.js', '/js/animations.js', '/js/app-enhancements.js',
  '/js/modules/i18n.js', '/js/modules/audio-guide.js', '/js/modules/modal.js', '/js/modules/tickets.js', '/js/modules/map.js', '/js/modules/analytics.js', '/js/modules/official-exhibits.js', '/data/official-exhibits.json',
  '/pages/expositions.html', '/pages/history.html', '/pages/events.html',
  '/pages/gallery.html', '/pages/contacts.html', '/manifest.json',
  '/data/i18n/ru.json', '/data/i18n/tj.json', '/data/i18n/en.json',
  '/data/official-exhibits.json', '/images/official/museum-1.jpg', '/images/official/museum-2.jpg', '/images/official/museum-3.jpg', '/images/official/museum-4.jpg', '/images/official/museum-5.jpg', '/images/official/museum-6.jpg', '/images/official/museum-7.jpg', '/images/official/museum-8.jpg', '/images/official/museum-9.jpg',
  '/voices/rus.mp3', '/voices/taj.mp3', '/voices/eng.mp3'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request).then(response => {
    if (!response.ok) return response;
    const copy = response.clone();
    if (new URL(event.request.url).origin === self.location.origin) caches.open(CACHE).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => event.request.mode === 'navigate' ? caches.match('/index.html') : Response.error())));
});
