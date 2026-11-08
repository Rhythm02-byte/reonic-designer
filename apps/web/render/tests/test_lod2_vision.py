from render.lod2_vision import FALLBACK, HouseStyle, _validate


def test_missing_input_falls_back():
    assert _validate(None) == HouseStyle()


def test_bad_values_are_clamped_to_fallback():
    bad = _validate({
        "roof_material": "lava", "roof_color_hex": "nope", "wall_color_hex": "also-nope",
        "window_width_m": 99, "window_height_m": -1, "window_spacing_m": 0.1,
        "sill_height_m": 50, "floor_height_m": 1, "confidence": 2,
    })
    assert bad == HouseStyle()


def test_good_values_pass_through():
    good = _validate({**FALLBACK, "roof_material": "metal", "roof_color_hex": "#445566", "confidence": 0.8})
    assert good.roof_material == "metal"
    assert good.roof_color_hex == "#445566"
    assert good.confidence == 0.8


def test_spacing_never_shrinks_below_window_width():
    narrow_spacing = _validate({**FALLBACK, "window_width_m": 2.0, "window_spacing_m": 2.0})
    assert narrow_spacing.window_spacing_m >= narrow_spacing.window_width_m + 0.3
