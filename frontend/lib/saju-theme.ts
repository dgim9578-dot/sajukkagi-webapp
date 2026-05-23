/** 오행 테마 — Python ``saju_storage.THEME_CONFIG`` 와 동기 */

export type ElementHan = "木" | "火" | "土" | "金" | "水";
export type ThemeSlug = "wood" | "fire" | "earth" | "metal" | "water";

export type ThemeConfigEntry = {
  name: string;
  emoji: string;
  gradient: string;
  accent: string;
  primary_soft: string;
  gradient_css: string;
  bg_pattern: string;
  font_weight: string;
  vibe: string;
};

export const THEME_CONFIG: Record<ElementHan, ThemeConfigEntry> = {
  木: {
    name: "목기운",
    emoji: "🌳🌱",
    gradient: "from-emerald-400 to-green-500",
    accent: "#10b981",
    primary_soft: "#d1fae5",
    gradient_css: "linear-gradient(135deg, #10b981, #34d399)",
    bg_pattern: "leaf",
    font_weight: "medium",
    vibe: "성장형, 자유로운",
  },
  火: {
    name: "화기운",
    emoji: "🔥",
    gradient: "from-red-400 to-orange-500",
    accent: "#ef4444",
    primary_soft: "#fee2e2",
    gradient_css: "linear-gradient(135deg, #ef4444, #f97316)",
    bg_pattern: "flame",
    font_weight: "semibold",
    vibe: "열정적, 밝고 강렬",
  },
  土: {
    name: "토기운",
    emoji: "🏔️🌾",
    gradient: "from-amber-400 to-yellow-600",
    accent: "#d4af37",
    primary_soft: "#fef3c7",
    gradient_css: "linear-gradient(135deg, #d4af37, #fbbf24)",
    bg_pattern: "earth",
    font_weight: "medium",
    vibe: "안정적, 신뢰와 실속",
  },
  金: {
    name: "금기운",
    emoji: "✨⚔️",
    gradient: "from-slate-300 to-gray-400",
    accent: "#94a3b8",
    primary_soft: "#f1f5f9",
    gradient_css: "linear-gradient(135deg, #94a3b8, #cbd5e1)",
    bg_pattern: "metal",
    font_weight: "semibold",
    vibe: "결단형, 원칙과 정리",
  },
  水: {
    name: "수기운",
    emoji: "💧🌊",
    gradient: "from-blue-500 to-indigo-600",
    accent: "#3b82f6",
    primary_soft: "#dbeafe",
    gradient_css: "linear-gradient(135deg, #3b82f6, #6366f1)",
    bg_pattern: "wave",
    font_weight: "normal",
    vibe: "지혜형, 유연하고 깊은",
  },
};

const ELEMENT_SLUG: Record<ElementHan, ThemeSlug> = {
  木: "wood",
  火: "fire",
  土: "earth",
  金: "metal",
  水: "water",
};

const STEM_ELEMENT: Record<string, ElementHan> = {
  甲: "木",
  乙: "木",
  丙: "火",
  丁: "火",
  戊: "土",
  己: "土",
  庚: "金",
  辛: "金",
  壬: "水",
  癸: "水",
};

const BRANCH_ELEMENT: Record<string, ElementHan> = {
  寅: "木",
  卯: "木",
  巳: "火",
  午: "火",
  辰: "土",
  戌: "土",
  丑: "土",
  未: "土",
  申: "金",
  酉: "金",
  亥: "水",
  子: "水",
};

export type SajuTheme = {
  dominant_element: ElementHan;
  day_stem: string;
  day_element: ElementHan;
  slug: ThemeSlug;
  /** CSS ``data-theme`` — ``slug`` 사용 (예: wood). 레거시 식별자는 ``theme_id``. */
  theme_key: ThemeSlug;
  theme_id: string;
  primary_color: string;
  primary_soft: string;
  gradient_css: string;
  emoji: string;
  nickname: string;
  vibe: string;
  config: ThemeConfigEntry;
};

