"use client";
// The Blender-built house (web/blender/house.py). Component sizes switch named nodes on and off.
import { Canvas, useFrame, useThree, type ThreeEvent } from "@react-three/fiber";
import { Environment, Html, Lightformer, OrbitControls, PerspectiveCamera, useGLTF } from "@react-three/drei";
import { useReducedMotion } from "motion/react";
import { Suspense, useEffect, useMemo, useRef, type RefObject } from "react";
import type { Mesh, Object3D } from "three";
import type { Target, Values } from "@/lib/api";
import { LABEL, num, PANEL_KWP, UNIT } from "@/lib/copy";

const URL = "/models/house.glb";
const MAX_PANELS = 30;
const BATTERY_KWH = 5; // one stacked module per started 5 kWh, up to 5
const SIDE = {
  center: "-translate-x-1/2 -translate-y-1/2",
  above: "-translate-x-1/2 -translate-y-[calc(100%+6px)]",
  left: "-translate-x-[calc(100%+8px)] -translate-y-1/2",
  right: "translate-x-2 -translate-y-1/2",
};
const TARGET: [number, number, number] = [-1.2, 2.6, 0];

// Narrow (taller) views back the camera off so the whole house stays in frame. Resizing resets the orbit.
function Camera() {
  const aspect = useThree((s) => s.size.width / s.size.height);
  const d = 1.08 * Math.max(1, 1.45 / aspect);
  const position: [number, number, number] = [TARGET[0] - 10.8 * d, TARGET[1] + 11.4 * d, TARGET[2] + 27 * d];
  return <PerspectiveCamera makeDefault position={position} fov={30} near={0.5} far={200} />;
}

export type HouseProps = {
  values: Values;
  hasEv: boolean;
  selected?: Target | null;
  onSelect?: (t: Target) => void;
  labels?: Partial<Record<Target, string>>; // overrides the default "Solar 9 kWp" label text
};

function targetOf(o: Object3D | null): Target | null {
  for (; o; o = o.parent) {
    if (o.name.startsWith("PV_Panel")) return "pv_kwp";
    if (/^Battery_\d$/.test(o.name)) return "battery_kwh";
    if (o.name === "HeatPump") return "heat_pump_kw";
    if (o.name === "Wallbox") return "wallbox_kw";
  }
  return null;
}

