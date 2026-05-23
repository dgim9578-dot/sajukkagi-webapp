import type { SajuBriefing } from "@/types/saju-briefing";

/** FastAPI 없이도 「3D 브리핑 체험」이 동작하도록 하는 로컬 샘플 */
export function getLocalSampleBriefing(): SajuBriefing {
  return {
    fingerprint: "test_sample_123",
    display_name: "김사주",
    sample: true,
    consultation_type: "general",
    overview: {
      day_master: "丙",
      day_master_element: "火",
      balance_score: 78,
      main_keywords: ["열정", "성장", "리더십", "표현"],
    },
    pillars_3d: [
      {
        index: 0,
        slot: "year",
        pillar: "甲子",
        stem: { char: "甲", element: "wood", color: "#4ade80" },
        branch: { char: "子", element: "water", color: "#60a5fa" },
      },
      {
        index: 1,
        slot: "month",
        pillar: "乙丑",
        stem: { char: "乙", element: "wood", color: "#4ade80" },
        branch: { char: "丑", element: "earth", color: "#fbbf24" },
      },
      {
        index: 2,
        slot: "day",
        pillar: "丙寅",
        stem: { char: "丙", element: "fire", color: "#f87171" },
        branch: { char: "寅", element: "wood", color: "#4ade80" },
      },
      {
        index: 3,
        slot: "hour",
        pillar: "丁卯",
        stem: { char: "丁", element: "fire", color: "#f87171" },
        branch: { char: "卯", element: "wood", color: "#4ade80" },
      },
    ],
    energy_flow: {
      strong: ["火", "木"],
      weak: ["水", "金"],
      generate: [
        { from: "木", to: "火" },
        { from: "火", to: "土" },
      ],
      control: [
        { from: "水", to: "火" },
        { from: "火", to: "金" },
      ],
    },
    ten_god: {
      counts: { 비견: 2, 식신: 1, 정재: 1, 편관: 1, 정인: 1 },
    },
    visual_themes: {
      primary: "#d4af37",
      accent: "#f97316",
      bg: "#050508",
    },
    life_insights: {
      wealth: {
        id: "wealth",
        title: "재물운",
        emoji: "💰",
        score: 7,
        summary: "꾸준한 루틴이 쌓일수록 입·출이 안정됩니다.",
        color: "#D4AF37",
      },
      marriage: {
        id: "love",
        title: "혼인운",
        emoji: "❤️",
        score: 9,
        summary:
          "감정의 흐름이 활발하고, 먼저 다가가면 인연이 붙기 쉬운 시기입니다.",
        color: "#F472B6",
      },
      career: {
        id: "career",
        title: "커리어운",
        emoji: "💼",
        score: 8,
        summary: "역할이 분명해질수록 성과가 드러나는 흐름입니다.",
        color: "#60A5FA",
      },
      health: {
        id: "health",
        title: "원국 체질 힌트",
        emoji: "🩺",
        score: null,
        summary:
          "火 기운이 두드러져 심장·혈액·정신 쪽 과부하·열감에 유의하면 좋습니다.",
        color: "#F472B6",
      },
    },
    fortune_cards: [
      {
        id: "wealth",
        title: "재물운",
        emoji: "💰",
        score: 70,
        summary: "꾸준한 루틴이 쌓일수록 입·출이 안정됩니다.",
        color: "#D4AF37",
        particle: "coin",
      },
      {
        id: "love",
        title: "혼인운",
        emoji: "❤️",
        score: 90,
        summary:
          "감정의 흐름이 활발하고, 먼저 다가가면 인연이 붙기 쉬운 시기입니다.",
        color: "#F472B6",
        particle: "heart",
      },
      {
        id: "career",
        title: "커리어운",
        emoji: "💼",
        score: 80,
        summary: "역할이 분명해질수록 성과가 드러나는 흐름입니다.",
        color: "#60A5FA",
        particle: "star",
      },
      {
        id: "health",
        title: "원국 체질 힌트",
        emoji: "🩺",
        score: 0,
        summary:
          "火 기운이 두드러져 심장·혈액·정신 쪽 과부하·열감에 유의하면 좋습니다.",
        color: "#F472B6",
        particle: "star",
      },
    ],
    recommendations: [
      {
        title: "올해는 표현력을 키우세요",
        desc: "말과 글로 자신의 강점을 드러내면 기회가 따라옵니다.",
      },
      {
        title: "무리한 확장은 피하세요",
        desc: "에너지가 강한 만큼 과로·충동 결정에 주의하세요.",
      },
    ],
    shareable: {
      title: "김사주님의 사주 브리핑",
      thumbnail_keywords: ["열정", "성장", "리더십"],
    },
  };
}
