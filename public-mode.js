(() => {
  "use strict";

  window.SAFARMA_PUBLIC_MODE = true;

  const PROFILE_KEY = "sm-profile";
  const params = new URLSearchParams(location.search);
  const neutralProfile = Object.freeze({
    origin: "DOH",
    customOrigin: "",
    adults: 2,
    children: 0,
    passport: "Qatar",
    passportExpiry: "",
    secondPassport: "",
    resStatus: "citizen",
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

  let profileApplied = false;

  function futureDate(days) {
    const value = new Date();
    value.setHours(12, 0, 0, 0);
    value.setDate(value.getDate() + days);
    return value.toISOString().slice(0, 10);
  }

  function isFa() {
    return document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  }

  function hasSavedProfile() {
    try {
      const value = localStorage.getItem(PROFILE_KEY);
      if (!value) return false;
      const parsed = JSON.parse(value);
      return Boolean(parsed && typeof parsed === "object");
    } catch (_) {
      return false;
    }
  }

  function applyNeutralProfile() {
    if (profileApplied || hasSavedProfile()) return;
    try {
      if (typeof p === "undefined") return;
      p = JSON.parse(JSON.stringify(neutralProfile));
      profileApplied = true;
      if (typeof welcome === "function") welcome();
    } catch (_) {}
  }

  function updatePublicCopy() {
    document.body.classList.add("safarma-public-edition");
    document.querySelector("#gift")?.classList.add("hide");

    const eyebrow = document.querySelector(".hero .eyebrow");
    if (eyebrow) {
      eyebrow.textContent = isFa() ? "برنامه‌ریز هوشمند سفر برای همه" : "Global AI travel planning";
    }

    document.querySelectorAll('a[href="./plans.html"]').forEach((link) => {
      link.setAttribute("href", "./pricing.html");
    });

    const preset = document.querySelector("#trabzonPresetButton");
    if (preset && params.get("showPersonalPreset") !== "1") preset.remove();
  }

  function boot() {
    document.title = "SafarMa | سفرِ ما — AI Travel Planning";
    updatePublicCopy();
    applyNeutralProfile();

    const observer = new MutationObserver(() => {
      updatePublicCopy();
      applyNeutralProfile();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    let attempts = 0;
    const timer = setInterval(() => {
      updatePublicCopy();
      applyNeutralProfile();
      attempts += 1;
      if (profileApplied || hasSavedProfile() || attempts > 80) clearInterval(timer);
    }, 100);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
