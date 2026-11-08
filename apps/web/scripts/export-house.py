"""Local, bounded address-to-GLB worker. Upstream geometry and downloaded tiles stay in ignored cache."""
from __future__ import annotations
import importlib, json, math, os, pathlib, shutil, subprocess, sys, time, types

job_dir, exporter, lat, lng, node = sys.argv[1:]
job_dir, exporter = pathlib.Path(job_dir).resolve(), pathlib.Path(exporter).resolve()
lat, lng = float(lat), float(lng)
state_path = job_dir / 'job.json'
job = json.loads(state_path.read_text('utf-8'))
job['pid'] = os.getpid()

def update(stage, **changes):
    job.update(stage=stage, updatedAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **changes)
    temp = state_path.with_suffix('.tmp')
    temp.write_text(json.dumps(job), encoding='utf-8')
    os.replace(temp, state_path)

def run(command, cwd, timeout):
    kw = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
    proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', **kw)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            import signal
            os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise RuntimeError('House import exceeded its time limit. Retry a smaller area or use the fallback.')
    if proc.returncode:
        (job_dir / 'worker-error.log').write_text(out[-8000:], encoding='utf-8')
        raise RuntimeError('The house exporter could not finish. Coverage or the upstream service may be unavailable; the fallback remains usable.')
    return out

try:
    update('Downloading the building and nearby roof context')
    delta_lat = 45 / 111320
    delta_lng = delta_lat / max(0.1, math.cos(math.radians(lat)))
    bbox = f'{lat-delta_lat:.9f},{lng-delta_lng:.9f},{lat+delta_lat:.9f},{lng+delta_lng:.9f}'
    script = exporter / 'google_map_export_bridge/exporter/earth-export.cjs'
    out = run([node, str(script), '--bbox='+bbox, '--level=20'], job_dir, 240)
    directory = None
    for line in out.splitlines():
        if line.startswith('GMEB::done '): directory = pathlib.Path(json.loads(line.split(' ', 1)[1])['dir'])
    if directory is None: raise RuntimeError('No 3D geometry returned for this location.')
    if not directory.is_absolute(): directory = job_dir / directory
    directory = directory.resolve()
    if not directory.is_relative_to(job_dir): raise RuntimeError('Unexpected exporter output path.')
    update('Converting globe coordinates into a metre-scale roof model')
    # Load only upstream pure-Python georeferencing modules; do not install or activate a Blender add-on.
    pkg = types.ModuleType('roof_export_dependency')
    pkg.__path__ = [str(exporter / 'google_map_export_bridge')]
    sys.modules[pkg.__name__] = pkg
    transform = importlib.import_module('roof_export_dependency.obj_transform')
    report = transform.transform_obj(str(directory / 'model.obj'), level_ground=False, requested_level=20)
    if report.coverage == 'flat' or report.relief_m < 2:
        raise RuntimeError('Only flat imagery was returned for this address. Use the fallback or a manually measured roof.')
    bpy_candidates = [os.environ.get('BLENDER_PATH'), shutil.which('blender'), '/Applications/Blender.app/Contents/MacOS/Blender']
    if os.name == 'nt':
        for version in ['Blender 4.3', 'Blender 5.2']:
            bpy_candidates.append(str(pathlib.Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Blender Foundation' / version / 'blender.exe'))
    blender = next((p for p in bpy_candidates if p and pathlib.Path(p).is_file()), None)
    if not blender: raise RuntimeError('Blender was not found. Set BLENDER_PATH to its executable, then retry.')
    revision = subprocess.run(['git', '-C', str(exporter), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    update('Packaging textures and the real house for the 3D viewer')
    converter = pathlib.Path(__file__).with_name('house-to-glb.py')
    run([blender, '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(converter), '--', report.output_path, str(job_dir / 'house.glb')], job_dir, 120)
    if not (job_dir / 'house.glb').is_file() or (job_dir / 'house.glb').stat().st_size > 50_000_000:
        raise RuntimeError('The exported scene is unavailable or too large for the demo viewer.')
    geometry = json.loads((job_dir / 'geometry.json').read_text())
    update('Ready: confirm the roof before using its panel capacity', state='ready', origin={'lat': report.latitude, 'lng': report.longitude},
           modelUrl=f"/api/real-house/{job['id']}/model", triangles=geometry['triangles'], exporterRevision=revision)
except Exception as exc:
    update('Import unavailable; the fallback house is still available', state='failed', error=str(exc)[:500])
    sys.exit(1)
