(() => {
  "use strict";

  const PLAN_KEY = "sm-imported-plan";
  const PLAN_ID = "trabzon-2026-amir-sanaz";

  const PRESET = Object.freeze({
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
    mode: "ideas",
    wanted: "Trabzon",
    regions: ["near"],
    styles: ["nature", "relax", "romantic"],
    flight: "direct",
    maxHours: 6,
    stay: "four",
    transport: "car",
    food: "balanced",
    halal: true,
    priority: "overall"
  });

  const COPY = {
    fa: {
      eyebrow: "برنامه واقعی امیر و ساناز",
      title: "سفر ۶ روزه ترابزون",
      summary: "دوحه → ترابزون · ۶ تا ۱۱ آگوست ۲۰۲۶ · دو نفر · بودجه ۱۳٬۵۰۰ QAR",
      load: "بازکردن برنامه ترابزون",
      loaded: "برنامه ترابزون وارد SafarMa شد.",
      draft: "پیش‌نویس واردشده · نیازمند بررسی زنده",
      budgetTitle: "بودجه واردشده از برنامه",
      expected: "محدوده پیشنهادی",
      expectedValue: "۱۱٬۰۰۰ تا ۱۳٬۵۰۰ QAR",
      economy: "اقتصادی: ۷٬۵۰۰ تا ۱۰٬۲۰۰ QAR",
      comfortable: "راحت‌تر: ۱۴٬۷۰۰ تا ۱۹٬۵۰۰ QAR",
      notesTitle: "تصمیم‌های اولیه سفر",
      notes: [
        "اولویت با پرواز مستقیم است؛ قیمت و روز پرواز باید زنده بررسی شود.",
        "هتل ۴ ستاره و اجاره ماشین برای این برنامه انتخاب شده‌اند.",
        "یادداشت ویزا و اعتبار پاسپورت از پیش‌نویس آمده و باید از منبع رسمی دوباره تأیید شود.",
        "هیچ قیمت، ظرفیت پرواز یا قانون ورود در این کارت تأیید زنده محسوب نمی‌شود."
      ],
      live: "بررسی زنده با Belink Commander",
      itineraryTitle: "برنامه ۵ شب / ۶ روز",
      days: [
        "ورود به ترابزون، تحویل ماشین، هتل، شام و میدان مرکزی",
        "اوزون‌گل؛ طبیعت‌گردی و توقف‌های دیدنی مسیر",
        "صومعه سوملا و هامسی‌کوی",
        "ریزه و آیدر؛ گشت کامل روزانه",
        "داخل ترابزون، بوزتپه، عمارت آتاتورک، خرید سبک و کافه",
        "صبح آزاد، تحویل ماشین و بازگشت به دوحه"
      ]
    },
    en: {
      eyebrow: "Amir & Sanaz real trip plan",
      title: "Six-day Trabzon trip",
      summary: "Doha → Trabzon · 6–11 August 2026 · two travellers · QAR 13,500 budget",
      load: "Open the Trabzon plan",
      loaded: "The Trabzon plan was loaded into SafarMa.",
      draft: "Imported draft · live verification required",
      budgetTitle: "Budget imported from the plan",
      expected: "Recommended working range",
      expectedValue: "QAR 11,000–13,500",
      economy: "Economy: QAR 7,500–10,200",
      comfortable: "More comfortable: QAR 14,700–19,500",
      notesTitle: "Initial travel decisions",
      notes: [
        "A nonstop flight is preferred; dates, availability and price must be checked live.",
        "A four-star hotel and rental car are selected for this itinerary.",
        "Visa and passport notes came from the imported draft and require a new official-source check.",
        "No fare, seat availability or entry rule in this card is a live confirmation."
      ],
      live: "Run live check with Belink Commander",
      itineraryTitle: "Five nights / six days",
      days: [
        "Arrive in Trabzon, collect the car, hotel check-in, dinner and central square",
        "Full-day Uzungöl nature route",
        "Sümela Monastery and Hamsiköy",
        "Rize and Ayder full-day excursion",
        "Trabzon city, Boztepe, Atatürk Mansion, light shopping and cafés",
        "Free morning, return the car and fly back to Doha"
      ]
    }
  };

  const isFa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  const text = () => (isFa() ? COPY.fa : COPY.en);
  const qs = (selector, root = document) => root.querySelector(selector);

  function appReady() {
    try {
      return typeof p === "object" && p && typeof save === "function" && typeof showResult === "function";
    } catch (_) {
      return false;
    }
  }

  function setPreset() {
    if (!appReady()) return;
    Object.assign(p, JSON.parse(JSON.stringify(PRESET)));
    save();
    localStorage.setItem(PLAN_KEY, PLAN_ID);
    showResult();
    setTimeout(() => {
      decorateResult();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, 50);
  }

  function mountWelcomeCard() {
    if (!appReady() || qs("#trabzonPlanCard")) return;
    const hero = qs("#app .hero");
    if (!hero || !qs("#start", hero)) return;
    const copy = text();
    const card = document.createElement("section");
    card.id = "trabzonPlanCard";
    card.className = "card trabzon-plan-card";
    card.innerHTML = `
      <small>${copy.eyebrow}</small>
      <h2>${copy.title}</h2>
      <p>${copy.summary}</p>
      <button class="secondary full" id="loadTrabzonPlan">${copy.load}</button>
      <span class="trabzon-plan-warning">${copy.draft}</span>`;
    hero.insertAdjacentElement("afterend", card);
    qs("#loadTrabzonPlan", card)?.addEventListener("click", setPreset);
  }

  function itineraryMarkup(copy) {
    return copy.days.map((item, index) => `
      <div class="day trabzon-imported-day">
        <b>${isFa() ? "روز" : "Day"} ${index + 1}</b>${item}
      </div>`).join("");
  }

  function decorateResult() {
    if (!appReady() || localStorage.getItem(PLAN_KEY) !== PLAN_ID) return;
    let practicalId = "";
    try { practicalId = result?.practical?.id || ""; } catch (_) {}
    if (practicalId && practicalId !== "trabzon") return;

    const copy = text();
    const hero = qs(".resultHero,.result-hero");
    if (!hero) return;

    let badge = qs("#trabzonImportedBadge");
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "trabzonImportedBadge";
      badge.className = "trabzon-imported-badge";
      hero.appendChild(badge);
    }
    badge.textContent = copy.draft;

    const timeline = qs(".timeline");
    if (timeline) {
      const title = timeline.closest(".card")?.querySelector("h2");
      if (title) title.textContent = copy.itineraryTitle;
      timeline.innerHTML = itineraryMarkup(copy);
    }

    if (!qs("#trabzonImportedDetails")) {
      const cards = [...document.querySelectorAll("#app > .card")];
      const costCard = cards.find((card) => qs(".money", card));
      const details = document.createElement("section");
      details.id = "trabzonImportedDetails";
      details.className = "card trabzon-imported-details";
      details.innerHTML = `
        <small>${copy.draft}</small>
        <h2>${copy.budgetTitle}</h2>
        <div class="trabzon-budget-main"><span>${copy.expected}</span><b>${copy.expectedValue}</b></div>
        <div class="trabzon-budget-grid"><span>${copy.economy}</span><span>${copy.comfortable}</span></div>
        <h3>${copy.notesTitle}</h3>
        <ul>${copy.notes.map((item) => `<li>${item}</li>`).join("")}</ul>
        <button class="primary full" id="trabzonLiveCheck">${copy.live}</button>`;
      (costCard || hero).insertAdjacentElement("afterend", details);
      qs("#trabzonLiveCheck", details)?.addEventListener("click", () => {
        if (window.BELINK_AI?.analyze) window.BELINK_AI.analyze();
        else qs("#onlineCard")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }

  function mountStyles() {
    if (qs("#trabzonPlanStyles")) return;
    const style = document.createElement("style");
    style.id = "trabzonPlanStyles";
    style.textContent = `
      .trabzon-plan-card{position:relative;overflow:hidden;border-color:rgba(117,231,255,.25)!important;background:linear-gradient(145deg,rgba(5,25,47,.94),rgba(12,42,56,.9))!important}
      .trabzon-plan-card:before{content:"TZX";position:absolute;inset-inline-end:16px;top:8px;font-size:54px;font-weight:1000;color:rgba(117,231,255,.07);letter-spacing:-.06em}
      .trabzon-plan-card small,.trabzon-imported-details>small{color:#75e7ff;letter-spacing:.08em}.trabzon-plan-card h2{margin:6px 0}.trabzon-plan-card p{color:#aec3d6;line-height:1.7}
      .trabzon-plan-warning,.trabzon-imported-badge{display:inline-flex;margin-top:9px;padding:6px 9px;border-radius:999px;background:rgba(248,207,99,.1);border:1px solid rgba(248,207,99,.25);color:#ffe69b;font-size:10px;font-weight:800}
      .trabzon-imported-badge{margin-bottom:4px}.trabzon-imported-details{border-color:rgba(248,207,99,.2)!important}.trabzon-imported-details h2,.trabzon-imported-details h3{margin-bottom:8px}
      .trabzon-budget-main{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:13px;border-radius:16px;background:rgba(117,231,255,.07);border:1px solid rgba(117,231,255,.14)}
      .trabzon-budget-main span{color:#9eb8cd;font-size:11px}.trabzon-budget-main b{color:#f8cf63;font-size:18px}.trabzon-budget-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:9px 0 15px}.trabzon-budget-grid span{padding:10px;border-radius:13px;background:rgba(255,255,255,.04);color:#abc0d2;font-size:11px}
      .trabzon-imported-details ul{padding-inline-start:20px;color:#aec3d6;line-height:1.75}.trabzon-imported-details li{margin:6px 0}.trabzon-imported-day{border-color:rgba(117,231,255,.13)!important}
      @media(max-width:520px){.trabzon-budget-grid{grid-template-columns:1fr}.trabzon-budget-main{align-items:flex-start;flex-direction:column}}
    `;
    document.head.appendChild(style);
  }

  function boot() {
    mountStyles();
    const observer = new MutationObserver(() => {
      mountWelcomeCard();
      decorateResult();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    const timer = setInterval(() => {
      if (!appReady()) return;
      clearInterval(timer);
      mountWelcomeCard();
      decorateResult();
    }, 100);
    setTimeout(() => clearInterval(timer), 15000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
