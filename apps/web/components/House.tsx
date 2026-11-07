"use client";
// WebGL only exists in the browser, so the scene is never rendered on the server.
import dynamic from "next/dynamic";
import { Component, type ComponentProps, type ReactNode } from "react";

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
      fallback={
        <div className="grid h-full place-items-center p-6 text-center text-sm text-body">
          <p className="max-w-sm">
            {props.description}
            <span className="mt-1 block text-xs text-muted">The 3D view needs WebGL, which this browser has turned off.</span>
          </p>
        </div>
      }
    >
      <Scene {...props} />
    </NoWebGL>
  );
}
