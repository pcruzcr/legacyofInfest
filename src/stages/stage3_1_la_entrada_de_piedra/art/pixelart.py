"""Primitivas de pixel-art para Stage 3-1 (seccion 5.2 del brief).
Todo con PIL. Tiles de 16x16. Organico = supersample 4x + LANCZOS.
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter
from palette import (
    PIEDRA, GRAFITO, TERRACOTA, CESPED, FOLLAJE, TRONCO, VIDRIO, METAL, FLOR,
    hx, ramp_rgb, lerp_color, dither_pixel, surface_noise_mask, RNG_SEED,
)

T = 16  # tile size


def new_tile(bg=(0, 0, 0, 0)):
    return Image.new("RGBA", (T, T), bg)


def ramp_fill_dithered(img, ramp_hex, top_light=True, ao_top=False, ao_bottom=True,
                        noise=6, seed=RNG_SEED, x0=0, y0=0, w=T, h=T):
    """Rellena un rectangulo con una rampa vertical de 5 tonos (dithering
    Bayer entre bandas), linea de AO de 1-2px, y ruido de superficie."""
    ramp = ramp_rgb(ramp_hex)
    n = len(ramp)
    px = img.load()
    for yy in range(y0, y0 + h):
        t = (yy - y0) / max(1, h - 1)
        # luz arriba (t=0) si top_light, si no luz abajo
        tt = (1 - t) if top_light else t
        scaled = tt * (n - 1)
        lo = int(scaled)
        lo = max(0, min(n - 2, lo))
        frac = scaled - lo
        for xx in range(x0, x0 + w):
            idx = lo + 1 if dither_pixel(xx, yy, frac) else lo
            px[xx, yy] = ramp[idx] + (255,)
    # AO: 1-2px del tono mas oscuro en los bordes de contacto
    if ao_bottom:
        for xx in range(x0, x0 + w):
            px[xx, y0 + h - 1] = ramp[0] + (255,)
            if h > 1:
                yv = px[xx, y0 + h - 2]
                px[xx, y0 + h - 2] = lerp_color(yv[:3], ramp[0], 0.4) + (255,)
    if ao_top:
        for xx in range(x0, x0 + w):
            px[xx, y0] = ramp[min(n - 1, len(ramp) - 1)] + (255,)
    # ruido de superficie reproducible
    pts = surface_noise_mask(w, h, noise, seed=seed + x0 * 131 + y0)
    for (nx, ny) in pts:
        xx, yy = x0 + nx, y0 + ny
        if x0 <= xx < x0 + w and y0 <= yy < y0 + h:
            cur = px[xx, yy][:3]
            idx = ramp.index(min(ramp, key=lambda c: sum((a - b) ** 2 for a, b in zip(c, cur))))
            newidx = max(0, min(n - 1, idx + random.Random(seed + xx * 7 + yy * 13).choice([-1, 1])))
            px[xx, yy] = ramp[newidx] + (255,)
    return img


def terrain_variant(ramp_hex, variant, kind="ground", seed=RNG_SEED):
    """Tile de terreno con textura ESTRUCTURADA (Plan seccion 5.3/6):
    bloques irregulares con junta de mortero de 1px, esquinas descascaradas,
    musgo en juntas horizontales, AO de 1-2px bajo cada hilada. Nada de
    ruido por pixel ni dithering sobre el relleno (solo en los 1-2px de
    frontera bloque/junta)."""
    img = new_tile()
    s = seed + variant * 977
    rng = random.Random(s)
    ramp = ramp_rgb(ramp_hex)
    px = img.load()
    follaje = ramp_rgb(FOLLAJE)

    if kind == "ground":
        # 2 hiladas de bloques de ancho irregular (adoquin)
        rows = [(0, 8), (8, 8)]
        for ry, rh in rows:
            x = 0
            while x < T:
                bw = rng.choice([5, 6, 7])
                bw = min(bw, T - x)
                tone = ramp[rng.choice([2, 2, 3])]
                for yy in range(ry, ry + rh):
                    for xx in range(x, x + bw):
                        px[xx, yy] = tone + (255,)
                # highlight superior del bloque (luz desde arriba)
                for xx in range(x, x + bw):
                    px[xx, ry] = ramp[min(4, ramp.index(tone) + 1)] + (255,)
                # junta vertical (mortero, 1px, tono mas oscuro)
                jx = x + bw
                if jx < T:
                    for yy in range(ry, ry + rh):
                        px[jx, yy] = ramp[0] + (255,)
                # esquina descascarada ocasional
                if rng.random() < 0.3 and bw > 3:
                    cx = x + rng.randrange(0, bw)
                    px[min(T - 1, cx), ry] = ramp[0] + (255,)
                x += bw + 1
        # junta horizontal entre hiladas + AO + musgo esporadico
        for xx in range(T):
            px[xx, 7] = ramp[0] + (255,)
            if rng.random() < 0.25:
                px[xx, 7] = follaje[rng.choice([2, 3])] + (255,)
        # AO de 2px bajo el tile (linea de contacto con lo de abajo)
        for xx in range(T):
            px[xx, T - 1] = ramp[0] + (255,)
            cur = px[xx, T - 2][:3]
            px[xx, T - 2] = lerp_color(cur, ramp[0], 0.45) + (255,)

    elif kind == "wall":
        # hiladas de bloque de muro, alternadas (aparejo real), con junta
        row_h = 4
        for ry in range(0, T, row_h):
            off = 3 if (ry // row_h) % 2 else 0
            x = off - row_h if off else 0
            while x < T:
                bw = row_h - 1
                x0, x1 = max(0, x), min(T, x + bw)
                if x1 > x0:
                    tone = ramp[rng.choice([1, 2, 2, 3])]
                    for yy in range(ry, min(T, ry + row_h - 1)):
                        for xx in range(x0, x1):
                            px[xx, yy] = tone + (255,)
                    for xx in range(x0, x1):
                        px[xx, ry] = ramp[min(4, ramp.index(tone) + 1)] + (255,)
                x += row_h
            # junta horizontal (mortero) + AO
            for xx in range(T):
                px[xx, min(T - 1, ry + row_h - 1)] = ramp[0] + (255,)
        # musgo en un par de juntas horizontales inferiores
        for ry in range(row_h, T, row_h):
            if rng.random() < 0.4:
                for xx in range(T):
                    if rng.random() < 0.5:
                        px[xx, min(T - 1, ry - 1)] = follaje[2] + (255,)
    elif kind == "block":
        # bloque solido (terracota/vidrio) con junta perimetral leve
        tone = ramp[2]
        for yy in range(T):
            for xx in range(T):
                px[xx, yy] = tone + (255,)
        for xx in range(T):
            px[xx, 0] = ramp[3] + (255,)
            px[xx, T - 1] = ramp[0] + (255,)
        for yy in range(T):
            px[0, yy] = ramp[1] + (255,)
    return img


def grass_top_variant(variant, seed=RNG_SEED):
    """Cesped: tierra con estratos + briznas de 3-6px que rompen el borde
    superior (nunca una linea recta de mas de 6px). Plan 6.5/D.5."""
    img = new_tile()
    px = img.load()
    s = seed + variant * 631
    rng = random.Random(s)
    ces = ramp_rgb(CESPED)
    tronco = ramp_rgb(TRONCO)
    # tierra: 2-3 estratos horizontales de grosor variable
    y = 6
    strata = []
    while y < T:
        h = rng.choice([3, 4, 5])
        strata.append((y, min(T, y + h)))
        y += h
    for i, (y0, y1) in enumerate(strata):
        tone = tronco[1 + (i % 3)]
        for yy in range(y0, y1):
            for xx in range(T):
                px[xx, yy] = tone + (255,)
        for xx in range(T):
            px[xx, y0] = tronco[0] + (255,)
        if rng.random() < 0.5:
            px[rng.randrange(T), (y0 + y1) // 2] = tronco[4] + (255,)  # piedrita
    # capa de pasto (bloque solido) hasta la linea base irregular
    base = [6 + rng.choice([-1, 0, 0, 1]) for _ in range(T)]
    for xx in range(T):
        for yy in range(base[xx], 6):
            px[xx, yy] = ces[rng.choice([1, 2, 2])] + (255,)
    # briznas que sobresalen del borde (3-6px), densidad variable
    x = 0
    while x < T:
        if rng.random() < 0.75:
            bh = rng.randrange(3, 7)
            top = base[x] - bh
            tone = ces[rng.choice([2, 3, 4])]
            for yy in range(max(0, top), base[x]):
                px[x, yy] = tone + (255,)
            if x + 1 < T and rng.random() < 0.4:
                for yy in range(max(0, top + 1), base[x]):
                    px[x + 1, yy] = ces[3] + (255,)
        x += rng.choice([1, 1, 2])
    return img


def gothic_window(ramp_glass, ramp_frame, lit=True):
    img = new_tile()
    px = img.load()
    frame = ramp_rgb(ramp_frame)
    glass = ramp_rgb(ramp_glass)
    for y in range(T):
        for x in range(T):
            px[x, y] = frame[1] + (255,)
    # arco ojival simple
    for y in range(2, T - 2):
        inset = max(0, 4 - int((y - 2) * 0.6)) if y < 6 else 3
        for x in range(3 + inset, T - 3 - inset):
            g = glass[3] if lit else glass[1]
            if dither_pixel(x, y, 0.5) and lit:
                g = glass[4]
            px[x, y] = g + (255,)
    for x in range(T):
        px[x, T - 1] = frame[0] + (255,)
    for y in range(T):
        px[1, y] = frame[3] + (255,) if 2 < y < T - 2 else px[1, y]
    return img


def column_tile(ramp_hex, part="shaft"):
    img = new_tile()
    ramp_fill_dithered(img, ramp_hex, top_light=True, ao_bottom=False, noise=3, x0=4, y0=0, w=8, h=T)
    px = img.load()
    ramp = ramp_rgb(ramp_hex)
    if part == "capital":
        for x in range(0, T):
            for y in range(0, 5):
                w = max(0, 6 - abs(x - 8))
                if abs(x - 8) <= 7 - y:
                    px[x, y] = ramp[3] + (255,)
        for x in range(T):
            px[x, 4] = ramp[0] + (255,)
    for y in range(T):
        px[3, y] = (0, 0, 0, 0)
        px[T - 4, y] = (0, 0, 0, 0)
        if 4 <= y or part != "capital":
            pass
    return img


def blob_mask(size, seed, n_ellipses=8, scale=4, blur=0.8, lobe_gap=True):
    """Union de elipses -> mascara suavizada (para nubes/copas). size=(w,h) final."""
    w, h = size
    big = Image.new("L", (w * scale, h * scale), 0)
    d = ImageDraw.Draw(big)
    rng = random.Random(seed)
    for _ in range(n_ellipses):
        cx = rng.uniform(w * 0.14, w * 0.86) * scale
        cy = rng.uniform(h * 0.38, h * 0.88) * scale
        rx = rng.uniform(w * 0.16, w * 0.30) * scale
        ry = rng.uniform(h * 0.20, h * 0.36) * scale
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    big = big.filter(ImageFilter.GaussianBlur(scale * blur))
    small = big.resize((w, h), Image.LANCZOS)
    return small


def cloud_sprite(w, h, seed, tones, light_from="right", size_class="media"):
    """Nube (Plan seccion 6.4): base plana y oscura, lobulos apoyados en
    y_base, sombreado en 5 bandas apiladas HACIA EL LADO DE LUZ (no por
    profundidad de mascara), rim light solo en el borde iluminado,
    dithering SOLO en 2-3px de frontera entre bandas (nunca sobre el
    relleno)."""
    rng = random.Random(seed)
    y_base = int(h * 0.82)
    big_scale = 4
    big = Image.new("L", (w * big_scale, h * big_scale), 0)
    d = ImageDraw.Draw(big)
    n_lobes = rng.randint(8, 12)
    for i in range(n_lobes):
        frac = i / max(1, n_lobes - 1)
        bell = max(0.35, 1.0 - abs(frac - 0.5) * 1.7)  # campana: mas grandes al centro
        r = (w * 0.10 * bell + w * 0.05 * rng.random()) * big_scale
        cx = (w * 0.08 + frac * w * 0.84) * big_scale
        cy = y_base * big_scale - r * rng.uniform(0.35, 0.75)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    for _ in range(rng.randint(3, 5)):
        r = w * rng.uniform(0.07, 0.13) * big_scale
        cx = (w * 0.25 + rng.random() * w * 0.5) * big_scale
        cy = y_base * big_scale - r * rng.uniform(1.2, 2.4)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    # base plana: recorta todo por debajo de y_base (nada cuelga mas de 4px)
    d.rectangle([0, (y_base + 4) * big_scale, w * big_scale, h * big_scale], fill=0)
    big = big.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))  # cierre morfologico ~2px
    mask = big.resize((w, h), Image.LANCZOS)
    mpx = mask.load()

    sign = -1 if light_from == "right" else 1
    n = len(tones)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    alpha_by_class = {"lejana": (150, 185), "media": (205, 230), "cercana": (240, 255)}
    a_lo, a_hi = alpha_by_class.get(size_class, (205, 230))

    for y in range(h):
        for x in range(w):
            a = mpx[x, y]
            if a < 60:
                continue
            # banda base oscura: 25% inferior de la nube = tono 1 (duro, sin dithering)
            if y > y_base - (y_base * 0.25):
                local_band = 0
            else:
                lit_amount = (x / w) if light_from == "right" else (1 - x / w)
                height_amount = 1.0 - (y / max(1, y_base))
                score = 0.20 + 0.50 * lit_amount + 0.30 * height_amount
                scaled = min(n - 1.01, max(0.0, score * (n - 1)))
                lo = int(scaled)
                frac = scaled - lo
                # dithering SOLO en la franja real de transicion entre bandas
                # (frac cerca de 0.5, banda de ~30% del paso -> 2-3px reales)
                if 0.35 < frac < 0.65 and lo < n - 1:
                    local_band = lo + 1 if dither_pixel(x, y, 0.5) else lo
                else:
                    local_band = lo if frac <= 0.5 else min(n - 1, lo + 1)
            alpha = a_hi if a > 150 else int(a_lo + (a / 150) * (a_hi - a_lo))
            px[x, y] = tones[local_band][:3] + (alpha,)

    # rim light: 2px del tono mas claro, solo contorno del lado iluminado
    rim_x_range = range(int(w * 0.55), w) if light_from == "right" else range(0, int(w * 0.45))
    for x in rim_x_range:
        for y in range(h):
            if mpx[x, y] < 60:
                continue
            neigh = mpx[min(w - 1, x + (1 if light_from == "right" else -1)), y]
            if neigh < 60:  # borde real de la mascara
                px[x, y] = tones[-1][:3] + (a_hi,)
    return img


def tree_sprite(tiles_w, tiles_h, seed, flowers=False, silhouette=False):
    """Arbol de tiles_w x tiles_h tiles (16px c/u). 3 capas: tronco, follaje
    en clusters, hojas sueltas. Sombra de contacto en base."""
    w, h = tiles_w * T, tiles_h * T
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    tronco = ramp_rgb(TRONCO)
    follaje = ramp_rgb(FOLLAJE)
    flor = ramp_rgb(FLOR)

    # tronco con raices
    trunk_w = max(3, w // 8)
    tx = w // 2
    for y in range(h - 6, h * 3 // 5, -1):
        wob = int(1.2 * (1 if (y // 3) % 2 == 0 else -1))
        left = tx - trunk_w // 2 + wob
        right = tx + trunk_w // 2 + wob
        for x in range(left, right):
            shade = tronco[2] if x < tx else tronco[3]
            img.putpixel((x, y), shade + (255,))
        img.putpixel((left, y), tronco[1] + (255,))
        img.putpixel((right - 1, y), tronco[0] + (255,))
    # raices
    for dx in (-trunk_w, trunk_w):
        for i in range(4):
            rx = tx + dx // 2 + (dx // abs(dx)) * i
            ry = h - 6 + i // 2
            if 0 <= rx < w and 0 <= ry < h:
                img.putpixel((rx, ry), tronco[1] + (255,))

    # follaje: 3-5 clusters solapados via blob_mask, tono segun silhouette
    canopy_h = int(h * 0.62)
    canopy_top = 0
    cmask_w, cmask_h = w, canopy_h
    n_clusters = rng.randint(3, 5)
    canopy = Image.new("RGBA", (cmask_w, cmask_h), (0, 0, 0, 0))
    for i in range(n_clusters):
        cw = int(cmask_w * rng.uniform(0.45, 0.8))
        ch = int(cmask_h * rng.uniform(0.5, 0.85))
        m = blob_mask((cw, ch), seed + i * 31, n_ellipses=6)
        cx = rng.randrange(0, max(1, cmask_w - cw))
        cy = rng.randrange(0, max(1, cmask_h - ch))
        cpx = canopy.load()
        mpx = m.load()
        for yy in range(ch):
            for xx in range(cw):
                a = mpx[xx, yy]
                if a < 50:
                    continue
                dest = (cx + xx, cy + yy)
                if not (0 <= dest[0] < cmask_w and 0 <= dest[1] < cmask_h):
                    continue
                # luz direccional: viene del horizonte (derecha, Acto I)
                lit = (xx / cw) > 0.45
                if silhouette:
                    tone = follaje[1] if lit else follaje[0]
                else:
                    tone = follaje[3] if lit else follaje[1]
                    if lit and (xx / cw) > 0.75:
                        tone = follaje[4]
                cur = cpx[dest]
                if cur[3] < a:
                    cpx[dest] = tone + (min(255, a + 30),)
    img.alpha_composite(canopy, (0, canopy_top))

    if flowers and not silhouette:
        fpx = img.load()
        for _ in range(rng.randint(10, 16)):
            fx = rng.randrange(w // 6, w - w // 6)
            fy = rng.randrange(canopy_top, canopy_h)
            if fpx[fx, fy][3] > 0:
                fpx[fx, fy] = flor[rng.randint(2, 4)] + (255,)

    # hojas sueltas fuera del contorno
    for _ in range(rng.randint(15, 26)):
        lx = int(rng.gauss(w / 2, w * 0.32))
        ly = int(rng.gauss(canopy_h * 0.45, canopy_h * 0.3))
        if 0 <= lx < w and 0 <= ly < canopy_h:
            tone = follaje[rng.randint(1, 3)]
            img.putpixel((lx, ly), tone + (220,))

    # sombra de contacto eliptica
    shadow = Image.new("RGBA", (w, T), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    ew = int(w * 0.55)
    sd.ellipse([(w - ew) // 2, 4, (w + ew) // 2, 12], fill=CESPED_SHADOW())
    img.alpha_composite(shadow, (0, h - T))
    return img


def CESPED_SHADOW():
    c = ramp_rgb(CESPED)[0]
    return c + (90,)


def bush_sprite(tiles_w, tiles_h, seed, ramp_hex=None):
    ramp_hex = ramp_hex or FOLLAJE
    w, h = tiles_w * T, tiles_h * T
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask = blob_mask((w, h - 3), seed, n_ellipses=5)
    ramp = ramp_rgb(ramp_hex)
    px = img.load()
    mpx = mask.load()
    for y in range(h - 3):
        for x in range(w):
            a = mpx[x, y]
            if a < 60:
                continue
            lit = (x / w) > 0.45
            idx = 3 if lit else 1
            px[x, y] = ramp[idx] + (255 if a > 120 else 200,)
    for x in range(w):
        px[x, h - 3] = ramp[0] + (200,)
    return img


def flower_cluster(seed):
    img = new_tile()
    px = img.load()
    rng = random.Random(seed)
    flor = ramp_rgb(FLOR)
    ces = ramp_rgb(CESPED)
    for x in range(T):
        for y in range(11, T):
            px[x, y] = ces[rng.choice([0, 1])] + (255,)
    for _ in range(rng.randint(3, 5)):
        fx = rng.randrange(1, T - 1)
        fy = rng.randrange(4, 11)
        img.putpixel((fx, fy), flor[2] + (255,))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= fx + dx < T and 0 <= fy + dy < T:
                px[fx + dx, fy + dy] = flor[rng.randint(3, 4)] + (255,)
    return img


def farola(lit=True):
    img = new_tile()
    px = img.load()
    metal = ramp_rgb(METAL)
    for y in range(6, T):
        px[7, y] = metal[1] + (255,)
        px[8, y] = metal[2] + (255,)
    for x in range(4, 12):
        px[x, 5] = metal[0] + (255,)
    glow = (232, 190, 120, 220) if lit else metal[3] + (255,)
    for x in range(5, 11):
        for y in range(1, 5):
            if (x - 7.5) ** 2 / 9 + (y - 3) ** 2 / 4 <= 1:
                px[x, y] = glow
    return img


def fog_tile(sky_color, top_alpha=0, bottom_alpha=120, w=T, h=T):
    """Franja de niebla horizontal (Plan 6.1): color muestreado del cielo,
    alpha creciente de arriba (0) a abajo (bottom_alpha, donde se apoya el
    plano de adelante). Va como fila completa entre dos planos."""
    img = new_tile()
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        a = int(top_alpha + (bottom_alpha - top_alpha) * t)
        for x in range(w):
            px[x, y] = sky_color[:3] + (a,)
    return img


def haze_band(warm_color, w=T, h=T, alpha=70):
    """Calima aditiva del horizonte: franja calida uniforme, blend aditivo
    en el ensamblado (se pinta con BLEND_RGB_ADD si el motor lo permite;
    aqui se deja como alpha-over suave)."""
    img = new_tile()
    px = img.load()
    for y in range(h):
        # Antes era alpha uniforme, y en pantalla se leia como una franja
        # con dos bordes duros de lado a lado: parecia un fallo de dibujado,
        # no calima. Ahora cae a cero en los dos extremos con una campana
        # (seno), asi la banda se funde con el cielo por arriba y por abajo.
        t = (y + 0.5) / h
        a = int(alpha * math.sin(math.pi * t))
        for x in range(w):
            px[x, y] = warm_color[:3] + (a,)
    return img


def ivy_strand(seed):
    img = new_tile()
    px = img.load()
    rng = random.Random(seed)
    follaje = ramp_rgb(FOLLAJE)
    x = rng.randrange(4, 12)
    for y in range(T):
        x += rng.choice([-1, 0, 0, 1])
        x = max(1, min(T - 2, x))
        if rng.random() < 0.85:
            px[x, y] = follaje[rng.randint(2, 4)] + (255,)
        if rng.random() < 0.3:
            px[max(0, x - 1), y] = follaje[rng.randint(1, 3)] + (255,)
    return img


# =========================================================================
# ANIMACION (Entrega II) — variantes por fotograma.
#
# pyscroll anima baldosas de forma nativa cuando el TMX declara
# <tile id="N"><animation><frame tileid=".." duration=".."/></animation>.
# Confirmado en .venv/Lib/site-packages/pyscroll/orthographic.py:414
# (process_animation_queue) y data.py:150 (reload_animations). Por eso los
# fotogramas son baldosas normales del mismo atlas: no hace falta tocar el
# motor, solo declarar la animacion en el tileset del TMX.
#
# Todas las funciones son deterministas: dependen de (seed, phase), nunca de
# random() en tiempo de ejecucion.
# =========================================================================

def _shift_tile(base, amount, anchor="bottom"):
    """Desplaza el contenido de una baldosa lateralmente con un gradiente.

    `anchor="bottom"`: la base queda fija y la punta se dobla (hiedra que
    cuelga desde arriba se ancla arriba; una brizna se ancla abajo). El
    desplazamiento es proporcional a la distancia al ancla, que es lo que
    hace que se lea como flexion y no como traslacion.
    """
    bp = base.load()
    out = new_tile()
    op = out.load()
    for y in range(T):
        t = (y / (T - 1)) if anchor == "top" else (1.0 - y / (T - 1))
        d = int(round(amount * t))
        for x in range(T):
            c = bp[x, y]
            if c[3]:
                nx = x + d
                if 0 <= nx < T:
                    op[nx, y] = c
    return out


#: Amplitud del vaiven, en pixeles, para un ciclo de 4 fotogramas.
SWAY_CYCLE = (0, 1, 0, -1)


def ivy_strand_frame(seed, phase):
    """Hiedra meciendose. Cuelga del muro, asi que se ancla arriba."""
    return _shift_tile(ivy_strand(seed), SWAY_CYCLE[phase % 4], anchor="top")


def flower_cluster_frame(seed, phase):
    """Flores meciendose. Nacen del suelo, asi que se anclan abajo."""
    return _shift_tile(flower_cluster(seed), SWAY_CYCLE[phase % 4], anchor="bottom")


def farola_frame(phase, n=4):
    """Farola encendida con llama parpadeante.

    El halo y el nucleo laten juntos con una sinusoide: el radio vertical y
    el alpha del halo crecen y decrecen en fase. Un parpadeo con salto brusco
    se lee como error de dibujado; uno continuo se lee como fuego.
    """
    img = new_tile()
    px = img.load()
    metal = ramp_rgb(METAL)
    for y in range(6, T):
        px[7, y] = metal[1] + (255,)
        px[8, y] = metal[2] + (255,)
    for x in range(4, 12):
        px[x, 5] = metal[0] + (255,)

    k = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase / float(n)))
    ry = 2.0 + 0.9 * k
    halo = (232, 190, 120, 70 + int(60 * k))
    core = (255, 200 + int(45 * k), 140, 255)
    for x in range(3, 13):
        for y in range(0, 6):
            if (x - 7.5) ** 2 / ((ry + 2.2) ** 2) + (y - 3) ** 2 / ((ry + 1.4) ** 2) <= 1.0:
                px[x, y] = halo
    for x in range(5, 11):
        for y in range(1, 5):
            if (x - 7.5) ** 2 / 9.0 + (y - 3) ** 2 / (ry * ry) <= 1.0:
                px[x, y] = core
    return img


def gothic_window_frame(ramp_glass, ramp_frame, phase, n=4):
    """Ventana iluminada con la vela de dentro temblando.

    Se modula el brillo del vidrio, no su forma: la carpinteria de piedra no
    se mueve. Amplitud baja a proposito — una ventana que pulsa fuerte se
    lee como semaforo.
    """
    img = gothic_window(ramp_glass, ramp_frame, lit=True)
    px = img.load()
    k = 0.5 + 0.5 * math.sin(2.0 * math.pi * (phase / float(n)) + 0.7)
    f = 0.88 + 0.20 * k
    for y in range(T):
        for x in range(T):
            r, g, b, a = px[x, y]
            if a and (r > 90 and g > 70):          # solo el vidrio, no el marco
                px[x, y] = (min(255, int(r * f)), min(255, int(g * f)),
                            min(255, int(b * f)), a)
    return img


def fog_tile_frame(sky_color, phase, n=4, top_alpha=0, bottom_alpha=130):
    """Niebla a la deriva: onda horizontal de alpha que se desplaza.

    El gradiente vertical se mantiene (es lo que la ata al plano de atras) y
    encima viaja una onda suave. Como la fila entera usa la misma baldosa, la
    onda tiene periodo exacto de un tile y no aparecen costuras.
    """
    img = new_tile()
    px = img.load()
    ph = 2.0 * math.pi * (phase / float(n))
    for y in range(T):
        t = y / (T - 1)
        base = top_alpha + (bottom_alpha - top_alpha) * t
        for x in range(T):
            w = math.sin(2.0 * math.pi * (x / float(T)) + ph)
            a = int(max(0, min(255, base + 14.0 * w * t)))
            px[x, y] = sky_color[:3] + (a,)
    return img


def darken(img, factor):
    """Multiplica el color de una baldosa sin tocar su alpha.

    Se usa para el subsuelo: la roca bajo el camino se dibuja con la misma
    textura que los muros —para que el material sea reconocible— pero mas
    oscura cuanto mas profunda, que es lo que la manda al fondo de la
    jerarquia visual en vez de convertirla en lo mas contrastado de la
    pantalla.
    """
    out = img.copy()
    px = out.load()
    for y in range(out.size[1]):
        for x in range(out.size[0]):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (int(r * factor), int(g * factor), int(b * factor), a)
    return out


def gothic_gate(w_tiles=8, h_tiles=14, seed=31000):
    """El gran arco de entrada: el hito visual del nivel.

    La especificacion de direccion de arte pedia "un destino visual", no
    una catedral. Asi que esto es deliberadamente simple: dos torres
    laterales, un arco apuntado en medio, y luz calida saliendo del hueco.
    Todo cabe en 8 x 14 baldosas de 16 px.

    Tres decisiones que lo hacen leerse como gotico y no como un portal
    generico:

    1. El arco es APUNTADO, no de medio punto. Un arco romanico es un
       semicirculo; el gotico se traza con dos arcos de circunferencia
       cuyos centros estan separados, y por eso sube en punta. Ese pico es
       la firma del estilo y se nota incluso en silueta a 128 px.
    2. Las dovelas se dibujan una a una con junta visible, en vez de
       pintar el contorno del arco de un solo color. Un arco sin dovelas
       se lee como un agujero recortado en una pared.
    3. La luz sale del hueco hacia afuera, no de la piedra. En un nivel
       cuya paleta es violeta frio, el unico calido tiene que estar donde
       se quiere que mire el jugador — y aqui es la salida.
    """
    W, H = w_tiles * 16, h_tiles * 16
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    pied = ramp_rgb(PIEDRA)
    graf = ramp_rgb(GRAFITO)
    calido = (0xff, 0xc2, 0x6a)

    torre_w = W // 4
    cuerpo_y = H // 5

    def bloque(x0, x1, y0, y1, rampa, tono=2):
        for x in range(max(0, x0), min(W, x1)):
            for y in range(max(0, y0), min(H, y1)):
                # Sillares: junta de 1 px cada 8 en horizontal y cada 6 en
                # vertical, desplazada en filas alternas. Un muro sin junta
                # es un rectangulo de color.
                fila = (y - y0) // 6
                junta = (y - y0) % 6 == 0 or (x + fila * 4) % 8 == 0
                t = tono - 1 if junta else tono
                # Luz direccional: el sol se pone a la derecha.
                if x > x1 - 3:
                    t = min(4, t + 1)
                elif x < x0 + 2:
                    t = max(0, t - 1)
                px[x, y] = rampa[max(0, min(4, t))] + (255,)

    # Torres laterales
    for tx in (0, W - torre_w):
        bloque(tx, tx + torre_w, cuerpo_y, H, pied, 2)
        # Aguja
        alto_aguja = cuerpo_y
        for j in range(alto_aguja):
            a = max(1, int(torre_w * (j / alto_aguja) ** 0.8))
            x0 = tx + (torre_w - a) // 2
            for x in range(max(0, x0), min(W, x0 + a)):
                px[x, j] = graf[2 if x > x0 else 3] + (255,)

    # Cuerpo entre torres
    bloque(torre_w, W - torre_w, cuerpo_y + 10, H, pied, 2)

    # Hueco del arco apuntado. Dos circunferencias con los centros
    # separados: eso es lo que hace la punta.
    hueco_x0, hueco_x1 = torre_w + 8, W - torre_w - 8
    ancho = hueco_x1 - hueco_x0
    arranque = H - int(H * 0.44)
    # Arco apuntado equilatero: cada arco de circunferencia tiene radio
    # igual a la LUZ del vano y su centro en el arranque CONTRARIO. Asi la
    # punta queda a 0,866 x la luz por encima del arranque.
    #
    # El primer intento puso los dos centros en el eje del vano, y con los
    # dos centros en el mismo sitio las dos circunferencias coinciden: sale
    # un medio punto romanico, sin punta. Es un error de un caracter que
    # borra el estilo entero.
    radio = ancho
    cx_izq, cx_der = hueco_x1, hueco_x0
    for y in range(0, H):
        for x in range(hueco_x0, hueco_x1):
            dentro = False
            if y >= arranque:
                dentro = True
            else:
                d_i = ((x - cx_izq) ** 2 + (y - arranque) ** 2) ** 0.5
                d_d = ((x - cx_der) ** 2 + (y - arranque) ** 2) ** 0.5
                dentro = d_i <= radio and d_d <= radio
            if not dentro:
                continue
            # Degradado calido hacia el fondo del hueco.
            t = (y - arranque) / max(1, H - arranque)
            if y < arranque:
                px[x, y] = (0x18, 0x10, 0x24, 255)
            else:
                m = 0.30 + 0.55 * t
                px[x, y] = (int(calido[0] * m), int(calido[1] * m),
                            int(calido[2] * m), 255)

    # Dovelas: anillo de sillares siguiendo el trazado del arco.
    for x in range(hueco_x0 - 6, hueco_x1 + 6):
        for y in range(0, arranque + 2):
            if not (0 <= x < W):
                continue
            d_i = ((x - cx_izq) ** 2 + (y - arranque) ** 2) ** 0.5
            d_d = ((x - cx_der) ** 2 + (y - arranque) ** 2) ** 0.5
            en_anillo = (radio < d_i <= radio + 6 and d_d <= radio + 6) or \
                        (radio < d_d <= radio + 6 and d_i <= radio + 6)
            if en_anillo:
                ang = int((d_i + d_d) * 0.7) % 5
                px[x, y] = pied[3 if ang else 1] + (255,)

    # Emblema de INVENIO sobre la clave: rombo de vidrio iluminado.
    ex, ey = W // 2, arranque - int(ancho * 0.75)
    for dy in range(-7, 8):
        for dx in range(-7, 8):
            if abs(dx) + abs(dy) <= 7 and 0 <= ex + dx < W and 0 <= ey + dy < H:
                borde = abs(dx) + abs(dy) >= 6
                px[ex + dx, ey + dy] = (
                    (pied[1] if borde else calido) + (255,))

    # Derrame de luz del hueco sobre la piedra de alrededor.
    for x in range(max(0, hueco_x0 - 10), min(W, hueco_x1 + 10)):
        for y in range(arranque, H):
            if hueco_x0 <= x < hueco_x1:
                continue
            d = min(abs(x - hueco_x0), abs(x - hueco_x1))
            r, g, b, a = px[x, y]
            if a:
                k = max(0.0, 0.22 * (1 - d / 10))
                px[x, y] = (int(r + (calido[0] - r) * k),
                            int(g + (calido[1] - g) * k),
                            int(b + (calido[2] - b) * k), 255)
    return img
