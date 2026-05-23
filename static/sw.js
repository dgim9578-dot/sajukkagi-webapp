/* 사주까기 PWA — Streamlit `…/app/static/` 범위 캐시. 앱 HTML·API는 서버가 처리합니다. */
const CACHE = "saju-pwa-static-v2";

function scopeBase() {
  const u = new URL(self.registration.scope);
  return u.href.replace(/\/?$/, "/");
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
