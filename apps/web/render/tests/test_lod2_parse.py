from pathlib import Path

from render.lod2_parse import find_building_at

_GML = """<?xml version="1.0" encoding="UTF-8"?>
<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0" xmlns:bldg="http://www.opengis.net/citygml/building/2.0" xmlns:gml="http://www.opengis.net/gml">
  <core:cityObjectMember>
    <bldg:Building gml:id="BLDG_1">
      <bldg:boundedBy>
        <bldg:GroundSurface>
          <bldg:lod2MultiSurface>
            <gml:MultiSurface>
              <gml:surfaceMember>
                <gml:Polygon>
                  <gml:exterior>
                    <gml:LinearRing>
                      <gml:posList srsDimension="3">100 100 50 110 100 50 110 110 50 100 110 50 100 100 50</gml:posList>
                    </gml:LinearRing>
                  </gml:exterior>
                </gml:Polygon>
              </gml:surfaceMember>
            </gml:MultiSurface>
          </bldg:lod2MultiSurface>
        </bldg:GroundSurface>
      </bldg:boundedBy>
      <bldg:boundedBy>
        <bldg:WallSurface>
          <bldg:lod2MultiSurface>
            <gml:MultiSurface>
              <gml:surfaceMember>
                <gml:Polygon>
                  <gml:exterior>
                    <gml:LinearRing>
                      <gml:posList srsDimension="3">100 100 50 110 100 50 110 100 55 100 100 55 100 100 50</gml:posList>
                    </gml:LinearRing>
                  </gml:exterior>
                </gml:Polygon>
              </gml:surfaceMember>
            </gml:MultiSurface>
          </bldg:lod2MultiSurface>
        </bldg:WallSurface>
      </bldg:boundedBy>
      <bldg:boundedBy>
        <bldg:RoofSurface>
          <bldg:lod2MultiSurface>
            <gml:MultiSurface>
              <gml:surfaceMember>
                <gml:Polygon>
                  <gml:exterior>
                    <gml:LinearRing>
                      <gml:posList srsDimension="3">100 100 55 110 100 55 110 110 55 100 110 55 100 100 55</gml:posList>
                    </gml:LinearRing>
                  </gml:exterior>
                </gml:Polygon>
              </gml:surfaceMember>
            </gml:MultiSurface>
          </bldg:lod2MultiSurface>
        </bldg:RoofSurface>
      </bldg:boundedBy>
    </bldg:Building>
  </core:cityObjectMember>
</core:CityModel>
"""


def _fixture(tmp_path: Path) -> Path:
    path = tmp_path / "fixture.gml"
    path.write_text(_GML)
    return path


def test_finds_building_containing_point(tmp_path: Path):
    geometry = find_building_at(_fixture(tmp_path), 105, 105)
    assert geometry is not None
    assert len(geometry.footprint) == 4
    assert len(geometry.walls) == 1
    assert len(geometry.roofs) == 1
    # local frame: origin at footprint centroid (105, 105), ground z (50) subtracted
    assert (-5.0, -5.0, 0.0) in geometry.footprint
    assert (5.0, 5.0, 0.0) in geometry.footprint


def test_returns_none_outside_any_footprint(tmp_path: Path):
    assert find_building_at(_fixture(tmp_path), 500, 500) is None
