"use client";

import dynamic from "next/dynamic";
import { useMemo, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { Swiper as SwiperReact, SwiperSlide } from "swiper/react";
import type { Swiper as SwiperInstance } from "swiper";
import "swiper/css";

import BriefingParticles from "./BriefingParticles";
import { getStreamlitHomeUrl } from "@/lib/saju-app-url";
import { resolveCoreInterpretation } from "@/lib/briefing-core-slide";
import { resolveFortuneCards } from "@/lib/briefing-fortune";
import type { FortuneCard, SajuBriefing } from "@/types/saju-briefing";
import { ELEMENT_FALLBACK_COLORS } from "@/types/saju-briefing";

/** three.js / R3F는 서버에서 번들되지 않도록 클라이언트만 로드 */
const Saju3DChart = dynamic(() => import("./Saju3DChart"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[320px] items-center justify-center rounded-2xl border border-white/10 bg-black/40 text-sm text-slate-400">
      3D 사주 차트 불러오는 중…
    </div>
  ),
});

const SajuEnergyFlow3D = dynamic(() => import("./SajuEnergyFlow3D"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[280px] items-center justify-center rounded-2xl border border-white/10 bg-black/40 text-sm text-slate-400">
      오행 3D 불러오는 중…
    </div>
  ),
});

export interface SajuBriefingDeckProps {
  briefing: SajuBriefing;
  /** Streamlit iframe 등 좁은 영역 — 100dvh 대신 부모 높이에 맞춤 */
  embedMode?: boolean;
  /** 「처음으로」 — Streamlit 사주까기 랜딩(STEP1) */
  homeUrl?: string;
}

const DECK_SECTIONS = [
  {
    icon: "✨",
    title: "핵심·일간",
    desc: "키워드와 균형",
    detail:
      "사주의 중심인 일간(日干)과 오행 성향, 올해 균형 지수를 키워드로 요약합니다.",
  },
  {
    icon: "🌀",
    title: "오행 에너지",
    desc: "생극·상극 3D",
    detail:
      "木·火·土·金·水의 강약과 상생·상극 관계를 3D로 시각화해 에너지 흐름을 봅니다.",
  },
  {
    icon: "🧬",
    title: "사주 팔자",
    desc: "4주 3D 차트",
    detail:
      "년·월·일·시 네 기둥(四柱)을 3D로 돌려보며 천간·지지·십성을 확인합니다.",
  },
  {
    icon: "🎴",
    title: "운세 카드",
    desc: "재물·혼인·커리어·체질",
    detail:
      "재물운·혼인운·커리어운·원국 체질 힌트를 STEP3와 같은 문장으로 카드 슬라이드에 표시합니다.",
  },
  {
    icon: "📜",
    title: "십성·조언",
    desc: "올해 핵심 정리",
    detail:
      "십성(十星) 분포와 올해 실천 조언을 정리한 마무리 슬라이드입니다.",
  },
] as const;

function DeckProgressBar({
  current,
  total,
  label,
  embedMode,
}: {
  current: number;
  total: number;
  label: string;
  embedMode?: boolean;
}) {
  const pct = total > 0 ? ((current + 1) / total) * 100 : 0;
  return (
    <div
      className={`pointer-events-none absolute inset-x-0 top-0 z-40 px-4 ${embedMode ? "pt-11 sm:pt-12" : "pt-3 sm:pt-4"}`}
    >
      <div className="mx-auto flex max-w-lg items-center gap-3">
        <span className="shrink-0 text-xs font-semibold text-amber-400/90">
          {current + 1} / {total}
        </span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-400"
            initial={false}
            animate={{ width: `${pct}%` }}
            transition={{ duration: 0.35 }}
          />
        </div>
        <span className="max-w-[8rem] truncate text-right text-[10px] text-white/50 sm:max-w-[10rem] sm:text-xs">
          {label}
        </span>
      </div>
    </div>
  );
}

