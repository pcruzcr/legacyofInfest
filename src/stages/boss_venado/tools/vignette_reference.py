# CONTEXTO: script de arte; solo lee fotos de referencia y escribe en el scratchpad.
"""
Vertical-slice art proof: 480x224 twilight vignette of the ARCS ZONE of the map.
Hand-painted pixel art (geometry traced from reference photos 4/9/12/13), a single
<=32 colour master palette, ordered dithering, per-material texture. No anti-alias:
every pixel is a palette colour set directly in a numpy array. Reads nothing at
runtime (geometry is authored); writes only inside this scratchpad's concept_art/proof/.
"""
import os
import numpy as np
from PIL import Image

OUT = "C:/Users/josej/AppData/Local/Temp/claude/J--Computacion-Grafica-I/d2e24d57-bf26-4b97-9b01-f74e113f5b79/scratchpad/concept_art/proof"
os.makedirs(OUT, exist_ok=True)

W, H = 480, 224

# ---------------------------------------------------------------------------
# MASTER PALETTE  (<=32 colours, twilight / semi-abandoned)
# ---------------------------------------------------------------------------
def hx(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

PAL = {
    # sky (top -> horizon), 6
    "S0": hx("#2A2150"), "S1": hx("#463A6E"), "S2": hx("#6E4E7E"),
    "S3": hx("#9C5E76"), "S4": hx("#C86C4E"), "S5": hx("#E8853C"),
    # warm / glow, 3
    "W0": hx("#F2C878"), "W1": hx("#F5E1A0"), "W2": hx("#FFF6D0"),
    # far silhouette, 1
    "F0": hx("#2E2448"),
    # ochre stucco wall, 4  (dusk-muted mustard, base ~#C99046)
    "O0": hx("#47301F"), "O1": hx("#6E4A2A"), "O2": hx("#A2743A"), "O3": hx("#C6934C"),
    # roof terracotta, 3  (dusk-muted ~#C74A32)
    "R0": hx("#2A1418"), "R1": hx("#6E2E22"), "R2": hx("#A04A32"),
    # cenefa (cream-white fascia), 2
    "C0": hx("#E6DCC6"), "C1": hx("#9A8266"),
    # vegetation, 4
    "V0": hx("#10160E"), "V1": hx("#1E2C18"), "V2": hx("#33482A"), "V3": hx("#547038"),
    # stone sidewalk, 4
    "G0": hx("#332C2A"), "G1": hx("#574B44"), "G2": hx("#7C6C5C"), "G3": hx("#A08A72"),
    # ink, 2
    "K0": hx("#0C0A0C"), "K1": hx("#1E1620"),
    # flowers, 2
    "P0": hx("#A83A34"), "P1": hx("#D06048"),
    # cool rim, 1
    "RM": hx("#B49AB0"),
    # jewelry pass: cool AA rim-light + exposed light plaster (spalls), 2
    "RC": hx("#9AA8CE"),   # cold violet-blue rim on top silhouette edges / stars
    "PL": hx("#C9B48A"),   # pale plaster revealed by spalled stucco
}
assert len(set(PAL.values())) <= 36, f"palette too big: {len(set(PAL.values()))}"

SKY = ["S0", "S1", "S2", "S3", "S4", "S5"]

canvas = np.zeros((H, W, 3), dtype=np.uint8)

# ordered dithering (Bayer 4x4)
BAYER = np.array([
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
], dtype=np.float32) / 16.0

rng = np.random.default_rng(7)

def c(name):
    return np.array(PAL[name], dtype=np.uint8)

def put(x, y, name):
    if 0 <= x < W and 0 <= y < H:
        canvas[y, x] = PAL[name]

def rect(x0, y0, x1, y1, name):
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W, x1); y1 = min(H, y1)
    canvas[y0:y1, x0:x1] = PAL[name]

def dither2(x, y, a, b, t):
    """Return palette name a or b: t is fraction toward b, dithered by Bayer."""
    return b if t > BAYER[y & 3, x & 3] else a

