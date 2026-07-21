(async () => {
  const parts = [
    "app1a.js",
    "app1b.js",
    "compat.js",
    "fix-data.js",
    "app2a.js",
    "app2b.js",
    "app3.js",
    "app4.js",
    "app5.js",
    "online-v2.js",
    "result-guard.js"
  ];

  try {
    const source = [];
    for (const part of parts) {
      const response = await fetch(`./${part}?v=6`, { cache: "no-store" });
      if (!response.ok) throw new Error(`${part}: HTTP ${response.status}`);
      source.push(await response.text());
    }

    const blobUrl = URL.createObjectURL(
      new Blob([source.join("\n")], { type: "text/javascript" })
    );
    const script = document.createElement("script");
    script.src = blobUrl;
    script.onload = () => URL.revokeObjectURL(blobUrl);
    script.onerror = () => {
      URL.revokeObjectURL(blobUrl);
      throw new Error("SafarMa application script could not start.");
    };
    document.body.appendChild(script);
  } catch (error) {
    console.error(error);
    const message = document.createElement("div");
    message.style.cssText = "position:fixed;inset:20px;z-index:9999;margin:auto;max-width:520px;height:max-content;padding:20px;border-radius:18px;background:#fff;color:#0B2A4A;box-shadow:0 16px 50px #0003;font-family:system-ui;text-align:center";
    message.innerHTML = `<strong>SafarMa could not start.</strong><br><small>Please refresh the page. If the problem continues, clear Safari website data and reopen the link.</small>`;
    document.body.appendChild(message);
  }
})();