function House({ values, hasEv, selected, onSelect, labels, overlay }: HouseProps & { overlay: RefObject<HTMLDivElement | null> }) {
  const { scene } = useGLTF(URL, false, false); // no Draco/Meshopt: nothing is fetched from a CDN
  const invalidate = useThree((s) => s.invalidate);
  const still = useReducedMotion() ?? false;

  const nodes = useMemo(() => {
    scene.traverse((o) => {
      if ((o as Mesh).isMesh) o.castShadow = o.receiveShadow = true;
    });
    const get = (name: string) => {
      const o = scene.getObjectByName(name);
      if (!o) throw new Error(`house.glb is missing node ${name}; re-export web/blender/house.py`);
      return o;
    };
    const range = (n: number, f: (i: number) => string) => Array.from({ length: n }, (_, i) => get(f(i + 1)));
    return {
      pv: range(MAX_PANELS, (i) => `PV_Panel_${String(i).padStart(2, "0")}`),
      battery: range(5, (i) => `Battery_${i}`),
      heatPump: get("HeatPump"),
      fan: get("HeatPump_Fan"),
      wallbox: get("Wallbox"),
      car: get("Car"),
    };
  }, [scene]);

  // ponytail: one roof face holds 30 panels (13.5 kWp); larger systems are shown full, the label keeps the real size.
  const pvCount = Math.min(MAX_PANELS, Math.round(values.pv_kwp / PANEL_KWP));
  const batteryCount = Math.min(5, Math.ceil(values.battery_kwh / BATTERY_KWH));
  const items = useMemo(
    () => [
      ...nodes.pv.map((o, i) => ({ o, on: i < pvCount })),
      ...nodes.battery.map((o, i) => ({ o, on: i < batteryCount })),
      { o: nodes.heatPump, on: values.heat_pump_kw > 0 },
      { o: nodes.wallbox, on: values.wallbox_kw > 0 },
      { o: nodes.car, on: hasEv || values.wallbox_kw > 0 },
    ],
    [nodes, pvCount, batteryCount, values.heat_pump_kw, values.wallbox_kw, hasEv],
  );

  // Whatever changes pops in (or out) one after another, 25 ms apart.
  // The scene graph is mutated through a ref: three.js objects are mutable by design, React state is not.
  const live = useRef(items);
  const changedAt = useRef<number | null>(null);
  const delays = useRef(new Map<Object3D, number>());
  useEffect(() => {
    live.current = items;
    const instant = changedAt.current === null || still;
    let k = 0;
    for (const { o, on } of live.current) {
      if (instant) {
        o.scale.setScalar(on ? 1 : 0);
        o.visible = on;
      } else if (o.scale.x !== (on ? 1 : 0)) delays.current.set(o, k++ * 0.025);
    }
    changedAt.current = performance.now() / 1000;
    invalidate();
  }, [items, still, invalidate]);

  useFrame((_, dt) => {
    const since = performance.now() / 1000 - (changedAt.current ?? 0);
    let moving = false;
    for (const { o, on } of live.current) {
      const target = on ? 1 : 0;
      if (o.scale.x === target) continue;
      moving = true;
      if (since < (delays.current.get(o) ?? 0)) continue;
      const next = o.scale.x + (target - o.scale.x) * Math.min(1, dt * 10);
      o.scale.setScalar(Math.abs(next - target) < 0.005 ? target : next);
      // eslint-disable-next-line react-hooks/immutability -- per-frame three.js mutation is how R3F animates
      o.visible = o.scale.x > 0;
    }
    if (nodes.heatPump.visible && !still) {
      nodes.fan.rotateY(dt * 6);
      moving = true;
    }
    if (moving) invalidate();
  });

  const pick = (e: ThreeEvent<MouseEvent>) => {
    const t = targetOf(e.object);
    if (!t || !onSelect) return;
    e.stopPropagation();
    onSelect(t);
  };
  const hover = (on: boolean) => (e: ThreeEvent<PointerEvent>) => {
    if (onSelect && targetOf(e.object)) document.body.style.cursor = on ? "pointer" : "";
  };

  // Where each label sits (three.js coords: x east, y up, z south) and which side of that point it hangs on.
  const anchors: Record<Target, { at: [number, number, number]; side: keyof typeof SIDE }> = {
    pv_kwp: { at: [0, 7.5, 2.3], side: "center" },
    // Above the stack, not beside it: to the left it lands on the car and reads as the car's battery.
    battery_kwh: { at: [-5.3, 0.3 + 0.4 * batteryCount, 4.65], side: "above" },
    heat_pump_kw: { at: [5.1, 1.15, 5.25], side: "above" },
    wallbox_kw: { at: [-4.05, 1.0, 4.65], side: "right" },
  };

  return (
    <>
      <primitive object={scene} onClick={pick} onPointerOver={hover(true)} onPointerOut={hover(false)} />
      {(Object.keys(anchors) as Target[])
        .filter((t) => values[t] > 0)
        .map((t) => (
          // A fixed portal: without it Html re-targets once R3F connects events, and the remount can wipe the label.
          <Html key={t} portal={overlay as RefObject<HTMLElement>} position={anchors[t].at} zIndexRange={[20, 0]}>
            <button
              type="button"
              tabIndex={-1} // the component cards are the keyboard path; these pills mirror them
              aria-hidden
              onClick={() => onSelect?.(t)}
              className={`${SIDE[anchors[t].side]} block whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-medium shadow-sm ring-1 transition-colors ${
                selected === t ? "bg-ink text-paper ring-ink" : "bg-paper/95 text-ink ring-zinc-200 hover:bg-white"
              } ${onSelect ? "cursor-pointer" : "pointer-events-none"}`}
            >
              {labels?.[t] ?? `${LABEL[t]} ${num(values[t])} ${UNIT[t]}`}
            </button>
          </Html>
        ))}
    </>
  );
}

useGLTF.preload(URL, false, false);

export default function HouseScene(props: HouseProps & { description: string }) {
  const { description, ...house } = props;
  const overlay = useRef<HTMLDivElement>(null);
  return (
    <div ref={overlay} role="img" aria-label={description} className="relative h-full w-full">
      <Canvas
        shadows
        frameloop="demand"
        dpr={[1, 2]}
        onPointerMissed={() => (document.body.style.cursor = "")}
      >
        <Camera />
        <hemisphereLight args={["#ffffff", "#e9e4d6", 1.1]} />
        <directionalLight
          position={[-14, 24, 18]}
          intensity={2.2}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-18}
          shadow-camera-right={18}
          shadow-camera-top={18}
          shadow-camera-bottom={-18}
          shadow-bias={-0.0004}
        />
        <Environment resolution={128}>
          <Lightformer form="rect" intensity={2} position={[0, 10, 10]} scale={[20, 6, 1]} />
          <Lightformer form="rect" intensity={0.8} position={[-10, 4, -6]} scale={[10, 4, 1]} />
        </Environment>
        <Suspense fallback={null}>
          <House {...house} overlay={overlay} />
        </Suspense>
        <OrbitControls
          target={TARGET}
          enablePan={false}
          minDistance={18}
          maxDistance={48}
          minPolarAngle={0.5}
          maxPolarAngle={1.38}
          makeDefault
        />
      </Canvas>
    </div>
  );
}
