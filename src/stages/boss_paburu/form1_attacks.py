"""
Ataques de la Forma 1 — "La Cabeza de Piedra" (GDD §4).

    STONE_SPIT   cada  4 s — 3 proyectiles en arco, separación 15°, 0.5 c/u
    EYE_BEAM     cada  8 s — rayo horizontal 8px @200px/s, telegraph 0.5 s, 1.0
    EL SELLO     cada 10 s — 5 columnas que dibujan el sello, telegraph 0.8 s,
                             0.5 de daño, dejan marcas grabadas permanentes

Cada clase es autónoma: sabe avanzar su propio estado (`update`), exponer
sus rects de daño (`damage_rects`) y dibujarse (`draw`). El boss solo
decide *cuándo* nacen y las tiene en una lista. Esto mantiene
`boss_paburu.py` legible cuando lleguen las formas 2-4.

Este archivo NO modifica engine/ ni framework/ — solo los usa.

Mapeo académico (ver README.md del stage):
  - Unidad II  — tiro parabólico y rotación de vectores en STONE_SPIT;
                 polar→cartesiano con escalado anisótropo en el sello.
  - Unidad VI  — easings de `math_utils` en el ascenso y retracción de
                 las columnas (interpolación no lineal).
  - Unidad V   — color: las marcas grabadas usan la paleta del cementerio.
"""
from __future__ import annotations

import math

import pygame

from src.engine.utils.math_utils import (
    ease_in_quad,
    ease_out_quad,
    vec2_distance,
    vec2_normalize,
)
from src.framework.processing.curve_tools import CurveTools
from src.stages.boss_paburu import arena
from src.stages.boss_paburu.sprites import load_sheet

# ══════════════════════════════════════════════════════════════════
#  STONE_SPIT — 3 proyectiles de piedra en arco
# ══════════════════════════════════════════════════════════════════

_PROJECTILE_FRAMES: list[pygame.Surface] | None = None


def load_projectile_frames() -> list[pygame.Surface]:
    """Cachea las 3 rotaciones de la piedra. [] si todavía no hay arte."""
    global _PROJECTILE_FRAMES
    if _PROJECTILE_FRAMES is None:
        _PROJECTILE_FRAMES = load_sheet("stone_proyectil", 8, 8)
    return _PROJECTILE_FRAMES

