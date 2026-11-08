"""Background worker for lib/lod2-jobs.ts: render-lod2-house.py <job-dir> <lat> <lng>."""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # apps/web, so the `render` package imports
from render import house_render  # noqa: E402


def update(status: Path, **fields) -> None:
    job = json.loads(status.read_text())
    status.write_text(json.dumps({**job, **fields, "updatedAt": datetime.now(timezone.utc).isoformat()}))


def main() -> int:
    job_dir, lat, lng = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
    status = job_dir / "job.json"
    update(status, pid=os.getpid(), stage="Building LoD2 house")
    try:
        result = house_render.render(lat, lng)
        shutil.copyfile(house_render.CACHE_DIR / f"{result['id']}.glb", job_dir / "house.glb")
    except house_render.HouseRenderError as exc:
        update(status, state="failed", error=str(exc))
        return 1
    except Exception as exc:  # never leak a traceback to the UI
        print(f"render-lod2-house.py: {exc!r}", file=sys.stderr)
        update(status, state="failed", error="The LoD2 render failed.")
        return 1
    update(status, state="ready", stage="Ready", panels=result.get("panels"), source=result.get("source"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
