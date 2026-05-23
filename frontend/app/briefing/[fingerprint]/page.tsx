"use client";

import dynamic from "next/dynamic";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

const SajuBriefingDeck = dynamic(() => import("@/components/SajuBriefingDeck"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[420px] items-center justify-center bg-black text-amber-200/80">
      3D 브리핑 덱 불러오는 중…
    </div>
  ),
});
import { fetchBriefingByFingerprint } from "@/lib/briefing-api";
import { getLocalSampleBriefing } from "@/lib/demo-briefing";
import { getStreamlitHomeUrl } from "@/lib/saju-app-url";
import type { SajuBriefing } from "@/types/saju-briefing";
import { ELEMENT_FALLBACK_COLORS } from "@/types/saju-briefing";

function LoadingScreen({
  fingerprint,
  onUseSample,
}: {
  fingerprint?: string;
  onUseSample?: () => void;
}) {
  const isSample = fingerprint === SAMPLE_FP;
  return (
    <div className="flex min-h-[100dvh] w-full items-center justify-center bg-black px-4">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-6 h-16 w-16 animate-spin rounded-full border-4 border-amber-400 border-t-transparent" />
        <p className="text-xl text-white">당신의 사주를 아름답게 브리핑 중...</p>
        <p className="mt-4 text-sm text-slate-400">
          {isSample
            ? "샘플 브리핑을 준비하고 있습니다."
            : "잠시만 기다려 주세요. (최대 8초)"}
        </p>
        {onUseSample && !isSample ? (
          <button
            type="button"
            onClick={onUseSample}
            className="mt-6 rounded-full border border-amber-500/40 px-6 py-3 text-sm text-amber-200 hover:bg-amber-500/10"
          >
            샘플 브리핑으로 미리 보기
          </button>
        ) : null}
      </div>
    </div>
  );
}

function ErrorScreen({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white">
      <div className="px-6 text-center">
        <p className="mb-4 text-2xl">⚠️ {message}</p>
        <div className="flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <button
            type="button"
            onClick={onRetry}
            className="rounded-full bg-white px-8 py-4 font-semibold text-black transition hover:bg-amber-400"
          >
            다시 시도하기
          </button>
          <a
            href={getStreamlitHomeUrl(null)}
            className="rounded-full border border-white/30 px-8 py-4 font-semibold transition hover:bg-white/10"
          >
            사주까기 홈으로
          </a>
        </div>
        <p className="mt-6 max-w-md text-sm text-slate-400">
          본인 브리핑은 STEP2에서 「저장하고 사주 분석 시작하기」를 눌렀는지 확인해
          주세요. Streamlit만 켜져 있어도 로드되도록 설정되어 있습니다. 그래도 안 되면
          Next.js(<code className="text-amber-500/90">npm run dev:lan</code>)를
          재시작한 뒤 STEP3을 새로고침하세요.
        </p>
      </div>
    </div>
  );
}

const SAMPLE_FP = "test_sample_123";

