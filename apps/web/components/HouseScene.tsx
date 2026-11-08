"use client";
// The Blender-built house (web/blender/house.py). Component sizes switch named nodes on and off.
import { Canvas, type ThreeEvent, useFrame, useThree } from "@react-three/fiber";
import { Environment, Html, Lightformer, OrbitControls, PerspectiveCamera, useGLTF } from "@react-three/drei";
import { useReducedMotion } from "motion/react";
import { Suspense, useEffect, useMemo, useRef, type RefObject } from "react";
import { Box3, type BufferGeometry, Color, type Material, type Mesh, type MeshStandardMaterial, type Object3D, Vector3 } from "three";
import { TARGETS, type Target, type Values } from "@/lib/api";
import { LABEL, num, PANEL_KWP, UNIT } from "@/lib/copy";

const URL = "/models/house.glb";
const MAX_PANELS = 24; // slots on the east roof face, around its skylights
const BATTERY_KWH = 5; // one stacked module per started 5 kWh, up to 5
const TARGET: [number, number, number] = [0.5, 2.6, -0.5];

// Narrow (taller) views back the camera off so the whole house stays in frame. Resizing resets the orbit.
function Camera() {
  const aspect = useThree((s) => s.size.width / s.size.height);
  const d = 1.08 * Math.max(1, 1.45 / aspect);
  // From the front right: the street side, the solar roof and the heat pump wall are all in view.
  const position: [number, number, number] = [TARGET[0] + 16.5 * d, TARGET[1] + 11.4 * d, TARGET[2] + 27.5 * d];
  return <PerspectiveCamera makeDefault position={position} fov={30} near={0.5} far={200} />;
}

export type Existing = { pv_kwp: number; battery_kwh: number; wallbox: boolean };

export type HouseProps = {
  values: Values;
  autoRotate?: boolean;
  modules?: number | null; // ours: the engine's PV module count; wins over kWp / PANEL_KWP
  hasEv: boolean;
  existing?: Existing; // already on the house: drawn in grey, before the proposed parts
  labels?: Partial<Record<Target, string>>; // overrides the default "PV 9 kWp" label text
  selected?: Target | null;
  onSelect?: (t: Target) => void; // markers and parts become clickable when set
};

const NONE: Existing = { pv_kwp: 0, battery_kwh: 0, wallbox: false };
const HIGHLIGHT = new Color("#2E9E6B");
const GREY = new Color("#A7ACB3");

// Which proposal a clicked part belongs to, by its node name (see web/blender/house.py).
function targetOf(o: Object3D | null): Target | null {
  for (; o; o = o.parent) {
    if (o.name.startsWith("PV_Panel_")) return "pv_kwp";
    if (o.name.startsWith("Battery_")) return "battery_kwh";
    if (o.name === "HeatPump") return "heat_pump_kw";
    if (o.name === "Wallbox") return "wallbox_kw";
  }
  return null;
}

type Part = { o: Object3D; on: boolean; old?: boolean };