function DeckNavControls({
  current,
  total,
  label,
  onPrev,
  onNext,
  showSwipeHint = false,
}: {
  current: number;
  total: number;
  label: string;
  onPrev: () => void;
  onNext: () => void;
  showSwipeHint?: boolean;
}) {
  const atStart = current <= 0;
  const atEnd = current >= total - 1;

  return (
    <div className="mt-8 shrink-0 border-t border-white/10 px-1 pt-6 pb-2">
      {showSwipeHint && (
        <p className="mb-3 text-center text-xs text-white/45 sm:text-sm">
          터치·드래그로 넘기거나 아래 버튼을 누르세요
        </p>
      )}
      <div className="mx-auto flex w-full max-w-md items-center gap-2">
        <button
          type="button"
          onClick={onPrev}
          disabled={atStart}
          className="flex min-h-[3rem] flex-1 items-center justify-center gap-1 rounded-xl border border-white/10 bg-white/5 px-3 text-sm font-semibold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-30"
          aria-label="이전 슬라이드"
        >
          <span aria-hidden>←</span>
          <span className="hidden sm:inline">이전</span>
        </button>
        <div className="min-w-[5.5rem] shrink-0 px-1 text-center">
          <p className="text-[10px] uppercase tracking-wider text-amber-500/80">
            {label}
          </p>
          <p className="text-sm font-bold text-white">
            {current + 1}{" "}
            <span className="font-normal text-white/40">/ {total}</span>
          </p>
        </div>
        <button
          type="button"
          onClick={onNext}
          disabled={atEnd}
          className="flex min-h-[3rem] flex-1 items-center justify-center gap-1 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-3 text-sm font-bold text-black transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-30"
          aria-label="다음 슬라이드"
        >
          <span className="hidden sm:inline">다음</span>
          <span aria-hidden>→</span>
        </button>
      </div>
    </div>
  );
}

type DeckNavProps = {
  current: number;
  total: number;
  label: string;
  onPrev: () => void;
  onNext: () => void;
  showSwipeHint?: boolean;
};

function SlideScrollPanel({
  children,
  navProps,
}: {
  children: ReactNode;
  navProps: DeckNavProps;
}) {
  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-y-auto overflow-x-hidden overscroll-y-contain">
      <div className="w-full shrink-0">{children}</div>
      <div className="w-full shrink-0 px-3 pb-6 sm:px-4">
        <DeckNavControls {...navProps} />
      </div>
    </div>
  );
}

