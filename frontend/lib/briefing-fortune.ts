import type { FortuneCard, LifeInsightItem, SajuBriefing } from "@/types/saju-briefing";

const LIFE_ORDER = ["wealth", "marriage", "career", "health"] as const;

function particleForKey(key: string): FortuneCard["particle"] {
  if (key === "wealth") return "coin";
  if (key === "marriage") return "heart";
  return "star";
}

function lifeItemToCard(item: LifeInsightItem, key: string): FortuneCard | null {
  const summary = String(item.summary || "").trim();
  if (!summary) return null;
  const score10 = item.score;
  return {
    id: item.id || key,
    title: item.title || key,
    emoji: item.emoji || "✨",
    score:
      key === "health" || score10 == null
        ? 0
        : Math.max(42, Math.min(96, Number(score10) * 10)),
    summary,
    color: item.color || "#d4af37",
    particle: particleForKey(key),
  };
}

/** STEP3 life_insights와 동일 문장·항목 순서로 운세 슬라이드를 만듭니다. */
export function resolveFortuneCards(briefing: SajuBriefing): FortuneCard[] {
  const life = briefing.life_insights;
  if (life && typeof life === "object") {
    const cards: FortuneCard[] = [];
    for (const key of LIFE_ORDER) {
      const item = life[key as keyof typeof life];
      if (!item) continue;
      const card = lifeItemToCard(item, key);
      if (card) cards.push(card);
    }
    if (cards.length > 0) return cards;
  }
  return briefing.fortune_cards ?? [];
}
