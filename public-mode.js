(() => {
  "use strict";

  window.SAFARMA_PUBLIC_MODE = true;
  window.SAFARMA_STORAGE_SCOPE = "public";

  const params = new URLSearchParams(location.search);
  const originalStorage = {
    getItem: Storage.prototype.getItem,
    setItem: Storage.prototype.setItem,
    removeItem: Storage.prototype.removeItem,
  };

  function scopedKey(value) {
    const key = String(value || "");
    if (key.startsWith("sm-public-") || key.startsWith("belink-ai-public-") || key.startsWith("safarma-public-")) return key;
    if (key.startsWith("sm-")) return `sm-public-${key.slice(3)}`;
    if (key === "belink-ai-client-token") return "belink-ai-public-client-token";
    if (key === "belink-ai-session-id") return "belink-ai-public-session-id";
    if (key === "safarma-active-preset") return "safarma-public-active-preset";
    return key;
  }

  if (!window.__SAFARMA_PUBLIC_STORAGE_PATCHED__) {
    window.__SAFARMA_PUBLIC_STORAGE_PATCHED__ = true;
    Storage.prototype.getItem = function getItem(key) {
      return originalStorage.getItem.call(this, this === window.localStorage ? scopedKey(key) : key);
    };
    Storage.prototype.setItem = function setItem(key, value) {
      return originalStorage.setItem.call(this, this === window.localStorage ? scopedKey(key) : key, value);
    };
    Storage.prototype.removeItem = function removeItem(key) {
      return originalStorage.removeItem.call(this, this === window.localStorage ? scopedKey(key) : key);
    };
  }

  function futureDate(days) {
    const value = new Date();
    value.setHours(12, 0, 0, 0);
    value.setDate(value.getDate() + days);
    return value.toISOString().slice(0, 10);
  }

  const neutralProfile = Object.freeze({
    origin: "DOH",
    customOrigin: "",
    adults: 2,
    children: 0,
    passport: "Other",
    passportExpiry: "",
    secondPassport: "",
    resStatus: "none",
    resCountry: "",
    resExpiry: "",
    start: futureDate(30),
    days: 6,
    flex: 3,
    budget: 12000,
    mode: "open",
    wanted: "",
    regions: ["near"],
    styles: [],
    flight: "any",
    maxHours: 12,
    stay: "four",
    transport: "needed",
    food: "balanced",
    halal: true,
    priority: "overall"
  });

  try {
    if (!localStorage.getItem("sm-profile")) localStorage.setItem("sm-profile", JSON.stringify(neutralProfile));
    if (!localStorage.getItem("sm-lang")) localStorage.setItem("sm-lang", "fa");
    localStorage.setItem("sm-gift-open", "1");
  } catch (_) {}

  function isFa() {
    return document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  }

  function updatePublicCopy() {
    document.body.classList.add("safarma-public-edition");
    document.querySelector("#gift")?.classList.add("hide");

    const eyebrow = document.querySelector(".hero .eyebrow");
    if (eyebrow) eyebrow.textContent = isFa() ? "برنامه‌ریز هوشمند سفر برای همه" : "Global AI travel planning";

    document.querySelectorAll('a[href="./plans.html"]').forEach((link) => link.setAttribute("href", "./pricing.html"));

    const preset = document.querySelector("#trabzonPresetButton");
    if (preset && params.get("showPersonalPreset") !== "1") preset.remove();
  }

  function boot() {
    document.title = "SafarMa | سفرِ ما — AI Travel Planning";
    updatePublicCopy();
    new MutationObserver(updatePublicCopy).observe(document.body, { childList: true, subtree: true });
  }

  window.SAFARMA_PUBLIC_STORAGE = Object.freeze({
    scope: "public",
    scopedKey,
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
