"""PC/모바일 클라이언트가 서버 최신 UI 빌드와 맞도록 강제 동기화."""

from __future__ import annotations

import html
import json

import streamlit as st

from saju_app.release import full_release_id, sw_cache_name

_INJECT_FLAG = "_saju_client_release_guard_injected"
_LS_KEY = "saju_app_release_v1"
_ATTEMPTS_KEY = "saju_reload_attempts_v1"

_CLIENT_SYNC_JS = """
(() => {
  const cfg = window.__sajuClientSyncCfg || {};
  const getWin = () => {
    try {
      if (window.parent && window.parent.document) return window.parent;
    } catch (e) {}
    try {
      if (window.top && window.top.document) return window.top;
    } catch (e) {}
    return window;
  };
  const pw = getWin();
  const doc = pw.document;
  if (!doc) return;

  const rid = String(cfg.release || "");
  const lsKey = String(cfg.lsKey || "saju_app_release_v1");
  const attemptsKey = String(cfg.attemptsKey || "saju_reload_attempts_v1");
  const swCache = String(cfg.swCache || "");
  const lanHint = String(cfg.lanHint || "");

  const clearPwaCaches = () => {
    try {
      if (pw.caches && pw.caches.keys) {
        pw.caches.keys().then((keys) => {
          keys.forEach((k) => {
            if (!k) return;
            if (k.startsWith("saju-pwa") || (swCache && k === swCache)) {
              pw.caches.delete(k);
            }
          });
        });
      }
    } catch (e) {}
    try {
      if (pw.navigator && pw.navigator.serviceWorker) {
        pw.navigator.serviceWorker.getRegistrations().then((regs) => {
          regs.forEach((r) => {
            try { r.unregister(); } catch (e2) {}
          });
        });
      }
    } catch (e) {}
  };

  const hardReload = () => {
    let attempts = 0;
    try {
      attempts = parseInt(pw.sessionStorage.getItem(attemptsKey) || "0", 10) || 0;
    } catch (e) {}
    if (attempts >= 3) return;
    try { pw.sessionStorage.setItem(attemptsKey, String(attempts + 1)); } catch (e) {}
    clearPwaCaches();
    try {
      const u = new URL(pw.location.href);
      if (u.searchParams.get("_saju_r") !== rid) {
        u.searchParams.set("_saju_r", rid);
        pw.location.replace(u.toString());
        return;
      }
    } catch (e) {}
    try { pw.location.reload(); } catch (e2) {}
  };

  const prev = (() => {
    try { return pw.localStorage.getItem(lsKey) || ""; } catch (e) { return ""; }
  })();

  if (prev && prev !== rid) {
    try { pw.localStorage.setItem(lsKey, rid); } catch (e) {}
    hardReload();
    return;
  }
  if (!prev) {
    try { pw.localStorage.setItem(lsKey, rid); } catch (e) {}
  }
  try {
    if (pw.sessionStorage.getItem(attemptsKey)) {
      pw.sessionStorage.removeItem(attemptsKey);
    }
  } catch (e) {}

  try {
    pw.addEventListener("pageshow", (ev) => {
      if (!ev || !ev.persisted) return;
      let stored = "";
      try { stored = pw.localStorage.getItem(lsKey) || ""; } catch (e) {}
      if (stored && stored !== rid) hardReload();
    });
  } catch (e) {}

  if (lanHint) {
    try {
      const host = String(pw.location.hostname || "");
      const onLocalDev =
        host === "localhost" ||
        host === "127.0.0.1" ||
        /^192\\.168\\./.test(host) ||
        /^10\\./.test(host);
      const hintHost = (() => {
        try { return new URL(lanHint).hostname; } catch (e) { return ""; }
      })();
      const staleTunnel =
        /trycloudflare\\.com$/i.test(host) ||
        /ngrok/i.test(host) ||
        (/\\.streamlit\\.app$/i.test(host) && onLocalDev);
      if (staleTunnel && hintHost && host !== hintHost) {
        const id = "saju-lan-url-banner";
        if (!doc.getElementById(id)) {
          const el = doc.createElement("div");
          el.id = id;
          el.setAttribute("translate", "no");
          el.setAttribute(
            "style",
            "position:fixed;bottom:0;left:0;right:0;z-index:99999;padding:10px 12px;"
            + "background:#2a2620;color:#f5efe2;font-size:13px;line-height:1.4;"
            + "border-top:1px solid rgba(212,175,55,0.45);text-align:center;"
          );
          el.innerHTML =
            "이 주소는 예전 터널/북마크일 수 있습니다. 같은 Wi-Fi에서 "
            + '<a href="' + lanHint + "?_saju_r=" + encodeURIComponent(rid)
            + '" style="color:#f4d179;font-weight:700;">' + lanHint + "</a>"
            + " 로 다시 열어 주세요.";
          (doc.body || doc.documentElement).appendChild(el);
        }
      }
    } catch (e) {}
  }
})();
"""


