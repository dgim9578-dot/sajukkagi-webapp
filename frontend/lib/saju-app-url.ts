/** Streamlit 사주까기 홈(STEP1 랜딩) — 3D 브리핑 「처음으로」 이동 대상 */

export function getStreamlitHomeUrl(homeFromQuery?: string | null): string {
  const q = String(homeFromQuery || "").trim();
  if (q && (q.startsWith("http://") || q.startsWith("https://"))) {
    try {
      const u = new URL(q);
      return `${u.origin}/`;
    } catch {
      /* fall through */
    }
  }
  const base = (
    process.env.NEXT_PUBLIC_SAJU_APP_URL || "http://localhost:8501"
  ).replace(/\/$/, "");
  return `${base}/`;
}
