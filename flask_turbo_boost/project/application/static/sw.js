var cacheName = 'news-v2';

var appShellFiles = [
  '/static/css/libs/tailwind.min.css',
  '/static/fonts/THSarabunNew/THSarabunNew.ttf',
  '/static/js/libs/respond.min.js',
  '/static/js/libs/jquery.min.js',
  '/static/icons/icon-512.png',
  '/static/icons/icon-256.png',
  '/static/icons/icon-128.png',
  '/static/icons/icon-64.png',
  '/static/icons/icon-48.png',
  '/static/icons/icon-32.png',
];

self.addEventListener('install', function(e) {
  console.log('[Service Worker] Install');
  e.waitUntil(
    caches.open(cacheName).then(function(cache) {
      console.log('[Service Worker] Caching all: app shell and content');
      return cache.addAll(appShellFiles);
    })
  );
});


self.addEventListener('fetch', function(e) {
  // console.log(e.request.url)
  e.respondWith(
    caches.match(e.request).then(function(r) {
      console.log('[Service Worker] Fetching resource: '+e.request.url, r);
      return r || fetch(e.request).then(function(response) {
        return caches.open(cacheName).then(function(cache) {
          console.log('[Service Worker] Caching new resource: '+e.request.url);
          // cache.put(e.request, response.clone());
          return response;
        });
      });
    })
  );
});


self.addEventListener('activate', (event) => {
  var cacheKeeplist = [cacheName];

  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (cacheKeeplist.indexOf(key) === -1) {
          return caches.delete(key);
        }
      }));
    })
  );
});
