import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "사주프로 | 3D 사주 브리핑",
  description:
    "3D 사주팔자 · 스와이프 운세 카드 · API 연동 통합 브리핑 덱",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