function House({ values, modules, hasEv, /* ours: modules */ existing = NONE, labels, selected = null, onSelect, overlay }: HouseProps & { overlay: RefObject<HTMLDivElement | null> }) {
  const { scene } = useGLTF(URL, false, false); // no Draco/Meshopt: nothing is fetched from a CDN
  const invalidate = useThree((s) => s.invalidate);
  const still = useReducedMotion() ?? false;

  const nodes = useMemo(() => {
    scene.updateMatrixWorld(true);
    const get = (name: string) => {
      const o = scene.getObjectByName(name);
      if (!o) throw new Error(`house.glb is missing node ${name}; re-export web/blender/house.py`);
      // Measured once, at full size: hidden parts are scaled to 0 later, and labels still need their place.
      o.userData.box = new Box3().setFromObject(o);
      return o;
    };
    const range = (n: number, f: (i: number) => string) => Array.from({ length: n }, (_, i) => get(f(i + 1)));
    const groups = {
      pv_kwp: range(MAX_PANELS, (i) => `PV_Panel_${String(i).padStart(2, "0")}`),
      battery_kwh: range(5, (i) => `Battery_${i}`),
      heat_pump_kw: [get("HeatPump")],
      wallbox_kw: [get("Wallbox")],
    } satisfies Record<Target, Object3D[]>;
    // Each proposal gets its own copy of every material it uses, so lighting one up leaves the others alone.
    // The grey copy marks equipment the home already has.
    for (const t of TARGETS) {
      const copies = new Map<Material, Material>();
      for (const g of groups[t]) {
        g.traverse((o) => {
          const m = o as Mesh<BufferGeometry, MeshStandardMaterial>;
          if (!m.isMesh) return;
          if (!copies.has(m.material)) copies.set(m.material, m.material.clone());
          const own = copies.get(m.material) as MeshStandardMaterial;
          const grey = own.clone();
          grey.color.lerp(GREY, 0.75);
          m.userData.own = own;
          m.userData.grey = grey;
          m.material = own;
        });
      }
    }
    scene.traverse((o) => {
      if ((o as Mesh).isMesh) o.castShadow = o.receiveShadow = true;
    });
    return { ...groups, fan: get("HeatPump_Fan"), car: get("Car") };
  }, [scene]);

  // ponytail: one roof face holds 24 panels (10.8 kWp); larger systems are shown full, the label keeps the real size.
  const pvOld = Math.min(MAX_PANELS, Math.round(existing.pv_kwp / PANEL_KWP));
  const pvNew = Math.min(MAX_PANELS - pvOld, values.pv_kwp > 0 && modules ? modules : Math.round(values.pv_kwp / PANEL_KWP)); // ours: modules
  const batOld = Math.min(5, Math.ceil(existing.battery_kwh / BATTERY_KWH));
  const batNew = Math.min(5 - batOld, Math.ceil(values.battery_kwh / BATTERY_KWH));
  const wbOld = existing.wallbox && values.wallbox_kw === 0;
  const items = useMemo<Part[]>(
    () => [
      ...nodes.pv_kwp.map((o, i) => ({ o, on: i < pvOld + pvNew, old: i < pvOld })),
      ...nodes.battery_kwh.map((o, i) => ({ o, on: i < batOld + batNew, old: i < batOld })),
      { o: nodes.heat_pump_kw[0], on: values.heat_pump_kw > 0 },
      { o: nodes.wallbox_kw[0], on: values.wallbox_kw > 0 || existing.wallbox, old: wbOld },
      { o: nodes.car, on: hasEv || values.wallbox_kw > 0 || existing.wallbox },
    ],
    [nodes, pvOld, pvNew, batOld, batNew, values.heat_pump_kw, values.wallbox_kw, existing.wallbox, wbOld, hasEv],
  );

  // Grey for what exists, a warm glow on the selected proposal.
  useEffect(() => {
    for (const { o, old } of items) {
      const lit = selected !== null && !old && targetOf(o) === selected;
      o.traverse((c) => {
        const m = c as Mesh;
        if (!m.isMesh || !m.userData.own) return;
        const mat = (old ? m.userData.grey : m.userData.own) as MeshStandardMaterial;
        mat.emissive.copy(lit ? HIGHLIGHT : BLACK);
        mat.emissiveIntensity = lit ? 0.45 : 0;
        m.material = mat;
      });
    }
    invalidate();
  }, [items, selected, invalidate]);

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
    if (nodes.heat_pump_kw[0].visible && !still) {
      nodes.fan.rotateY(dt * 6);
      moving = true;
    }
    if (moving) invalidate();
  });

  // A label sits just above the parts it names, wherever the Blender script put them.
  // Solar sits on the roof: its label goes on the panels rather than floating above the ridge.
  const anchor = (t: Target, os: Object3D[]): [number, number, number] => {
    const b = new Box3();
    os.forEach((o) => b.union(o.userData.box as Box3));
    const c = b.getCenter(new Vector3());
    return [c.x, t === "pv_kwp" ? c.y : b.max.y + 0.25, c.z];
  };
  const markers: { key: string; t: Target; at: [number, number, number]; text: string; old?: boolean }[] = [];
  for (const t of TARGETS) {
    const shown = items.filter((p) => p.on && !p.old && targetOf(p.o) === t).map((p) => p.o);
    const was = items.filter((p) => p.on && p.old && targetOf(p.o) === t).map((p) => p.o);
    if (values[t] > 0 && shown.length) {
      markers.push({ key: t, t, at: anchor(t, shown), text: labels?.[t] ?? `${LABEL[t]} ${num(values[t])} ${UNIT[t]}` });
    }
    if (was.length) {
      const text = t === "pv_kwp" ? `Existing PV ${num(existing.pv_kwp)} kWp` : t === "battery_kwh" ? `Existing battery ${num(existing.battery_kwh)} kWh` : `Existing ${LABEL[t].toLowerCase()}`;
      markers.push({ key: `old-${t}`, t, at: anchor(t, was), text, old: true });
    }
  }

  return (
    <>
      <primitive
        object={scene}
        onClick={
          onSelect &&
          ((e: ThreeEvent<MouseEvent>) => {
            const t = targetOf(e.object);
            if (t && values[t] > 0) {
              e.stopPropagation();
              onSelect(t);
            }
          })
        }
      />
      {markers.map((m) => (
        // A fixed portal: without it Html re-targets once R3F connects events, and the remount can wipe the label.
        <Html key={m.key} portal={overlay as RefObject<HTMLElement>} position={m.at} center zIndexRange={[20, 0]}>
          {onSelect && !m.old ? (
            <button
              type="button"
              aria-pressed={selected === m.t}
              onClick={() => onSelect(m.t)}
              className={`${CHIP} cursor-pointer hover:ring-zinc-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 aria-pressed:bg-ink aria-pressed:text-paper aria-pressed:ring-ink`}
            >
              {m.text}
            </button>
          ) : (
            <span className={`${CHIP} pointer-events-none ${m.old ? "bg-sand text-quiet" : ""}`}>{m.text}</span>
          )}
        </Html>
      ))}
    </>
  );
}

const CHIP = "block whitespace-nowrap rounded-full bg-paper/95 px-2.5 py-1 text-xs font-medium text-ink shadow-sm ring-1 ring-zinc-200";
const BLACK = new Color(0, 0, 0);

useGLTF.preload(URL, false, false);

export default function HouseScene(props: HouseProps & { description: string }) {
  const { description, autoRotate = false, ...house } = props;
  const still = useReducedMotion() ?? false;
  const overlay = useRef<HTMLDivElement>(null);
  return (
    <div ref={overlay} className="relative h-full w-full">
      <p className="sr-only">{description}</p>
      <Canvas aria-hidden shadows frameloop="demand" dpr={[1, 2]}>
        <Camera />
        <hemisphereLight args={["#ffffff", "#e9e4d6", 1.1]} />
        <directionalLight
          position={[14, 24, 18]} // front right, so the solar roof faces the light
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
          autoRotate={autoRotate && !still}
          autoRotateSpeed={0.45}
          enablePan={false}
          minDistance={20}
          maxDistance={55}
          minPolarAngle={0.5}
          maxPolarAngle={1.38}
          makeDefault
        />
      </Canvas>
    </div>
  );
}
