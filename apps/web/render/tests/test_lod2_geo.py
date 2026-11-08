from render.lod2_fetch import in_schleswig_holstein_bbox, sh_tile_filename, sh_tile_url
from render.lod2_geo import in_bavaria_bbox, tile_filename, tile_id, wgs84_to_utm32


def test_projection_matches_bavaria_wms_grid():
    # Verified live against https://geoservices.bayern.de/od/wms/grid/v1/opendatagrid (Munich, near Marienplatz):
    # that point resolves to tile 690_5334.gml.
    e, n = wgs84_to_utm32(48.134, 11.5776)
    assert tile_filename(*tile_id(e, n)) == "690_5334.gml"


def test_bavaria_bbox():
    assert in_bavaria_bbox(48.1351, 11.582)  # Munich
    assert not in_bavaria_bbox(52.52, 13.405)  # Berlin
    assert not in_bavaria_bbox(53.55, 9.99)  # Hamburg


def test_tile_id_is_lower_left_of_2km_cell():
    assert tile_id(690001, 5333999) == (690, 5332)
    assert tile_id(691999, 5334000) == (690, 5334)


def test_schleswig_holstein_tiles_follow_official_open_gbd_naming():
    # Kiel, verified against the LVermGeo SH LoD2 mass-download index.
    easting, northing = wgs84_to_utm32(54.3233, 10.1228)
    assert sh_tile_filename(easting, northing) == "LoD2_32_573_6020_1_SH.xml"
    assert "file=LoD2_32_573_6020_1_SH.xml" in sh_tile_url(easting, northing)
    assert "km=32570_6020" in sh_tile_url(easting, northing)


def test_schleswig_holstein_coverage_gate():
    assert in_schleswig_holstein_bbox(54.3233, 10.1228)  # Kiel
    assert not in_schleswig_holstein_bbox(52.52, 13.405)  # Berlin
