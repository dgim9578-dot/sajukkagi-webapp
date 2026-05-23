"use client";

import type { ReactNode } from "react";
import { useSajuTheme, type UseSajuThemeOptions } from "@/hooks/useSajuTheme";
import type { SajuTheme } from "@/lib/saju-theme";

export type SajuThemeProviderProps = {
  children: ReactNode;
  gapja: string[] | null | undefined;
  apiTheme?: UseSajuThemeOptions["apiTheme"];
  className?: string;
};

/**
 * ``data-theme={slug}`` + CSS 변수(--primary, --gradient)로 전체 하위 UI에 테마 적용.
 */
export function SajuThemeProvider({
  children,
  gapja,
  apiTheme,
  className = "",
}: SajuThemeProviderProps) {
  const theme = useSajuTheme(gapja, { apiTheme });

  return (
    <div
      data-theme={theme.theme_key}
      data-theme-id={theme.theme_id}
      className={`min-h-screen transition-all duration-700 ${className}`.trim()}
      style={
        {
          ["--primary" as string]: theme.primary_color,
          ["--primary-soft" as string]: theme.primary_soft,
          ["--gradient" as string]: theme.gradient_css,
        } as React.CSSProperties
      }
    >
      <div className="saju-theme-shell min-h-screen bg-gradient-to-br from-[var(--primary-soft)] to-white dark:from-[var(--primary-soft)]/20 dark:to-[#0a0a14]">
        {children}
      </div>
    </div>
  );
}

export type { SajuTheme };
