"""Looks at real photos of a building and extracts the facade/roof style details LoD2
geometry can't carry (window grid, roof material, real colours), via Claude Sonnet 5
vision with a forced tool call so the shape is always valid.

Untrusted model output is a trust boundary: every field is clamped to a sane range in
`_validate` before it reaches the Blender script. A missing key, a disabled API, or a
low-confidence read all fall back to FALLBACK rather than failing the whole render --
a plausible generic German house beats no house.
"""
from __future__ import annotations

import base64
import os
import re
from dataclasses import dataclass, field

HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ROOF_MATERIALS = ("tile", "slate", "metal", "flat_membrane")

FALLBACK = {
    "roof_material": "tile", "roof_color_hex": "#9A6150", "wall_color_hex": "#F4F1EA",
    "window_width_m": 1.1, "window_height_m": 1.3, "window_spacing_m": 2.4,
    "sill_height_m": 0.9, "floor_height_m": 2.7, "confidence": 0.0,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "roof_material": {"type": "string", "enum": list(ROOF_MATERIALS)},
        "roof_color_hex": {"type": "string", "description": "dominant roof colour, e.g. #9A6150"},
        "wall_color_hex": {"type": "string", "description": "dominant facade/render colour, e.g. #F4F1EA"},
        "window_width_m": {"type": "number", "description": "typical window width in metres"},
        "window_height_m": {"type": "number", "description": "typical window height in metres"},
        "window_spacing_m": {"type": "number", "description": "centre-to-centre spacing between windows in metres"},
        "sill_height_m": {"type": "number", "description": "height of the window sill above ground in metres"},
        "floor_height_m": {"type": "number", "description": "storey height in metres (ground to next floor's sill row)"},
        "confidence": {"type": "number", "description": "0..1: how clearly the photos show these details"},
    },
    "required": list(FALLBACK),
    "additionalProperties": False,
}

TOOL = {
    "name": "describe_house_style",
    "description": "Record the building's roof material/colour and window grid as seen in the two photos.",
    "strict": True,
    "input_schema": SCHEMA,
}

PROMPT = (
    "The first image is a street-level photo of this building's facade; the second is a satellite "
    "crop of its roof. Determine: the roof's material (tile/slate/metal/flat_membrane) and dominant "
    "colour; the facade's dominant wall colour; and the repeating window grid (typical window width, "
    "height, centre-to-centre spacing, sill height above ground, and storey height). If a photo is "
    "missing the building, obstructed, or a grey 'no imagery' placeholder, say so via a low confidence "
    "rather than guessing. Call describe_house_style with your best reading."
)


@dataclass
class HouseStyle:
    roof_material: str = FALLBACK["roof_material"]
    roof_color_hex: str = FALLBACK["roof_color_hex"]
    wall_color_hex: str = FALLBACK["wall_color_hex"]
    window_width_m: float = FALLBACK["window_width_m"]
    window_height_m: float = FALLBACK["window_height_m"]
    window_spacing_m: float = FALLBACK["window_spacing_m"]
    sill_height_m: float = FALLBACK["sill_height_m"]
    floor_height_m: float = FALLBACK["floor_height_m"]
    confidence: float = field(default=0.0)


def _clamp(v, lo, hi, default):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) and lo <= v <= hi else default


def _validate(raw: dict) -> HouseStyle:
    """Trust boundary: the vision model's JSON is well-shaped (forced schema) but its *values* are
    still a guess, so every number is clamped to a range Blender can build a sane house from."""
    if not isinstance(raw, dict):
        return HouseStyle()
    hex_roof = raw.get("roof_color_hex")
    hex_wall = raw.get("wall_color_hex")
    style = HouseStyle(
        roof_material=raw.get("roof_material") if raw.get("roof_material") in ROOF_MATERIALS else FALLBACK["roof_material"],
        roof_color_hex=hex_roof if isinstance(hex_roof, str) and HEX_RE.match(hex_roof) else FALLBACK["roof_color_hex"],
        wall_color_hex=hex_wall if isinstance(hex_wall, str) and HEX_RE.match(hex_wall) else FALLBACK["wall_color_hex"],
        window_width_m=_clamp(raw.get("window_width_m"), 0.4, 3.0, FALLBACK["window_width_m"]),
        window_height_m=_clamp(raw.get("window_height_m"), 0.4, 3.0, FALLBACK["window_height_m"]),
        window_spacing_m=_clamp(raw.get("window_spacing_m"), 1.0, 8.0, FALLBACK["window_spacing_m"]),
        sill_height_m=_clamp(raw.get("sill_height_m"), 0.2, 2.0, FALLBACK["sill_height_m"]),
        floor_height_m=_clamp(raw.get("floor_height_m"), 2.0, 4.0, FALLBACK["floor_height_m"]),
        confidence=_clamp(raw.get("confidence"), 0.0, 1.0, 0.0),
    )
    # a window grid wider than its spacing would overlap -- keep spacing the generous one
    style.window_spacing_m = max(style.window_spacing_m, style.window_width_m + 0.3)
    return style


def analyze(facade_jpeg: bytes, aerial_jpeg: bytes) -> HouseStyle:
    """Calls Sonnet 5 vision; any failure or low-confidence read returns the FALLBACK style."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return HouseStyle()
    try:
        import anthropic
    except ImportError:
        return HouseStyle()

    def b64(data: bytes) -> str:
        return base64.standard_b64encode(data).decode()

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            tools=[TOOL],
            tool_choice={"type": "tool", "name": "describe_house_style"},
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(facade_jpeg)}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(aerial_jpeg)}},
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
    except anthropic.APIError:
        return HouseStyle()

    call = next((b for b in response.content if b.type == "tool_use"), None)
    style = _validate(call.input if call else None)
    # a hesitant read (placeholder photo, obstructed view, ...) is worth less than the plain default
    return style if style.confidence >= 0.4 else HouseStyle()


if __name__ == "__main__":
    import sys

    def demo():
        """ponytail self-check: schema-shaped garbage in, clamped-and-defaulted style out."""
        assert _validate(None) == HouseStyle()
        bad = _validate({"roof_material": "lava", "roof_color_hex": "nope", "window_width_m": 99,
                          "window_spacing_m": 0.1, "confidence": 0.9})
        assert bad.roof_material == "tile" and bad.roof_color_hex == FALLBACK["roof_color_hex"]
        assert bad.window_width_m == FALLBACK["window_width_m"] and bad.window_spacing_m >= bad.window_width_m + 0.3
        good = _validate({**FALLBACK, "roof_material": "metal", "roof_color_hex": "#445566", "confidence": 0.8})
        assert good.roof_material == "metal" and good.confidence == 0.8
        print("lod2_vision self-check passed")

    if len(sys.argv) == 1:
        demo()
    else:
        from pathlib import Path
        facade, aerial = Path(sys.argv[1]).read_bytes(), Path(sys.argv[2]).read_bytes()
        print(analyze(facade, aerial))
