/**
 * 서버 전용 — FastAPI(`saju_storage`) 브리핑 API 프록시.
 * Python 함수를 직접 import 할 수 없으므로 `SAJU_API_URL`로 HTTP 호출합니다.
 */

import { loadBriefingFromLocalProject } from "@/lib/briefing-load-local";
import type { SajuBriefing } from "@/types/saju-briefing";

const BACKEND_URL =
  process.env.SAJU_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

interface BriefingLoadResponse {
  success?: boolean;
  briefing?: SajuBriefing;
  message?: string;
  error?: string;
}

/** `saju_storage.get_briefing_by_fingerprint` + 캐시 조회 (FastAPI GET) */
export async function get_briefing_by_fingerprint(
  fingerprint: string
): Promise<SajuBriefing | null> {
  const fp = String(fingerprint || "").trim();
  if (!fp) return null;

  const url = `${BACKEND_URL}/api/briefing/get/${encodeURIComponent(fp)}`;
  let res: Response | null = null;
  try {
    res = await fetch(url, { cache: "no-store" });
  } catch {
    res = null;
  }

  if (res?.ok) {
    const data = (await res.json()) as BriefingLoadResponse;
    if (data.briefing) return data.briefing;
  }

  return loadBriefingFromLocalProject(fp);
}

/** `saju_storage.get_sample_briefing` */
export async function get_sample_briefing(): Promise<SajuBriefing | null> {
  const res = await fetch(`${BACKEND_URL}/api/briefing/sample`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  const data = (await res.json()) as BriefingLoadResponse;
  return data.briefing ?? null;
}
