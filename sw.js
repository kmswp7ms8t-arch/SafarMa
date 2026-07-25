const CACHE = "safarma-rc4-v13-20260725";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./styles.css?v=13",
  "./online-v2.css?v=13",
  "./belink-ai.css?v=13",
  "./safarma-final-v8.css?v=13",
  "./belink-runtime.js?v=13",
  "./belink-client-runtime.js?v=13",
  "./loader.js?v=13",
  "./compat.js?v=13",
  "./fix-data.js?v=13",
  "./result-guard.js?v=13",
  "./app1a.js?v=13",
  "./app1b.js?v=13",
  "./app2a.js?v=13",
  "./app2b.js?v=13",
  "./app3.js?v=13",
  "./app4.js?v=13",
  "./app5.js?v=13",
  "./online-v2.js?v=13",
  "./belink-ai.js?v=13",
  "./safarma-specialists-v8.js?v=13",
  "./belink-connected-v2.js?v=6",
  "./privacy-controls.js?v=1",
  "./legal.html",
  "./plans.html",
  "./manifest.webmanifest?v=13",
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
