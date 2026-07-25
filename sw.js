const CACHE = "safarma-v15-public-personal-20260725";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./public.html",
  "./styles.css?v=15",
  "./online-v2.css?v=15",
  "./belink-ai.css?v=15",
  "./safarma-final-v8.css?v=15",
  "./belink-runtime.js?v=15",
  "./belink-client-runtime.js?v=15",
  "./loader.js?v=15",
  "./compat.js?v=15",
  "./fix-data.js?v=15",
  "./result-guard.js?v=15",
  "./app1a.js?v=15",
  "./app1b.js?v=15",
  "./app2a.js?v=15",
  "./app2b.js?v=15",
  "./app3.js?v=15",
  "./app4.js?v=15",
  "./app5.js?v=15",
  "./online-v2.js?v=15",
  "./belink-ai.js?v=15",
  "./safarma-specialists-v8.js?v=15",
  "./belink-connected-v2.js?v=8",
  "./privacy-controls.js?v=3",
  "./trabzon-preset.js?v=2",
  "./public-mode.js?v=1",
  "./legal.html",
  "./plans.html",
  "./pricing.html",
  "./manifest.webmanifest?v=15",
  "./manifest-public.webmanifest?v=15",
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
        .catch(async () => {
          const exact = await caches.match(request);
          if (exact) return exact;
          if (url.pathname.endsWith("/public.html")) return caches.match("./public.html");
          if (url.pathname.endsWith("/app.html")) return caches.match("./app.html");
          if (url.pathname.endsWith("/pricing.html")) return caches.match("./pricing.html");
          return caches.match("./index.html");
        })
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
