"use client";

import { motion } from "framer-motion";

import type { BriefingGenerateRequest } from "@/lib/briefing-api";
import { DEMO_BRIEFING_REQUEST } from "@/lib/briefing-api";

interface BriefingLandingProps {
  loading: boolean;
  onStartSample: () => void;
  onStartGenerate: (req: BriefingGenerateRequest) => void;
}

export default function BriefingLanding({
  loading,
  onStartSample,
  onStartGenerate,
}: BriefingLandingProps) {
  return (
    <div className="mx-auto flex min-h-[calc(100dvh-3.5rem)] max-w-lg flex-col justify-center px-6 py-12">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-amber-500/90">
          Interactive Briefing
        </p>
        <h1 className="mt-3 text-4xl font-black leading-tight md:text-5xl">
          사주를
          <br />
          <span className="text-amber-400">한 장씩</span> 읽다
        </h1>
        <p className="mt-5 text-base leading-relaxed text-slate-400">
          3D 사주팔자 · 운세 카드 · 올해 조언을 스와이프로 넘기며 확인합니다.
          Python API와 연동된 통합 예제입니다.
        </p>

        <div className="mt-10 space-y-3">
          <button
            type="button"
            disabled={loading}
            onClick={onStartSample}
            className="w-full rounded-2xl bg-gradient-to-r from-amber-500 to-amber-600 py-4 text-lg font-bold text-black transition hover:from-amber-400 disabled:opacity-50"
          >
            {loading ? "불러오는 중…" : "샘플 브리핑 시작"}
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => onStartGenerate(DEMO_BRIEFING_REQUEST)}
            className="w-full rounded-2xl border border-slate-600 bg-slate-900/80 py-4 text-lg font-semibold text-white transition hover:border-amber-500/50 disabled:opacity-50"
          >
            API로 브리핑 생성 (데모 데이터)
          </button>
        </div>

        <ul className="mt-10 space-y-2 text-sm text-slate-500">
          <li>· 슬라이드 1~2: 오프닝 · 일간 키워드</li>
          <li>· 슬라이드 3~4: 오행 3D · 사주 4주 차트</li>
          <li>· 이후: 재물·혼인·커리어·체질 카드 · 조언 (STEP3와 동일 해석)</li>
        </ul>
      </motion.div>
    </div>
  );
}
