/** `generate_saju_briefing` / `get_sample_briefing` 응답 타입 */

export interface PillarStem3D {
  char: string;
  element: string;
  element_name?: string;
  yin_yang?: string;
  ten_god?: string;
  color?: string;
  soft_color?: string;
}

export interface PillarBranch3D {
  char: string;
  element?: string;
  element_name?: string;
  color?: string;
  hidden_stems?: Array<{
    stem: string;
    element?: string;
    ten_god?: string;
  }>;
}

export interface Pillar3D {
  index: number;
  slot: string;
  pillar: string;
  stem: PillarStem3D;
  branch: PillarBranch3D;
}

export interface VisualThemes {
  primary: string;
  accent: string;
  bg: string;
}

export interface EnergyFlow {
  strong: string[];
  weak: string[];
  generate: Array<{ from: string; to: string }>;
  control: Array<{ from: string; to: string }>;
}

export interface FortuneCard {
  id: string;
  title: string;
  emoji: string;
  score: number;
  summary: string;
  color: string;
  particle?: string;
}

export interface LifeInsightItem {
  id: string;
  title: string;
  emoji: string;
  score: number | null;
  summary: string;
  color: string;
}

/** 3D 덱 「핵심」 슬라이드 — 일간·키워드·균형 해석 */
export interface CoreSlideInterpretation {
  headline: string;
  slide_purpose: string;
  summary: string;
  day_pillar?: string;
  day_stem_role?: string;
  keyword_notes?: Array<{ keyword: string; meaning: string }>;
  balance_label?: string;
  balance_comment?: string;
  insight_bullets?: string[];
}

export interface SajuBriefing {
  fingerprint: string;
  display_name: string;
  generated_at?: string;
  consultation_type?: string;
  sample?: boolean;
  overview: {
    day_master: string;
    day_master_element: string;
    balance_score: number;
    main_keywords: string[];
    core_interpretation?: CoreSlideInterpretation;
  };
  pillars_3d: Pillar3D[];
  energy_flow?: EnergyFlow;
  ten_god?: {
    counts?: Record<string, number>;
    strength?: Array<[string, number]> | Record<string, number>;
  };
  visual_themes?: VisualThemes;
  fortune_cards?: FortuneCard[];
  life_insights?: Record<string, LifeInsightItem>;
  recommendations?: Array<{ title: string; desc: string }>;
  gapja_meta?: Record<string, unknown>;
  shareable?: {
    title?: string;
    thumbnail_keywords?: string[];
  };
  match?: {
    score?: number;
    day_branch_rel?: string;
    user_name?: string;
    partner_name?: string;
  };
}

export const SLOT_LABELS_KO: Record<string, string> = {
  year: "년주",
  month: "월주",
  day: "일주",
  hour: "시주",
};

export const ELEMENT_FALLBACK_COLORS: Record<string, string> = {
  "木": "#22C55E",
  "火": "#EF4444",
  "土": "#D4AF37",
  "金": "#E5E7EB",
  "水": "#3B82F6",
};
