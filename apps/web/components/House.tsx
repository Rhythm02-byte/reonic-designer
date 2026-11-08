"use client";
// WebGL only exists in the browser, so the scene is never rendered on the server.
import dynamic from "next/dynamic";
import { Component, type ComponentProps, type ReactNode } from "react";
import { TARGETS } from "@/lib/api";
import { LABEL, num, UNIT } from "@/lib/copy";

const Scene = dynamic(() => import("./HouseScene"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse rounded-2xl bg-sand" aria-label="Loading the 3D house" />,
});

// Without WebGL (GPU blocklisted, disabled in settings) the canvas throws; the numbers next to it must keep working.
class NoWebGL extends Component<{ fallback: ReactNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

export function House(props: ComponentProps<typeof Scene>) {
  return (
    <NoWebGL
      // A corrected/generated model deserves a fresh error boundary. Without
      // this, one transient GLB error leaves the fallback stuck on screen.
      key={props.modelUrl ?? "demo-house"}
      fallback={
        <div className="grid h-full place-items-center p-6 text-sm text-body">
          <div className="w-full max-w-xs space-y-3">
            <ul className="divide-y divide-zinc-200 rounded-xl bg-white ring-1 ring-zinc-200">
              {TARGETS.map((t) => (
                <li key={t} className="flex justify-between gap-3 px-3 py-2">
                  <span className="text-ink">{LABEL[t]}</span>
                  <span className="tabular-nums">{props.values[t] > 0 ? `${num(props.values[t])} ${UNIT[t]}` : "Not included"}</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-muted">The 3D view could not load. Check WebGL or try reloading this house model.</p>
          </div>
        </div>
      }
    >
      <Scene {...props} />
    </NoWebGL>
  );
}
