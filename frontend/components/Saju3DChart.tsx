"use client";

import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls, Text } from "@react-three/drei";
import { Suspense, useMemo } from "react";

import type { Pillar3D, VisualThemes } from "@/types/saju-briefing";
import { ELEMENT_FALLBACK_COLORS, SLOT_LABELS_KO } from "@/types/saju-briefing";

interface PillarProps {
  position: [number, number, number];
  label: string;
  stem: string;
  branch: string;
  color: string;
  isDayMaster?: boolean;
}

function Pillar({
  position,
  label,
  stem,
  branch,
  color,
  isDayMaster = false,
}: PillarProps) {
  const height = isDayMaster ? 4.2 : 3.8;

  return (
    <group position={position}>
      <mesh castShadow receiveShadow>
        <cylinderGeometry args={[0.45, 0.55, height, 32]} />
        <meshStandardMaterial
          color={color}
          metalness={0.55}
          roughness={0.32}
          emissive={isDayMaster ? color : "#000000"}
          emissiveIntensity={isDayMaster ? 0.35 : 0}
        />
      </mesh>

      <Text
        position={[0, height / 2 + 1.05, 0]}
        fontSize={0.28}
        color="#d4af37"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.02}
        outlineColor="#000000"
      >
        {label}
      </Text>

      <Text
        position={[0, height / 2 + 0.55, 0]}
        fontSize={0.65}
        color="#fff8ec"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.03}
        outlineColor="#000000"
      >
        {stem}
      </Text>

      <Text
        position={[0, -height / 2 - 0.55, 0]}
        fontSize={0.72}
        color="#f5e0b8"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.03}
        outlineColor="#000000"
      >
        {branch}
      </Text>

      {isDayMaster && (
        <pointLight position={[0, 2, 0]} color={color} intensity={2.5} distance={8} />
      )}
    </group>
  );
}

export interface Saju3DChartProps {
  pillars: Pillar3D[];
  visualThemes?: VisualThemes;
  className?: string;
  autoRotate?: boolean;
}

export default function Saju3DChart({
  pillars,
  visualThemes,
  className = "",
  autoRotate = true,
}: Saju3DChartProps) {
  const coloredPillars = useMemo(() => {
    const list = Array.isArray(pillars) ? pillars : [];
    return list.slice(0, 4).map((p, index) => {
      const isDayMaster = index === 2;
      const el = p.stem?.element || "水";
      const pillarColor =
        p.stem?.color ||
        ELEMENT_FALLBACK_COLORS[el] ||
        visualThemes?.primary ||
        "#3B82F6";
      const color = isDayMaster
        ? visualThemes?.primary || pillarColor
        : pillarColor;

      return {
        key: `${p.slot}-${index}`,
        position: [(index - 1.5) * 2.8, 0, 0] as [number, number, number],
        label: SLOT_LABELS_KO[p.slot] || p.slot,
        stem: p.stem?.char || "?",
        branch: p.branch?.char || "?",
        color,
        isDayMaster,
      };
    });
  }, [pillars, visualThemes]);

  return (
    <div
      className={`relative w-full h-[520px] min-h-[420px] rounded-3xl overflow-hidden border border-slate-800 bg-gradient-to-b from-slate-950 to-black ${className}`}
    >
      <Canvas
        shadows
        camera={{ position: [0, 6, 12], fov: 45 }}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={["#050508"]} />
        <Suspense fallback={null}>
          <ambientLight intensity={0.55} />
          <directionalLight position={[8, 12, 6]} intensity={1.1} castShadow />
          <pointLight position={[-6, 4, -4]} intensity={0.45} color="#d4af37" />

          {coloredPillars.map((p) => (
            <Pillar
              key={p.key}
              position={p.position}
              label={p.label}
              stem={p.stem}
              branch={p.branch}
              color={p.color}
              isDayMaster={p.isDayMaster}
            />
          ))}

          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.2, 0]} receiveShadow>
            <circleGeometry args={[8, 64]} />
            <meshStandardMaterial color="#0f172a" metalness={0.2} roughness={0.85} />
          </mesh>

          <Environment preset="night" />
          <OrbitControls
            enablePan={false}
            minDistance={6}
            maxDistance={18}
            autoRotate={autoRotate}
            autoRotateSpeed={0.35}
          />
        </Suspense>
      </Canvas>

      <div className="pointer-events-none absolute bottom-6 left-6 text-white">
        <p className="text-sm opacity-70">드래그로 회전 · 스크롤로 줌</p>
      </div>
    </div>
  );
}
