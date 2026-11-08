import json
from pathlib import Path

import pytest

from render import house_render
from render.lod2_parse import BuildingGeometry


def test_coordinates_validate_the_map_payload():
    assert house_render.coordinates({"lat": 48.1351, "lng": 11.582}) == (48.1351, 11.582)
    with pytest.raises(house_render.HouseRenderError):
        house_render.coordinates({"lat": float("nan"), "lng": 11.582})
    with pytest.raises(house_render.HouseRenderError):
        house_render.coordinates({"lat": 91, "lng": 11.582})


def test_render_uses_cached_glb_without_fetching(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(house_render, "CACHE_DIR", tmp_path)
    key = house_render.cache_key(48.1351, 11.582)
    (tmp_path / f"{key}.glb").write_bytes(b"glTF")
    expected = {"id": key, "url": f"/api/house/{key}.glb", "panels": 16, "source": "Bavaria LoD2"}
    (tmp_path / f"{key}.json").write_text(json.dumps(expected))
    monkeypatch.setattr(house_render, "fetch_tile", lambda *_: pytest.fail("cache should avoid a tile download"))
    assert house_render.render(48.1351, 11.582) == expected
    assert house_render.model_path(key) == tmp_path / f"{key}.glb"
    assert house_render.model_path("../secret") is None


def test_render_passes_local_geometry_to_blender(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(house_render, "CACHE_DIR", tmp_path)
    geometry = BuildingGeometry(
        footprint=[(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
        walls=[[(-1, -1, 0), (1, -1, 0), (1, -1, 3), (-1, -1, 3)]],
        roofs=[[(-1, -1, 3), (1, -1, 3), (1, 1, 3), (-1, 1, 3)]],
    )
    monkeypatch.setattr(house_render, "fetch_tile", lambda *_: tmp_path / "tile.gml")
    monkeypatch.setattr(house_render, "find_building_at", lambda *_: geometry)

    def fake_blender(args, **_kwargs):
        source, output = Path(args[-2]), Path(args[-1])
        assert json.loads(source.read_text())["roofs"] == [[[ -1, -1, 3], [1, -1, 3], [1, 1, 3], [-1, 1, 3]]]
        output.write_bytes(b"glTF")
        return type("Done", (), {"stdout": "{'panels': 16}"})()

    monkeypatch.setattr(house_render.subprocess, "run", fake_blender)
    result = house_render.render(48.1351, 11.582)
    assert result["panels"] == 16
    assert (tmp_path / f"{result['id']}.glb").read_bytes() == b"glTF"