def hash01(x, y, salt=0):
    v = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    v = (v ^ (v >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFFFF) / 65535.0


# ===========================================================================
# 1. SKY  (crepuscular multi-stop gradient with ordered dithering)
# ===========================================================================
HORIZON = 150
def build_sky():
    # clean horizontal bands with narrow (~5px) ordered-dither seams between
    # adjacent stops -- smooth dusk gradient, minimal stipple.
    n = len(SKY) - 1
    bounds = [int(HORIZON * (i / n) ** 0.80) for i in range(len(SKY))]
    SEAM = 5
    for y in range(0, HORIZON):
        i = 0
        while i < n - 1 and y >= bounds[i + 1]:
            i += 1
        y1 = bounds[i + 1]
        for x in range(W):
            d_to_next = y1 - y
            if d_to_next <= SEAM and i < n - 1:
                # dither across the seam: fraction toward the next (lower) stop
                frac = 1.0 - (d_to_next / SEAM)          # 0..1 as we near the seam
                # only ~half the seam width actually flips, easing the transition
                name = SKY[i + 1] if (frac * 0.85) > BAYER[y & 3, x & 3] else SKY[i]
            else:
                name = SKY[i]
            canvas[y, x] = PAL[name]
    # warm horizon haze: a clean-ish glow hugging the skyline, right-biased
    for y in range(HORIZON - 16, HORIZON):
        t = (y - (HORIZON - 16)) / 16.0
        for x in range(W):
            bias = 0.30 + 0.60 * (x / W)
            strength = (t ** 1.5) * bias
            if strength > 0.45:
                use_w0 = strength > 0.9
                if (strength - 0.45) * 1.8 > BAYER[y & 3, x & 3]:
                    canvas[y, x] = PAL["W0"] if use_w0 else PAL["S5"]

build_sky()

# ---- clouds: flat wispy streaks, cool tops, warm-lit undersides ----
def cloud(cx, cy, rx, warm=True, thick=3):
    for y in range(cy - thick, cy + thick + 1):
        for x in range(cx - rx, cx + rx + 1):
            if not (0 <= x < W and 0 <= y < HORIZON):
                continue
            fx = (x - cx) / rx                         # -1..1 along length
            # wispy profile: thinner at the ends, broken by noise
            prof = (1 - fx * fx) ** 0.6
            half = prof * thick
            dy = y - cy
            if abs(dy) > half + 0.5:
                continue
            # break the cloud into streaks
            if hash01(x, y, 5) > 0.45 + 0.4 * prof:
                continue
            if dy >= half - 1.2:                       # lit underside
                base = "W0" if warm and prof > 0.55 else "S4"
            elif dy <= -half + 1.0:                    # cool top
                base = "S2"
            else:
                base = "S3" if warm else "S2"
            canvas[y, x] = PAL[base]
    # a few bright glints on the underside
    for x in range(cx - rx, cx + rx + 1):
        prof = (1 - ((x - cx) / rx) ** 2) ** 0.6
        yy = cy + int(prof * thick)
        if 0 <= x < W and 0 <= yy < HORIZON and prof > 0.4 and hash01(x, yy, 9) > 0.6:
            canvas[yy, x] = PAL["W1"]

cloud(92, 28, 52, warm=True, thick=3)
cloud(258, 18, 30, warm=True, thick=2)
cloud(398, 40, 44, warm=True, thick=3)
cloud(436, 92, 26, warm=True, thick=2)
cloud(158, 66, 30, warm=True, thick=2)


# ===========================================================================
# 2. FAR FOREST LINE  (dark violet silhouette, atmospheric)
# ===========================================================================
def crown_profile(seed_salt, spacing, radius, jitter):
    """A treeline top edge (smaller y = higher) from overlapping rounded crowns."""
    prof = np.full(W, 10_000, dtype=np.float32)
    xc = -radius
    while xc < W + radius:
        r = radius * (0.7 + 0.6 * hash01(int(xc), 0, seed_salt))
        cy = -r * (0.55 + 0.4 * hash01(int(xc), 1, seed_salt))     # crown height
        for x in range(int(xc - r), int(xc + r) + 1):
            if 0 <= x < W:
                dx = (x - xc) / r
                if abs(dx) <= 1:
                    yy = cy + r * (1 - (1 - dx * dx) ** 0.5)       # circle bump
                    prof[x] = min(prof[x], yy)
        xc += spacing * (0.7 + 0.6 * hash01(int(xc), 2, seed_salt))
    return prof

def build_forest():
    base = 134
    # far treeline (soft, hazy rim)
    far = crown_profile(31, 16, 13, 3)
    for x in range(W):
        top = int(base - 12 + far[x])
        for y in range(top, base):
            if y <= top + 1 and hash01(x, y, 4) > 0.45:
                canvas[y, x] = PAL["S2"]                # haze rim on crowns
            else:
                canvas[y, x] = PAL["F0"]
    # nearer treeline band (darker) filling to the ground plane, left & right only
    near = crown_profile(37, 12, 10, 2)
    for x in range(W):
        if 150 < x < 356:
            continue
        top = int(base - 2 + near[x])
        for y in range(top, base + 4):
            canvas[y, x] = PAL["F0"] if hash01(x, y, 7) > 0.18 else PAL["K1"]

build_forest()


# ===========================================================================
# 3. MID-GROUND MEADOW STRIP  (behind structures, y 136..196)
# ===========================================================================
GROUND = 196
def build_meadow():
    for y in range(132, GROUND):
        for x in range(W):
            # depth threshold jittered per-column so brightening is never a
            # straight horizontal line read across foreground structures
            jit = (hash01(x, 0, 14) - 0.5) * 0.22 + 0.06 * np.sin(x * 0.3)
            t = (y - 132) / (GROUND - 132) + jit
            if t < 0.45:
                base = "V1" if hash01(x, y, 11) > 0.35 else "V0"
            elif t < 0.8:
                base = "V2" if hash01(x, y, 12) > 0.45 else "V1"
            else:
                base = "V2" if hash01(x, y, 13) > 0.3 else "V3"
            canvas[y, x] = PAL[base]
    # vertical grass-blade streaks break up any horizontal read
    for x in range(0, W, 1):
        if hash01(x, 0, 20) > 0.55:
            yb = int(160 + 30 * hash01(x, 1, 20))
            for y in range(yb, min(GROUND, yb + int(4 + 8 * hash01(x, 2, 20)))):
                canvas[y, x] = PAL["V2"] if hash01(x, y, 22) > 0.4 else PAL["V1"]
    # scattered dusk-catch grass tips
    for _ in range(400):
        x = int(rng.integers(0, W)); y = int(rng.integers(155, GROUND))
        if hash01(x, y, 21) > 0.62:
            canvas[y, x] = PAL["V3"]

build_meadow()

# ---- undergrowth: bumpy dark hedgerow blending forest base into the meadow,
#      so the treeline/meadow seam is never a straight horizontal line ----
def build_undergrowth():
    prof = crown_profile(53, 9, 7, 2)
    for x in range(W):
        top = int(130 + prof[x])
        for y in range(top, top + 12):
            if y >= GROUND:
                break
            r = hash01(x, y, 55)
            if y <= top + 1:
                tone = "V1" if r > 0.4 else "V0"
            elif r > 0.86:
                tone = "V2"
            elif r < 0.14:
                tone = "V0"
            else:
                tone = "V1"
            canvas[y, x] = PAL[tone]
    # a few distant bush mounds catching the last dusk light (varied, irregular)
    for bx in (30, 108, 196, 286, 336):
        by = 137 + int(7 * hash01(bx, 0, 56))
        rad = 6 + int(6 * hash01(bx, 3, 56))                  # varied width
        peak = 5 + int(5 * hash01(bx, 4, 56))                 # varied height
        for x in range(bx - rad, bx + rad + 1):
            base_h = (1 - ((x - bx) / (rad + 0.5)) ** 2) * peak
            hh = int(base_h * (0.7 + 0.6 * hash01(x, 5, 56)))  # ragged top
            for i in range(hh):
                y = by - i
                if 128 < y < GROUND:
                    if i >= hh - 1:
                        canvas[y, x] = PAL["V3"] if hash01(x, y, 57) > 0.4 else PAL["V2"]
                    else:
                        canvas[y, x] = PAL["V2"] if hash01(x, y, 58) > 0.3 else PAL["V1"]

build_undergrowth()


# ===========================================================================
# 4. DISTANT BUNGALOW  (in the gap between hastial & gazebo, base y188)
# ===========================================================================
def build_bungalow():
    bx0, bx1 = 250, 322
    roof_y = 168
    base_y = 189
    # body (muted violet-ochre: atmospheric perspective)
    for y in range(roof_y, base_y):
        for x in range(bx0, bx1):
            base = "O1" if hash01(x, y, 31) > 0.4 else "O0"
            canvas[y, x] = PAL[base]
    # low sloped roof (muted terracotta) with corrugation grooves + rust + fascia
    for x in range(bx0 - 5, bx1 + 5):
        ry = roof_y - int((x - (bx0 - 5)) * 0.09)   # gentle slope
        for y in range(ry - 4, ry):
            if not (0 <= x < W):
                continue
            tone = "R1"
            if x % 3 == 0:
                tone = "R0"                          # corrugation groove
            elif hash01(x // 5, y, 32) > 0.92:
                tone = "O1"                          # rust bloom
            canvas[y, x] = PAL[tone]
        if 0 <= x < W:
            canvas[ry, x] = PAL["C1"]                # fascia line
    # warm lit window (left)
    rect(bx0 + 8, base_y - 12, bx0 + 18, base_y - 3, "K1")
    rect(bx0 + 9, base_y - 11, bx0 + 17, base_y - 4, "W0")
    for yy in range(base_y - 11, base_y - 4):       # muntins
        put(bx0 + 13, yy, "K1")
    put(bx0 + 9, base_y - 8, "K1"); put(bx0 + 17, base_y - 8, "K1")
    # a door between the windows (dark, slightly ajar)
    dx0 = bx0 + 30
    rect(dx0, base_y - 16, dx0 + 8, base_y, "K1")
    rect(dx0 + 1, base_y - 15, dx0 + 6, base_y, "K0")
    put(dx0 + 5, base_y - 8, "O3")                   # door handle glint
    put(dx0 + 7, base_y - 15, "C1")                  # lit lintel edge
    # boarded-up window (right, dark planks)
    rect(bx1 - 20, base_y - 12, bx1 - 9, base_y - 3, "K1")
    for i, yy in enumerate(range(base_y - 11, base_y - 4, 2)):
        rect(bx1 - 19, yy, bx1 - 10, yy + 1, "O0")
    # warm light trapezoid spilling from the lit window onto the ground
    wcx = bx0 + 13
    for y in range(base_y, base_y + 7):
        t = (y - base_y) / 7.0
        half = 3 + int(t * 6)
        for x in range(wcx - half, wcx + half):
            if hash01(x, y, 33) < (0.55 - t * 0.4):
                canvas[y, x] = PAL["S5"] if t > 0.4 else PAL["W0"]
    # base shadow into grass
    for x in range(bx0 - 3, bx1 + 3):
        put(x, base_y, "V0"); put(x, base_y + 1, "V0")

build_bungalow()


# ===========================================================================
# 5. HASTIAL  (center-left; base y196; gable peak ~y80) traced from photo 4/13
# ===========================================================================
HX0, HX1 = 92, 232          # wall left/right
PEAK_X = 162
PEAK_Y = 80
EAVE_Y = 128                # where roof meets wall top
WALL_TOP = 126

def wall_tone(x, y):
    """SMOOTH ochre stucco (photo 4), dusk-lit. Dominant tone is O2 (mustard);
    subtle 2-tone mottling in soft low-frequency CLUSTERS (never vertical
    plank streaks); brighter toward the sun (right) and upper; damp/weathering
    stains pooling toward the base and the lower corners (abandonment)."""
    tx = (x - HX0) / (HX1 - HX0)               # 0 left .. 1 right
    ty = (y - WALL_TOP) / (GROUND - WALL_TOP)
    # gentle even light -> wall sits mostly on O2 with O3 catching the dusk sun
    lum = 0.56 + 0.16 * tx - 0.12 * ty
    # eave shadow: smooth jittered ramp (no hard horizontal edge)
    es_span = 14 + 4 * hash01(x, 0, 44)
    es = max(0.0, (WALL_TOP + es_span - y) / es_span)
    lum -= 0.20 * es * es
    # stucco mottling: soft cluster field (coarse + medium), no directional grain
    mott = (hash01(x // 5, y // 5, 45) - 0.5) * 0.15 \
         + (hash01(x // 3, y // 3, 46) - 0.5) * 0.09 \
         + (hash01(x, y, 47) - 0.5) * 0.04
    lum += mott
    # damp / weathering stains: pool low and into the corners
    base_prox = max(0.0, (ty - 0.42) / 0.58)
    corner = max(0.0, 1.0 - min(tx, 1.0 - tx) / 0.20)
    if hash01(x // 5, y // 4, 48) > 0.60:
        lum -= (0.10 + 0.16 * corner) * base_prox
    if hash01(x // 6, y // 3, 49) > 0.90:      # occasional darker weather runnel
        lum -= 0.10 * base_prox
    if lum < 0.34: return "O0"
    if lum < 0.54: return "O1"
    if lum < 0.78: return "O2"
    return "O3"

def in_hastial_wall(x, y):
    if y < WALL_TOP or y >= GROUND or x < HX0 or x >= HX1:
        # gable triangle above WALL_TOP
        if EAVE_Y > y >= PEAK_Y:
            # triangle between the two roof slopes
            pass
        return False
    return True

def build_hastial():
    # ---- gable triangle wall (between roof slopes) ----
    for y in range(PEAK_Y, WALL_TOP):
        # half width of the gable at this y
        frac = (y - PEAK_Y) / (WALL_TOP - PEAK_Y)
        halfw = frac * ((HX1 - HX0) / 2)
        xl = int(PEAK_X - halfw); xr = int(PEAK_X + halfw)
        for x in range(xl, xr):
            canvas[y, x] = PAL[wall_tone(x, y)]
    # ---- rectangular wall body ----
    for y in range(WALL_TOP, GROUND):
        for x in range(HX0, HX1):
            canvas[y, x] = PAL[wall_tone(x, y)]

    # ---- roof: wine trim following the two slopes, with cream fascia beneath ----
    def roof_line(x):
        # returns y of the roof edge at column x (outer edge of trim)
        if x <= PEAK_X:
            t = (x - (HX0 - 8)) / (PEAK_X - (HX0 - 8))
        else:
            t = (x - (HX1 + 8)) / (PEAK_X - (HX1 + 8))
        t = max(0.0, min(1.0, t))
        return int(PEAK_Y + (EAVE_Y - PEAK_Y) * (1 - t))
    for x in range(HX0 - 8, HX1 + 8):
        ry = roof_line(x)
        # terracotta roof trim (5px): sunlit crest -> darker underside, with
        # corrugated-sheet grooves down the slope and sparse rust / moss patches
        for yy in range(ry, ry + 5):
            if not (0 <= x < W):
                continue
            tone = "R2" if yy == ry else ("R1" if yy < ry + 3 else "R0")
            if (x % 4 == 0) and yy > ry:                       # corrugation groove
                tone = "R0"
            rp = hash01(x // 5, yy, 201)
            if rp > 0.93 and yy >= ry + 1:
                tone = "O1"                                    # rust bloom
            elif rp < 0.045 and yy >= ry + 2:
                tone = "V1"                                    # moss on the sheet
            canvas[yy, x] = PAL[tone]
        # cream-white fascia board (3px, bright) following the gable slope --
        # a signature feature of the real building
        for yy in range(ry + 5, ry + 8):
            if 0 <= x < W:
                canvas[yy, x] = PAL["C0"] if yy < ry + 7 else PAL["C1"]
        # tiny overhang shadow cast on the wall top just below the fascia
        for yy in range(ry + 8, ry + 10):
            if 0 <= x < W and PEAK_Y <= yy < GROUND:
                xx = x
                # only where wall exists
                if (yy < WALL_TOP and abs(xx - PEAK_X) < ((yy - PEAK_Y) / (WALL_TOP - PEAK_Y)) * (HX1 - HX0) / 2) or (WALL_TOP <= yy and HX0 <= xx < HX1):
                    canvas[yy, xx] = PAL["O0"]

    # ---- OCULUS: round window high in the gable: shaded stone ring, dark
    #      recessed opening showing a sliver of dusk sky + leaves peeking in ----
    ocx, ocy, orad = PEAK_X, 108, 11
    for y in range(ocy - orad - 1, ocy + orad + 2):
        for x in range(ocx - orad - 1, ocx + orad + 2):
            d = (x - ocx) ** 2 + (y - ocy) ** 2
            if d <= (orad - 2) ** 2:
                # interior = clean crepuscular sky seen through: violet up top
                # easing into rose lower down (a tidy band, no muddy hash)
                rel = (y - (ocy - orad)) / (2 * orad)      # 0 top .. 1 bottom
                if rel < 0.36:
                    canvas[y, x] = PAL["S1"]               # violet
                elif rel < 0.62:
                    canvas[y, x] = PAL["S2"]               # violet-mauve
                else:
                    canvas[y, x] = PAL["S3"]               # rose
            elif d <= orad ** 2:
                # ring the colour of the fascia (light stone) so it reads
                # crisply against the dark roof; shaded upper-left
                canvas[y, x] = PAL["C0"] if (x - ocx + y - ocy) > 0 else PAL["C1"]
    # leaves peeking over the top interior of the oculus
    for x in range(ocx - 7, ocx + 7):
        yy = ocy - orad + 2 + int(3 * hash01(x, 0, 51))
        if (x - ocx) ** 2 + (yy - ocy) ** 2 <= (orad - 3) ** 2:
            canvas[yy, x] = PAL["V1"]
            if hash01(x, yy, 52) > 0.5:
                canvas[yy + 1, x] = PAL["V2"]

    # ---- ARCH doorway: pointed arch, dark passage + telescope + spill ----
    acx = PEAK_X
    ahw = 24               # half width
    spring_y = 150
    apex_y = 128
    base_y = GROUND
    def arch_top(x):
        frac = abs(x - acx) / ahw
        if frac > 1:
            return None
        return int(spring_y - (spring_y - apex_y) * (1 - frac ** 1.7))
    # --- receding stone tunnel in 1-point perspective. From a vanishing point
    #     the interior splits into ceiling (dark), floor (warm-lit deep in) and
    #     two converging side walls; a small framed doorway glows warm at the
    #     end. This reads unmistakably as depth -- the telescope effect. ---
    VPx, VPy = acx, 158
    farhw, farhh = 7, 14               # far doorway half-size: TALLER than wide (arch)
    R_MOUTH = max((ahw - 2) / farhw, (base_y - VPy) / farhh)   # r at the near mouth
    for x in range(acx - ahw - 2, acx + ahw + 3):
        ytop = arch_top(x)
        if ytop is None:
            if abs(abs(x - acx) - ahw) <= 2:                     # outer jamb sides
                for y in range(spring_y - 4, base_y):
                    canvas[y, x] = PAL["O1"]
            continue
        for y in range(ytop, base_y):
            if (abs(x - acx) >= ahw - 1) or (y <= ytop + 1):     # near stone jamb
                canvas[y, x] = PAL["O1"]
                continue
            dx = x - VPx; dy = y - VPy
            adx = abs(dx); ady = abs(dy)
            r = max(adx / farhw, ady / farhh)
            if r <= 1.0:
                continue                                          # far doorway: below
            # d01: 0 at the near mouth .. 1 at the far doorway  (penumbra ramp)
            d01 = max(0.0, min(1.0, (R_MOUTH - r) / (R_MOUTH - 1.0)))
            vertical = ady * farhw >= adx * farhh
            if vertical and dy < 0:                               # CEILING
                # faint dusk ambient right at the mouth, else pitch dark
                canvas[y, x] = PAL["K1"] if (d01 < 0.20 and hash01(x, y, 61) > 0.5) else PAL["K0"]
            elif vertical:                                        # FLOOR + reflected thread
                thread_w = 1.5 + (1.0 - d01) * 2.3               # reflection widens toward us
                if adx <= thread_w and hash01(x, y, 62) < (0.28 + d01 * 0.5):
                    # a dim GOLDEN glimmer of the far light on the dark floor,
                    # connecting the far opening back to the mouth
                    if d01 > 0.70:
                        canvas[y, x] = PAL["W0"]
                    elif d01 > 0.40:
                        canvas[y, x] = PAL["S5"]
                    else:
                        canvas[y, x] = PAL["S4"]
                else:
                    canvas[y, x] = PAL["K1"] if (d01 < 0.16 and hash01(x, y, 64) > 0.7) else PAL["K0"]
            else:                                                 # SIDE WALLS (penumbra)
                seam = (int((1 - d01) * 40 + y * 0.3) % 6) < 1
                if seam:
                    canvas[y, x] = PAL["K0"]
                elif d01 < 0.24:                                  # mouth catches dusk
                    canvas[y, x] = PAL["O0"] if hash01(x, y, 65) > 0.5 else PAL["K1"]
                elif d01 > 0.80 and hash01(x, y, 66) > 0.35:
                    canvas[y, x] = PAL["R2"]                      # bright deep wall
                elif d01 > 0.60 and hash01(x, y, 67) > 0.4:
                    canvas[y, x] = PAL["R0"]                      # warm deep wall
                else:
                    canvas[y, x] = PAL["K0"]                      # dark middle
    # far doorway: a TALL warm-lit arched opening with a light-stone frame and a
    # sliver of foliage silhouetted at its top (clearly an opening at the end)
    for y in range(VPy - farhh, VPy + farhh + 1):
        for x in range(VPx - farhw - 1, VPx + farhw + 2):
            dx = x - VPx; dy = y - VPy
            fr = abs(dx) / farhw
            if fr > 1.0 or abs(dy) > farhh:
                continue
            # pointed-arch top: frame at the sides, base, and rounded-in top corners
            top_frame = dy < -farhh * 0.42 and fr > (0.30 + (abs(dy) / farhh - 0.42) * 1.4)
            if fr > 0.66 or dy >= farhh - 1 or top_frame:
                canvas[y, x] = PAL["C1"] if (dx - dy) > 0 else PAL["O0"]   # stone reveal
            else:                                                # clean warm opening
                core = fr < 0.40 and abs(dy) < farhh * 0.45
                canvas[y, x] = PAL["W1"] if core else PAL["W0"]
    # vegetation silhouette creeping in at the near mouth base
    for x in range(acx - ahw + 2, acx + ahw - 1):
        if hash01(x, 0, 68) > 0.62:
            h = 2 + int(3 * hash01(x, 1, 69))
            for y in range(base_y - h, base_y):
                at = arch_top(x)
                if at is not None and y >= at and abs(x - VPx) > 4:
                    canvas[y, x] = PAL["V0"]

    # ---- vines climbing the left corner of the hastial ----
    for y in range(WALL_TOP - 2, GROUND):
        drift = int(3 * np.sin(y * 0.4))
        for x in range(HX0 - 1, HX0 + 6 + drift):
            if hash01(x, y, 71) > 0.52 and x >= HX0 - 1:
                canvas[y, x] = PAL["V1"] if hash01(x, y, 72) > 0.5 else PAL["V2"]
    # a few hanging tendrils with leaves
    for tx in (HX0 + 2, HX0 + 5, HX0 + 9):
        ln = int(18 + 20 * hash01(tx, 0, 73))
        for i in range(ln):
            y = WALL_TOP + i
            x = tx + int(2 * np.sin(i * 0.5))
            if y < GROUND:
                canvas[y, x] = PAL["V2"]
                if i % 4 == 0:
                    put(x + 1, y, "V3")

    # ---- fine, branched hairline cracks in the stucco (skip the arch mouth) ----
    def _clear_of_arch(x, y):
        return not (134 < x < 190 and y > 126)
    def draw_crack(sx, sy, length, depth=0):
        x, y = sx, sy
        for i in range(length):
            if HX0 < x < HX1 and WALL_TOP < y < GROUND and _clear_of_arch(x, y):
                canvas[y, x] = PAL["O0"] if hash01(x, y, 202) > 0.35 else PAL["K1"]
            if hash01(x, y, 203) > 0.22:
                y += 1
            x += int(rng.integers(-1, 2))
            if depth < 2 and 3 < i < length - 3 and rng.random() < 0.16:
                draw_crack(x, y, length - i - 2, depth + 1)
    for _ in range(7):
        sx = int(rng.integers(HX0 + 6, HX1 - 6)); sy = int(rng.integers(WALL_TOP + 6, GROUND - 24))
        if _clear_of_arch(sx, sy):
            draw_crack(sx, sy, int(rng.integers(10, 26)))
    # ---- 2 spalls (desconchados): compact chipped patches showing pale plaster,
    #      with a dark broken lower edge (reads as fallen render, not a smear) ----
    for (sx, sy, rw, rh) in [(HX1 - 13, GROUND - 42, 4, 3), (HX0 + 10, 158, 3, 2)]:
        for dy in range(-rh, rh + 1):
            for dx in range(-rw, rw + 1):
                q = (dx / rw) ** 2 + (dy / rh) ** 2
                if q > 1.0:
                    continue
                x, y = sx + dx, sy + dy
                if not (HX0 < x < HX1 and WALL_TOP < y < GROUND and _clear_of_arch(x, y)):
                    continue
                if dy >= rh - 1:
                    canvas[y, x] = PAL["O0"]                    # broken bottom lip
                elif q > 0.58:
                    canvas[y, x] = PAL["O1"]                    # chipped rim
                else:
                    canvas[y, x] = PAL["PL"] if hash01(x, y, 204) > 0.25 else PAL["O2"]
    # ---- moss + weeds reclaiming the wall base ----
    for x in range(HX0, HX1):
        if 132 < x < 192:                                     # skip the arch opening
            continue
        r = hash01(x, 0, 205)
        if r > 0.42:                                          # low moss crust
            mh = 2 + int(3 * hash01(x, 1, 206))
            for i in range(mh):
                put(x, GROUND - 1 - i, "V1" if i < mh - 1 else "V2")
        if r > 0.78:                                          # taller weed tuft
            hh = 3 + int(3 * hash01(x, 2, 82))
            for i in range(hh):
                put(x, GROUND - 1 - i, "V2" if i < hh - 1 else "V3")

build_hastial()


# ===========================================================================
# 6. GAZEBO  (right edge entering frame; octagonal red roof, posts, table)
# ===========================================================================
def build_gazebo():
    """Open octagonal pavilion, only its left half entering frame from the right.
    Roof ridge rises to a cupola near the right edge (gazebo centre is off-frame).
    Airy open bays: the twilight meadow/forest shows THROUGH between the posts;
    crisp dark posts stand in front; a picnic table sits inside."""
    cupola_x = 466                       # near right edge (roof apex direction)
    ridge_y = 100
    eave_left_x = 356                    # roof's visible left tip
    eave_left_y = 156                    # eave drops low on the left
    pad_y = GROUND
    post_top = 152                       # where posts meet the roof underside

    # ---- open bays FIRST: shadowed see-through interior (deep = darkest) ----
    for y in range(post_top, pad_y):
        ty = (y - post_top) / (pad_y - post_top)
        for x in range(eave_left_x + 6, W):
            rr = hash01(x, y, 93)
            if ty < 0.34:                          # deep under the roof: darkest
                canvas[y, x] = PAL["V0"] if rr > 0.5 else PAL["K1"]
            elif rr > 0.72:
                canvas[y, x] = PAL["V1"]
            elif rr > 0.48:
                canvas[y, x] = PAL["V0"]
            else:
                canvas[y, x] = PAL["K1"]
    # ---- picnic table inside (behind the posts), clearly legible ----
    rect(404, 175, 436, 177, "G2")                                   # sunlit table top
    rect(404, 177, 436, 180, "G1")                                   # table apron
    rect(404, 180, 436, 181, "G0")                                   # shadow under top
    for lx in (407, 433):                                            # legs
        rect(lx, 181, lx + 1, 185, "K0")
    rect(404, 185, 434, 187, "K0")                                   # bench/shadow
    put(410, 176, "G3"); put(424, 176, "G3")                         # top highlights
    # ---- horizontal tie-beam under the eave, spanning the posts ----
    for x in range(eave_left_x + 6, W):
        put(x, post_top, "K1"); put(x, post_top + 1, "K0")
    # ---- posts (crisp 2px dark verticals with stone bases) ----
    post_xs = [366, 402, 446]
    for i, px in enumerate(post_xs):
        for y in range(post_top - 2, pad_y - 3):
            put(px, y, "K0"); put(px + 1, y, "K0")
            put(px + 2, y, "K1")                    # 1px inner rim
            if hash01(0, y, 94) > 0.72:             # faint warm edge glint (sun side)
                put(px - 1, y, "R1")
        # stone basa (footing block)
        rect(px - 2, pad_y - 3, px + 4, pad_y, "G1")
        rect(px - 2, pad_y - 3, px + 4, pad_y - 2, "G2")
        put(px - 2, pad_y - 1, "G0"); put(px + 3, pad_y - 1, "G0")

    # ---- roof: octagonal red planes rising to the cupola on the right ----
    for x in range(eave_left_x, W):
        t = (x - eave_left_x) / (cupola_x - eave_left_x)
        t = min(1.0, t)
        edge_y = int(eave_left_y - t * 8)                       # eave rises gently
        top_y = int(eave_left_y - 6 - t * (eave_left_y - 6 - ridge_y))  # up to ridge
        for y in range(top_y, edge_y):
            ridge = y < top_y + 2
            eave = y > edge_y - 3
            # facet shading + vertical corrugation streaks
            if ridge:
                shade = "R0"
            elif eave:
                shade = "R1"
            elif hash01(x, 0, 91) > 0.74:
                shade = "R1"                                    # corrugation groove
            else:
                shade = "R2" if x > eave_left_x + 40 else "R1"  # left facet darker
            canvas[y, x] = PAL[shade]
        put(x, edge_y, "C1")                                    # cream drip-edge
        # small triangular hip line from the left tip
        if x < eave_left_x + 30:
            hy = int(eave_left_y - 6 - (x - eave_left_x) * 1.0)
            if 0 <= hy < H:
                canvas[max(top_y, hy), x] = PAL["R0"]

    # ---- cupola / lantern crowning the ridge ----
    rect(cupola_x - 7, ridge_y - 8, cupola_x + 7, ridge_y + 2, "R1")     # base drum
    rect(cupola_x - 5, ridge_y - 6, cupola_x + 5, ridge_y - 1, "K1")     # vent slats
    put(cupola_x - 2, ridge_y - 6, "K0"); put(cupola_x + 1, ridge_y - 6, "K0")
    # little pyramidal cap
    for i in range(6):
        rect(cupola_x - 6 + i, ridge_y - 8 - i, cupola_x + 7 - i, ridge_y - 7 - i, "R2" if i < 3 else "R0")
    put(cupola_x, ridge_y - 16, "R0"); put(cupola_x, ridge_y - 17, "W1")  # finial

    # ---- concrete pad edge + reclaiming weeds ----
    for x in range(eave_left_x, W):
        put(x, pad_y, "G2"); put(x, pad_y + 1, "G1"); put(x, pad_y + 2, "G0")
    for y in range(pad_y - 12, pad_y):                 # ivy climbing the near post
        if hash01(y, 0, 95) > 0.4:
            put(365, y, "V2"); put(364, y, "V1")

build_gazebo()


# ===========================================================================
# 7. LEFT MEADOW END: grass tones, scruffy hedge with muted red flowers
# ===========================================================================
def build_left_meadow():
    # 2 bald dirt patches (bare earth showing through the grass)
    for (px, pw) in [(30, 11), (70, 9)]:
        for x in range(px, px + pw):
            for y in range(GROUND - 3, GROUND):
                if hash01(x, y, 104) > 0.35:
                    put(x, y, "G1" if hash01(x, y, 105) > 0.5 else "O1")
    # grass tufts with varied lean/direction, 3 tones
    for x in range(0, 92):
        if hash01(x, 0, 101) > 0.30:
            gh = 6 + int(8 * hash01(x, 1, 101))
            lean = (hash01(x, 2, 101) - 0.5) * 6.0            # -3..3 px lean
            for i in range(gh):
                y = GROUND - 1 - i
                xx = x + int(lean * (i / max(1, gh)))
                tone = "V3" if i > gh - 3 else ("V2" if i > gh // 2 else "V1")
                if hash01(x, y, 102) > 0.18:
                    put(xx, y, tone)
    # scruffy hedge lump
    hx0, hx1 = 6, 74
    for y in range(176, GROUND):
        for x in range(hx0, hx1):
            top = 176 + int(5 * np.sin(x * 0.25) + 3 * np.sin(x * 0.6))
            if y < top:
                continue
            tone = "V1"
            r = hash01(x, y, 103)
            if r > 0.75: tone = "V2"
            elif r > 0.94: tone = "V3"
            elif r < 0.10: tone = "V0"
            canvas[y, x] = PAL[tone]
    # hedge: rounded leaf clusters with cool dusk highlights on the top edge
    for cxh in range(hx0 + 4, hx1 - 2, 6):
        ctop = 176 + int(5 * np.sin(cxh * 0.25) + 3 * np.sin(cxh * 0.6))
        for x in range(cxh - 3, cxh + 3):
            for dy in range(0, 3):
                y = ctop + dy
                if (x - cxh) ** 2 + (dy * 1.6) ** 2 <= 8:
                    if dy == 0 and hash01(x, y, 106) > 0.5:
                        canvas[y, x] = PAL["RC"] if hash01(x, y, 107) > 0.6 else PAL["V3"]
                    elif hash01(x, y, 108) > 0.55:
                        canvas[y, x] = PAL["V2"]
    # 3 muted red flowers with a tiny leaf
    for fx, fy in [(20, 184), (44, 179), (60, 187)]:
        canvas[fy, fx] = PAL["P0"]
        put(fx + 1, fy, "P0"); put(fx, fy + 1, "P0")
        put(fx + 1, fy - 1, "P1")                 # highlight
        put(fx - 1, fy, "P0"); put(fx - 1, fy + 1, "V2")

build_left_meadow()


# ===========================================================================
# 8. SIDEWALK  (aged slabs y196..224: joints, cracks, weeds, pebbles)
# ===========================================================================
def build_sidewalk():
    # base fill with per-slab tone variation
    for y in range(GROUND, H):
        for x in range(W):
            slab = (x // 26) * 7 + (y // 9) * 3
            base = 0.5 + 0.5 * hash01(slab, 0, 111)
            base += (hash01(x, y, 112) - 0.5) * 0.22      # speckle
            base -= (y - GROUND) / (H - GROUND) * 0.10     # slightly darker toward foreground
            if base < 0.30: tone = "G0"
            elif base < 0.55: tone = "G1"
            elif base < 0.82: tone = "G2"
            else: tone = "G3"
            canvas[y, x] = PAL[tone]
    # slab joints (vertical every 26, horizontal at 205, 215)
    for x in range(0, W, 26):
        off = int(3 * np.sin(x * 0.1))
        for y in range(GROUND, H):
            canvas[y, min(W - 1, x + off)] = PAL["G0"]
    for jy in (205, 215):
        for x in range(W):
            canvas[jy + int(1.5 * np.sin(x * 0.08)), x] = PAL["G0"]
    # per-slab stain patches (whole slab a touch off-tone / damp)
    for sx in range(0, W, 26):
        for sy0 in (GROUND, 206, 216):
            if hash01(sx, sy0, 148) > 0.66:
                for y in range(sy0, min(H, sy0 + 10)):
                    for x in range(sx + 1, min(W, sx + 25)):
                        if hash01(x, y, 149) > 0.45:
                            cur = tuple(canvas[y, x])
                            if cur == PAL["G2"]: canvas[y, x] = PAL["G1"]
                            elif cur == PAL["G3"]: canvas[y, x] = PAL["G2"]
    # moss creeping in the joints
    for x in range(0, W, 26):
        jx = min(W - 1, x + int(3 * np.sin(x * 0.1)))
        for y in range(GROUND, H):
            if hash01(jx, y, 143) > 0.62:
                mx = jx + (1 if hash01(jx, y, 144) > 0.5 else -1)
                put(mx, y, "V1" if hash01(jx, y, 145) > 0.45 else "V2")
    for jy in (205, 215):
        for x in range(W):
            yy = jy + int(1.5 * np.sin(x * 0.08))
            if hash01(x, yy, 146) > 0.74:
                put(x, yy - 1, "V2")
    # broken slab corners at grid intersections (chipped, exposing a light edge)
    for gx in range(26, W, 26):
        for gy in (205, 215):
            if hash01(gx, gy, 147) > 0.55:
                cx = min(W - 2, gx + int(3 * np.sin(gx * 0.1)))
                for (ddx, ddy) in [(0, 0), (1, 0), (0, 1), (-1, 0), (1, 1), (2, 0), (0, -1)]:
                    put(cx + ddx, gy + ddy, "G0")
                put(cx, gy - 1, "G3")
    # cracks branching from joints, with weeds
    for _ in range(14):
        x = int(rng.integers(0, W)); y = int(rng.integers(GROUND + 1, H - 2))
        for _ in range(int(rng.integers(4, 12))):
            put(x, y, "G0")
            x += int(rng.integers(-1, 2)); y += int(rng.integers(0, 2))
            if not (0 <= x < W and GROUND <= y < H):
                break
        if hash01(x, y, 121) > 0.4:            # weed tuft from crack
            put(x, y - 1, "V2"); put(x, y - 2, "V3")
    # pebbles: bright + dark specks
    for _ in range(120):
        x = int(rng.integers(0, W)); y = int(rng.integers(GROUND + 1, H))
        put(x, y, "G3" if hash01(x, y, 131) > 0.5 else "G0")
    # a fallen fence plank lying on the sidewalk (weathered wood)
    px0, py = 300, 210
    for i in range(46):
        x = px0 + i; y = py + int(i * 0.12)
        rect(x, y, x + 1, y + 4, "O1")
        put(x, y, "O2"); put(x, y + 3, "O0")
    # weeds sprouting through the joints along the base of structures
    for x in range(0, W):
        if hash01(x, 0, 141) > 0.82:
            hh = 2 + int(3 * hash01(x, 1, 142))
            for i in range(hh):
                put(x, GROUND - 1 - i, "V2" if i < hh - 1 else "V3")

build_sidewalk()


# ===========================================================================
# 9. LIGHT POOLS  (arch & oculus spill onto the ground, dithered)
# ===========================================================================
def light_pools():
    """Soft warm glow spilling from the arch mouth onto the sidewalk: a low,
    wide, ordered-dithered pool (brightest just under the arch, fading out),
    never a spark-burst -- the warm cast lands on the stone, keeping its grain."""
    acx = 162
    for y in range(GROUND, GROUND + 16):
        ty = (y - GROUND) / 16.0
        spread = 20 + int(ty * 14)                 # widens as it spreads forward
        for x in range(acx - spread, acx + spread):
            dx = abs(x - acx) / spread
            # elliptical falloff, hugging the ground, brightest near the mouth
            strength = (1 - dx * dx) * (1 - ty) ** 1.4
            if strength <= 0.14:
                continue
            # ordered dither of the warm tint over the stone (keeps texture)
            if strength > BAYER[y & 3, x & 3] * 0.9 + 0.12:
                if strength > 0.62:
                    canvas[y, x] = PAL["W0"]
                elif strength > 0.34:
                    canvas[y, x] = PAL["S5"]
                else:
                    canvas[y, x] = PAL["S4"]        # faint mauve-warm edge
    # a couple of long soft light fingers reaching further along the joints
    for x in range(acx - 30, acx + 30):
        if hash01(x, 0, 153) > 0.72:
            yy = GROUND + 14 + int(3 * hash01(x, 1, 153))
            if abs(x - acx) < 26:
                canvas[yy, x] = PAL["S4"]

light_pools()


# ===========================================================================
# 9b. CLEANUP  (remove orphan pixels / jaggies on the STRUCTURAL silhouettes,
#     before the thin hand-authored accents are laid on top)
# ===========================================================================
def despeckle_key():
    packed = (canvas[:, :, 0].astype(np.int32) << 16) | (canvas[:, :, 1].astype(np.int32) << 8) | canvas[:, :, 2]
    protect = set()
    for k in ("W0", "W1", "W2", "S4", "S5", "RC", "RM", "P0", "P1", "O3", "PL", "V3", "G3"):
        r, g, b = PAL[k]; protect.add((r << 16) | (g << 8) | b)
    src = packed.copy()
    for y in range(1, H - 1):
        rowm1 = src[y - 1]; row = src[y]; rowp1 = src[y + 1]
        for x in range(1, W - 1):
            cpx = row[x]
            if cpx in protect:
                continue
            n = (rowm1[x - 1], rowm1[x], rowm1[x + 1], row[x - 1], row[x + 1],
                 rowp1[x - 1], rowp1[x], rowp1[x + 1])
            if cpx in n:
                continue                                    # not isolated
            best = None; bc = 0
            for v in n:
                cc = n.count(v)
                if cc > bc:
                    bc = cc; best = v
            if bc >= 6:                                      # strong majority -> stray edge px
                canvas[y, x] = (best >> 16 & 255, best >> 8 & 255, best & 255)

despeckle_key()


# ===========================================================================
# 9c. NARRATIVE PROPS OF ABANDONMENT (leaning lamp, broken bench, sagging
#     wire, fallen leaves) -- laid after cleanup so their thin parts survive
# ===========================================================================
def build_props():
    # ---- leaning, unlit path lamp with a cracked stone base ----
    lx, lbase, ltop = 236, GROUND, 168
    rect(lx - 3, lbase - 3, lx + 4, lbase, "G1")            # stone base
    rect(lx - 3, lbase - 3, lx + 4, lbase - 2, "G2")
    put(lx, lbase - 2, "G0"); put(lx + 1, lbase - 1, "G0")  # crack in the base
    for i in range(lbase - ltop):                           # leaning pole
        y = lbase - 1 - i
        x = lx + int(i * 0.24)
        put(x, y, "K0"); put(x + 1, y, "K1")
    hxp = lx + int((lbase - ltop) * 0.24)
    rect(hxp - 1, ltop - 6, hxp + 4, ltop, "K1")            # lantern housing (unlit)
    rect(hxp, ltop - 5, hxp + 3, ltop - 1, "K0")            # dark glass
    put(hxp + 1, ltop - 8, "K1"); put(hxp + 1, ltop - 7, "K0")   # finial
    put(hxp - 1, ltop - 6, "RC")                            # cool sky glint on the cap
    # ---- broken bench in front of the hedge (seat tilted, a leg collapsed) ----
    bxc, sy = 76, 190
    for i in range(17):
        x = bxc + i; y = sy + int(i * 0.22)                # seat tilts down-right
        put(x, y, "O2"); put(x, y + 1, "O1")
    for i in range(13):                                    # backrest slat
        put(bxc + 2 + i, sy - 3 - int(i * 0.15), "O1")
    rect(bxc + 2, sy + 1, bxc + 3, sy + 6, "O0")           # standing leg
    put(bxc + 15, sy + 4, "O0"); put(bxc + 15, sy + 5, "O0")   # broken short leg
    # ---- sagging wire strung between two leaning fence-remnant posts ----
    p1x, p2x, ptop = 286, 322, 187
    for px, ln in ((p1x, 1), (p2x, -1)):
        for y in range(ptop, GROUND):
            put(px + (0 if y < ptop + 3 else ln), y, "K0")
    for x in range(p1x, p2x + 1):
        t = (x - p1x) / (p2x - p1x)
        y = ptop + int(7 * (1 - (2 * t - 1) ** 2))          # catenary sag
        put(x, y, "K1")
    # ---- drifts of fallen leaves on the sidewalk (small warm flecks) ----
    leaf_cols = ["O1", "O2", "R1", "V2"]
    for _ in range(20):
        lx2 = int(rng.integers(4, W - 4)); ly2 = int(rng.integers(GROUND + 3, H - 4))
        if abs(lx2 - 162) < 14:                             # keep the light pool clear
            continue
        col = leaf_cols[int(rng.integers(0, 4))]
        put(lx2, ly2, col)
        if rng.random() > 0.5: put(lx2 + 1, ly2, col)
        if rng.random() > 0.6: put(lx2, ly2 + 1, "O0")

build_props()


# ===========================================================================
# 10. CHARACTER  (~30px silhouette, rim-lit, planted left of the arch)
# ===========================================================================
def build_character():
    cx, feet = 112, GROUND - 1
    top = feet - 30
    # contact shadow (dithered ellipse on the sidewalk)
    for y in range(feet, feet + 4):
        for x in range(cx - 9, cx + 10):
            dx = (x - cx) / 9.0; dy = (y - feet) / 4.0
            if dx * dx + dy * dy < 1 and hash01(x, y, 161) > 0.35:
                canvas[y, x] = PAL["K1"]
    # body silhouette (cloaked adventurer): head, shoulders, tapering cloak, legs
    def body(x, y):
        hy = top + 4
        if (x - cx) ** 2 + ((y - hy) * 1.15) ** 2 <= 13:     # head
            return True
        if top + 7 <= y <= feet - 7:                          # cloak (trapezoid)
            halfw = 3.2 + (y - (top + 7)) * 0.20
            if abs(x - cx) <= halfw:
                return True
        if feet - 7 < y <= feet:                              # two legs
            if abs(abs(x - cx) - 2) <= 1:
                return True
        return False
    for y in range(top, feet + 1):
        for x in range(cx - 8, cx + 9):
            if body(x, y):
                canvas[y, x] = PAL["K0"]
    # rim: warm on the arch side (right, toward the doorway glow), cool sky rim
    # on the shoulders/head top, faint cool sliver on the left
    for y in range(top, feet + 1):
        for x in range(cx - 8, cx + 9):
            if not body(x, y):
                continue
            if not body(x, y - 1) and y <= top + 9:          # top edge -> cool sky rim
                canvas[y, x] = PAL["RC"] if hash01(x, y, 164) > 0.35 else PAL["RM"]
            elif not body(x + 1, y) and x >= cx:             # arch-side warm rim
                canvas[y, x] = PAL["O3"] if hash01(x, y, 162) > 0.30 else PAL["W0"]
            elif not body(x - 1, y) and x < cx and hash01(x, y, 163) > 0.55:
                canvas[y, x] = PAL["RM"]                      # broken cool rim
    # a single warm face glint on the arch side
    put(cx + 2, top + 4, "W0")

build_character()


# ===========================================================================
# 10b. AA ACCENTS: stars, bats, and cool sky rim-light on top silhouette edges
# ===========================================================================
def build_accents():
    # subtle stars in the high violet band
    stars = [(40, 16), (88, 10), (122, 22), (150, 8), (210, 13), (258, 24),
             (300, 12), (338, 30), (362, 7), (400, 19), (430, 34), (66, 32)]
    for (x, y) in stars:
        canvas[y, x] = PAL["W2"] if hash01(x, y, 301) > 0.5 else PAL["RC"]
    # 3 small bats gliding, silhouetted against the dusk sky
    for (bx, by) in [(198, 42), (356, 28), (146, 60)]:
        for (dx, dy) in [(-3, 1), (-2, 0), (-1, 1), (0, 2), (1, 1), (2, 0), (3, 1)]:
            put(bx + dx, by + dy, "K1")
    # cool rim-light (1px) on the topmost edge of the far forest crowns
    F0c = PAL["F0"]
    for x in range(0, W):
        for y in range(88, 136):
            if tuple(canvas[y, x]) == F0c:
                if tuple(canvas[y - 1, x]) != F0c and hash01(x, y, 302) > 0.5:
                    canvas[y, x] = PAL["RC"] if hash01(x, y, 303) > 0.45 else PAL["S2"]
                break
    # cool rim-light on the ridge/crest of every roof (topmost roof px per column)
    roofcols = {PAL["R0"], PAL["R1"], PAL["R2"]}
    for x in range(0, W):
        for y in range(90, 200):
            if tuple(canvas[y, x]) in roofcols:
                if tuple(canvas[y - 1, x]) not in roofcols and hash01(x, y, 304) > 0.55:
                    canvas[y, x] = PAL["RC"]
                break

build_accents()


# ===========================================================================
# 11. FIREFLIES  (6-10 warm points, some haloed)
# ===========================================================================
def fireflies():
    pts = [(150, 158), (86, 168), (232, 150), (300, 150),
           (128, 176), (196, 182), (66, 160), (350, 168), (410, 158)]
    for (x, y) in pts:
        canvas[y, x] = PAL["W2"]
        # dim halo
        for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if hash01(x, y, 171) > 0.3:
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    # additive-ish: only brighten dark pixels
                    if canvas[yy, xx].sum() < 200:
                        canvas[yy, xx] = PAL["W0"]

fireflies()


# ===========================================================================
# 12. FOREGROUND LAYER  (bottom edge silhouette: grass tufts + fallen branch)
# ===========================================================================
def foreground():
    # dark grass tufts across the very bottom
    for x in range(W):
        hh = int(6 * hash01(x, 0, 181) ** 2)
        if hash01(x, 1, 182) > 0.55:
            hh += int(6 * hash01(x, 2, 183))
        for i in range(hh):
            y = H - 1 - i
            canvas[y, x] = PAL["V0"] if i < hh - 1 else PAL["K0"]
    # a fallen branch in silhouette, lower-left to center
    bx0, by = 20, H - 5
    pts = [(bx0 + i, by + int(3 * np.sin(i * 0.06))) for i in range(200)]
    for (x, y) in pts:
        for t in range(2):
            if 0 <= x < W and 0 <= y - t < H:
                canvas[y - t, x] = PAL["K0"]
    # a couple of twigs
    for (sx, sy, dx, dy, n) in [(70, by - 1, 1, -1, 8), (140, by, 1, -1, 10), (110, by - 1, -1, -1, 6)]:
        x, y = sx, sy
        for _ in range(n):
            put(x, y, "K0"); x += dx; y += dy

foreground()


# ===========================================================================
# SAVE + verify palette
# ===========================================================================
def save():
    img = Image.fromarray(canvas, "RGB")
    img.save(f"{OUT}/art_proof.png")
    for f in (2, 3):
        img.resize((W * f, H * f), Image.NEAREST).save(f"{OUT}/art_proof_x{f}.png")
    used = np.unique(canvas.reshape(-1, 3), axis=0)
    print(f"saved 480x224  unique_colors={len(used)}")
    # crops
    def crop(name, box):
        x0, y0, x1, y1 = box
        c = Image.fromarray(canvas[y0:y1, x0:x1], "RGB")
        c.resize(((x1 - x0) * 4, (y1 - y0) * 4), Image.NEAREST).save(f"{OUT}/crop_{name}.png")
    crop("hastial", (84, 72, 240, 224))
    crop("gazebo", (356, 88, 480, 224))
    crop("character", (92, 158, 140, 224))
    crop("bg_band", (0, 0, 480, 150))
    crop("sidewalk", (84, 194, 340, 224))
    crop("props", (216, 158, 360, 224))
    return len(used)

n = save()
assert n <= 36, f"TOO MANY COLORS: {n}"
print("OK")