class StoneProjectile:
    """Una piedra escupida. Movimiento parabólico puro (Unidad II).

    Integración explícita de la cinemática, no una curva pre-muestreada:
        v ← v + g·Δt        (aceleración constante)
        p ← p + v·Δt        (integración de Euler semi-implícita)

    Se usa Euler semi-implícito (velocidad primero) porque con Δt
    variable conserva mejor la forma de la parábola que el explícito.
    """

    RADIUS = 4
    GRAVITY = 420.0        # px/s²
    DAMAGE = 0.5           # GDD §4: 0.5 corazones cada uno
    LIFETIME = 4.0         # red de seguridad: nada vive para siempre

    def __init__(self, origin: pygame.Vector2, velocity: pygame.Vector2) -> None:
        self.pos = pygame.Vector2(origin)
        self.vel = pygame.Vector2(velocity)
        self.alive = True
        self.spin = 0.0            # solo visual: la piedra rota al volar
        self._life = self.LIFETIME

    def update(self, dt: float) -> None:
        self.vel.y += self.GRAVITY * dt
        self.pos += self.vel * dt
        self.spin += dt * 8.0
        self._life -= dt

        hit_floor = self.pos.y + self.RADIUS >= arena.FLOOR_Y
        out_of_arena = not (
            arena.PLAY_LEFT <= self.pos.x <= arena.PLAY_RIGHT
        )
        if hit_floor or out_of_arena or self._life <= 0.0:
            self.alive = False

    @property
    def rect(self) -> pygame.Rect:
        r = self.RADIUS
        return pygame.Rect(
            int(self.pos.x) - r, int(self.pos.y) - r, r * 2, r * 2,
        )

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        cx = int(self.pos.x - offset.x)
        cy = int(self.pos.y - offset.y)
        frames = load_projectile_frames()
        if frames:
            # 3 rotaciones talladas; el giro visual las cicla.
            f = frames[int(self.spin) % len(frames)]
            surface.blit(f, (cx - f.get_width() // 2, cy - f.get_height() // 2))
            return
        # Sin arte: cuadrado rotado = piedra irregular volando.
        pts = []
        for k in range(4):
            a = self.spin + k * math.pi / 2.0
            pts.append((
                cx + self.RADIUS * math.cos(a),
                cy + self.RADIUS * math.sin(a),
            ))
        pygame.draw.polygon(surface, (150, 148, 138), pts)
        pygame.draw.polygon(surface, (70, 100, 72), pts, 1)


# El mínimo NO es cosmético: con 0.55 s un tiro a corta distancia salía
# con 10 px de arco, o sea una recta. 0.80 s da ~28 px de arco pegado al
# boss y ~45 px a media arena — se lee como parábola en todo el rango,
# que es lo que pide el GDD ("escupe 3 proyectiles en arco").
SPIT_TIME_MIN = 0.80
SPIT_TIME_MAX = 1.25
SPIT_TIME_REF = 320.0     # px que corresponden a 1 s de vuelo


def spit_flight_time(origin: pygame.Vector2, target: pygame.Vector2) -> float:
    """Tiempo de vuelo proporcional a la distancia (Unidad II).

    Usa `math_utils.vec2_distance`, es decir ‖target − origin‖₂:

        t = clamp( d / 320 ,  0.55 , 1.25 )

    Con un tiempo fijo, un tiro a 40 px salía casi vertical —la piedra
    subía 200 px para caer al lado del boss— y uno a 700 px salía
    plano. Escalar el tiempo con la distancia mantiene el arco legible
    en todo el ancho de la arena. Los topes evitan los dos extremos:
    ni un lob eterno de cerca, ni un disparo raso de lejos.
    """
    d = vec2_distance(origin, target)
    return max(SPIT_TIME_MIN, min(SPIT_TIME_MAX, d / SPIT_TIME_REF))


def spit_velocities(
    origin: pygame.Vector2,
    target: pygame.Vector2,
    flight_time: float | None = None,
    spread_deg: float = 15.0,
) -> list[pygame.Vector2]:
    """Las 3 velocidades iniciales de STONE_SPIT (Unidad II).

    Paso 1 — resolver el tiro parabólico para que la piedra *central*
    caiga sobre `target` en exactamente `flight_time` segundos.
    De  Δp = v₀·t + ½·g·t²  se despeja:

        v₀x = Δx / t
        v₀y = Δy / t − ½·g·t

    Paso 2 — las otras dos salen de **rotar** ese vector ±15°, que es la
    "separación de 15°" del GDD. Rotación 2D canónica:

        ⎡x'⎤   ⎡cos θ  −sen θ⎤ ⎡x⎤
        ⎣y'⎦ = ⎣sen θ   cos θ⎦ ⎣y⎦

    Rotar en vez de recalcular tres tiros mantiene el módulo |v₀| igual
    en las tres piedras: el abanico se abre, no se desbalancea.

    Nota de diseño: se apunta a la posición *actual* del jugador, nunca a
    una predicción. La cabeza de piedra "juzga sin mirar" (GDD §2.1) —
    castiga quedarse quieto, no persigue.
    """
    delta = target - origin
    t = spit_flight_time(origin, target) if flight_time is None else flight_time
    t = max(t, 0.05)
    base = pygame.Vector2(
        delta.x / t,
        delta.y / t - 0.5 * StoneProjectile.GRAVITY * t,
    )
    return [base.rotate(-spread_deg), pygame.Vector2(base), base.rotate(spread_deg)]


# ══════════════════════════════════════════════════════════════════
#  EYE_BEAM — rayo horizontal con telegraph
# ══════════════════════════════════════════════════════════════════

class EyeBeam:
    """Rayo horizontal disparado desde los ojos (GDD §4).

    Ciclo: TELEGRAPH (0.5 s, los ojos brillan, sin daño) → el frente
    avanza a 200px/s hasta salir de la arena.

    Calibración de la altura — el detalle que importa: el daño se resuelve
    contra el **hurtbox** del jugador, que es más chico que su rect. Con el
    suelo del TMX en y=560, `Player.hurtbox` vale:

        de pie       → y 532..560   (rect.y+4, 28 de alto)
        agachado     → y 542..560   (rect.y+14, 18 de alto)
        en one-way   → y 452..480   (mismo offset, 80px más arriba)

    El rayo sale de los ojos (y=534) con 8px de alto → ocupa 530..538:

        de pie       → solapa 532..538 (6px)  → TOCADO
        agachado     → 538 < 542 (4px de aire) → esquiva
        en one-way   → 480 < 530              → esquiva

    Es decir: se esquiva agachándose O subiendo, tal como pide el GDD.
    Los márgenes son de 4-6px, así que si cambia la altura del suelo del
    TMX o el hurtbox del `Player`, hay que recalibrar `EYE_DY`.
    """

    TELEGRAPH = 0.5        # GDD §4: "los ojos brillan 0.5 s antes"
    SPEED = 200.0          # px/s
    HEIGHT = 8             # px
    DAMAGE = 1.0

    def __init__(self, eye_pos: pygame.Vector2, direction: int) -> None:
        self.origin = pygame.Vector2(eye_pos)
        self.direction = 1 if direction >= 0 else -1
        self.telegraph_timer = self.TELEGRAPH
        self.length = 0.0
        self.alive = True

    @property
    def is_telegraphing(self) -> bool:
        return self.telegraph_timer > 0.0

    def update(self, dt: float) -> None:
        if self.telegraph_timer > 0.0:
            self.telegraph_timer -= dt
            return
        self.length += self.SPEED * dt
        tip = self.origin.x + self.direction * self.length
        if not (arena.PLAY_LEFT <= tip <= arena.PLAY_RIGHT):
            self.alive = False

    @property
    def rect(self) -> pygame.Rect | None:
        """Rect de daño, o None mientras está en telegraph."""
        if self.is_telegraphing or self.length <= 0.0:
            return None
        x0 = self.origin.x if self.direction > 0 else self.origin.x - self.length
        return pygame.Rect(
            int(x0), int(self.origin.y - self.HEIGHT / 2),
            int(self.length), self.HEIGHT,
        )

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.is_telegraphing:
            # Telegraph: línea fina parpadeante marcando la trayectoria.
            if int(self.telegraph_timer * 16.0) % 2 == 0:
                y = int(self.origin.y - offset.y)
                x0 = int(self.origin.x - offset.x)
                x1 = arena.PLAY_RIGHT if self.direction > 0 else arena.PLAY_LEFT
                pygame.draw.line(
                    surface, (0, 140, 70), (x0, y), (int(x1 - offset.x), y), 1,
                )
            return
        r = self.rect
        if r is None:
            return
        r = r.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, arena.COL_SPECTRAL, r)
        pygame.draw.rect(surface, (220, 255, 235), r.inflate(0, -4))


# ══════════════════════════════════════════════════════════════════
#  EL SELLO — 5 columnas que graban el sello ceremonial
# ══════════════════════════════════════════════════════════════════

# Geometría del sello: un círculo ceremonial apoyado en el suelo, visto
# desde la cámara lateral. Se dibuja como elipse (Rx ≠ Ry) porque eso es
# el escorzo de un círculo en perspectiva: se lee "en el piso" y no
# "flotando en el aire".
SEAL_CENTER_X = (arena.SEAL_ZONE_X0 + arena.SEAL_ZONE_X1) / 2.0   # 400
SEAL_CENTER_Y = arena.FLOOR_Y - 28.0                              # 532
SEAL_RX = 104.0
# Ry = 28 para que el borde inferior de la elipse caiga justo sobre la línea
# del suelo (532 + 28 = 560): el sello se apoya en el piso, no lo atraviesa.
SEAL_RY = 28.0
SEAL_POINTS = 5                    # GDD §4: "5 columnas"
SEAL_ROTATION_STEP = 30.0          # cada invocación gira el pentágono

COL_SEAL_ENGRAVED = (58, 92, 66)   # marca vieja: verde piedra apagado
COL_SEAL_FRESH = (0, 200, 100)     # marca recién grabada
COL_ANIMA = (170, 255, 210)        # la luz de un nombre
COL_ANIMA_TAIL = (60, 150, 110)    # su estela


def seal_vertices(rotation_deg: float) -> list[pygame.Vector2]:
    """Los 5 vértices del pentágono del sello (Unidad II).

    Conversión polar → cartesiana con **escalado anisótropo**:

        p(θ) = C + (Rx·cos θ,  Ry·sen θ)

    que es la composición de tres transformaciones elementales del temario:
    generación en coordenadas polares, escalado no uniforme (Rx ≠ Ry, el
    escorzo) y traslación al centro C.

    `rotation_deg` gira la figura entera: cada invocación de EL SELLO usa
    una rotación distinta, así las columnas nunca emergen dos veces en las
    mismas X y las marcas acumuladas van tejiendo el sello completo.
    """
    step = 360.0 / SEAL_POINTS
    out: list[pygame.Vector2] = []
    for k in range(SEAL_POINTS):
        theta = math.radians(-90.0 + k * step + rotation_deg)
        out.append(pygame.Vector2(
            SEAL_CENTER_X + SEAL_RX * math.cos(theta),
            SEAL_CENTER_Y + SEAL_RY * math.sin(theta),
        ))
    return out


class SealColumn:
    """Una columna de piedra que emerge del suelo y se retrae.

    Fases (segundos): telegraph 0.8 → sube 0.35 → sostiene 1.0 → baja 0.4.
    El telegraph son grietas luminosas en la base, sin daño: el GDD pide
    0.8 s de aviso porque 5 columnas simultáneas sin lectura previa serían
    daño no evitable, y Paburu "no es crueldad gratuita" (§1).
    """

    WIDTH = 16
    HEIGHT = 48            # GDD §6.2: columnas de 16×48
    TELEGRAPH = 0.8        # GDD §4
    RISE = 0.35
    HOLD = 1.0
    RETRACT = 0.4
    DAMAGE = 0.5

    TOTAL = TELEGRAPH + RISE + HOLD + RETRACT

    def __init__(self, x: float) -> None:
        self.x = float(x)
        self.elapsed = 0.0
        self.alive = True

    def update(self, dt: float) -> None:
        self.elapsed += dt
        if self.elapsed >= self.TOTAL:
            self.alive = False

    @property
    def is_telegraphing(self) -> bool:
        return self.elapsed < self.TELEGRAPH

    @property
    def extension(self) -> float:
        """Altura visible ahora mismo, en px. 0 durante el telegraph.

        Unidad VI — interpolación no lineal: sube con `ease_out_quad`
        (arranque brusco, la piedra revienta el suelo) y baja con
        `ease_in_quad` (se hunde despacio y acelera). Las dos son del
        `math_utils` del framework, no reimplementadas acá.
        """
        t = self.elapsed - self.TELEGRAPH
        if t < 0.0:
            return 0.0
        if t < self.RISE:
            return self.HEIGHT * ease_out_quad(t / self.RISE)
        if t < self.RISE + self.HOLD:
            return float(self.HEIGHT)
        t_out = (t - self.RISE - self.HOLD) / self.RETRACT
        return self.HEIGHT * (1.0 - ease_in_quad(min(t_out, 1.0)))

    @property
    def rect(self) -> pygame.Rect | None:
        ext = int(self.extension)
        if ext <= 0:
            return None
        return pygame.Rect(
            int(self.x - self.WIDTH / 2), arena.FLOOR_Y - ext, self.WIDTH, ext,
        )

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        if self.is_telegraphing:
            # Grietas luminosas en la base: crecen hasta el momento de salir.
            p = 1.0 - (self.elapsed / self.TELEGRAPH)
            half = int(2 + 8 * (1.0 - p))
            y = int(arena.FLOOR_Y - offset.y)
            x = int(self.x - offset.x)
            bright = int(80 + 175 * (1.0 - p))
            pygame.draw.line(
                surface, (0, bright, int(bright * 0.55)),
                (x - half, y - 1), (x + half, y - 1), 2,
            )
            return
        r = self.rect
        if r is None:
            return
        r = r.move(-int(offset.x), -int(offset.y))
        pygame.draw.rect(surface, (120, 118, 110), r)
        pygame.draw.rect(surface, (70, 100, 72), r, 2)
        # Corona: la cara superior de la columna, siempre visible.
        pygame.draw.rect(surface, arena.COL_STONE_PALE, (r.x, r.y, r.width, 3))


class SealCast:
    """Una invocación de EL SELLO: las 5 columnas de una misma rotación."""

    def __init__(self, rotation_deg: float) -> None:
        self.rotation = rotation_deg
        self.vertices = seal_vertices(rotation_deg)
        self.columns = [SealColumn(v.x) for v in self.vertices]

    @property
    def alive(self) -> bool:
        return any(c.alive for c in self.columns)

    def update(self, dt: float) -> None:
        for c in self.columns:
            c.update(dt)

    def damage_rects(self) -> list[pygame.Rect]:
        return [r for r in (c.rect for c in self.columns) if r is not None]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        for c in self.columns:
            c.draw(surface, offset)


class SealAnima:
    """Un ánima: la luz de un nombre que sube de una marca recién grabada.

    Narrativa (GDD §2.2): las marcas del sello son **nombres** — cada
    portador que esperó la prueba y nunca llegó a rendirla. Cuando una
    columna se retrae y deja su marca, ese nombre se despierta un
    instante: una luz sube, se curva hacia el centro del sello donde
    está Kavë, y se apaga. No hace daño. Es la arena recordando en voz
    alta.

    ── Unidad III — Curvas ──────────────────────────────────────────
    La trayectoria NO es una recta ni una parábola: es una **spline de
    Catmull-Rom** que pasa por cuatro puntos de control calculados por
    ánima:

        P0 = la marca (base de la columna)
        P1 = P0 + (desvío lateral, −34)     ← el ánima sube y se abre
        P2 = punto medio hacia el centro, más alto todavía
        P3 = el centro del sello (donde está Kavë)

    Se elige Catmull-Rom y no Bézier porque la spline **pasa por** sus
    puntos de control, no solo los aproxima: así el ánima arranca
    exactamente en su marca y termina exactamente en el centro, que es
    justo lo que la narrativa necesita. La curva se muestrea una sola
    vez al nacer (`CurveTools.catmull_rom`) y después se recorre con
    `CurveTools.sample_path`, que interpola dentro de la polilínea.

    ── Unidad II — Vectores ─────────────────────────────────────────
    `vec2_distance` mide cuánto le falta al ánima para llegar al centro
    y de ahí sale su desvanecimiento; `vec2_normalize` da la dirección
    de avance, con la que se orienta la estela.
    """

    SAMPLES = 24          # resolución de la polilínea
    LIFETIME = 1.6        # segundos de vuelo
    FADE_RADIUS = 46.0    # a esta distancia del centro ya se está apagando

    def __init__(self, mark: pygame.Vector2, index: int, total: int) -> None:
        centre = pygame.Vector2(SEAL_CENTER_X, SEAL_CENTER_Y)
        # El desvío lateral se reparte para que las 5 ánimas no se
        # superpongan: cada una sale abriéndose hacia su propio lado.
        spread = (index - (total - 1) / 2.0) * 13.0
        p1 = pygame.Vector2(mark.x + spread, mark.y - 34)
        p2 = pygame.Vector2((mark.x + centre.x) / 2 + spread * 0.5, mark.y - 48)
        control = [(mark.x, mark.y), (p1.x, p1.y), (p2.x, p2.y), (centre.x, centre.y)]

        self.path = CurveTools.catmull_rom(control, self.SAMPLES)
        self.pos = pygame.Vector2(mark)
        self.heading = pygame.Vector2(0, -1)
        self.t = 0.0
        self.alive = True
        self._prev = pygame.Vector2(mark)

    def update(self, dt: float) -> None:
        self.t += dt / self.LIFETIME
        if self.t >= 1.0:
            self.t = 1.0
            self.alive = False
        x, y = CurveTools.sample_path(self.path, self.t)
        self._prev.update(self.pos)
        self.pos.update(x, y)
        delta = self.pos - self._prev
        if delta.length_squared() > 0.0001:
            # Unidad II: dirección de avance como vector unitario.
            self.heading = vec2_normalize(delta)

    @property
    def alpha(self) -> float:
        """Se apaga al acercarse al centro (Unidad II — `vec2_distance`)."""
        centre = pygame.Vector2(SEAL_CENTER_X, SEAL_CENTER_Y)
        d = vec2_distance(self.pos, centre)
        near = min(1.0, d / self.FADE_RADIUS)     # 0 en el centro, 1 lejos
        birth = min(1.0, self.t / 0.15)           # aparece rápido
        return max(0.0, min(1.0, near * birth))

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        a = self.alpha
        if a <= 0.02:
            return
        x = int(self.pos.x - offset.x)
        y = int(self.pos.y - offset.y)
        # Estela: 5px hacia atrás sobre la dirección de avance.
        tail = self.pos - self.heading * 5.0
        pygame.draw.line(
            surface, COL_ANIMA_TAIL,
            (int(tail.x - offset.x), int(tail.y - offset.y)), (x, y), 1,
        )
        pygame.draw.circle(surface, COL_ANIMA, (x, y), 2 if a > 0.5 else 1)
        if a > 0.7:
            surface.set_at((x, y - 1), (240, 255, 245))


class SealMemory:
    """Las marcas grabadas: la memoria de la arena (GDD §1 pilar 2, §2.2).

    Decisión de diseño: las marcas son **solo memoria visual**, sin
    colisión. Narrativamente son nombres — cada
    portador que esperó la prueba, con Kavë al centro (§2.2) —, no
    trampas. Mecánicamente, dejarlas inertes evita que la arena se vuelva
    impracticable en las Formas 3 y 4, y respeta el orden de sacrificio
    del §7 (EL SELLO visual es lo primero recortable: si es solo visual,
    no bloquea a nadie).

    Se acumulan durante todo el combate, no se limpian entre formas: al
    final el sello está completo y legible, que es lo que pide la
    secuencia de derrota (§6, paso 6).
    """

    def __init__(self) -> None:
        self.rotations: list[float] = []
        self._t = 0.0

    def update(self, dt: float) -> None:
        """Reloj propio del sello, para que las marcas respiren.

        Grabadas y quietas se leían como un dibujo pegado sobre el suelo:
        aparecían de golpe y ahí se quedaban, idénticas, hasta el final del
        combate. Un latido lento las convierte en lo que el lore dice que
        son —nombres que todavía están ahí— sin volverlas ruido visual: el
        pulso es de brillo, no de posición, así que no compite con la
        lectura de los ataques.

        Es además coherente con la secuencia de derrota (GDD §6, paso 6),
        donde las marcas "brillan una última vez": si nunca brillaron
        durante la pelea, ese brillo final no significaría nada.
        """
        self._t += dt

    def engrave(self, rotation_deg: float) -> None:
        self.rotations.append(rotation_deg)

    @property
    def count(self) -> int:
        return len(self.rotations)

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Dibuja el sello acumulado: el aro + una estrella por invocación.

        La estrella de 5 puntas sale de unir cada vértice con el que está
        a *dos* posiciones (paso 2 sobre 5), no con el contiguo — eso es
        el pentagrama {5/2}. Con varias rotaciones superpuestas el
        resultado se lee como un sello ceremonial complejo.
        """
        if not self.rotations:
            return
        ox, oy = int(offset.x), int(offset.y)

        # Aro exterior: aparece con la primera invocación.
        ring = pygame.Rect(
            int(SEAL_CENTER_X - SEAL_RX) - ox,
            int(SEAL_CENTER_Y - SEAL_RY) - oy,
            int(SEAL_RX * 2), int(SEAL_RY * 2),
        )
        pygame.draw.ellipse(surface, COL_SEAL_ENGRAVED, ring, 1)

        # Latido: una onda lenta que recorre las marcas. Cada estrella entra
        # con un desfase propio, así el sello no parpadea entero como una
        # lámpara sino que ondula, como si las marcas se fueran acordando de
        # a una. La más reciente late más fuerte: todavía está fresca.
        last = len(self.rotations) - 1
        for i, rot in enumerate(self.rotations):
            fresca = i == last
            fase = self._t * 1.15 - i * 0.55
            pulso = 0.5 + 0.5 * math.sin(fase)
            base = COL_SEAL_FRESH if fresca else COL_SEAL_ENGRAVED
            k = (0.45 + 0.55 * pulso) if fresca else (0.62 + 0.38 * pulso)
            color = (
                int(base[0] * k), int(base[1] * k), int(base[2] * k),
            )
            pts = seal_vertices(rot)
            for m in range(SEAL_POINTS):
                a = pts[m]
                b = pts[(m + 2) % SEAL_POINTS]      # paso 2 → pentagrama
                pygame.draw.line(
                    surface, color,
                    (int(a.x) - ox, int(a.y) - oy),
                    (int(b.x) - ox, int(b.y) - oy), 1,
                )
            for p in pts:
                pygame.draw.circle(
                    surface, color, (int(p.x) - ox, int(p.y) - oy), 2,
                )
