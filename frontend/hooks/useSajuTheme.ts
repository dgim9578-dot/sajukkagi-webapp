"use client";

import { useMemo } from "react";
import {
  buildSajuThemeFromGapja,
  mergeThemeFromApi,
  type SajuTheme,
} from "@/lib/saju-theme";

export type UseSajuThemeOptions = {
  /** 백엔드 ``build_saju_theme_meta`` 의 ``theme`` 블록 */
  apiTheme?: Record<string, unknown> | null;
};

/**
 * gapja(四柱) 또는 API theme 으로 오행 테마 계산.
 * ``theme.theme_key`` / ``theme.slug`` → CSS ``data-theme="wood"`` 등.
 */
export function useSajuTheme(
  gapja: string[] | null | undefined,
  options?: UseSajuThemeOptions
): SajuTheme {
  const apiTheme = options?.apiTheme;
  return useMemo(
    () => mergeThemeFromApi(gapja, apiTheme),
    [gapja, apiTheme]
  );
}

export { buildSajuThemeFromGapja };
