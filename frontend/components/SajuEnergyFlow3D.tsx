"use client";

import { Canvas } from "@react-three/fiber";
import { Line, OrbitControls, Text } from "@react-three/drei";
import { Suspense, useMemo } from "react";

import type { EnergyFlow } from "@/types/saju-briefing";
import { ELEMENT_FALLBACK_COLORS } from "@/types/saju-briefing";

const ELEMENT_ORDER = ["木", "火", "土", "金", "水"] as const;

const RING_RADIUS = 2.4;

function elementPosition(index: number): [number, number, number] {
  const angle = (index / ELEMENT_ORDER.length) * Math.PI * 2 - Math.PI / 2;
  return [
    Math.cos(angle) * RING_RADIUS,
    0,
    Math.sin(angle) * RING_RADIUS,
  ];
}

function ElementNode({
  element,
  position,
  strong,
  weak,
}: {
  element: string;
  position: [number, number, number];
  strong: boolean;
  weak: boolean;
}) {
  const color = ELEMENT_FALLBACK_COLORS[element] ?? "#d4af37";
  const scale = strong ? 1.15 : weak ? 0.82 : 1;
  const emissive = strong ? 0.55 : weak ? 0.12 : 0.28;

  return (
    <group position={position} scale={scale}>
      <mesh castShadow>
        <sphereGeometry args={[0.42, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={emissive}
          metalness={0.4}
          roughness={0.35}
        />
      </mesh>
      <Text
        position={[0, 0.75, 0]}
        fontSize={0.38}
        color="#fff8ec"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.025}
        outlineColor="#000000"
      >
        {element}
      </Text>
    </group>
  );
}

function FlowArrow({
  from: fromEl,
  to: toEl,
  kind,
}: {
  from: string;
  to: string;
  kind: "generate" | "control";
}) {
  const fromIdx = ELEMENT_ORDER.indexOf(fromEl as (typeof ELEMENT_ORDER)[number]);
  const toIdx = ELEMENT_ORDER.indexOf(toEl as (typeof ELEMENT_ORDER)[number]);
  if (fromIdx < 0 || toIdx < 0) return null;

  const a = elementPosition(fromIdx);
  const b = elementPosition(toIdx);
  const mid: [number, number, number] = [
    (a[0] + b[0]) / 2,
    0.55,
    (a[2] + b[2]) / 2,
  ];
  const color = kind === "generate" ? "#34d399" : "#f87171";

  return (
    <Line
      points={[a, mid, b]}
      color={color}
      lineWidth={kind === "generate" ? 2.2 : 1.6}
      transparent
      opacity={0.85}
    />
  );
}

function EnergyScene({ energy }: { energy: EnergyFlow }) {
  const strongSet = useMemo(
    () => new Set(energy.strong ?? []),
    [energy.strong]
  );
  const weakSet = useMemo(() => new Set(energy.weak ?? []), [energy.weak]);

  const generate = (energy.generate ?? []).slice(0, 8);
  const control = (energy.control ?? []).slice(0, 8);

  return (
    <>
      <ambientLight intensity={0.45} />
      <pointLight position={[4, 6, 4]} intensity={1.2} color="#fbbf24" />
      <pointLight position={[-4, 3, -3]} intensity={0.6} color="#60a5fa" />

      {ELEMENT_ORDER.map((el, i) => (
        <ElementNode
          key={el}
          element={el}
          position={elementPosition(i)}
          strong={strongSet.has(el)}
          weak={weakSet.has(el)}
        />
      ))}

      {generate.map((g, i) => (
        <FlowArrow
          key={`gen-${g.from}-${g.to}-${i}`}
          from={g.from}
          to={g.to}
          kind="generate"
        />
      ))}
      {control.map((c, i) => (
        <FlowArrow
          key={`ctl-${c.from}-${c.to}-${i}`}
          from={c.from}
          to={c.to}
          kind="control"
        />
      ))}

      <OrbitControls
        enablePan={false}
        minDistance={4}
        maxDistance={9}
        autoRotate
        autoRotateSpeed={0.35}
      />
    </>
  );
}

export interface SajuEnergyFlow3DProps {
  energy: EnergyFlow;
  className?: string;
}

export default function SajuEnergyFlow3D({
  energy,
  className = "",
}: SajuEnergyFlow3DProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-white/10 bg-black ${className}`}
    >
      <Canvas
        camera={{ position: [0, 3.2, 6.2], fov: 42 }}
        shadows
        className="!h-full min-h-[280px] w-full"
        style={{ height: "100%", minHeight: 280 }}
      >
        <Suspense fallback={null}>
          <EnergyScene energy={energy} />
        </Suspense>
      </Canvas>
      <div className="pointer-events-none absolute bottom-2 left-0 right-0 flex justify-center gap-4 text-[10px] text-slate-400">
        <span className="text-emerald-400/90">● 생(生)</span>
        <span className="text-rose-400/80">● 극(剋)</span>
      </div>
    </div>
  );
}