function BriefingFingerprintPageInner() {
  const params = useParams();
  const searchParams = useSearchParams();
  const embed = searchParams.get("embed") === "1";
  const homeUrl = getStreamlitHomeUrl(searchParams.get("home"));

  const fingerprint = Array.isArray(params.fingerprint)
    ? params.fingerprint[0]
    : params.fingerprint;

  const [briefing, setBriefing] = useState<SajuBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!fingerprint) {
      setError("브리핑 주소가 올바르지 않습니다.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchBriefingByFingerprint(fingerprint);
      setBriefing(data);
    } catch (e) {
      setBriefing(null);
      setError(
        e instanceof Error ? e.message : "브리핑을 불러오지 못했습니다."
      );
    } finally {
      setLoading(false);
    }
  }, [fingerprint]);

  useEffect(() => {
    if (fingerprint === SAMPLE_FP) {
      setBriefing(getLocalSampleBriefing());
      setLoading(false);
      setError(null);
      return;
    }
    load();
  }, [fingerprint, load]);

  const handleShare = async () => {
    if (!briefing) return;
    const title =
      briefing.shareable?.title ?? `${briefing.display_name}님의 사주 브리핑`;
    const text = "나의 사주를 3D로 만나보세요!";
    const url = typeof window !== "undefined" ? window.location.href : "";
    try {
      if (navigator.share) {
        await navigator.share({ title, text, url });
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
        alert("링크가 복사되었습니다.");
      }
    } catch {
      /* 사용자가 공유 취소 */
    }
  };

  const loadSample = useCallback(() => {
    setBriefing(getLocalSampleBriefing());
    setError(null);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <LoadingScreen fingerprint={fingerprint} onUseSample={loadSample} />
    );
  }
  if (error || !briefing) {
    return <ErrorScreen message={error ?? "브리핑을 불러오지 못했습니다."} onRetry={load} />;
  }

  const theme = briefing.visual_themes;
  const accent = theme?.primary ?? "#d4af37";
  if (embed) {
    return (
      <main className="flex h-[min(88dvh,820px)] min-h-[480px] flex-col overflow-hidden bg-black text-white">
        <SajuBriefingDeck briefing={briefing} embedMode homeUrl={homeUrl} />
      </main>
    );
  }

  return (
    <main className="flex h-[100dvh] flex-col overflow-hidden bg-black text-white">
      <header
        className="fixed inset-x-0 top-0 z-50 border-b border-white/10 backdrop-blur-lg"
        style={{ backgroundColor: `${theme?.bg ?? "#000000"}cc` }}
      >
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-4 sm:px-6 sm:py-5">
          <div className="flex min-w-0 items-center gap-3">
            <a
              href={homeUrl}
              className="shrink-0 rounded-lg border border-white/15 px-2 py-1 text-sm text-amber-200 hover:bg-white/5"
              aria-label="사주까기 홈으로"
            >
              ← 홈
            </a>
            <div className="min-w-0">
              <p className="truncate text-base font-bold sm:text-lg">
                {briefing.shareable?.title ?? `${briefing.display_name}님의 사주`}
              </p>
              <p className="text-xs text-amber-400">
                Saju Briefing Deck
                {briefing.sample ? " · 체험 샘플" : " · 결과 보기"}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 gap-2 sm:gap-4">
            <button
              type="button"
              onClick={() => window.print()}
              className="hidden items-center gap-2 rounded-full border border-white/30 px-4 py-2.5 text-sm transition hover:bg-white/10 sm:flex"
            >
              🖼️ 저장
            </button>
            <button
              type="button"
              onClick={handleShare}
              className="rounded-full bg-gradient-to-r from-amber-400 to-orange-500 px-4 py-2.5 text-sm font-semibold text-black transition hover:brightness-110 sm:px-6"
            >
              공유
            </button>
          </div>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-hidden pt-[4.5rem] sm:pt-20">
        <SajuBriefingDeck briefing={briefing} embedMode={false} homeUrl={homeUrl} />
      </div>

      <aside className="pointer-events-none fixed bottom-28 right-4 z-[35] hidden max-w-[200px] rounded-xl border border-white/10 bg-black/70 p-3 text-xs backdrop-blur lg:block">
        <p className="font-semibold" style={{ color: accent }}>
          에너지 흐름
        </p>
        <p className="mt-1 text-slate-400">
          강: {(briefing.energy_flow?.strong ?? []).join(" · ") || "—"}
        </p>
        <p className="mt-1 text-slate-400">
          약: {(briefing.energy_flow?.weak ?? []).join(" · ") || "—"}
        </p>
        <div className="mt-2 flex gap-1">
          {Object.entries(ELEMENT_FALLBACK_COLORS).map(([el, col]) => (
            <span
              key={el}
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: col }}
              title={el}
            />
          ))}
        </div>
      </aside>

      <div className="fixed bottom-6 right-4 z-50 sm:right-6">
        <a
          href={homeUrl}
          className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-lg font-bold text-black shadow-2xl shadow-black/50 transition hover:scale-105 active:scale-95"
          aria-label="사주까기 홈으로"
          title="사주까기 홈 (STEP1)"
        >
          ⌂
        </a>
      </div>
    </main>
  );
}

export default function BriefingFingerprintPage() {
  return (
    <Suspense
      fallback={
        <LoadingScreen fingerprint={SAMPLE_FP} />
      }
    >
      <BriefingFingerprintPageInner />
    </Suspense>
  );
}
