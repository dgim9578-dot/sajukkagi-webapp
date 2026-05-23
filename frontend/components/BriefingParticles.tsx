"use client";

interface BriefingParticlesProps {
  kind?: string;
  color?: string;
}

export default function BriefingParticles({
  kind = "star",
  color = "#d4af37",
}: BriefingParticlesProps) {
  const cls =
    kind === "heart"
      ? "briefing-particles--heart"
      : kind === "coin"
        ? "briefing-particles--coin"
        : "briefing-particles--star";

  return (
    <div
      className={`briefing-particles pointer-events-none absolute inset-0 overflow-hidden ${cls}`}
      style={{ ["--bp-color" as string]: color }}
      aria-hidden
    />
  );
}
