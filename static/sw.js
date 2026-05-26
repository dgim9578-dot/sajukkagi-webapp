/* 사주까기 PWA — 정적 아이콘만 캐시. Streamlit HTML/WS는 항상 네트워크 우선. */
const CACHE = "saju-pwa-static-20260519-accordion-v5";

function scopeBase() {
  const u = new URL(self.registration.scope);
  return u.href.replace(/\/?$/, "/");
}

function isAppDocumentRequest(req, url) {
  if (req.mode === "navigate") return true;
  const dest = req.destination || "";
  if (dest === "document" || dest === "iframe") return true;
  const p = url.pathname || "";
  if (p === "/" || p.endsWith("/")) return true;
  if (p.includes("_stcore") || p.includes("streamlit")) return true;
  return false;
}

function isStaticAsset(url) {
  const p = url.pathname || "";
  return (
    p.includes("/app/static/") &&
    (p.endsWith(".png") ||
      p.endsWith(".svg") ||
      p.endsWith(".webp") ||
      p.endsWith(".json") ||
      p.endsWith("manifest.json") ||
      p.endsWith("sw.js"))
  );
}

self.addEventListener("install", (event) => {
  const base = scopeBase();
  const urls = [
    base + "manifest.json",
    base + "sw.js",
    base + "icons/icon-192.png",
    base + "icons/icon-512.png",
    base + "icons/icon.svg",
  ];
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(urls))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.map((k) => {
            if (k !== CACHE && k.startsWith("saju-pwa-")) {
              return caches.delete(k);
            }
            return Promise.resolve();
          })
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || req.headers.has("range")) {
    return;
  }
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) {
    return;
  }
  var scopePath = new URL(self.registration.scope).pathname;
  if (!scopePath.endsWith("/")) {
    scopePath += "/";
  }
  if (!url.pathname.startsWith(scopePath)) {
    return;
  }

  if (isAppDocumentRequest(req, url) || !isStaticAsset(url)) {
    event.respondWith(
      fetch(req).catch(() => caches.match(req))
    );
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      const net = fetch(req).then((res) => {
        const copy = res.clone();
        if (res.ok) {
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      });
      return cached || net;
    })
  );
});
