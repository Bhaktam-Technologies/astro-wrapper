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

    # Determine the reference planet for House 1 (Lagna/Ascendant)
    # For Moon Chart, we use Moon as the reference. For Sun Chart, we use Sun.
    ref_name = "Lagna"
    if title and "Moon" in title:
        ref_name = "Moon"
    elif title and "Sun" in title:
        ref_name = "Sun"

    # Find the starting sign for House 1
    start_sign = 1
    for entry in chart_data:
        p_name = entry.get("planet", "").lower()
        p_id = str(entry.get("planet_id", "")).lower()
        if p_name == ref_name.lower() or p_id == ref_name[0].lower() or (ref_name == "Lagna" and (p_name == "as" or p_id == "l")):
            start_sign = int(entry["sign_number"])
            break

    # Group planets by House (1-12)
    house_planets = {h: [] for h in range(1, 13)}
    for entry in chart_data:
        sign_num = int(entry["sign_number"])
        h = (sign_num - start_sign) % 12 + 1
        
        p_name = entry.get("planet", "")
        p_id = str(entry.get("planet_id", ""))
        if p_name.lower() == ref_name.lower() or p_id.lower() == ref_name[0].lower():
            # Label the reference planet as "La" (or its abbr) in House 1
            abbr = "La" if ref_name == "Lagna" else PLANET_ABBR.get(ref_name, ref_name[:2])
            deg = float(entry.get("degrees", 0))
            house_planets[h].insert(0, (abbr, deg))
        else:
            abbr = PLANET_ABBR.get(p_name, p_name[:2])
            deg  = float(entry.get("degrees", 0))
            house_planets[h].append((abbr, deg))

    # Sign Number (Rashi) to display in each house corner
    house_sign_num = {h: (start_sign - 1 + h - 1) % 12 + 1 for h in range(1, 13)}

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
      * "house"       → shows "H9" + planets          (default)
      * "cusp"        → shows "H9 \u00b7 283\u00b0" (cusp mid)
      * "sign_number" → shows Rashi number in corner
      * "none"        → just planets, no house prefix
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
            elif label_mode == "sign_number":
                hlabel = str(sign_idx + 1)
            elif label_mode == "none":
                hlabel = ""
            else:
                hlabel = f"H{cell['house']}"
            if hlabel:
                color = "red" if label_mode == "sign_number" else "darkgreen"
                draw.text((x + cell_w - 48, y + 2), hlabel,
                          fill=color, font=house_font)

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

    # Determine rotation offset: we want the house containing Lagna (or House 1) at the Top
    # In North Indian charts, the Top Diamond is traditionally House 1.
    # We find which h_num from the data should be in Polygon 1.
    # Usually, House 1 is the one we want at the Top.
    # If the API data is already house-ordered, we map h_num directly to Polygon h_num.
    # If the user says it's "opposite", it might be because they want House 1 at the Top
    # but the API returned a fixed Aries-based chart. 
    # However, we'll stick to H1=Top and ensure House 1 from data goes there.
    
    # house_polys[h] maps house number (1-12) to polygon vertices
    # H1=Top, H4=Left, H7=Bottom, H10=Right
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
    house_outer = {
        1: T,  2: TL, 3: L,  4: L,
        5: BL, 6: B,  7: B,  8: BR,
        9: R,  10: R, 11: TR, 12: T,
    }

    # Build per-house data directly from the input houses_list
    region_data = {}
    for h_entry in houses_list:
        h_num = int(h_entry.get("house", 0))
        if h_num < 1 or h_num > 12: continue
        
        sign_name = h_entry.get("sign", "")
        sign_idx = SIGN_NAMES_FULL.index(sign_name) if sign_name in SIGN_NAMES_FULL else 0
        
        planets_to_draw = []
        is_lagna_house = False
        for p in h_entry.get("planets", []):
            abbr = PLANET_ABBR.get(p, p[:2])
            if p in {"Lagna", "As", "L"}:
                planets_to_draw.insert(0, "La")
                is_lagna_house = True
            else:
                planets_to_draw.append(abbr)

        region_data[h_num] = {
            "sign_idx": sign_idx,
            "house_label": h_num,
            "planets": planets_to_draw,
            "cusp_mid": h_entry.get("cusp_mid"),
            "is_lagna": is_lagna_house
        }

    # Determine rotation: find which house has Lagna. 
    # If no house has "La", we assume House 1 is the top.
    lagna_h = 1
    for h_num, rd in region_data.items():
        if rd["is_lagna"]:
            lagna_h = h_num
            break
    
    # rotation_offset: house h_num will be placed in polygon ((h_num - lagna_h) % 12) + 1
    # This ensures lagna_h goes to polygon 1 (Top).
    
    # --- Draw chart lines ---
    draw.rectangle([ox, oy, ox + S, oy + S], outline="black", width=2)
    line_color = (160, 80, 0)
    for pair in [(T, R), (R, B), (B, L), (L, T), (TL, BR), (TR, BL)]:
        draw.line([pair[0], pair[1]], fill=line_color, width=1)

    # --- Fill each region ---
    # Polygon p_num (1..12) should contain House h_num
    # where House lagna_h goes to Polygon 1.
    # So House h_num goes to Polygon p_num = (h_num - lagna_h) % 12 + 1
    # Conversely, Polygon p_num contains House h_num = (p_num - 1 + lagna_h - 1) % 12 + 1
    
    for p_num, pts in house_polys.items():
        h_num = (p_num - 1 + lagna_h - 1) % 12 + 1
        rd = region_data.get(h_num)
        if not rd: continue
        
        sign_short = SIGN_NAMES_SHORT[rd["sign_idx"]]
        cx_c, cy_c = _centroid(pts)
        outer = house_outer[p_num]

        # House/Sign label in corner
        if label_mode != "none":
            if label_mode == "cusp" and rd["cusp_mid"] is not None:
                hlabel = f"H{rd['house_label']} \u00b7 {float(rd['cusp_mid']):.0f}\u00b0"
            elif label_mode == "sign_number":
                hlabel = str(rd["sign_idx"] + 1)
            else:
                hlabel = f"H{rd['house_label']}"
            
            nx = cx_c + (outer[0] - cx_c) * 0.42
            ny = cy_c + (outer[1] - cy_c) * 0.42
            bb = draw.textbbox((0, 0), hlabel, font=house_font)
            draw.text((nx - (bb[2]-bb[0])/2, ny - (bb[3]-bb[1])/2), hlabel, 
                      fill="red" if label_mode == "sign_number" else "darkgreen", font=house_font)

        # Build list of lines to draw in the center
        lines = []
        for p in rd["planets"]:
            lines.append(("planet", p))

        # Layout calculations
        planet_lines = [l for l in lines if l[0] == "planet"]
        other_lines = [l for l in lines if l[0] != "planet"]
        planet_rows = (len(planet_lines) + 1) // 2 if len(planet_lines) > 4 else len(planet_lines)
        total_h = (len(other_lines) + planet_rows) * 14
        
        shift_factor = 0.18
        inner_x = cx_c + (outer[0] - cx_c) * shift_factor
        inner_y = cy_c + (outer[1] - cy_c) * shift_factor
        
        current_y = inner_y - total_h / 2
        color_map = {"sign": "darkred", "planet": "darkblue"}
        font_map  = {"sign": sign_font,  "planet": planet_font}

        for kind, text in other_lines:
            f = font_map[kind]
            bb = draw.textbbox((0, 0), text, font=f)
            draw.text((inner_x - (bb[2]-bb[0])/2, current_y), text, fill=color_map[kind], font=f)
            current_y += 14

        if len(planet_lines) > 4:
            col_size = (len(planet_lines) + 1) // 2
            for i, p_item in enumerate(planet_lines):
                p_text = p_item[1]
                col = 0 if i < col_size else 1
                row = i if i < col_size else i - col_size
                tx = inner_x - 16 if col == 0 else inner_x + 16
                ty = current_y + row * 14
                bb = draw.textbbox((0, 0), p_text, font=planet_font)
                draw.text((tx - (bb[2]-bb[0])/2, ty), p_text, fill=color_map["planet"], font=planet_font)
        else:
            for kind, text in planet_lines:
                f = font_map[kind]
                bb = draw.textbbox((0, 0), text, font=f)
                draw.text((inner_x - (bb[2]-bb[0])/2, current_y), text, fill=color_map[kind], font=f)
                current_y += 14

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
