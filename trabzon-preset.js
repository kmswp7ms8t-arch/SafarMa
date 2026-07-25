(() => {
  "use strict";

  const PROFILE_KEY = "sm-profile";
  const PRESET_ID = "amir-sanaz-trabzon-2026";
  const PRESET = Object.freeze({
    id: PRESET_ID,
    titleFa: "سفر ترابزون امیر و ساناز",
    titleEn: "Amir & Sanaz Trabzon Trip",
    status: "estimate_needs_live_verification",
    sourceNoteFa: "برآورد اولیه بر پایه برنامه آماده‌شده؛ قیمت، پرواز، ویزا، امنیت و موجودی باید هنگام اجرا دوباره بررسی شوند.",
    sourceNoteEn: "Initial estimate based on the prepared plan; prices, flights, entry rules, safety and availability must be checked again when used.",
    profile: {
      origin: "DOH",
      customOrigin: "",
      adults: 2,
      children: 0,
      passport: "Iran",
      passportExpiry: "",
      secondPassport: "",
      resStatus: "gcc",
      resCountry: "Qatar",
      resExpiry: "",
      start: "2026-08-06",
      days: 6,
      flex: 3,
      budget: 13500,
      mode: "specific",
      wanted: "Trabzon",
      regions: ["near"],
      styles: ["nature", "relax", "romantic"],
      flight: "prefer",
      maxHours: 9,
      stay: "four",
      transport: "car",
      food: "balanced",
      halal: true,
      priority: "overall",
      presetId: PRESET_ID,
      estimateLowQar: 11000,
      estimateHighQar: 13500,
      preferredAirline: "Qatar Airways direct when practical",
      alternativeAirline: "Turkish Airlines via Istanbul",
      itinerary: [
        "Arrival in Trabzon, hotel and city centre",
        "Uzungol full day",
        "Sumela Monastery and Hamsikoy",
        "Rize and Ayder",
        "Trabzon city, Boztepe and Ataturk Mansion",
        "Return to Doha"
      ]
    }
  });

  const isFa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  const esc = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  function loadCurrentProfile() {
    try {
      const current = JSON.parse(localStorage.getItem(PROFILE_KEY) || "null");
      return current && typeof current === "object" ? current : {};
    } catch (_) {
      return {};
    }
  }

  function savePreset() {
    const current = loadCurrentProfile();
    const merged = { ...current, ...PRESET.profile };
    try {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(merged));
      localStorage.setItem("safarma-active-preset", PRESET.id);
      localStorage.removeItem("belink-ai-session-id");
    } catch (_) {}
    location.href = `${location.pathname}?v=15&preset=${encodeURIComponent(PRESET.id)}`;
  }

  function closeModal() {
    document.querySelector("#trabzonPresetModal")?.remove();
  }

  function openModal() {
    closeModal();
    const fa = isFa();
    const modal = document.createElement("div");
    modal.id = "trabzonPresetModal";
    modal.className = "trabzon-preset-modal";
    const daysFa = [
      "روز ۱: پرواز دوحه به ترابزون، هتل و مرکز شهر",
      "روز ۲: اوزون‌گل",
      "روز ۳: صومعه سوملا و هامسی‌کوی",
      "روز ۴: ریزه و آیدر",
      "روز ۵: ترابزون، بوزتپه و عمارت آتاتورک",
      "روز ۶: بازگشت به دوحه"
    ];
    const daysEn = PRESET.profile.itinerary;
    modal.innerHTML = `
      <section role="dialog" aria-modal="true" aria-labelledby="trabzonPresetTitle">
        <button class="tp-close" type="button" aria-label="Close">×</button>
        <small>SAFARMA PERSONAL PRESET</small>
        <h2 id="trabzonPresetTitle">${esc(fa ? PRESET.titleFa : PRESET.titleEn)}</h2>
        <div class="tp-meta">
          <span>${fa ? "۶ تا ۱۱ آگوست ۲۰۲۶" : "6–11 August 2026"}</span>
          <span>${fa ? "۲ مسافر" : "2 travellers"}</span>
          <span>QAR 11,000–13,500</span>
        </div>
        <p class="tp-warning">${esc(fa ? PRESET.sourceNoteFa : PRESET.sourceNoteEn)}</p>
        <ul>${(fa ? daysFa : daysEn).map((item) => `<li>${esc(item)}</li>`).join("")}</ul>
        <div class="tp-actions">
          <button type="button" class="tp-primary">${fa ? "بارگذاری این برنامه" : "Load this plan"}</button>
          <button type="button" class="tp-secondary">${fa ? "بستن" : "Close"}</button>
        </div>
      </section>`;
    document.body.appendChild(modal);
    modal.querySelector(".tp-close")?.addEventListener("click", closeModal);
    modal.querySelector(".tp-secondary")?.addEventListener("click", closeModal);
    modal.querySelector(".tp-primary")?.addEventListener("click", savePreset);
    modal.addEventListener("click", (event) => { if (event.target === modal) closeModal(); });
  }

  function mount() {
    if (document.querySelector("#trabzonPresetButton")) return;
    const button = document.createElement("button");
    button.id = "trabzonPresetButton";
    button.type = "button";
    button.className = "trabzon-preset-button";
    button.innerHTML = `<b>TRABZON</b><span>${isFa() ? "برنامه ما" : "Our plan"}</span>`;
    button.addEventListener("click", openModal);
    document.body.appendChild(button);
  }

  function addStyles() {
    if (document.querySelector("#trabzonPresetStyles")) return;
    const style = document.createElement("style");
    style.id = "trabzonPresetStyles";
    style.textContent = `
      .trabzon-preset-button{position:fixed;z-index:74;right:max(12px,calc((100vw - 520px)/2 + 12px));bottom:calc(88px + env(safe-area-inset-bottom));border:1px solid rgba(248,207,99,.32);border-radius:15px;padding:9px 12px;background:linear-gradient(145deg,rgba(7,28,53,.96),rgba(22,11,43,.96));color:#eff8ff;box-shadow:0 18px 42px #0008;display:flex;flex-direction:column;align-items:flex-start;backdrop-filter:blur(18px)}
      .trabzon-preset-button b{font-size:10px;letter-spacing:.14em;color:#f8cf63}.trabzon-preset-button span{font-size:9px;color:#a9c3d8;margin-top:2px}
      .trabzon-preset-modal{position:fixed;inset:0;z-index:180;display:grid;place-items:center;padding:18px;background:rgba(0,4,12,.78);backdrop-filter:blur(13px)}
      .trabzon-preset-modal section{position:relative;width:min(520px,100%);max-height:min(760px,88vh);overflow:auto;padding:24px;border-radius:28px;background:linear-gradient(150deg,#071a31,#160d2e);border:1px solid rgba(117,231,255,.22);color:#eff8ff;box-shadow:0 30px 90px #000c}
      .trabzon-preset-modal small{color:#75e7ff;letter-spacing:.13em;font-size:9px}.trabzon-preset-modal h2{margin:8px 0 12px;font-size:25px}.trabzon-preset-modal ul{margin:15px 0;padding-inline-start:22px;color:#bed0df;line-height:1.8}.trabzon-preset-modal li{margin:4px 0}
      .tp-close{position:absolute;top:12px;inset-inline-end:12px;width:34px;height:34px;border-radius:50%;border:1px solid #ffffff1c;background:#ffffff0b;color:#fff;font-size:22px}.tp-meta{display:flex;flex-wrap:wrap;gap:7px}.tp-meta span{padding:7px 9px;border-radius:999px;background:#ffffff08;border:1px solid #75e7ff18;color:#d7e8f4;font-size:10px}.tp-warning{padding:12px;border-radius:15px;background:#f8cf6310;border:1px solid #f8cf6330;color:#f7e5ae;line-height:1.7;font-size:11px}.tp-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px}.tp-actions button{padding:13px;border-radius:15px;font-weight:900}.tp-primary{border:0;background:linear-gradient(135deg,#75e7ff,#c084fc);color:#06111f}.tp-secondary{border:1px solid #ffffff1c;background:#ffffff08;color:#eff8ff}
      @media(max-width:560px){.trabzon-preset-button span{display:none}.trabzon-preset-button{padding:10px}.tp-actions{grid-template-columns:1fr}}
    `;
    document.head.appendChild(style);
  }

  window.SAFARMA_PRESETS = Object.freeze({ ...(window.SAFARMA_PRESETS || {}), trabzon: PRESET });
  addStyles();
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
