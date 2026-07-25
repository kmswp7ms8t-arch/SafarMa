(() => {
  "use strict";

  const API_STORAGE = "belink-ai-api-base";
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const isFa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";

  function backendConfigured() {
    try {
      const runtime = window.BELINK_RUNTIME_CONFIG || {};
      const query = new URLSearchParams(location.search).get("api");
      return Boolean(query || runtime.apiBase || localStorage.getItem(API_STORAGE));
    } catch (_) {
      return false;
    }
  }

  function showLaunchNotice() {
    qs("#safarmaLaunchNotice")?.remove();
    const toast = document.createElement("div");
    toast.id = "safarmaLaunchNotice";
    toast.className = "safarma-launch-notice-toast";
    toast.textContent = isFa()
      ? "تحلیل متصل Belink AI در مرحله راه‌اندازی است. نتیجه داخلی SafarMa همچنان قابل استفاده است."
      : "Connected Belink AI is being launched. SafarMa’s built-in planning result remains available.";
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
  }

  function mountResultNotice() {
    if (backendConfigured() || qs("#safarmaPublicAiNotice")) return;
    const hero = qs(".resultHero,.result-hero");
    if (!hero) return;
    const note = document.createElement("section");
    note.id = "safarmaPublicAiNotice";
    note.className = "safarma-public-ai-notice";
    note.innerHTML = `<b>${isFa() ? "نسخه عمومی SafarMa فعال است" : "SafarMa public planner is active"}</b><p>${isFa() ? "برنامه‌ریزی داخلی و بررسی‌های عمومی قابل استفاده‌اند. تحلیل متصل Belink Commander پس از تکمیل راه‌اندازی سرور فعال می‌شود." : "Built-in planning and public checks are available. Connected Belink Commander analysis will activate after the production server launch."}</p>`;
    hero.insertAdjacentElement("afterend", note);
  }

  function cleanTechnicalUi() {
    if (backendConfigured()) {
      qs("#safarmaPublicAiNotice")?.remove();
      return;
    }
    qs("#belinkBackendBadge")?.remove();
    qsa('.safarma-business-links a[href*="github.com"]').forEach((link) => link.remove());
    mountResultNotice();
  }

  function interceptTechnicalSetup(event) {
    if (backendConfigured()) return;
    const target = event.target.closest("#belinkConnectedAnalyzeResult,#belinkConnectedAnalyzeDrawer,#belinkBackendBadge");
    if (!target) return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    showLaunchNotice();
  }

  function addStyles() {
    if (qs("#safarmaPublicLaunchStyles")) return;
    const style = document.createElement("style");
    style.id = "safarmaPublicLaunchStyles";
    style.textContent = `
      .safarma-public-ai-notice{margin:12px 0 16px;padding:14px 15px;border-radius:18px;background:linear-gradient(145deg,rgba(8,29,51,.94),rgba(21,13,42,.94));border:1px solid rgba(117,231,255,.18);color:#edf9ff;box-shadow:0 16px 38px rgba(0,0,0,.28)}
      .safarma-public-ai-notice b{display:block;color:#75e7ff;margin-bottom:5px}.safarma-public-ai-notice p{margin:0;color:#a9bfd1;line-height:1.75;font-size:12px}
      .safarma-launch-notice-toast{position:fixed;z-index:250;left:50%;bottom:145px;transform:translateX(-50%);width:min(88vw,480px);padding:13px 15px;border-radius:16px;background:#061426;color:#eef9ff;border:1px solid rgba(117,231,255,.28);box-shadow:0 22px 60px rgba(0,0,0,.65);text-align:center;font:700 12px/1.65 system-ui}
    `;
    document.head.appendChild(style);
  }

  function boot() {
    addStyles();
    document.addEventListener("click", interceptTechnicalSetup, true);
    cleanTechnicalUi();
    const observer = new MutationObserver(cleanTechnicalUi);
    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
