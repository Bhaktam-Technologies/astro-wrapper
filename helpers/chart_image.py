# astro-wrapper — Copyright (C) 2026 Bhaktam Technologies
# Licensed under the GNU Affero General Public License v3.0 or later.
# See LICENSE and NOTICE in the project root for full terms.

"""
Vedic astrology chart renderer (North Indian & South Indian styles) using Pillow.
Generates PNG images from rasi_chart data returned by pyjhora_helper.
"""
import io
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Sign layout for South Indian chart (fixed sign positions, 4x4 grid)
#   Pisces(11)  Aries(0)     Taurus(1)    Gemini(2)
#   Aquarius(10)                          Cancer(3)
#   Capricorn(9)                          Leo(4)
#   Sagittarius(8) Scorpio(7) Libra(6)   Virgo(5)
# sign_index is 0-based internally; sign_number in chart_data is 1-based.
# ---------------------------------------------------------------------------
SIGN_NAMES_SHORT = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"
]
SIGN_NAMES_FULL = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# (row, col) in 4x4 grid for each 0-based sign index
SOUTH_INDIAN_POSITIONS = {
    0: (0, 1),   # Aries
    1: (0, 2),   # Taurus
    2: (0, 3),   # Gemini
    3: (1, 3),   # Cancer
    4: (2, 3),   # Leo
    5: (3, 3),   # Virgo
    6: (3, 2),   # Libra
    7: (3, 1),   # Scorpio
    8: (3, 0),   # Sagittarius
    9: (2, 0),   # Capricorn
    10: (1, 0),  # Aquarius
    11: (0, 0),  # Pisces
}

PLANET_ABBR = {
    "Lagna": "As",
    "Sun": "Su",
    "Moon": "Mo",
    "Mars": "Ma",
    "Mercury": "Me",
    "Jupiter": "Ju",
    "Venus": "Ve",
    "Saturn": "Sa",
    "Rahu": "Ra",
    "Ketu": "Ke",
    "Uranus": "Ur",
    "Neptune": "Ne",
    "Pluto": "Pl",
}


def _group_planets_by_sign(chart_data, label_mode="degrees"):
    """Group planet labels by 0-based sign index.

    sign_number in chart_data is 1-based (1=Aries … 12=Pisces);
    we convert to 0-based for use as a dict key so callers can look up
    by the same 0-based index used in SOUTH_INDIAN_POSITIONS.

    label_mode:
      * "degrees"     → "Su 29°"   (default)
      * "sign_number" → "Su 7"     (1-based rashi number)
      * "both"        → "Su 7 · 29°"
      * "none"        → "Su"
    """
    houses = {}
    for entry in chart_data:
        sign_num_1based = int(entry["sign_number"])          # 1-based from API
        sign_idx = sign_num_1based - 1                       # 0-based for grid lookup
        planet = entry["planet"]
        abbr = PLANET_ABBR.get(planet, planet[:2])
        deg = entry.get("degrees", 0)
        if label_mode == "sign_number":
            label = f"{abbr} {sign_num_1based}"
        elif label_mode == "both":
            label = f"{abbr} {sign_num_1based} · {deg:.0f}\u00b0"
        elif label_mode == "none":
            label = abbr
        else:
            label = f"{abbr} {deg:.0f}\u00b0"
        houses.setdefault(sign_idx, []).append(label)
    return houses


def _try_load_font(size):
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# South Indian chart
# ---------------------------------------------------------------------------

