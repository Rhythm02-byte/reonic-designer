# Home Energy Designer: web frontend

Next.js app with the planner view (`/`) and the homeowner view (`/offer#…`). Every number comes from the Python
API in `src/reonic/api.py`; this app only shows it.

```bash
# from the repo root: the JSON API, local only
PYTHONPATH=src .venv/bin/uvicorn reonic.api:app --host 127.0.0.1 --port 8000

# here
pnpm install
pnpm dev            # http://localhost:3000, /api/* is proxied to 127.0.0.1:8000 (next.config.ts)
pnpm lint && pnpm build
```

- **3D house:** `public/models/house.glb`, built in Blender from a bought TurboSquid model (`3D_house10.blend`).
  Only the GLB is committed; the `.blend` stays out of the repo (licence). To rebuild it:
  `blender -b /path/to/3D_house10.blend --python blender/house.py`. `components/HouseScene.tsx` shows and hides its
  named nodes (`PV_Panel_01…24`, `Battery_1…5`, `HeatPump`, `Wallbox`, `Car`). Without WebGL the page falls back to text.
- **Share link:** the offer (home inputs, recommendation, allowed options) travels in the URL hash, so it never
  reaches a server log. It carries the home's data: share it only with that customer.
- **Not deployed:** the API reads the Reonic data and model, which stay with the team.
