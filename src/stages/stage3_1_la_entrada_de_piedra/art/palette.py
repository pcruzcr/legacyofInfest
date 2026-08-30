"""
Paleta y utilidades de dithering/AO/ruido para el reskin de Stage 3-1.
Basado en BRIEF_ESCENARIO_31.md seccion 4 y 5.2.
Todas las rampas van de sombra profunda -> luz (indice 0 = mas oscuro).
"""
import random

# --- Rampas de material (seccion 4.1) ---
PIEDRA    = ["#1b1826", "#2e2a3d", "#474156", "#635c73", "#857d94"]
GRAFITO   = ["#14131c", "#22212e", "#343243", "#4a4759", "#666277"]
TERRACOTA = ["#4a1f18", "#7a3221", "#a84e2c", "#d4783f", "#f0a35c"]
CESPED    = ["#14261a", "#1f3d25", "#2f6338", "#458f4b", "#66b862"]
FOLLAJE   = ["#101f1c", "#1a3330", "#275048", "#3a7263", "#57a184"]
TRONCO    = ["#1a1114", "#2b1d21", "#422f31", "#5c4442", "#7a5d55"]
VIDRIO    = ["#0f1a24", "#16283a", "#1f3d56", "#2d5c7d", "#4a89ad"]
METAL     = ["#16141d", "#262231", "#3a3548", "#545065", "#7a7590"]

# flores / detalles violeta-rosados (extendida, coherente con Acto I)
FLOR      = ["#2b1522", "#4a1f3a", "#7a3560", "#b8548c", "#e88fc2"]

# --- Cielo Acto I (cenit -> horizonte), referencia; el cielo real ya lo
#     trae assets/backgrounds/zone3/bg_zone3_far.png (parallax oficial) ---
ACTO_I_SKY = ["#2b1b3d", "#43214f", "#5e2a56", "#8c3a5e", "#b84a64", "#d4576b", "#e8735f", "#f0895f"]

RNG_SEED = 20260819


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def ramp_rgb(ramp):
    return [hx(c) for c in ramp]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def mix_toward(color, target, amount):
    """Mezcla `color` hacia `target` en `amount` (0..1)."""
    return lerp_color(color, target, amount)


def desaturate(color, amount):
    """amount 0..1, 1 = gris total (luma)."""
    luma = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    gray = (luma, luma, luma)
    return lerp_color(color, gray, amount)


def atmospheric_blend(color, sky_color, amount, sat_shift):
    """Seccion 4.3: mezcla hacia el color del cielo + ajusta saturacion."""
    c = mix_toward(color, sky_color, amount)
    if sat_shift < 0:
        c = desaturate(c, -sat_shift)
    return tuple(max(0, min(255, int(v))) for v in c)


def dither_pixel(x, y, t, pattern="bayer2"):
    """Devuelve True si el pixel (x,y) debe tomar el tono 'alto' segun un
    umbral t (0..1) usando un patron Bayer 2x2 (dithering ordenado)."""
    bayer2 = [[0, 2], [3, 1]]
    threshold = (bayer2[y % 2][x % 2] + 0.5) / 4.0
    return t > threshold


def ramp_index_dithered(x, y, t, n):
    """t en 0..1 sobre una rampa de n tonos, con dithering ordenado entre
    los dos indices vecinos (evita bandas duras)."""
    scaled = t * (n - 1)
    lo = int(scaled)
    lo = max(0, min(n - 2, lo))
    frac = scaled - lo
    return lo + 1 if dither_pixel(x, y, frac) else lo


def surface_noise_mask(w, h, count, seed=RNG_SEED):
    """Devuelve un set de (x,y) para ruido de superficie reproducible."""
    rng = random.Random(seed)
    pts = set()
    lo = max(1, count // 2)
    hi = max(lo, count)
    n = rng.randint(lo, hi)
    for _ in range(n):
        pts.add((rng.randrange(w), rng.randrange(h)))
    return pts


def tile_variant_index(x, y, n_variants, seed=RNG_SEED):
    """Hash deterministico (x,y) -> variante de tile (seccion 5.2 #7)."""
    h = (x * 73856093) ^ (y * 19349663) ^ seed
    h &= 0xffffffff
    return h % n_variants
