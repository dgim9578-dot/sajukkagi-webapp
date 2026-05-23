import type { CoreSlideInterpretation, SajuBriefing } from "@/types/saju-briefing";

const EL_KO: Record<string, string> = {
  木: "목",
  火: "화",
  土: "토",
  金: "금",
  水: "수",
};

/** API에 core_interpretation이 없을 때 최소 폴백 */
export function resolveCoreInterpretation(
  briefing: SajuBriefing
): CoreSlideInterpretation {
  const core = briefing.overview?.core_interpretation;
  if (core?.summary) {
    return core;
  }

  const dm = briefing.overview?.day_master ?? "—";
  const el = briefing.overview?.day_master_element ?? "";
  const kws = briefing.overview?.main_keywords ?? [];
  const score = briefing.overview?.balance_score ?? "—";
  const elKo = EL_KO[el] ?? el;

  return {
    headline: "핵심 — 당신 사주의 중심축(일간)",
    slide_purpose:
      "사주 네 기둥 중 **일간**은 ‘나’의 성향과 선택의 기준입니다. 이후 운세 카드는 이 기준 위의 영역별 해석입니다.",
    summary: `일간 ${dm}(${elKo})은 이 사주에서 성격·컨디션·결정의 중심입니다. 키워드는 그 기운이 삶에서 드러나는 방식을 요약합니다.`,
    keyword_notes: kws.map((kw) => ({
      keyword: kw,
      meaning: `${elKo}·팔자 흐름에서 자주 보이는 성향 키워드입니다.`,
    })),
    balance_label: "오행 균형 지수",
    balance_comment: `균형 지수 ${score} — 오행이 얼마나 한쪽으로 치우쳤는지를 숫자로 요약한 참고 지표입니다.`,
    insight_bullets: [
      "일간은 ‘무엇을 하면 편한가’의 기준입니다.",
      "키워드는 강점·성향을 짧게 압축한 것입니다.",
      "뒤 슬라이드의 재물·혼인·커리어는 이 기준에 맞춘 영역 해석입니다.",
    ],
  };
}