def _lan_mobile_url_hint() -> str:
    """같은 PC Streamlit 서버에 붙을 모바일 LAN URL (있을 때만)."""
    try:
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
        finally:
            sock.close()
        if ip and not ip.startswith("127."):
            return f"http://{ip}:8501"
    except Exception:
        pass
    return ""


def sync_server_release() -> str:
    """서버 세션·STEP 렌더 캐시를 현재 릴리스 ID에 맞춥니다."""
    rid = full_release_id()
    prev = str(st.session_state.get("_saju_server_release") or "")
    if prev != rid:
        st.session_state["_saju_server_release"] = rid
        try:
            from saju_app.ui.steps import router as step_router

            step_router._STEP_RENDER_CACHE.clear()
        except Exception:
            pass
        for key in list(st.session_state.keys()):
            sk = str(key)
            if sk.startswith("_in4_widgets_ready_") or sk.startswith("_s2v3_widgets_ready_"):
                st.session_state.pop(key, None)
            if sk.startswith("_saju_step2_privacy_guard_injected_"):
                st.session_state.pop(key, None)
    return rid


def inject_client_release_guard() -> None:
    """브라우저 bfcache·PWA·옛 탭이 구 UI를 붙잡는 경우 자동 새로고침."""
    import streamlit.components.v1 as components

    rid = sync_server_release()
    flag_key = f"{_INJECT_FLAG}_{rid}"
    if st.session_state.get(flag_key):
        return
    st.session_state[flag_key] = True
    lan = _lan_mobile_url_hint()
    sw_cache = sw_cache_name()

    payload = json.dumps(
        {
            "release": rid,
            "lsKey": _LS_KEY,
            "attemptsKey": _ATTEMPTS_KEY,
            "swCache": sw_cache,
            "lanHint": lan,
        },
        ensure_ascii=False,
    )

    rid_esc = html.escape(rid, quote=True)
    lan_esc = html.escape(lan, quote=True) if lan else ""
    lan_meta = f'<meta name="saju-lan-hint" content="{lan_esc}" />' if lan else ""

    st.markdown(
        f"""
<meta name="saju-release" content="{rid_esc}" />
<meta name="google" content="notranslate" />
<meta name="googlebot" content="notranslate" />
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
<meta http-equiv="Pragma" content="no-cache" />
<meta http-equiv="Expires" content="0" />
{lan_meta}
""",
        unsafe_allow_html=True,
    )

    iframe_html = (
        "<!DOCTYPE html><html translate='no'><head><meta charset='utf-8'>"
        f"<script>window.__sajuClientSyncCfg={payload};</script>"
        f"</head><body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{_CLIENT_SYNC_JS}</script>"
        "</body></html>"
    )
    with st.container(key=f"saju_client_sync_{rid}"):
        components.html(iframe_html, height=0, scrolling=False)
