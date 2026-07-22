(() => {
  "use strict";
  // SafarMa connected release connector v2.

  const STORAGE_API = "belink-ai-api-base";
  const STORAGE_SESSION = "belink-ai-session-id";
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];
  const isFa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  const esc = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const clean = (value = "") => String(value || "").replace(/\s+/g, " ").trim();

  let apiBase = "";
  let health = null;
  let latestDecision = null;
  let sessionId = "";
  let connectedPanel = null;
  let initialized = false;
  let lastAutoSignature = "";
  let analysisInFlight = false;

  function safeStorageGet(key) {
    try { return localStorage.getItem(key) || ""; } catch (_) { return ""; }
  }
  function safeStorageSet(key, value) {
    try { if (value) localStorage.setItem(key, value); else localStorage.removeItem(key); } catch (_) {}
  }
  function normalizeBase(value = "") {
    const text = clean(value).replace(/\/+$/, "");
    if (!text) return "";
    try {
      const url = new URL(text);
      return /^https?:$/.test(url.protocol) ? url.origin + url.pathname.replace(/\/$/, "") : "";
    } catch (_) { return ""; }
  }
  function resolveApiBase() {
    const query = new URLSearchParams(location.search).get("api");
    const configured = normalizeBase(query || window.BELINK_AI_CONFIG?.apiBase || window.BELINK_AI_API_BASE || safeStorageGet(STORAGE_API));
    if (query && configured) safeStorageSet(STORAGE_API, configured);
    apiBase = configured;
    sessionId = safeStorageGet(STORAGE_SESSION);
    return apiBase;
  }

  function addDays(dateString, days) {
    const date = new Date(`${dateString || new Date().toISOString().slice(0, 10)}T12:00:00`);
    date.setDate(date.getDate() + Math.max(0, Number(days || 1) - 1));
    return date.toISOString().slice(0, 10);
  }

  function getDestinationNames() {
    const values = [];
    try {
      String(p?.wanted || "").split(/[,،\n]/).forEach((item) => { if (clean(item)) values.push(clean(item)); });
      const rows = [result?.practical, ...(result?.alts || [])];
      rows.forEach((item) => {
        const name = clean(item?.en || item?.fa || item?.country || "");
        if (name) values.push(name);
      });
    } catch (_) {}
    return [...new Set(values.map((item) => item.slice(0, 120)))].slice(0, 8);
  }

  function normalizedFlight(value) {
    return ({ direct: "direct", prefer: "prefer_direct", stop: "one_stop", any: "any" })[value] || "prefer_direct";
  }
  function normalizedStay(value) {
    return ({ three: "3-star hotel", four: "4-star hotel", five: "5-star hotel", apartment: "apartment", resort: "resort" })[value] || "4-star hotel";
  }
  function normalizedTransport(value) {
    return ({ car: "rental car", needed: "only if needed", none: "no car", driver: "private driver" })[value] || "only if needed";
  }
  function normalizedFood(value) {
    return ({ budget: "budget", balanced: "balanced", premium: "restaurant-focused" })[value] || "balanced";
  }

  function buildProfile() {
    const state = typeof p === "object" && p ? p : {};
    const start = state.start || new Date().toISOString().slice(0, 10);
    const days = Math.max(1, Number(state.days || 6));
    return {
      origin: clean(state.origin || "DOH").slice(0, 120),
      destination_candidates: getDestinationNames(),
      passport: clean(state.passport || "Iran").slice(0, 80),
      passport_expiry: state.passportExpiry || null,
      residence_country: ["citizen", "none"].includes(state.resStatus) ? null : (state.resCountry || null),
      residence_status: state.resStatus || "none",
      residence_expiry: ["citizen", "none"].includes(state.resStatus) ? null : (state.resExpiry || null),
      departure_date: start,
      return_date: addDays(start, days),
      travelers: Math.max(1, Number(state.adults || 2) + Number(state.children || 0)),
      budget_qar: Math.max(1, Number(state.budget || 13000)),
      trip_style: Array.isArray(state.styles) ? state.styles.slice(0, 8) : [],
      flight_preference: normalizedFlight(state.flight),
      accommodation: normalizedStay(state.stay),
      transport_preference: normalizedTransport(state.transport),
      food_preference: normalizedFood(state.food),
      halal_required: state.halal !== false,
      language: isFa() ? "fa" : "en"
    };
  }

  async function request(path, options = {}, timeoutMs = 45000) {
    if (!apiBase) throw new Error(isFa() ? "آدرس سرور Belink AI تنظیم نشده است." : "Belink AI backend is not configured.");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${apiBase}${path}`, {
        ...options,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...(sessionId ? { "X-Belink-Session": sessionId } : {}),
          ...(options.headers || {})
        }
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || data.message || `HTTP ${response.status}`);
      return data;
    } finally { clearTimeout(timer); }
  }

  async function checkHealth() {
    if (!apiBase) return null;
    try {
      health = await request("/health", { method: "GET", headers: {} }, 10000);
      updateConnectionBadges();
      return health;
    } catch (_) {
      health = null;
      updateConnectionBadges();
      return null;
    }
  }

  function modeLabel(mode) {
    if (mode === "connected") return isFa() ? "Belink AI متصل" : "Belink AI connected";
    if (apiBase && health) return isFa() ? "سرور متصل · AI آفلاین" : "Server connected · offline AI";
    return isFa() ? "هسته امن آفلاین" : "Secure offline core";
  }

  function updateConnectionBadges() {
    const connected = Boolean(apiBase && health);
    qsa("#belinkAiStatus,.belink-ai-status").forEach((row) => {
      row.classList.toggle("connected", connected && health?.ai_connected);
      row.classList.toggle("offline", !connected || !health?.ai_connected);
      const label = qs("span", row) || row;
      label.textContent = modeLabel(connected && health?.ai_connected ? "connected" : "offline");
    });
    let badge = qs("#belinkBackendBadge");
    if (!badge) {
      badge = document.createElement("button");
      badge.id = "belinkBackendBadge";
      badge.type = "button";
      badge.className = "belink-backend-badge";
      document.body.appendChild(badge);
      badge.addEventListener("click", openBackendSetup);
    }
    badge.className = `belink-backend-badge ${connected ? (health?.ai_connected ? "is-connected" : "is-offline") : "is-unconfigured"}`;
    badge.innerHTML = `<i></i><span>${esc(modeLabel(connected && health?.ai_connected ? "connected" : "offline"))}</span>`;
  }

  function openBackendSetup() {
    const current = apiBase || "";
    const value = prompt(isFa()
      ? "آدرس HTTPS سرور Belink AI را وارد کن. کلید API هرگز اینجا وارد نمی‌شود."
      : "Enter the HTTPS Belink AI backend URL. Never enter an API key here.", current);
    if (value === null) return;
    const normalized = normalizeBase(value);
    apiBase = normalized;
    safeStorageSet(STORAGE_API, normalized);
    health = null;
    checkHealth().then(autoAnalyzeIfReady);
    showToast(normalized
      ? (isFa() ? "آدرس سرور ذخیره شد." : "Backend URL saved.")
      : (isFa() ? "حالت آفلاین فعال شد." : "Offline mode enabled."));
  }

  function showToast(message) {
    qs(".belink-connect-toast")?.remove();
    const toast = document.createElement("div");
    toast.className = "belink-connect-toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2600);
  }

  function sourceCards(sources = []) {
    const valid = sources.filter((item) => item?.url).slice(0, 10);
    if (!valid.length) return `<p class="bc-muted">${isFa() ? "منبع آنلاین قابل‌نمایش دریافت نشد." : "No displayable online source was returned."}</p>`;
    return `<div class="bc-sources">${valid.map((item) => `<a href="${esc(item.url)}" target="_blank" rel="noopener"><b>${esc(item.title || "Source")}</b><small>${esc(item.classification || item.source_type || "source")} · ${esc(item.verification_status || "unknown")}</small></a>`).join("")}</div>`;
  }

  function findingLabel(value = "unknown") {
    const mapFa = { good: "مناسب", conditional: "مشروط", blocked: "مانع", unknown: "نامشخص" };
    const mapEn = { good: "Good", conditional: "Conditional", blocked: "Blocked", unknown: "Unknown" };
    return (isFa() ? mapFa : mapEn)[value] || value;
  }

  function verdictLabel(value = "needs_verification") {
    const fa = { feasible: "سفر شدنی است", conditional: "سفر با شرط شدنی است", not_feasible: "در شرایط فعلی شدنی نیست", needs_verification: "نیازمند تأیید نهایی" };
    const en = { feasible: "Trip is feasible", conditional: "Feasible with conditions", not_feasible: "Not feasible now", needs_verification: "Final verification required" };
    return (isFa() ? fa : en)[value] || value;
  }

  function renderConnectedDecision(data) {
    const decision = data?.decision;
    if (!decision) return;
    latestDecision = decision;
    if (data.session_id) {
      sessionId = data.session_id;
      safeStorageSet(STORAGE_SESSION, sessionId);
    }
    const hero = qs(".resultHero,.result-hero");
    if (!hero) return;
    connectedPanel?.remove();
    const panel = document.createElement("section");
    panel.className = `belink-connected-decision verdict-${decision.verdict}`;
    panel.innerHTML = `
      <div class="bc-head"><div><small>BELINK COMMANDER · ${esc(String(data.mode || "offline").toUpperCase())}</small><h2>${esc(verdictLabel(decision.verdict))}</h2></div><div class="bc-confidence"><b>${Number(decision.confidence || 0)}%</b><span>${isFa() ? "اطمینان" : "confidence"}</span></div></div>
      <p class="bc-summary">${esc(decision.executive_summary || decision.answer_to_user || "")}</p>
      <div class="bc-destination"><span>${isFa() ? "پیشنهاد اصلی" : "Primary recommendation"}</span><b>${esc(decision.primary_destination || "—")}</b><p>${esc(decision.why_this_destination || "")}</p></div>
      <div class="bc-cost"><span>${isFa() ? "بودجه امن" : "Safe budget"}</span><b>${Number(decision.cost?.total_low || 0).toLocaleString()} – ${Number(decision.cost?.total_high || 0).toLocaleString()} QAR</b></div>
      <div class="bc-findings">${(decision.specialist_findings || []).map((finding) => `<article class="finding-${esc(finding.status)}"><div><b>${esc(finding.specialist)}</b><em>${esc(findingLabel(finding.status))}</em></div><p>${esc(finding.summary)}</p>${sourceCards(finding.sources || [])}</article>`).join("")}</div>
      ${decision.unknowns?.length ? `<details><summary>${isFa() ? "موارد هنوز نامشخص" : "Still unknown"}</summary><ul>${decision.unknowns.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></details>` : ""}
      ${decision.next_actions?.length ? `<div class="bc-actions"><b>${isFa() ? "اقدام‌های بعدی" : "Next actions"}</b><ol>${decision.next_actions.map((item) => `<li>${esc(item)}</li>`).join("")}</ol></div>` : ""}
      <div class="bc-all-sources"><b>${isFa() ? "منابع بررسی‌شده" : "Checked sources"}</b>${sourceCards(decision.sources || [])}</div>
      <small class="bc-checked">${isFa() ? "زمان بررسی" : "Checked at"}: ${esc(decision.checked_at || new Date().toISOString())}</small>`;
    hero.insertAdjacentElement("afterend", panel);
    connectedPanel = panel;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function analyzeWithBelink(trigger = null, { automatic = false } = {}) {
    if (analysisInFlight) return;
    if (!apiBase) {
      if (automatic) return;
      openBackendSetup();
      if (!apiBase) return;
    }
    analysisInFlight = true;
    const button = trigger?.currentTarget || trigger || qs("#belinkConnectedAnalyzeResult") || qs("#belinkConnectedAnalyzeDrawer");
    const original = button?.textContent;
    if (button) {
      button.disabled = true;
      button.textContent = isFa() ? "در حال تحلیل واقعی…" : "Running connected analysis…";
    }
    try {
      const data = await request("/api/belink-ai/analyze", {
        method: "POST",
        body: JSON.stringify(buildProfile())
      }, 90000);
      renderConnectedDecision(data);
      health = { ...(health || {}), ai_connected: data.mode === "connected" };
      updateConnectionBadges();
      showToast(data.mode === "connected"
        ? (isFa() ? "تحلیل متصل Belink AI تکمیل شد." : "Connected Belink AI analysis completed.")
        : (isFa() ? "تحلیل امن آفلاین تکمیل شد؛ موارد نامشخص مشخص شده‌اند." : "Secure offline analysis completed; unknowns are labelled."));
    } catch (error) {
      showToast(`${isFa() ? "تحلیل کامل نشد" : "Analysis failed"}: ${clean(error.message)}`);
    } finally {
      analysisInFlight = false;
      if (button) {
        button.disabled = false;
        button.textContent = original || (isFa() ? "تحلیل با Belink Commander" : "Analyze with Belink Commander");
      }
    }
  }

  async function chatWithBelink(question) {
    if (!apiBase) throw new Error(isFa() ? "سرور Belink AI تنظیم نشده است." : "Belink AI backend is not configured.");
    const data = await request("/api/belink-ai/chat", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId || null,
        question: clean(question).slice(0, 1200),
        profile: buildProfile(),
        latest_decision: latestDecision
      })
    }, 70000);
    if (data.session_id) {
      sessionId = data.session_id;
      safeStorageSet(STORAGE_SESSION, sessionId);
    }
    return data.answer;
  }

  function enhanceDrawer() {
    const root = qs("#belinkAiRoot");
    const drawer = qs("#belinkAiDrawer");
    if (!root || !drawer || drawer.dataset.connectedEnhanced === "1") return;
    drawer.dataset.connectedEnhanced = "1";
    const status = qs("#belinkAiStatus", drawer);
    status?.insertAdjacentHTML("afterend", `<button class="bc-analyze-button" id="belinkConnectedAnalyzeDrawer">${isFa() ? "تحلیل با Belink Commander" : "Analyze with Belink Commander"}</button>`);
    qs("#belinkConnectedAnalyzeDrawer")?.addEventListener("click", analyzeWithBelink);

    const send = qs("#belinkAiSend");
    const input = qs("#belinkAiQuestion");
    const answer = qs("#belinkAiAnswer");
    const connectedSend = async (question) => {
      const text = clean(question);
      if (!text || !apiBase) return;
      answer.innerHTML = `<b>Belink Commander</b><p>${isFa() ? "در حال بررسی زمینه سفر…" : "Reviewing your trip context…"}</p>`;
      try {
        const response = await chatWithBelink(text);
        answer.innerHTML = `<b>Belink Commander</b><p>${esc(response.answer || "")}</p>${sourceCards(response.sources || [])}`;
        health = { ...(health || {}), ai_connected: true };
        updateConnectionBadges();
      } catch (error) {
        answer.innerHTML = `<b>Belink Commander</b><p>${esc(isFa() ? "اتصال کامل نشد؛ پاسخ محلی قبلی همچنان قابل استفاده است." : "Connected answer failed; the existing local answer remains available.")}</p><small>${esc(clean(error.message))}</small>`;
      }
    };
    send?.addEventListener("click", (event) => {
      if (!apiBase) return;
      event.stopImmediatePropagation();
      const value = input?.value || "";
      if (input) input.value = "";
      connectedSend(value);
    }, true);
    input?.addEventListener("keydown", (event) => {
      if (!apiBase || event.key !== "Enter") return;
      event.preventDefault();
      event.stopImmediatePropagation();
      const value = input.value;
      input.value = "";
      connectedSend(value);
    }, true);
    qsa("[data-q]", drawer).forEach((button) => button.addEventListener("click", (event) => {
      if (!apiBase) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      connectedSend(button.dataset.q || button.textContent);
    }, true));
    updateConnectionBadges();
  }

  function mountResultButton() {
    const hero = qs(".resultHero,.result-hero");
    if (!hero || qs("#belinkConnectedAnalyzeResult")) return;
    const button = document.createElement("button");
    button.id = "belinkConnectedAnalyzeResult";
    button.className = "bc-analyze-button standalone";
    button.textContent = isFa() ? "تحلیل نهایی با Belink Commander" : "Final analysis with Belink Commander";
    button.addEventListener("click", analyzeWithBelink);
    hero.insertAdjacentElement("afterend", button);
  }

  function profileSignature() {
    try { return JSON.stringify(buildProfile()); } catch (_) { return ""; }
  }

  async function autoAnalyzeIfReady() {
    if (!apiBase || !health || analysisInFlight || connectedPanel || !qs(".resultHero,.result-hero")) return;
    const signature = profileSignature();
    if (!signature || signature === lastAutoSignature) return;
    lastAutoSignature = signature;
    await analyzeWithBelink(null, { automatic: true });
  }

  function mountBusinessLinks() {
    const container = qs("#app");
    if (!container || qs(".safarma-business-links", container)) return;
    const links = document.createElement("div");
    links.className = "safarma-business-links";
    links.innerHTML = `<a href="./plans.html">${isFa() ? "پلن‌ها" : "Plans"}</a><a href="./legal.html">${isFa() ? "شرایط و حریم خصوصی" : "Terms & privacy"}</a><a href="https://github.com/kmswp7ms8t-arch/SafarMa/issues" target="_blank" rel="noopener">${isFa() ? "پشتیبانی فنی" : "Technical support"}</a>`;
    container.appendChild(links);
  }

  function mountStyles() {
    if (qs("#belinkConnectedStyles")) return;
    const style = document.createElement("style");
    style.id = "belinkConnectedStyles";
    style.textContent = `
      .belink-backend-badge{position:fixed;z-index:76;left:max(12px,calc((100vw - 520px)/2 + 12px));bottom:calc(88px + env(safe-area-inset-bottom));border:1px solid rgba(117,231,255,.18);border-radius:14px;padding:8px 10px;background:rgba(3,12,27,.92);color:#dff8ff;display:flex;align-items:center;gap:7px;box-shadow:0 15px 35px #0006;font:700 10px/1.2 system-ui;backdrop-filter:blur(18px)}
      .belink-backend-badge i{width:8px;height:8px;border-radius:50%;background:#fbbf24;box-shadow:0 0 12px currentColor}.belink-backend-badge.is-connected i{background:#4ade80}.belink-backend-badge.is-offline i{background:#60a5fa}.belink-backend-badge.is-unconfigured i{background:#fbbf24}
      .bc-analyze-button{width:100%;border:1px solid rgba(117,231,255,.2);border-radius:16px;padding:13px 14px;background:linear-gradient(135deg,#74e8ff,#c084fc);color:#07111f;font-weight:900;box-shadow:0 16px 34px rgba(117,231,255,.18)}.bc-analyze-button.standalone{margin:12px 0 16px}.bc-analyze-button:disabled{opacity:.6}
      .belink-connected-decision{margin:16px 0;padding:18px;border-radius:26px;color:#eef8ff;background:linear-gradient(145deg,rgba(5,25,47,.96),rgba(22,10,42,.93));border:1px solid rgba(117,231,255,.18);box-shadow:0 24px 60px #0007}.bc-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.bc-head small{color:#75e7ff;letter-spacing:.12em;font-size:9px}.bc-head h2{margin:5px 0;font-size:25px}.bc-confidence{min-width:76px;text-align:center;padding:11px;border-radius:16px;background:#ffffff0b;border:1px solid #75e7ff1f}.bc-confidence b{display:block;font-size:21px;color:#75e7ff}.bc-confidence span{font-size:9px;color:#9bb4cb}.bc-summary,.bc-destination p{color:#aec3d6;line-height:1.75}.bc-destination,.bc-cost,.bc-actions,.bc-all-sources{margin-top:12px;padding:13px;border-radius:17px;background:#ffffff0a;border:1px solid #75e7ff15}.bc-destination span,.bc-cost span{display:block;color:#75e7ff;font-size:10px;margin-bottom:5px}.bc-cost b{font-size:18px}.bc-findings{display:grid;gap:9px;margin-top:12px}.bc-findings article{padding:13px;border-radius:17px;background:#ffffff08;border:1px solid #ffffff0d}.bc-findings article>div{display:flex;justify-content:space-between;gap:8px}.bc-findings em{font-style:normal;font-size:10px;color:#75e7ff}.bc-findings p{color:#b1c4d7;line-height:1.65}.bc-sources{display:grid;gap:7px;margin-top:9px}.bc-sources a{display:block;padding:9px;border-radius:12px;background:#02081788;border:1px solid #75e7ff14;color:#eaf7ff;text-decoration:none}.bc-sources small{display:block;color:#8da8c0;margin-top:3px}.bc-muted,.bc-checked{color:#8da8c0}.bc-actions li,.belink-connected-decision li{margin:5px 0;color:#b6c9db}.belink-connect-toast{position:fixed;z-index:130;left:50%;bottom:155px;transform:translateX(-50%);max-width:min(88vw,480px);padding:12px 15px;border-radius:15px;background:#061426;color:#e9f8ff;border:1px solid #75e7ff2c;box-shadow:0 20px 55px #0009;text-align:center;font:700 12px/1.5 system-ui}
      .safarma-business-links{display:flex;justify-content:center;flex-wrap:wrap;gap:7px;margin:20px 0 8px;padding-bottom:10px}.safarma-business-links a{color:#9fdff1;text-decoration:none;padding:7px 10px;border:1px solid rgba(117,231,255,.12);border-radius:999px;background:rgba(255,255,255,.035);font-size:10px}.safarma-business-links a:hover{border-color:rgba(117,231,255,.36);color:#effbff}
      @media(max-width:560px){.belink-backend-badge span{display:none}.belink-backend-badge{padding:10px}.bc-head{flex-direction:column}.bc-confidence{align-self:flex-start}}
    `;
    document.head.appendChild(style);
  }

  function boot() {
    if (initialized) return;
    initialized = true;
    resolveApiBase();
    mountStyles();
    updateConnectionBadges();
    const observer = new MutationObserver(() => {
      enhanceDrawer();
      mountResultButton();
      mountBusinessLinks();
      autoAnalyzeIfReady();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    enhanceDrawer();
    mountResultButton();
    mountBusinessLinks();
    checkHealth().then(autoAnalyzeIfReady);
    window.BELINK_AI = Object.freeze({
      analyze: () => analyzeWithBelink(),
      configureBackend: openBackendSetup,
      health: () => health,
      apiBase: () => apiBase
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();