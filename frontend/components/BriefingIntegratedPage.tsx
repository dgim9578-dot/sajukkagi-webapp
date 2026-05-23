"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import BriefingLanding from "@/components/BriefingLanding";

const SajuBriefingDeck = dynamic(() => import("@/components/SajuBriefingDeck"), {
  ssr: false,
});
import BriefingShell from "@/components/layout/BriefingShell";
import {
  fetchSampleBriefing,
  generateBriefing,
  type BriefingGenerateRequest,
} from "@/lib/briefing-api";
import { getStreamlitHomeUrl } from "@/lib/saju-app-url";
import type { SajuBriefing } from "@/types/saju-briefing";
import { ELEMENT_FALLBACK_COLORS } from "@/types/saju-briefing";

type ViewMode = "landing" | "deck";

export default function BriefingIntegratedPage() {
  const router = useRouter();
  const [mode, setMode] = useState<ViewMode>("landing");
  const [briefing, setBriefing] = useState<SajuBriefing | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (fn: () => Promise<SajuBriefing>) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fn();
      setBriefing(data);
      setMode("deck");
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "브리핑을 불러오지 못했습니다. API 서버를 확인하세요."
      );
      setMode("landing");
    } finally {
      setLoading(false);
    }
  }, [router]);

  const handleSample = () => run(fetchSampleBriefing);

  const handleBack = () => {
    setMode("landing");
    setBriefing(null);
    setError(null);
  };

  if (mode === "deck" && briefing) {
    const theme = briefing.visual_themes;
    const accent = theme?.primary ?? "#d4af37";

    return (
      <BriefingShell immersive>
        <div
          className="fixed inset-x-0 top-0 z-[60] flex items-center justify-between border-b border-white/10 px-4 py-3 backdrop-blur-md"
          style={{ backgroundColor: `${theme?.bg ?? "#050508"}cc` }}
        >
          <a
            href={getStreamlitHomeUrl(null)}
            className="rounded-lg border border-white/15 px-3 py-1.5 text-sm text-slate-300 hover:bg-white/5"
          >
            ← 사주까기 홈
          </a>
          <div className="text-center">
            <p className="text-xs text-slate-500">
              {briefing.sample ? "샘플" : "브리핑"}
            </p>
            <p className="text-sm font-semibold" style={{ color: accent }}>
              {briefing.shareable?.title ?? `${briefing.display_name}님`}
            </p>
          </div>
          <button
            type="button"
            onClick={handleSample}
            disabled={loading}
            className="rounded-lg px-3 py-1.5 text-sm text-amber-400 hover:bg-white/5 disabled:opacity-50"
          >
            새로고침
          </button>
        </div>

        <div className="h-[100dvh] pt-12">
          <SajuBriefingDeck briefing={briefing} homeUrl={getStreamlitHomeUrl(null)} />
        </div>

        <aside className="pointer-events-none fixed bottom-20 right-4 z-[55] hidden max-w-[200px] rounded-xl border border-white/10 bg-black/70 p-3 text-xs backdrop-blur lg:block">
          <p className="font-semibold text-amber-400/90">에너지 흐름</p>
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
      </BriefingShell>
    );
  }

  return (
    <BriefingShell>
      {error && (
        <div className="mx-auto max-w-lg px-4 pt-4">
          <p className="rounded-xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
            {error}
            <br />
            <span className="mt-2 block text-xs opacity-80">
              터미널: uvicorn saju_app.api.app:app --reload --port 8000
            </span>
          </p>
        </div>
      )}
      <BriefingLanding
        loading={loading}
        onStartSample={handleSample}
        onStartGenerate={(req) => run(() => generateBriefing(req))}
      />
    </BriefingShell>
  );
}
