(() => {
  "use strict";

  const runtime = window.BELINK_RUNTIME_CONFIG || {};
  const API_STORAGE = "belink-ai-api-base";
  const CLIENT_STORAGE = "belink-ai-client-token";
  const SESSION_STORAGE = "belink-ai-session-id";
  const LOCAL_PREFIXES = ["sm-", "belink-ai-", "safarma-"];
  const qs = (selector, root = document) => root.querySelector(selector);
  const isFa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  let busy = false;

  function safeGet(key) {
    try { return localStorage.getItem(key) || ""; } catch (_) { return ""; }
  }

  function normalizeBase(value = "") {
    const text = String(value || "").trim().replace(/\/+$/, "");
    if (!text) return "";
    try {
      const url = new URL(text);
      const local = ["localhost", "127.0.0.1"].includes(url.hostname);
      if (url.protocol !== "https:" && !(local && url.protocol === "http:")) return "";
      return `${url.origin}${url.pathname.replace(/\/$/, "")}`;
    } catch (_) { return ""; }
  }

  function apiBase() {
    const query = new URLSearchParams(location.search).get("api");
    return normalizeBase(query || runtime.apiBase || safeGet(API_STORAGE));
  }

  function serverIdentityExists() {
    return Boolean(apiBase() && safeGet(CLIENT_STORAGE));
  }

  function parseJson(value) {
    try { return JSON.parse(value); } catch (_) { return null; }
  }

  function localSnapshot() {
    return {
      language: safeGet("sm-lang") || null,
      travel_profile: parseJson(safeGet("sm-profile")),
      backend_configured: Boolean(apiBase()),
      signed_client_identity_present: Boolean(safeGet(CLIENT_STORAGE)),
      installed_release: runtime.version || null,
    };
  }

  function showToast(message, kind = "info") {
    qs(".safarma-privacy-toast")?.remove();
    const toast = document.createElement("div");
    toast.className = `safarma-privacy-toast ${kind}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
  }

  function downloadJson(payload) {
    const date = new Date().toISOString().slice(0, 10);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `SafarMa-data-${date}.json`;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function exportData() {
    if (busy) return;
    busy = true;
    updateDisabledState(true);
    try {
      let server = null;
      const base = apiBase();
      if (base && safeGet(CLIENT_STORAGE)) {
        const response = await fetch(`${base}${runtime.userDataPath || "/api/belink-ai/user-data"}`, {
          method: "GET",
          headers: { "Accept": "application/json" },
          cache: "no-store",
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
        server = data;
      }
      downloadJson({
        format: "safarma-complete-export-v1",
        exported_at: new Date().toISOString(),
        local: localSnapshot(),
        server,
        note: server
          ? "The server export is scoped to this browser's signed anonymous client identity."
          : "No accessible server-side identity was available; this export contains local device data only.",
      });
      showToast(
        server
          ? (isFa() ? "فایل کامل اطلاعات SafarMa آماده شد." : "Your complete SafarMa data file is ready.")
          : (isFa() ? "فایل اطلاعات دستگاه آماده شد؛ داده سرور قابل شناسایی نبود." : "Local data was exported; no server identity was available."),
        "success"
      );
    } catch (error) {
      showToast(
        `${isFa() ? "دریافت اطلاعات انجام نشد" : "Data export failed"}: ${String(error.message || error)}`,
        "error"
      );
    } finally {
      busy = false;
      updateDisabledState(false);
    }
  }

  async function clearAppCaches() {
    if (!("caches" in window)) return;
    try {
      const names = await caches.keys();
      await Promise.all(names.filter((name) => name.startsWith("safarma-")).map((name) => caches.delete(name)));
    } catch (_) {}
  }

  function clearLocalAppData() {
    try {
      const keys = [];
      for (let index = 0; index < localStorage.length; index += 1) {
        const key = localStorage.key(index);
        if (key && LOCAL_PREFIXES.some((prefix) => key.startsWith(prefix))) keys.push(key);
      }
      keys.forEach((key) => localStorage.removeItem(key));
    } catch (_) {}
    try {
      const keys = [];
      for (let index = 0; index < sessionStorage.length; index += 1) {
        const key = sessionStorage.key(index);
        if (key && LOCAL_PREFIXES.some((prefix) => key.startsWith(prefix))) keys.push(key);
      }
      keys.forEach((key) => sessionStorage.removeItem(key));
    } catch (_) {}
    try { window.BELINK_CLIENT_RUNTIME?.resetClient?.(); } catch (_) {}
  }

  async function deleteData() {
    if (busy) return;
    const warning = isFa()
      ? "این کار پاسخ‌های فرم، تاریخچه سفر، گفت‌وگوها و حافظه متصل این مرورگر را حذف می‌کند و قابل بازگشت نیست. ابتدا فایل اطلاعاتت را دریافت کن. ادامه می‌دهی؟"
      : "This permanently deletes questionnaire answers, trips, chats and connected memory for this browser identity. Export your data first. Continue?";
    if (!window.confirm(warning)) return;

    const typed = window.prompt(
      isFa() ? "برای تأیید نهایی کلمه «حذف» را بنویس:" : "Type DELETE to confirm permanent deletion:"
    );
    if ((isFa() && typed !== "حذف") || (!isFa() && typed !== "DELETE")) {
      showToast(isFa() ? "حذف لغو شد." : "Deletion cancelled.");
      return;
    }

    busy = true;
    updateDisabledState(true);
    try {
      const base = apiBase();
      const hasIdentity = serverIdentityExists();
      let serverReceipt = null;
      if (hasIdentity) {
        const response = await fetch(`${base}${runtime.userDataPath || "/api/belink-ai/user-data"}`, {
          method: "DELETE",
          headers: { "Accept": "application/json" },
          cache: "no-store",
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.detail || `HTTP ${response.status}`);
        }
        serverReceipt = data;
      }

      clearLocalAppData();
      await clearAppCaches();
      try {
        sessionStorage.setItem("safarma-deletion-receipt", JSON.stringify({
          deleted_at: new Date().toISOString(),
          server: serverReceipt,
        }));
      } catch (_) {}
      location.replace(`${location.pathname}?v=13&deleted=1`);
    } catch (error) {
      // Do not discard the client token when server deletion fails; otherwise the
      // anonymous server data could become inaccessible and impossible to delete.
      showToast(
        `${isFa() ? "حذف کامل انجام نشد؛ اطلاعات دستگاه حفظ شد" : "Complete deletion failed; local identity was preserved"}: ${String(error.message || error)}`,
        "error"
      );
      busy = false;
      updateDisabledState(false);
    }
  }

  function updateDisabledState(disabled) {
    [qs("#safarmaExportData"), qs("#safarmaDeleteData")].forEach((button) => {
      if (button) button.disabled = disabled;
    });
  }

  function renderControls() {
    const app = qs("#app");
    if (!app) return;
    let panel = qs("#safarmaPrivacyControls");
    if (!panel) {
      panel = document.createElement("section");
      panel.id = "safarmaPrivacyControls";
      panel.className = "safarma-privacy-controls";
      app.appendChild(panel);
    }
    const lang = isFa() ? "fa" : "en";
    if (panel.dataset.lang === lang) return;
    panel.dataset.lang = lang;
    panel.innerHTML = isFa()
      ? `<div><small>کنترل اطلاعات</small><b>اطلاعات SafarMa در اختیار شماست</b><p>قبل از پاک‌کردن مرورگر یا تغییر دستگاه، فایل اطلاعات را دریافت کن. شناسه سرور ناشناس و وابسته به همین مرورگر است.</p></div><div class="safarma-privacy-actions"><button id="safarmaExportData" type="button">دریافت فایل اطلاعات</button><button id="safarmaDeleteData" type="button" class="danger">حذف کامل اطلاعات</button></div>`
      : `<div><small>DATA CONTROL</small><b>Your SafarMa data belongs to you</b><p>Export before clearing the browser or changing devices. The anonymous server identity belongs to this browser.</p></div><div class="safarma-privacy-actions"><button id="safarmaExportData" type="button">Export my data</button><button id="safarmaDeleteData" type="button" class="danger">Delete all my data</button></div>`;
    qs("#safarmaExportData")?.addEventListener("click", exportData);
    qs("#safarmaDeleteData")?.addEventListener("click", deleteData);
  }

  function mountStyles() {
    if (qs("#safarmaPrivacyStyles")) return;
    const style = document.createElement("style");
    style.id = "safarmaPrivacyStyles";
    style.textContent = `
      .safarma-privacy-controls{margin:14px 0 22px;padding:17px;border-radius:22px;background:rgba(7,20,38,.82);border:1px solid rgba(117,231,255,.14);box-shadow:0 18px 45px rgba(0,0,0,.25);color:#edf8ff}.safarma-privacy-controls small{display:block;color:#75e7ff;letter-spacing:.12em;font-size:9px}.safarma-privacy-controls b{display:block;margin:5px 0;font-size:15px}.safarma-privacy-controls p{margin:5px 0 12px;color:#9eb6cc;font-size:11px;line-height:1.7}.safarma-privacy-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.safarma-privacy-actions button{border:1px solid rgba(117,231,255,.18);border-radius:14px;padding:11px 9px;background:rgba(117,231,255,.07);color:#eaf8ff;font-weight:800}.safarma-privacy-actions button.danger{border-color:rgba(248,113,113,.3);background:rgba(248,113,113,.08);color:#fecaca}.safarma-privacy-actions button:disabled{opacity:.55}.safarma-privacy-toast{position:fixed;z-index:150;left:50%;bottom:155px;transform:translateX(-50%);width:min(88vw,480px);padding:12px 15px;border-radius:15px;background:#061426;color:#e9f8ff;border:1px solid rgba(117,231,255,.25);box-shadow:0 20px 55px rgba(0,0,0,.6);text-align:center;font:700 12px/1.5 system-ui}.safarma-privacy-toast.success{border-color:rgba(74,222,128,.35)}.safarma-privacy-toast.error{border-color:rgba(248,113,113,.4);color:#fecaca}@media(max-width:560px){.safarma-privacy-actions{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  function showDeletionReceipt() {
    if (new URLSearchParams(location.search).get("deleted") !== "1") return;
    setTimeout(() => showToast(
      isFa() ? "اطلاعات SafarMa از دستگاه و هویت متصل حذف شد." : "SafarMa data was removed from this device and connected identity.",
      "success"
    ), 500);
  }

  function boot() {
    mountStyles();
    renderControls();
    showDeletionReceipt();
    new MutationObserver(renderControls).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
