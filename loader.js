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
    "result-guard.js",
    "belink-ai.js"
  ];

  try {
    const source = [];
    for (const part of parts) {
      const response = await fetch(`./${part}?v=7`, { cache: "no-store" });
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
      throw new Error("Belink AI application script could not start.");
    };
    document.body.appendChild(script);
  } catch (error) {
    console.error(error);
    const message = document.createElement("div");
    message.style.cssText = "position:fixed;inset:20px;z-index:9999;margin:auto;max-width:520px;height:max-content;padding:20px;border-radius:18px;background:#071426;color:#eef8ff;border:1px solid #75e7ff33;box-shadow:0 16px 50px #0008;font-family:system-ui;text-align:center";
    message.innerHTML = `<strong>Belink AI could not start.</strong><br><small>Please refresh the page. If the problem continues, clear Safari website data and reopen the link.</small>`;
    document.body.appendChild(message);
  }
})();