const CACHE = "safarma-v14-trabzon-20260725";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./styles.css?v=14",
  "./online-v2.css?v=14",
  "./belink-ai.css?v=14",
  "./safarma-final-v8.css?v=14",
  "./belink-runtime.js?v=14",
  "./belink-client-runtime.js?v=14",
  "./loader.js?v=14",
  "./compat.js?v=14",
  "./fix-data.js?v=14",
  "./result-guard.js?v=14",
  "./app1a.js?v=14",
  "./app1b.js?v=14",
  "./app2a.js?v=14",
  "./app2b.js?v=14",
  "./app3.js?v=14",
  "./app4.js?v=14",
  "./app5.js?v=14",
  "./online-v2.js?v=14",
  "./belink-ai.js?v=14",
  "./safarma-specialists-v8.js?v=14",
  "./belink-connected-v2.js?v=7",
  "./privacy-controls.js?v=2",
  "./trabzon-preset.js?v=1",
  "./legal.html",
  "./plans.html",
  "./manifest.webmanifest?v=14",
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