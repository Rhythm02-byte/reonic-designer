// Optional haptics (web-haptics): nudge on a step snap, success on share, error on a red flag.
// Progressive enhancement: it loads lazily, only after a user gesture has asked for it, and every failure is silent.
import type { WebHaptics } from "web-haptics";

let instance: Promise<WebHaptics | null> | null = null;

function load() {
  instance ??= import("web-haptics").then(
    (m) => new m.WebHaptics(),
    () => null,
  );
  return instance;
}

export function haptic(kind: "nudge" | "success" | "error") {
  if (typeof window === "undefined" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  void load()
    .then((h) => h?.trigger(kind))
    .catch(() => {});
}