export function elementThemeSlug(elementOrSlug: string): ThemeSlug {
  const raw = (elementOrSlug || "").trim();
  if (raw in THEME_CONFIG) return ELEMENT_SLUG[raw as ElementHan];
  if (["wood", "fire", "earth", "metal", "water"].includes(raw)) return raw as ThemeSlug;
  const head = raw.split("_")[0];
  if (["wood", "fire", "earth", "metal", "water"].includes(head)) return head as ThemeSlug;
  return "earth";
}

function countElements(gapja: string[]): Record<ElementHan, number> {
  const counts: Record<ElementHan, number> = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };
  for (const pillar of gapja.slice(0, 4)) {
    const p = (pillar || "").trim();
    if (p.length >= 1) {
      const stemEl = STEM_ELEMENT[p[0]];
      if (stemEl) counts[stemEl] += 1;
    }
    if (p.length >= 2) {
      const branchEl = BRANCH_ELEMENT[p[1]];
      if (branchEl) counts[branchEl] += 1;
    }
  }
  return counts;
}

function dominantElement(
  counts: Record<ElementHan, number>,
  dayElement: ElementHan
): ElementHan {
  const entries = Object.entries(counts) as [ElementHan, number][];
  entries.sort((a, b) => {
    if (b[1] !== a[1]) return b[1] - a[1];
    if (a[0] === dayElement) return 1;
    if (b[0] === dayElement) return -1;
    return 0;
  });
  return entries[0]?.[0] ?? "土";
}

/** gapja(四柱)로 테마 계산 — API ``theme`` 블록이 없을 때 클라이언트 폴백 */
export function buildSajuThemeFromGapja(gapja: string[] | null | undefined): SajuTheme {
  const pillars = (gapja || []).map((x) => String(x || ""));
  const dayStem = pillars[2]?.[0] ?? "";
  const dayElement = STEM_ELEMENT[dayStem] ?? "土";
  const counts = countElements(pillars);
  const dom = dominantElement(counts, dayElement);
  const cfg = THEME_CONFIG[dom];
  const slug = ELEMENT_SLUG[dom];
  const themeId = dayStem ? `${slug}_${dayStem}` : slug;

  return {
    dominant_element: dom,
    day_stem: dayStem,
    day_element: dayElement,
    slug,
    theme_key: slug,
    theme_id: themeId,
    primary_color: cfg.accent,
    primary_soft: cfg.primary_soft,
    gradient_css: cfg.gradient_css,
    emoji: cfg.emoji,
    nickname: cfg.name,
    vibe: cfg.vibe,
    config: cfg,
  };
}

/** API/브리핑 JSON ``theme`` 객체 병합 */
export function mergeThemeFromApi(
  gapja: string[] | null | undefined,
  apiTheme?: Record<string, unknown> | null
): SajuTheme {
  const base = buildSajuThemeFromGapja(gapja);
  if (!apiTheme || typeof apiTheme !== "object") return base;

  const slug = elementThemeSlug(
    String(apiTheme.slug ?? apiTheme.theme_key ?? apiTheme.dominant_element ?? base.slug)
  );
  const dom = (apiTheme.dominant_element as ElementHan) || base.dominant_element;
  const cfg = THEME_CONFIG[dom in THEME_CONFIG ? dom : base.dominant_element];

  return {
    ...base,
    dominant_element: dom in THEME_CONFIG ? dom : base.dominant_element,
    day_stem: String(apiTheme.day_stem ?? base.day_stem),
    day_element: (apiTheme.day_element as ElementHan) || base.day_element,
    slug,
    theme_key: slug,
    theme_id: String(apiTheme.theme_key ?? `${slug}_${base.day_stem}`).includes("_")
      ? String(apiTheme.theme_key)
      : `${slug}_${base.day_stem}`,
    primary_color: String(apiTheme.primary_color ?? apiTheme.accent ?? cfg.accent),
    primary_soft: String(apiTheme.primary_soft ?? cfg.primary_soft),
    gradient_css: String(apiTheme.gradient_css ?? cfg.gradient_css),
    emoji: String(apiTheme.emoji ?? cfg.emoji),
    nickname: String(apiTheme.nickname ?? cfg.name),
    vibe: String(apiTheme.vibe ?? cfg.vibe),
    config: cfg,
  };
}