def generate_south_indian_chart(chart_data, title="Rasi Chart", size=600,
                                label_mode="degrees"):
    """South Indian style: signs are fixed in cells, planets/lagna move."""
    margin = 40
    title_height = 50
    img_w = size
    img_h = size + title_height
    cell_w = (size - 2 * margin) // 4
    cell_h = (size - 2 * margin) // 4

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    title_font = _try_load_font(18)
    sign_font = _try_load_font(11)
    planet_font = _try_load_font(10)

    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((img_w - tw) // 2, 10), title, fill="black", font=title_font)

    ox, oy = margin, margin + title_height
    for r in range(5):
        y = oy + r * cell_h
        draw.line([(ox, y), (ox + 4 * cell_w, y)], fill="black", width=2)
    for c in range(5):
        x = ox + c * cell_w
        draw.line([(x, oy), (x, oy + 4 * cell_h)], fill="black", width=2)

    cx1, cy1 = ox + cell_w, oy + cell_h
    cx2, cy2 = ox + 3 * cell_w, oy + 3 * cell_h
    draw.line([(cx1, cy1), (cx2, cy2)], fill="black", width=1)
    draw.line([(cx2, cy1), (cx1, cy2)], fill="black", width=1)

    houses = _group_planets_by_sign(chart_data, label_mode=label_mode)

    for sign_idx in range(12):
        row, col = SOUTH_INDIAN_POSITIONS[sign_idx]
        x = ox + col * cell_w
        y = oy + row * cell_h

        draw.text((x + 3, y + 2), SIGN_NAMES_SHORT[sign_idx], fill="red", font=sign_font)

        planets = houses.get(sign_idx, [])
        py = y + 16
        for p_label in planets:
            draw.text((x + 3, py), p_label, fill="darkblue", font=planet_font)
            py += 13

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# North Indian chart
# ---------------------------------------------------------------------------
# Construction: outer square + both full diagonals (TL→BR, TR→BL) +
# inner diamond (connecting midpoints T, R, B, L of each side).
# The diagonals intersect the diamond sides at P1..P4, creating 12 regions:
#   4 inner quadrilaterals  → H1 (bottom), H4 (right), H7 (top), H10 (left)
#   8 corner triangles (2 per corner) → H2–H3, H5–H6, H8–H9, H11–H12
# Houses go clockwise from H1. Signs rotate; Lagna sign goes in H1.
# ---------------------------------------------------------------------------

def _centroid(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def generate_north_indian_chart(chart_data, title="Rasi Chart", size=600,
                                label_mode="degrees"):
    """North Indian style — SS dark theme.

    Houses are fixed (H1=bottom-center, anti-clockwise to H12).
    Lagna sign rotates into H1. Each cell shows its house number once (gold),
    then planets as: degree on top line, abbreviation on next line (white).
    """
    margin = 30
    title_height = 44
    S = size - 2 * margin
    img_w = size
    img_h = size + title_height

    BG   = (10, 10, 10)
    GOLD = (255, 165, 0)
    WHITE = (255, 255, 255)

    img = Image.new("RGB", (img_w, img_h), BG)
    draw = ImageDraw.Draw(img)

    title_font  = _try_load_font(17)
    num_font    = _try_load_font(15)
    deg_font    = _try_load_font(9)
    planet_font = _try_load_font(12)

    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((img_w - tw) // 2, 8), title, fill=GOLD, font=title_font)

    ox = margin
    oy = margin + title_height

    def pt(rx, ry):
        return (ox + int(rx * S), oy + int(ry * S))

    TL = pt(0,   0);   TR = pt(1,   0)
    BR = pt(1,   1);   BL = pt(0,   1)
    T  = pt(.5,  0);   R  = pt(1,  .5)
    B  = pt(.5,  1);   L  = pt(0,  .5)
    C  = pt(.5,  .5)
    P1 = pt(.25, .25); P2 = pt(.75, .25)
    P3 = pt(.75, .75); P4 = pt(.25, .75)

    # Standard North Indian houses: H1=Top, H4=Left, H7=Bottom, H10=Right
    # house_polys[h] connects vertices for House h
    house_polys = {
        1:  [C, P1, T, P2],   # Top
        2:  [TL, T, P1],
        3:  [TL, P1, L],
        4:  [C, P4, L, P1],   # Left
        5:  [BL, P4, L],
        6:  [BL, B, P4],
        7:  [C, P3, B, P4],   # Bottom
        8:  [BR, P3, B],
        9:  [BR, R, P3],
        10: [C, P2, R, P3],   # Right
        11: [TR, P2, R],
        12: [TR, T, P2],
    }

    # Outer vertex for each house: used to push labels towards the outer wall
    house_outer = {
        1: T,  2: TL, 3: L,  4: L,
        5: BL, 6: B,  7: B,  8: BR,
        9: R,  10: R, 11: TR, 12: T,
    }

    # Fixed sign layout: position 1=Aries (bottom-center), anti-clockwise to 12=Pisces.
    # sign_number in chart_data is 1-based (1=Aries), matching the polygon key directly.

    # Find Lagna sign to determine the starting sign for House 1
    lagna_sign = 1
    for entry in chart_data:
        if entry.get("planet") == "Lagna" or entry.get("planet_id") == "L":
            lagna_sign = int(entry["sign_number"])
            break

    # Group planets by House (1-12)
    # House 1 always gets planets in lagna_sign, House 2 gets lagna_sign + 1, etc.
    house_planets = {h: [] for h in range(1, 13)}
    for entry in chart_data:
        sign_num = int(entry["sign_number"])
        # Calculate house number (1-based)
        h = (sign_num - lagna_sign) % 12 + 1
        
        if entry.get("planet") == "Lagna" or entry.get("planet_id") == "L":
            deg = float(entry.get("degrees", 0))
            house_planets[h].insert(0, ("La", deg))
        else:
            abbr = PLANET_ABBR.get(entry["planet"], entry["planet"][:2])
            deg  = float(entry.get("degrees", 0))
            house_planets[h].append((abbr, deg))

    # Determine which Sign Number (Rashi) to display in each house corner
    house_sign_num = {h: (lagna_sign - 1 + h - 1) % 12 + 1 for h in range(1, 13)}

    # --- Draw chart border + lines ---
    draw.rectangle([ox, oy, ox + S, oy + S], outline=GOLD, width=3)
    draw.line([T, R], fill=GOLD, width=2)
    draw.line([R, B], fill=GOLD, width=2)
    draw.line([B, L], fill=GOLD, width=2)
    draw.line([L, T], fill=GOLD, width=2)
    draw.line([TL, BR], fill=GOLD, width=2)
    draw.line([TR, BL], fill=GOLD, width=2)

    # --- Render each house cell ---
    for h, pts in house_polys.items():
        cx_c, cy_c = _centroid(pts)
        outer = house_outer[h]

        # Sign Number (Rashi): placed 38% of the way from centroid to the outer vertex
        nx = cx_c + (outer[0] - cx_c) * 0.38
        ny = cy_c + (outer[1] - cy_c) * 0.38
        sign_str = str(house_sign_num[h])
        nbbox = draw.textbbox((0, 0), sign_str, font=num_font)
        nw, nh = nbbox[2]-nbbox[0], nbbox[3]-nbbox[1]
        draw.text((nx - nw / 2, ny - nh / 2), sign_str, fill=GOLD, font=num_font)

        # Planets: stacked or gridded at inner position
        planets = house_planets[h]
        if not planets:
            continue

        show_degrees = label_mode != "none"
        line_h = 11 if show_degrees else 0
        name_h = 13
        spacing = 2
        
        # Shift planets AWAY from the center (C) and towards the outer boundary
        # This keeps them away from the inner diagonal lines.
        shift_factor = 0.18
        inner_x = cx_c + (outer[0] - cx_c) * shift_factor
        inner_y = cy_c + (outer[1] - cy_c) * shift_factor

        # If many planets, use two columns to prevent vertical overflow
        if len(planets) >= 3:
            col_size = (len(planets) + 1) // 2
            block_h = col_size * (line_h + name_h + spacing)
            
            for i, (abbr, deg) in enumerate(planets):
                col = 0 if i < col_size else 1
                row = i if i < col_size else i - col_size
                # Spread columns slightly
                tx = inner_x - 15 if col == 0 else inner_x + 15
                ty = inner_y - block_h / 2 + row * (line_h + name_h + spacing)
                
                if show_degrees:
                    deg_str = f"{int(round(deg)):02d}"
                    dbbox = draw.textbbox((0, 0), deg_str, font=deg_font)
                    draw.text((tx - (dbbox[2]-dbbox[0])/2, ty), deg_str, fill=GOLD, font=deg_font)
                
                pbbox = draw.textbbox((0, 0), abbr, font=planet_font)
                draw.text((tx - (pbbox[2]-pbbox[0])/2, ty + line_h), abbr, fill=WHITE, font=planet_font)
        else:
            block_h = len(planets) * (line_h + name_h + spacing)
            ty = inner_y - block_h / 2
            for abbr, deg in planets:
                if show_degrees:
                    deg_str = f"{int(round(deg)):02d}"
                    dbbox = draw.textbbox((0, 0), deg_str, font=deg_font)
                    draw.text((inner_x - (dbbox[2]-dbbox[0])/2, ty), deg_str, fill=GOLD, font=deg_font)
                
                pbbox = draw.textbbox((0, 0), abbr, font=planet_font)
                draw.text((inner_x - (pbbox[2]-pbbox[0])/2, ty + line_h), abbr, fill=WHITE, font=planet_font)
                ty += line_h + name_h + spacing

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Bhava / Chalit chart (South Indian style)
# ---------------------------------------------------------------------------

def generate_bhava_chart(bhava_data, title="Bhava / Chalit Chart", size=600,
                         label_mode="house", style="north"):
    """Render a bhava (chalit) chart in North or South Indian style.

    bhava_data: dict with 'houses' key — list of
      {house, sign, cusp_start, cusp_mid, cusp_end, planets, planet_ids}
    label_mode:
      * "house"      → shows "H9" + planets          (default)
      * "cusp"       → shows "H9 · 283°" (cusp mid)
      * "none"       → just planets, no house prefix
    style:
      * "north"      → North Indian diamond layout    (default)
      * "south"      → South Indian fixed-sign grid
    """
    houses_list = bhava_data.get("houses") if isinstance(bhava_data, dict) else bhava_data
    if not houses_list:
        raise ValueError("bhava_data has no 'houses' entries to render")

    sign_name_to_idx = {n: i for i, n in enumerate(SIGN_NAMES_FULL)}

    # Build per-sign-cell data: house number(s), planets, cusp_mid
    cells = {i: {"house": None, "planets": [], "cusp_mid": None} for i in range(12)}
    for h in houses_list:
        sign_idx = sign_name_to_idx.get(h.get("sign"))
        if sign_idx is None:
            cusp_start = float(h.get("cusp_start", 0))
            sign_idx = int(cusp_start // 30) % 12
        cell = cells[sign_idx]
        cell["house"] = int(h["house"]) if cell["house"] is None else f"{cell['house']}/{int(h['house'])}"
        cell["cusp_mid"] = h.get("cusp_mid", cell["cusp_mid"])
        for p in h.get("planets", []):
            cell["planets"].append(PLANET_ABBR.get(p, p[:2]))

    if style == "south":
        return _bhava_south(cells, title=title, size=size, label_mode=label_mode)
    return _bhava_north(cells, houses_list, title=title, size=size, label_mode=label_mode)


def _bhava_south(cells, title="Bhava / Chalit Chart", size=600, label_mode="house"):
    """South Indian fixed-sign grid for the bhava chart."""
    margin = 40
    title_height = 50
    img_w = size
    img_h = size + title_height
    cell_w = (size - 2 * margin) // 4
    cell_h = (size - 2 * margin) // 4

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    title_font  = _try_load_font(18)
    sign_font   = _try_load_font(11)
    house_font  = _try_load_font(14)
    planet_font = _try_load_font(11)

    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((img_w - tw) // 2, 10), title, fill="black", font=title_font)

    ox, oy = margin, margin + title_height
    for r in range(5):
        y = oy + r * cell_h
        draw.line([(ox, y), (ox + 4 * cell_w, y)], fill="black", width=2)
    for c in range(5):
        x = ox + c * cell_w
        draw.line([(x, oy), (x, oy + 4 * cell_h)], fill="black", width=2)
    cx1, cy1 = ox + cell_w, oy + cell_h
    cx2, cy2 = ox + 3 * cell_w, oy + 3 * cell_h
    draw.line([(cx1, cy1), (cx2, cy2)], fill="black", width=1)
    draw.line([(cx2, cy1), (cx1, cy2)], fill="black", width=1)

    for sign_idx in range(12):
        row, col = SOUTH_INDIAN_POSITIONS[sign_idx]
        x = ox + col * cell_w
        y = oy + row * cell_h
        cell = cells[sign_idx]

        draw.text((x + 3, y + 2), SIGN_NAMES_SHORT[sign_idx], fill="red", font=sign_font)

        if cell["house"] is not None:
            if label_mode == "cusp" and cell["cusp_mid"] is not None:
                hlabel = f"H{cell['house']} \u00b7 {float(cell['cusp_mid']):.0f}\u00b0"
            elif label_mode == "none":
                hlabel = ""
            else:
                hlabel = f"H{cell['house']}"
            if hlabel:
                draw.text((x + cell_w - 48, y + 2), hlabel,
                          fill="darkgreen", font=house_font)

        py = y + 20
        for p_abbr in cell["planets"]:
            draw.text((x + 3, py), p_abbr, fill="darkblue", font=planet_font)
            py += 14

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def _bhava_north(cells, houses_list, title="Bhava / Chalit Chart", size=600,
                 label_mode="house"):
    """North Indian diamond layout for the bhava chart.

    Houses are fixed in the 12 diamond regions (same geometry as generate_north_indian_chart).
    The Bhava-1 house determines which sign goes in region H1; subsequent signs follow
    clockwise — identical rotation logic to the rasi North Indian renderer.
    """
    margin = 40
    title_height = 50
    S = size - 2 * margin
    img_w = size
    img_h = size + title_height

    img = Image.new("RGB", (img_w, img_h), "white")
    draw = ImageDraw.Draw(img)

    title_font  = _try_load_font(18)
    sign_font   = _try_load_font(10)
    house_font  = _try_load_font(10)
    planet_font = _try_load_font(10)

    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((img_w - tw) // 2, 10), title, fill="black", font=title_font)

    ox = margin
    oy = margin + title_height

    def pt(rx, ry):
        return (ox + int(rx * S), oy + int(ry * S))

    TL = pt(0,   0);   TR = pt(1,   0)
    BR = pt(1,   1);   BL = pt(0,   1)
    T  = pt(.5,  0);   R  = pt(1,  .5)
    B  = pt(.5,  1);   L  = pt(0,  .5)
    C  = pt(.5,  .5)
    P1 = pt(.25, .25); P2 = pt(.75, .25)
    P3 = pt(.75, .75); P4 = pt(.25, .75)

    house_polys = {
        1:  [C, P3, B, P4],
        2:  [BR, P3, B],
        3:  [BR, R, P3],
        4:  [C, P2, R, P3],
        5:  [TR, P2, R],
        6:  [TR, T, P2],
        7:  [C, P1, T, P2],
        8:  [TL, T, P1],
        9:  [TL, P1, L],
        10: [C, P4, L, P1],
        11: [BL, P4, L],
        12: [BL, B, P4],
    }

    # Determine lagna sign from bhava-1 entry
    lagna_sign_1based = 1
    for h in houses_list:
        if int(h.get("house", 0)) == 1:
            sign_name = h.get("sign", "")
            if sign_name in SIGN_NAMES_FULL:
                lagna_sign_1based = SIGN_NAMES_FULL.index(sign_name) + 1
            else:
                cusp = float(h.get("cusp_start", 0))
                lagna_sign_1based = int(cusp // 30) % 12 + 1
            break

    # house_sign[h] = 0-based sign index placed in diamond region h
    house_sign = {h: (lagna_sign_1based - 1 + h - 1) % 12 for h in range(1, 13)}
    sign_to_region = {si: h for h, si in house_sign.items()}

    # Build per-region data from cells (keyed by sign index)
    region_data = {h: {"sign_idx": house_sign[h], "house_label": None,
                       "planets": [], "cusp_mid": None}
                   for h in range(1, 13)}
    for sign_idx, cell in cells.items():
        region = sign_to_region.get(sign_idx)
        if region is None:
            continue
        rd = region_data[region]
        rd["house_label"] = cell["house"]
        rd["planets"] = cell["planets"]
        rd["cusp_mid"] = cell["cusp_mid"]

    # --- Draw chart lines ---
    draw.rectangle([ox, oy, ox + S, oy + S], outline="black", width=2)
    line_color = (160, 80, 0)
    draw.line([T, R], fill=line_color, width=1)
    draw.line([R, B], fill=line_color, width=1)
    draw.line([B, L], fill=line_color, width=1)
    draw.line([L, T], fill=line_color, width=1)
    draw.line([TL, BR], fill=line_color, width=1)
    draw.line([TR, BL], fill=line_color, width=1)

    # --- Fill each region ---
    for region, pts in house_polys.items():
        rd = region_data[region]
        sign_short = SIGN_NAMES_SHORT[rd["sign_idx"]]
        cx_c, cy_c = _centroid(pts)

        # Build label lines: [sign, house_label, ...planets]
        lines = []

        # House label (e.g. "H3") in darkgreen
        if rd["house_label"] is not None and label_mode != "none":
            if label_mode == "cusp" and rd["cusp_mid"] is not None:
                hlabel = f"H{rd['house_label']} \u00b7 {float(rd['cusp_mid']):.0f}\u00b0"
            else:
                hlabel = f"H{rd['house_label']}"
            lines.append(("house", hlabel))

        # Sign abbr in darkred
        lines.append(("sign", sign_short))

        # Planets in darkblue
        for p in rd["planets"]:
            lines.append(("planet", p))

        total_h = len(lines) * 13
        top_y = cy_c - total_h / 2

        color_map = {"house": "darkgreen", "sign": "darkred", "planet": "darkblue"}
        font_map  = {"house": house_font,  "sign": sign_font,  "planet": planet_font}

        for kind, text in lines:
            f = font_map[kind]
            bb = draw.textbbox((0, 0), text, font=f)
            tw2 = bb[2] - bb[0]
            draw.text((cx_c - tw2 / 2, top_y), text, fill=color_map[kind], font=f)
            top_y += 13

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_chart_image(chart_data, chart_name="Rasi Chart", size=600,
                         label_mode="degrees", style="north"):
    """Generate chart image bytes.

    Args:
        chart_data: list from pyjhora_helper.get_rasi_chart() or any divisional chart
        chart_name: title for the chart
        size: image size in pixels
        label_mode: "degrees" | "sign_number" | "both" | "none"
        style: "north" (default) | "south"

    Returns:
        PNG image as bytes
    """
    if style == "south":
        return generate_south_indian_chart(
            chart_data, title=chart_name, size=size, label_mode=label_mode,
        )
    return generate_north_indian_chart(
        chart_data, title=chart_name, size=size, label_mode=label_mode,
    )
