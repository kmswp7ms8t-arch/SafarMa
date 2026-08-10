(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const fa = () => document.documentElement.lang === "fa" || document.documentElement.dir === "rtl";
  const esc = (value = "") => String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  function apiBase() {
    return window.BELINK_CLIENT_RUNTIME?.apiBase?.() || "";
  }

  function destination() {
    const hero = $(".resultHero,.result-hero");
    return $("h1", hero)?.textContent?.trim() || (fa() ? "مقصد رویایی ما" : "our dream destination");
  }

  function defaultPrompt() {
    const place = destination();
    return fa()
      ? `یک تصویر سینمایی و واقعی از سفر عاشقانه امیر و ساناز به ${place}، نور طلایی، منظره شاخص مقصد، کیفیت مجله سفر، بدون نوشته و لوگو`
      : `A cinematic, photorealistic travel moment for Amir and Sanaz in ${place}, golden light, iconic scenery, premium travel editorial, no text or logos`;
  }

  function setStatus(message, state = "") {
    const status = $("#belinkImagineStatus");
    status.className = `bi-status ${state}`;
    status.textContent = message;
  }

  async function createImage() {
    const prompt = $("#belinkImaginePrompt").value.trim();
    if (prompt.length < 3) {
      setStatus(fa() ? "لطفاً تصویر دلخواهت را توضیح بده." : "Please describe the image you want.", "error");
      return;
    }
    const base = apiBase();
    if (!base) {
      setStatus(fa() ? "اول سرور Belink AI را از نشان اتصال تنظیم کن." : "Configure the Belink AI backend from the connection badge first.", "error");
      return;
    }

    const button = $("#belinkImagineCreate");
    button.disabled = true;
    setStatus(fa() ? "Grok Imagine در حال ساخت تصویر است…" : "Grok Imagine is creating your image…", "loading");
    try {
      const response = await fetch(`${base}/api/belink-ai/imagine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      const url = new URL(data.image_url);
      if (url.protocol !== "https:") throw new Error("Invalid image URL");
      const result = $("#belinkImagineResult");
      result.innerHTML = `<img src="${esc(url.href)}" alt="${esc(prompt)}"><div><span>${fa() ? "ساخته‌شده با Grok Imagine" : "Created with Grok Imagine"}</span><a href="${esc(url.href)}" target="_blank" rel="noopener noreferrer">${fa() ? "بازکردن تصویر اصلی ↗" : "Open original image ↗"}</a></div>`;
      result.hidden = false;
      setStatus(fa() ? "تصویر سفر آماده است." : "Your travel image is ready.", "success");
    } catch (error) {
      setStatus(error.message || (fa() ? "ساخت تصویر انجام نشد." : "Image generation failed."), "error");
    } finally {
      button.disabled = false;
    }
  }

  function mount() {
    if ($("#belinkImagineRoot")) return;
    const root = document.createElement("div");
    root.id = "belinkImagineRoot";
    root.innerHTML = `
      <button class="bi-launch" id="belinkImagineLaunch" type="button"><span>◈</span><b>${fa() ? "تصویر سفر" : "Travel image"}</b></button>
      <div class="bi-backdrop" id="belinkImagineBackdrop" hidden></div>
      <section class="bi-studio" id="belinkImagineStudio" role="dialog" aria-modal="true" aria-labelledby="belinkImagineTitle" hidden>
        <header><div><small>GROK IMAGINE · BELINK AI</small><h2 id="belinkImagineTitle">${fa() ? "تصویر سفرت را بساز" : "Imagine your journey"}</h2></div><button id="belinkImagineClose" type="button" aria-label="Close">×</button></header>
        <p>${fa() ? "صحنه‌ای را که دوست داری بنویس؛ کلید خصوصی xAI فقط روی سرور امن می‌ماند." : "Describe the scene you want. Your private xAI key stays on the secure server."}</p>
        <label for="belinkImaginePrompt">${fa() ? "توضیح تصویر" : "Image prompt"}</label>
        <textarea id="belinkImaginePrompt" maxlength="1000" rows="5"></textarea>
        <button class="bi-create" id="belinkImagineCreate" type="button"><span>✦</span>${fa() ? "ساخت با Grok Imagine" : "Create with Grok Imagine"}</button>
        <div class="bi-status" id="belinkImagineStatus" aria-live="polite">${fa() ? "برای شروع، توضیح پیشنهادی را ویرایش کن." : "Edit the suggested prompt, then create."}</div>
        <figure class="bi-result" id="belinkImagineResult" hidden></figure>
      </section>`;
    document.body.appendChild(root);

    const studio = $("#belinkImagineStudio");
    const backdrop = $("#belinkImagineBackdrop");
    const open = () => {
      $("#belinkImaginePrompt").value = defaultPrompt();
      studio.hidden = false;
      backdrop.hidden = false;
      requestAnimationFrame(() => studio.classList.add("open"));
      document.body.classList.add("bi-open");
      $("#belinkImaginePrompt").focus();
    };
    const close = () => {
      studio.classList.remove("open");
      document.body.classList.remove("bi-open");
      setTimeout(() => { studio.hidden = true; backdrop.hidden = true; }, 220);
    };
    $("#belinkImagineLaunch").addEventListener("click", open);
    $("#belinkImagineClose").addEventListener("click", close);
    backdrop.addEventListener("click", close);
    $("#belinkImagineCreate").addEventListener("click", createImage);
    document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !studio.hidden) close(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
