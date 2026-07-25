(() => {
  "use strict";

  const API_STORAGE = "belink-ai-api-base";
  const CLIENT_STORAGE = "belink-ai-client-token";
  const runtime = window.BELINK_RUNTIME_CONFIG || {};
  const originalFetch = window.fetch.bind(window);

  function safeGet(key) {
    try { return localStorage.getItem(key) || ""; } catch (_) { return ""; }
  }

  function safeSet(key, value) {
    try {
      if (value) localStorage.setItem(key, value);
      else localStorage.removeItem(key);
    } catch (_) {}
  }

  function normalizeBase(value = "") {
    const text = String(value || "").trim().replace(/\/+$/, "");
    if (!text) return "";
    try {
      const parsed = new URL(text);
      if (!/^https?:$/.test(parsed.protocol)) return "";
      return `${parsed.origin}${parsed.pathname.replace(/\/$/, "")}`;
    } catch (_) { return ""; }
  }

  function configuredApiBase() {
    const query = new URLSearchParams(location.search).get("api");
    return normalizeBase(query || runtime.apiBase || window.BELINK_AI_API_BASE || safeGet(API_STORAGE));
  }

  function isApiRequest(url) {
    const base = configuredApiBase();
    return Boolean(base && (url === base || url.startsWith(`${base}/`)));
  }

  async function captureToken(response) {
    try {
      const data = await response.clone().json();
      if (data && typeof data.client_token === "string" && data.client_token.startsWith("b1.")) {
        safeSet(CLIENT_STORAGE, data.client_token);
      }
    } catch (_) {}
  }

  async function securedFetch(input, init = {}) {
    const inputUrl = typeof input === "string" || input instanceof URL ? String(input) : input.url;
    let resolved;
    try { resolved = new URL(inputUrl, location.href).href; } catch (_) { return originalFetch(input, init); }
    if (!isApiRequest(resolved)) return originalFetch(input, init);

    const token = safeGet(CLIENT_STORAGE);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    new Headers(init.headers || {}).forEach((value, key) => headers.set(key, value));
    if (token) headers.set(runtime.clientHeader || "X-Belink-Client", token);

    const requestInit = { ...init, headers };
    let response = await originalFetch(input, requestInit);

    // A token is tied to one backend secret. If the backend URL changes or its secret
    // rotates, transparently request a fresh anonymous identity once.
    if (response.status === 401 && token && !(input instanceof Request)) {
      safeSet(CLIENT_STORAGE, "");
      headers.delete(runtime.clientHeader || "X-Belink-Client");
      response = await originalFetch(input, { ...requestInit, headers });
    }

    captureToken(response);
    return response;
  }

  window.fetch = securedFetch;
  window.BELINK_AI_CONFIG = Object.freeze({
    ...(window.BELINK_AI_CONFIG || {}),
    apiBase: runtime.apiBase || window.BELINK_AI_CONFIG?.apiBase || "",
    autoAnalyze: runtime.autoAnalyze === true,
    analyzePath: runtime.analyzePath || "/api/belink-ai/analyze",
    chatPath: runtime.chatPath || "/api/belink-ai/chat"
  });

  window.BELINK_CLIENT_RUNTIME = Object.freeze({
    version: runtime.version || "unknown",
    apiBase: configuredApiBase,
    hasClientToken: () => Boolean(safeGet(CLIENT_STORAGE)),
    resetClient: () => safeSet(CLIENT_STORAGE, "")
  });
})();
