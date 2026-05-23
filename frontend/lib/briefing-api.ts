import type { SajuBriefing } from "@/types/saju-briefing";
import { getLocalSampleBriefing } from "@/lib/demo-briefing";

export interface BriefingGenerateRequest {
  display_name: string;
  birth: Record<string, unknown>;
  gapja: string[];
  consultation_type?: string;
  session_id?: string | null;
}

interface ApiBriefingResponse {
  success: boolean;
  fingerprint?: string;
  briefing?: SajuBriefing;
  message?: string;
}

const API_BASE = "";
const SAMPLE_FP = "test_sample_123";
const FETCH_TIMEOUT_MS = 8000;

async function fetchJsonWithTimeout(
  url: string,
  init?: RequestInit
): Promise<Response> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), FETCH_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: ctrl.signal, cache: "no-store" });
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchSampleBriefing(): Promise<SajuBriefing> {
  try {
    return await fetchSampleBriefingFromApi();
  } catch {
    return getLocalSampleBriefing();
  }
}

export async function fetchSampleBriefingFromApi(): Promise<SajuBriefing> {
  const res = await fetch(`${API_BASE}/api/briefing/sample`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`샘플 로드 실패 (${res.status})`);
  const data: ApiBriefingResponse = await res.json();
  if (!data.briefing) throw new Error("샘플 브리핑이 비어 있습니다.");
  return data.briefing;
}

export async function generateBriefing(
  body: BriefingGenerateRequest
): Promise<SajuBriefing> {
  const res = await fetch(`${API_BASE}/api/briefing/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`브리핑 생성 실패 (${res.status})`);
  const data: ApiBriefingResponse = await res.json();
  if (!data.briefing) throw new Error(data.message || "브리핑이 비어 있습니다.");
  return data.briefing;
}

export async function fetchBriefingByFingerprint(
  fingerprint: string
): Promise<SajuBriefing> {
  const fp = String(fingerprint || "").trim();
  if (fp === SAMPLE_FP) {
    try {
      return await fetchSampleBriefingFromApi();
    } catch {
      return getLocalSampleBriefing();
    }
  }

  try {
    const res = await fetchJsonWithTimeout(
      `${API_BASE}/api/briefing/get/${encodeURIComponent(fp)}`
    );
    if (!res.ok) throw new Error(`프로필 브리핑 로드 실패 (${res.status})`);
    const data: ApiBriefingResponse = await res.json();
    if (!data.briefing) throw new Error("브리핑을 찾을 수 없습니다.");
    return data.briefing;
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("브리핑 서버 응답이 없습니다. (시간 초과)");
    }
    throw e;
  }
}

export async function fetchMatchBriefingByFingerprint(
  fingerprint: string
): Promise<SajuBriefing> {
  const res = await fetch(
    `${API_BASE}/api/briefing/get/match/${encodeURIComponent(fingerprint)}`,
    { cache: "no-store" }
  );
  if (!res.ok) throw new Error(`궁합 브리핑 로드 실패 (${res.status})`);
  const data: ApiBriefingResponse = await res.json();
  if (!data.briefing) throw new Error("궁합 브리핑을 찾을 수 없습니다.");
  return data.briefing;
}

/** 데모용 — API 없이 UI만 볼 때 */
export const DEMO_BRIEFING_REQUEST: BriefingGenerateRequest = {
  display_name: "김사주",
  birth: {
    year: 1990,
    month: 3,
    day: 15,
    lunar: false,
    leap_month: false,
    time_str: "10:30",
  },
  gapja: ["甲子", "乙丑", "丙寅", "丁卯"],
  consultation_type: "general",
};
