import { existsSync } from "node:fs";
import path from "node:path";

/** The monorepo root: the first ancestor of the Next.js cwd that holds eval/run.py. */
export function repoRoot(): string | null {
  let dir = process.cwd();
  for (;;) {
    if (existsSync(path.join(dir, "eval", "run.py"))) return dir;
    const up = path.dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
}

export const historyFile = (root: string) => path.join(root, "eval", "history", "runs.jsonl");
