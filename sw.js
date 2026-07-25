const CACHE = "safarma-rc3-v12-20260725";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./styles.css?v=12",
  "./online-v2.css?v=12",
  "./belink-ai.css?v=12",
  "./safarma-final-v8.css?v=12",
  "./belink-runtime.js?v=12",
  "./belink-client-runtime.js?v=12",
  "./loader.js?v=12",
  "./compat.js?v=12",
  "./fix-data.js?v=12",
  "./result-guard.js?v=12",
  "./app1a.js?v=12",
  "./app1b.js?v=12",
  "./app2a.js?v=12",
  "./app2b.js?v=12",
  "./app3.js?v=12",
  "./app4.js?v=12",
  "./app5.js?v=12",
  "./online-v2.js?v=12",
  "./belink-ai.js?v=12",
  "./safarma-specialists-v8.js?v=12",
  "./belink-connected-v2.js?v=5",
  "./legal.html",
  "./plans.html",
  "./manifest.webmanifest?v=12",
  "./icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request, { cache: "no-store" })
        .then((response) => {
          if (response.ok) caches.open(CACHE).then((cache) => cache.put(request, response.clone()));
          return response;
        })
        .catch(async () => (await caches.match(request)) || caches.match("./index.html"))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request, { cache: "no-store" }).then((response) => {
        if (response.ok) caches.open(CACHE).then((cache) => cache.put(request, response.clone()));
        return response;
      });
      return cached || network;
    })
  );
});
