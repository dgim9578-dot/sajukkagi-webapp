"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

const SajuBriefingDeck = dynamic(() => import("@/components/SajuBriefingDeck"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[420px] items-center justify-center bg-black text-pink-200/80">
      궁합 3D 브리핑 불러오는 중…
    </div>
  ),
});
import { fetchBriefingByFingerprint } from "@/lib/briefing-api";
import type { SajuBriefing } from "@/types/saju-briefing";

function LoadingScreen() {
  return (
    <div className="flex min-h-[100dvh] items-center justify-center bg-black">
      <div className="text-center">
        <div className="mx-auto mb-6 h-16 w-16 animate-spin rounded-full border-4 border-pink-400 border-t-transparent" />
        <p className="text-xl text-white">궁합 브리핑을 불러오는 중...</p>
      </div>
    </div>
  );
}

export default function MatchBriefingPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const embed = searchParams.get("embed") === "1";

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
        e instanceof Error ? e.message : "궁합 브리핑을 불러오지 못했습니다."
      );
    } finally {
      setLoading(false);
    }
  }, [fingerprint]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingScreen />;
  if (error || !briefing) {
    return (
      <div className="flex min-h-[100dvh] items-center justify-center bg-black text-white">
        <div className="px-6 text-center">
          <p className="mb-4 text-2xl">⚠️ {error ?? "브리핑을 불러오지 못했습니다."}</p>
          <button
            type="button"
            onClick={load}
            className="rounded-full bg-white px-8 py-4 font-semibold text-black"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (embed) {
    return (
      <main className="h-full min-h-[420px] overflow-hidden bg-black text-white">
        <SajuBriefingDeck briefing={briefing} embedMode />
      </main>
    );
  }

  return (
    <main className="min-h-[100dvh] overflow-hidden bg-black text-white">
      <header className="fixed inset-x-0 top-0 z-50 border-b border-pink-500/20 bg-black/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="min-w-0">
            <p className="truncate text-lg font-bold text-pink-200">
              {briefing.shareable?.title ?? `${briefing.display_name} 궁합`}
            </p>
            <p className="text-xs text-pink-400/80">Match Briefing Deck</p>
          </div>
          <Link
            href="/"
            className="shrink-0 rounded-full border border-white/20 px-4 py-2 text-sm hover:bg-white/10"
          >
            처음으로
          </Link>
        </div>
      </header>
      <div className="h-[100dvh] pt-16">
        <SajuBriefingDeck briefing={briefing} />
      </div>
    </main>
  );
}
