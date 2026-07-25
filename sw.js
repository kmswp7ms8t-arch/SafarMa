const CACHE = "safarma-v16-public-launch-20260726";
const ASSETS = [
  "./",
  "./index.html",
  "./app.html",
  "./public.html",
  "./styles.css?v=16",
  "./online-v2.css?v=16",
  "./belink-ai.css?v=16",
  "./safarma-final-v8.css?v=16",
  "./belink-runtime.js?v=16",
  "./belink-client-runtime.js?v=16",
  "./loader.js?v=16",
  "./compat.js?v=16",
  "./fix-data.js?v=16",
  "./result-guard.js?v=16",
  "./app1a.js?v=16",
  "./app1b.js?v=16",
  "./app2a.js?v=16",
  "./app2b.js?v=16",
  "./app3.js?v=16",
  "./app4.js?v=16",
  "./app5.js?v=16",
  "./online-v2.js?v=16",
  "./belink-ai.js?v=16",
  "./safarma-specialists-v8.js?v=16",
  "./belink-connected-v2.js?v=9",
  "./privacy-controls.js?v=4",
  "./trabzon-preset.js?v=3",
  "./public-mode.js?v=2",
  "./public-launch-guard.js?v=1",
  "./legal.html",
  "./plans.html",
  "./pricing.html",
  "./robots.txt",
  "./sitemap.xml",
  "./manifest.webmanifest?v=16",
  "./manifest-public.webmanifest?v=16",
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
