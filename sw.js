const CACHE = "safarma-rc3-v11-20260725";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./styles.css",
  "./online-v2.css",
  "./belink-ai.css",
  "./safarma-final-v8.css",
  "./belink-runtime.js",
  "./belink-client-runtime.js",
  "./loader.js",
  "./compat.js",
  "./fix-data.js",
  "./result-guard.js",
  "./app1a.js",
  "./app1b.js",
  "./app2a.js",
  "./app2b.js",
  "./app3.js",
  "./app4.js",
  "./app5.js",
  "./online-v2.js",
  "./belink-ai.js",
  "./safarma-specialists-v8.js",
  "./belink-connected-v2.js",
  "./legal.html",
  "./plans.html",
  "./manifest.webmanifest",
  "./icon.svg"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
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