function OpeningSlide({
  briefing,
  totalSlides,
  keywords,
  homeUrl,
}: {
  briefing: SajuBriefing;
  totalSlides: number;
  keywords: string[];
  homeUrl: string;
}) {
  const dm = briefing.overview?.day_master ?? "";
  const el = briefing.overview?.day_master_element ?? "";

  return (
    <div className="relative flex w-full items-start justify-center bg-gradient-to-br from-[#1a0a2e] via-[#12081f] to-black px-4 py-10 pt-14">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        aria-hidden
      >
        <div className="absolute left-1/4 top-1/4 h-64 w-64 rounded-full bg-amber-500/20 blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 h-72 w-72 rounded-full bg-purple-600/25 blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55 }}
        className="relative z-10 w-full max-w-xl text-center"
      >
        <p className="mb-3 inline-block rounded-full border border-amber-500/35 bg-amber-500/10 px-4 py-1 text-xs font-semibold tracking-wide text-amber-200">
          INTERACTIVE SAJU BRIEFING · 총 {totalSlides}장
        </p>

        <div className="mb-6 rounded-2xl border border-white/15 bg-white/5 px-4 py-3 text-left text-sm leading-relaxed text-slate-200">
          {briefing.sample ? (
            <>
              <p className="font-bold text-amber-300">체험용 샘플 (김사주)</p>
              <p className="mt-2 text-white/80">
                이 화면은 <strong className="text-white">결과만 보는 3D 덱</strong>
                입니다. 이름·생년월일·시간 입력은{" "}
                <strong className="text-amber-200">사주까기(Streamlit)</strong>{" "}
                STEP2에서 합니다.
              </p>
              <a
                href={homeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 inline-block font-semibold text-amber-400 underline decoration-amber-500/50 underline-offset-2 hover:text-amber-300"
              >
                → 사주까기 홈으로 이동
              </a>
            </>
          ) : (
            <p className="text-white/80">
              입력하신 생년월일·시간을 바탕으로 계산된{" "}
              <strong className="text-white">브리핑 결과</strong>입니다. 아래
              목차 순서대로 넘기며 각 항목의 설명과 3D·카드를 확인하세요.
            </p>
          )}
        </div>

        <h1 className="text-4xl font-black leading-tight md:text-6xl">
          <span className="text-white">{briefing.display_name}님의</span>
          <br />
          <span className="bg-gradient-to-r from-amber-300 via-amber-400 to-orange-400 bg-clip-text text-transparent">
            사주 브리핑
          </span>
        </h1>
        {(dm || el) && (
          <p className="mt-4 text-lg text-slate-300 md:text-xl">
            일간 <span className="font-bold text-amber-300">{dm}</span>
            {el ? (
              <span className="text-slate-400"> · {el} 오행</span>
            ) : null}
          </p>
        )}
        {keywords.length > 0 && (
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {keywords.slice(0, 4).map((kw) => (
              <span
                key={kw}
                className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-amber-100/90"
              >
                {kw}
              </span>
            ))}
          </div>
        )}

        <p className="mb-3 text-left text-xs font-semibold uppercase tracking-wider text-amber-500/90">
          이 덱에서 다루는 내용
        </p>
        <div className="grid grid-cols-1 gap-2 text-left sm:grid-cols-2 sm:gap-3">
          {DECK_SECTIONS.map((s) => (
            <div
              key={s.title}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-3 backdrop-blur-sm"
            >
              <p className="text-lg leading-none">{s.icon}</p>
              <p className="mt-1 text-sm font-bold text-white">{s.title}</p>
              <p className="text-[11px] text-amber-200/70">{s.desc}</p>
              <p className="mt-2 text-xs leading-snug text-white/55">
                {s.detail}
              </p>
            </div>
          ))}
        </div>
      </motion.div>

      <motion.div
        className="pointer-events-none absolute right-3 top-1/2 hidden -translate-y-1/2 flex-col items-center gap-2 text-amber-400/70 sm:flex md:right-8"
        animate={{ x: [0, 8, 0] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
        aria-hidden
      >
        <span className="text-4xl">›</span>
        <span className="text-[10px] font-bold tracking-widest [writing-mode:vertical-rl]">
          NEXT
        </span>
      </motion.div>
    </div>
  );
}

function CoreDayMasterSlide({
  briefing,
  keywords,
}: {
  briefing: SajuBriefing;
  keywords: string[];
}) {
  const core = resolveCoreInterpretation(briefing);
  const dm = briefing.overview?.day_master ?? "—";
  const el = briefing.overview?.day_master_element ?? "";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="mx-auto max-w-xl px-4 pb-4 pt-14 text-left sm:px-6"
    >
      <p className="text-center text-xs font-semibold text-amber-500/80">
        2 · 핵심
      </p>
      <h2 className="mt-2 text-center text-2xl font-bold text-white md:text-3xl">
        {core.headline}
      </h2>

      <p className="mt-4 rounded-xl border border-amber-500/25 bg-amber-500/10 px-4 py-3 text-sm leading-relaxed text-amber-100/90">
        {core.slide_purpose}
      </p>

      <div className="mt-8 text-center">
        <p className="text-xs uppercase tracking-widest text-amber-500/60">
          일간 (Day Master)
        </p>
        <p className="mt-2 text-6xl font-black text-white">{dm}</p>
        <p className="mt-2 text-xl text-slate-300">
          {el} 오행
          {core.day_pillar ? (
            <span className="text-slate-500"> · 일주 {core.day_pillar}</span>
          ) : null}
        </p>
      </div>

      <p className="mt-6 text-sm leading-relaxed text-slate-300">
        {core.summary}
      </p>
      {core.day_stem_role ? (
        <p className="mt-3 text-sm leading-relaxed text-slate-400">
          {core.day_stem_role}
        </p>
      ) : null}

      {(core.keyword_notes?.length ?? 0) > 0 && (
        <div className="mt-8">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-amber-500/80">
            성향 키워드 — 무엇을 뜻하나요?
          </p>
          <ul className="space-y-2">
            {(core.keyword_notes ?? []).map((item) => (
              <li
                key={item.keyword}
                className="rounded-lg border border-white/10 bg-white/5 px-3 py-2.5"
              >
                <span className="font-semibold text-amber-200">
                  {item.keyword}
                </span>
                <span className="mt-1 block text-sm text-slate-400">
                  {item.meaning}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {keywords.length > 0 && !(core.keyword_notes?.length) && (
        <div className="mt-8 flex flex-wrap justify-center gap-2">
          {keywords.map((kw) => (
            <span
              key={kw}
              className="rounded-full border border-amber-500/40 bg-amber-500/10 px-4 py-2 text-sm text-amber-200"
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      <div className="mt-8 rounded-xl border border-white/10 bg-slate-900/60 px-4 py-3">
        <p className="text-xs font-semibold text-amber-400/90">
          {core.balance_label ?? "오행 균형 지수"}
        </p>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">
          {core.balance_comment}
        </p>
      </div>

      {(core.insight_bullets?.length ?? 0) > 0 && (
        <ul className="mt-6 list-disc space-y-2 pl-5 text-sm text-slate-400">
          {core.insight_bullets!.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
    </motion.div>
  );
}

function FortuneCardSlide({
  card,
  active,
}: {
  card: FortuneCard;
  active: boolean;
}) {
  return (
    <motion.div
      initial={false}
      animate={{
        scale: active ? 1 : 0.92,
        opacity: active ? 1 : 0.35,
      }}
      transition={{ duration: 0.35 }}
      className="relative mx-auto w-full max-w-lg overflow-hidden rounded-3xl border border-slate-700 bg-gradient-to-br from-slate-900 to-slate-800 p-10"
      style={{ borderColor: `${card.color}44` }}
    >
      <BriefingParticles kind={card.particle} color={card.color} />
      <div className="relative z-10 mb-6 text-center text-7xl">{card.emoji}</div>
      <h3 className="mb-4 text-center text-4xl font-bold">{card.title}</h3>
      {card.id !== "health" && card.score > 0 ? (
        <div
          className="mb-8 text-center text-6xl font-bold"
          style={{ color: card.color || "#fbbf24" }}
        >
          {card.score}%
        </div>
      ) : (
        <p className="mb-6 text-center text-sm text-slate-400">
          원국·대운 기준 참고 해석
        </p>
      )}
      <p className="text-center text-xl leading-relaxed opacity-90">
        {card.summary}
      </p>
    </motion.div>
  );
}

export default function SajuBriefingDeck({
  briefing,
  embedMode = false,
  homeUrl: homeUrlProp,
}: SajuBriefingDeckProps) {
  const homeUrl = getStreamlitHomeUrl(homeUrlProp);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [swiper, setSwiper] = useState<SwiperInstance | null>(null);

  const fortuneCards = resolveFortuneCards(briefing);
  const recommendations = briefing.recommendations ?? [];
  const keywords = briefing.overview?.main_keywords ?? [];

  const energy = briefing.energy_flow;
  const tenCounts = briefing.ten_god?.counts as
    | Record<string, number>
    | undefined;

  const slideLabels = useMemo(() => {
    const labels = ["시작", "핵심", "에너지", "사주팔자"];
    fortuneCards.forEach((c) => labels.push(c.title));
    if (tenCounts && Object.keys(tenCounts).length > 0) labels.push("십성");
    labels.push("조언");
    return labels;
  }, [fortuneCards, tenCounts]);

  const totalSlides = slideLabels.length;
  const fortuneSlideOffset = 4;

  const goPrev = () => swiper?.slidePrev();
  const goNext = () => swiper?.slideNext();

  const navProps: DeckNavProps = {
    current: currentSlide,
    total: totalSlides,
    label: slideLabels[currentSlide] ?? "",
    onPrev: goPrev,
    onNext: goNext,
    showSwipeHint: currentSlide === 0,
  };

  return (
    <div
      className={`briefing-deck-root flex h-full w-full flex-col overflow-hidden bg-black text-white ${
        embedMode ? "min-h-[420px]" : ""
      }`}
    >
      {embedMode && (
        <div className="absolute inset-x-0 top-0 z-50 border-b border-amber-500/25 bg-black/90 px-3 py-2 text-center text-xs text-amber-100/90 backdrop-blur-sm sm:text-sm">
          <strong className="text-amber-400">3D 사주 브리핑</strong>
          {" · "}
          아래 <strong>「다음」</strong> 또는 화면을 <strong>왼쪽으로 밀어</strong>{" "}
          {totalSlides}장을 넘깁니다
        </div>
      )}

      <div className="relative min-h-0 flex-1">
        <DeckProgressBar
          current={currentSlide}
          total={totalSlides}
          label={slideLabels[currentSlide] ?? ""}
          embedMode={embedMode}
        />

        <SwiperReact
          className="h-full w-full"
          spaceBetween={0}
          slidesPerView={1}
          onSwiper={setSwiper}
          onSlideChange={(sw: SwiperInstance) => setCurrentSlide(sw.activeIndex)}
        >
        <SwiperSlide className="!h-full bg-black">
          <SlideScrollPanel navProps={navProps}>
            <OpeningSlide
              briefing={briefing}
              totalSlides={totalSlides}
              keywords={keywords}
              homeUrl={homeUrl}
            />
          </SlideScrollPanel>
        </SwiperSlide>

        <SwiperSlide className="!h-full bg-gradient-to-b from-slate-950 to-black">
          <SlideScrollPanel navProps={navProps}>
            <CoreDayMasterSlide briefing={briefing} keywords={keywords} />
          </SlideScrollPanel>
        </SwiperSlide>

        <SwiperSlide className="!h-full bg-gradient-to-b from-slate-950 to-black">
          <SlideScrollPanel navProps={navProps}>
          <div className="flex flex-col items-center px-4 py-6 pt-14 md:px-6">
          <div className="w-full max-w-xl text-center">
            <p className="text-xs font-semibold text-amber-500/80">3 · 에너지</p>
            <h2 className="mt-2 text-3xl font-bold">오행 에너지 흐름</h2>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              목(木)·화(火)·토(土)·금(金)·수(水) 중 강한 기운은 활용 포인트,
              약한 기운은 보완이 필요한 영역입니다. 아래 3D에서 상생(生)·상극(克)
              화살표를 확인하세요.
            </p>
            <p className="mt-3 text-sm text-slate-500">
              강: {(energy?.strong ?? []).join(" · ") || "—"} · 약:{" "}
              {(energy?.weak ?? []).join(" · ") || "—"}
            </p>
          </div>
          {energy ? (
            <div className="mt-4 h-[min(42vh,360px)] w-full max-w-2xl px-2">
              <SajuEnergyFlow3D energy={energy} className="h-full min-h-[280px]" />
            </div>
          ) : (
            <p className="mt-8 text-slate-500">에너지 데이터가 없습니다.</p>
          )}
          <div className="mt-4 flex justify-center gap-2">
            {Object.entries(ELEMENT_FALLBACK_COLORS).map(([el, col]) => (
              <span
                key={el}
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: col }}
                title={el}
              />
            ))}
          </div>
          </div>
          </SlideScrollPanel>
        </SwiperSlide>

        <SwiperSlide className="!h-full bg-black">
          <SlideScrollPanel navProps={navProps}>
          <div className="flex min-h-0 flex-col pt-12">
          <div className="shrink-0 py-4 text-center">
            <p className="text-xs font-semibold text-amber-500/80">4 · 3D 팔자</p>
            <h2 className="mt-2 text-3xl font-bold md:text-4xl">당신의 사주 팔자</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-400">
              년·월·일·시 사주 네 기둥을 3D로 배치했습니다. 드래그로 회전시키며
              천간·지지·십성 색으로 기운을 비교해 보세요.
            </p>
          </div>
          <div className="min-h-0 flex-1 px-3 pb-6">
            <Saju3DChart
              pillars={briefing.pillars_3d}
              visualThemes={briefing.visual_themes}
              className="h-full min-h-[420px]"
            />
          </div>
          </div>
          </SlideScrollPanel>
        </SwiperSlide>

        {fortuneCards.map((card, idx) => (
          <SwiperSlide key={card.id} className="!h-full bg-black">
            <SlideScrollPanel navProps={navProps}>
            <div className="flex min-h-[50vh] items-center justify-center p-6 md:min-h-[60vh] md:p-8">
            <FortuneCardSlide
              card={card}
              active={currentSlide === fortuneSlideOffset + idx}
            />
            </div>
            </SlideScrollPanel>
          </SwiperSlide>
        ))}

        {tenCounts && Object.keys(tenCounts).length > 0 && (
          <SwiperSlide className="!h-full bg-black">
            <SlideScrollPanel navProps={navProps}>
            <div className="flex min-h-[50vh] items-center justify-center px-6 py-12">
            <div className="w-full max-w-lg">
              <h2 className="mb-8 text-center text-3xl font-bold">십성 분포</h2>
              <div className="space-y-3">
                {Object.entries(tenCounts)
                  .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
                  .slice(0, 6)
                  .map(([name, cnt]) => (
                    <div key={name} className="flex items-center gap-3">
                      <span className="w-14 shrink-0 text-sm text-slate-300">
                        {name}
                      </span>
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/10">
                        <div
                          className="h-full rounded-full bg-amber-500/80"
                          style={{
                            width: `${Math.min(100, (Number(cnt) || 0) * 18)}%`,
                          }}
                        />
                      </div>
                      <span className="w-6 text-right text-xs text-slate-500">
                        {cnt}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
            </div>
            </SlideScrollPanel>
          </SwiperSlide>
        )}

        <SwiperSlide className="!h-full bg-gradient-to-t from-black to-slate-950">
          <SlideScrollPanel navProps={navProps}>
          <div className="px-6 py-12">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="mb-10 text-4xl font-bold md:text-5xl">
              올해의 핵심 조언
            </h2>
            <div className="space-y-6 text-left">
              {recommendations.map((rec, i) => (
                <motion.div
                  key={rec.title}
                  initial={{ opacity: 0, x: -20 }}
                  animate={
                    currentSlide === slideLabels.length - 1
                      ? { opacity: 1, x: 0 }
                      : { opacity: 0.4, x: 0 }
                  }
                  transition={{ delay: i * 0.08 }}
                  className="rounded-2xl bg-slate-900/60 p-6"
                >
                  <p className="text-xl font-semibold md:text-2xl">{rec.title}</p>
                  <p className="mt-3 text-base opacity-80 md:text-lg">{rec.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
          </div>
          </SlideScrollPanel>
        </SwiperSlide>
        </SwiperReact>
      </div>
    </div>
  );
}
