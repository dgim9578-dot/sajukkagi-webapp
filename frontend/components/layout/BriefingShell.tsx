"use client";

import type { ReactNode } from "react";

interface BriefingShellProps {
  children: ReactNode;
  /** 덱 전체 화면 모드 — 헤더 최소화 */
  immersive?: boolean;
}

export default function BriefingShell({
  children,
  immersive = false,
}: BriefingShellProps) {
  if (immersive) {
    return <div className="min-h-[100dvh] bg-black text-white">{children}</div>;
  }

  return (
    <div className="flex min-h-[100dvh] flex-col bg-[#050508] text-white">
      <header className="sticky top-0 z-50 border-b border-white/10 bg-[#050508]/90 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <span className="text-lg font-black tracking-tight text-amber-400">
              사주프로
            </span>
            <span className="hidden text-xs text-slate-500 sm:inline">
              3D 브리핑
            </span>
          </div>
          <p className="text-xs text-slate-500">참고용 · 의료·법률 조언 아님</p>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
