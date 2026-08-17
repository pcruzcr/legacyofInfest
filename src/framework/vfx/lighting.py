from __future__ import annotations

import math

import numpy as np
import pygame

from src.engine.render.sprite_batch import SpriteBatch
from src.framework.vfx.sombras_proyectadas import ProyectorDeSombras


class LightSource:
    """A 2D point light with position, radius, color, and intensity."""

    #: Discos de luz ya calculados, compartidos por todos los focos.
    _gradient_cache: dict[tuple[int, int, tuple[int, int, int]], pygame.Surface] = {}

    #: Cuantización del radio, en píxeles. Coincide con el umbral de
    #: reconstrucción de `get_cached_gradient` (2 px): pedir menos grano del
    #: que se puede distinguir sólo llena la caché.
    _RADIUS_BUCKET = 4

    #: Cuantización de la intensidad. 0,05 son 20 escalones entre apagado y
    #: encendido — más de los que el ojo separa en un parpadeo.
    _INTENSITY_BUCKET = 0.05

    #: Tope de la caché. Con discos de hasta 280x280 px a 4 bytes por píxel,
    #: 128 entradas son unos 40 MB en el peor caso. Sin tope, medido sobre
    #: Stage 0: 182 MB en diez segundos y creciendo.
    _MAX_CACHED_GRADIENTS = 128

    def __init__(
        self,
        position: pygame.Vector2,
        radius: float = 80.0,
        color: tuple[int, int, int] = (255, 255, 200),
        intensity: float = 0.8,
        flicker: bool = False,
        flicker_speed: float = 4.0,
        flicker_amount: float = 0.15,
    ) -> None:
        self.position = position
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.flicker = flicker
        self.flicker_speed = flicker_speed
        self.flicker_amount = flicker_amount
        self._elapsed: float = 0.0
        self._gradient: pygame.Surface | None = None
        self._cached_radius: float = 0.0
        self._cached_intensity: float = -1.0
        self._cached_color: tuple[int, int, int] = (0, 0, 0)

    def update(self, dt: float) -> None:
        self._elapsed += dt

    def get_current_radius(self) -> float:
        if not self.flicker:
            return self.radius
        flicker = 1.0 + math.sin(self._elapsed * self.flicker_speed) * self.flicker_amount
        return self.radius * flicker

    def get_current_intensity(self) -> float:
        if not self.flicker:
            return self.intensity
        flicker = 1.0 + math.sin(self._elapsed * self.flicker_speed * 1.5 + 1.0) * self.flicker_amount
        return self.intensity * max(0.5, flicker)

    def build_gradient(
        self,
        radius: float,
        color: tuple[int, int, int],
        intensity: float | None = None,
    ) -> pygame.Surface:
        """Construye el disco de luz: brillante en el centro, nulo en el borde.

        AUD-086 — este método devolvía un disco completamente negro
        ------------------------------------------------------------
        La versión anterior calculaba el canal de color así::

            val = (self.intensity * falloff * 255).astype(np.uint8)
            arr[:, :, 0] = (val * color[0] / 255).astype(np.uint8)

        `val` es `uint8` y `color[0]` vale hasta 255, que **también cabe en un
        uint8**. NumPy conserva entonces el tipo pequeño y la multiplicación
        desborda en silencio: para un píxel central con `val = 216` y
        `color[0] = 255`, el producto no es 55.080 sino ``55.080 mod 256 =
        40``; dividir entre 255 da 0,157; convertir a entero da **0**.

        Es decir: todos los focos del juego eran discos negros y totalmente
        transparentes. El sistema de iluminación estaba instanciado, cableado,
        actualizándose cada fotograma y **no había iluminado jamás un píxel**.
        Medido, no deducido: el centro de un foco daba exactamente el mismo
        valor que la esquina de la pantalla.

        Por eso nadie reparó en que el brillo ambiente del prólogo estaba en
        1.0: aunque se hubiera bajado, el resultado habría sido oscuridad
        uniforme, no charcos de luz.

        La corrección es hacer la aritmética en coma flotante y convertir a
        entero una sola vez, al final.
        """
        intensidad = self.intensity if intensity is None else intensity
        # Cuantización de la clave. Sin esto la caché crece sin límite: medido
        # sobre Stage 0 con seis focos parpadeantes, **182 MB en diez segundos**
        # y subiendo de forma lineal, porque cada instante del parpadeo produce
        # un radio y una intensidad ligeramente distintos y por tanto una
        # entrada nueva. Redondear a cubos hace que el parpadeo recorra un
        # puñado de discos en vez de inventar uno por fotograma.
        r = max(1, round(radius / self._RADIUS_BUCKET) * self._RADIUS_BUCKET)
        cubo_intensidad = round(intensidad / self._INTENSITY_BUCKET)
        key = (r, cubo_intensidad, color)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            return cached
        intensidad = cubo_intensidad * self._INTENSITY_BUCKET

        size = r * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        ys, xs = np.ogrid[:size, :size]
        dist = np.sqrt((xs - r) ** 2 + (ys - r) ** 2)
        # Caída lineal recortada al círculo. Fuera del radio no hay luz.
        falloff = np.clip(1.0 - dist / r, 0.0, 1.0).astype(np.float32)
        falloff[dist > r] = 0.0
        nivel = falloff * float(intensidad)          # float32 en [0, 1]

        arr = pygame.surfarray.pixels3d(surf)
        alfa = pygame.surfarray.pixels_alpha(surf)
        try:
            for canal in range(3):
                arr[:, :, canal] = (nivel * color[canal]).astype(np.uint8)
            # El alfa no se usa en el mezclado actual (BLEND_RGBA_MAX opera
            # canal a canal), pero dejarlo en cero convertía el gradiente en
            # una superficie invisible para cualquier otro modo de mezcla, y
            # eso es una trampa para quien lo reutilice.
            alfa[:] = (nivel * 255.0).astype(np.uint8)
        finally:
            del arr
            del alfa

        self._store_gradient(key, surf)
        return surf

    @classmethod
    def _store_gradient(cls, key: tuple, surf: pygame.Surface) -> None:
        """Guarda el disco y expulsa el más antiguo si la caché se pasa.

        La caché es de clase: la comparten todos los focos del juego, que es lo
        que se quiere —dos antorchas iguales deben reutilizar el mismo disco—
        pero también significa que nada la vacía nunca. Un tope explícito es la
        diferencia entre una caché y una fuga de memoria.

        Los diccionarios de Python conservan el orden de inserción, así que
        `next(iter(...))` da la entrada más vieja sin estructuras adicionales.
        """
        cls._gradient_cache[key] = surf
        while len(cls._gradient_cache) > cls._MAX_CACHED_GRADIENTS:
            cls._gradient_cache.pop(next(iter(cls._gradient_cache)))

    #: Cuánto tiene que cambiar la intensidad para justificar reconstruir el
    #: disco. Un 2 % es menos de la mitad de un nivel de gris a intensidad
    #: plena: por debajo de eso nadie ve la diferencia y sólo se paga el coste.
    _INTENSITY_EPSILON = 0.02

    def get_cached_gradient(self) -> pygame.Surface:
        """Disco de luz del instante actual, reconstruido sólo si hace falta.

        AUD-087: la versión anterior sólo miraba el radio y el color. Un foco
        con parpadeo cambia **radio e intensidad** —`get_current_intensity`
        existe precisamente para eso— pero la intensidad no entraba ni en la
        decisión de reconstruir ni en la construcción, que usaba `self.intensity`
        fija. Resultado: la mitad del parpadeo no se veía.
        """
        current_radius = self.get_current_radius()
        current_intensity = self.get_current_intensity()
        if (
            self._gradient is None
            or abs(current_radius - self._cached_radius) > 2
            or abs(current_intensity - self._cached_intensity) > self._INTENSITY_EPSILON
            or self._cached_color != self.color
        ):
            self._gradient = self.build_gradient(
                current_radius, self.color, current_intensity)
            self._cached_radius = current_radius
            self._cached_intensity = current_intensity
            self._cached_color = self.color
        return self._gradient


class LightSystem:
    """Manages all 2D light sources and renders a light overlay."""

    def __init__(self, ambient_brightness: float = 0.3) -> None:
        #: AUD-278 — geometría que proyecta sombra. Vacía = apagado.
        self._obstaculos: list[pygame.Rect] = []
        self._proyector = ProyectorDeSombras()
        self.lights: list[LightSource] = []
        self.ambient_brightness = ambient_brightness
        #: Tinte de la luz ambiente. Blanco no tiñe. Lo usa el ciclo día/noche
        #: (F2.1) para que el amanecer sea cálido y la madrugada azul: la hora
        #: se comunica sobre todo por el color, no por la cantidad de luz, que
        #: si baja demasiado deja el nivel injugable.
        self.ambient_color: tuple[int, int, int] = (255, 255, 255)
        self._darkness_surf: pygame.Surface | None = None
        self._multiplier: pygame.Surface | None = None
        #: AUD-403 — hacia dónde y cuánto se alargan las sombras del sol
        #: (GAP-051). `(0, 0)` es «no hay sol que proyecte»: de noche, o con él
        #: justo encima. Es el caso por defecto, así que un escenario que no
        #: publique el ambiente se ve exactamente como antes.
        self.sombra_solar: tuple[float, float] = (0.0, 0.0)

    def set_sombra_solar(self, direccion_y_largo: tuple[float, float]) -> None:
        """De dónde viene el sol, para las sombras direccionales (AUD-403).

        Se recibe ya derivado —`EnvironmentState.direccion_de_sombra`— y no el
        azimut crudo, por lo mismo que `set_obstaculos` recibe la lista hecha:
        este sistema no sabe de horas ni de estaciones, sabe de sombras. Y así
        el cálculo vive en un solo sitio, que es lo que evita que las sombras
        de las paredes y las de los personajes acaben apuntando a sitios
        distintos.
        """
        self.sombra_solar = direccion_y_largo

    def set_obstaculos(self, rects: list[pygame.Rect] | None) -> None:
        """La geometría que tapa la luz (AUD-278).

        `None` o lista vacía la apaga, que es el caso por defecto: hasta aquí
        una antorcha al otro lado de un muro iluminaba igual que si el muro no
        existiera.

        Se recibe la lista ya hecha en vez de buscarla: este sistema no sabe
        de escenarios, y la escena ya tiene los sólidos que le pasa al jugador
        cada fotograma.
        """
        self._obstaculos = list(rects) if rects else []

    def add_light(self, light: LightSource) -> None:
        self.lights.append(light)

    def remove_light(self, light: LightSource) -> None:
        if light in self.lights:
            self.lights.remove(light)

    def clear(self) -> None:
        self.lights.clear()

    def update(self, dt: float, camera_offset: pygame.Vector2) -> None:
        for light in self.lights:
            light.update(dt)

    def render(self, target: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        mapa = self.render_map(target.get_size(), camera_offset)
        if mapa is not None:
            target.blit(mapa, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def render_map(self, size: tuple[int, int],
                   camera_offset: pygame.Vector2) -> pygame.Surface:
        """Compone el multiplicador de luz para un tamaño y lo devuelve.

        AUD-343 — mismo trabajo que `render`, pero sin aplicar nada al
        `target`: en la ruta de GPU el mapa se sube a la tarjeta y es el
        sombreador de iluminación quien lo multiplica sobre la escena, una
        vez, en el mismo punto del orden de pintado que aquí. Que la
        composición y la aplicación sean dos llamadas separadas es lo que
        evita que la luz se multiplique dos veces: una escena con la ruta de
        GPU llama a `render_map` (o se la deja hacer a `render`, que ahora es
        `render_map` + un blit) y el renderer hace la otra mitad.
        """
        w, h = size

        if self._multiplier is None or self._multiplier.get_size() != (w, h):
            self._multiplier = pygame.Surface((w, h), pygame.SRCALPHA)
        # El brillo modula cada canal del tinte, así que un tinte blanco da el
        # gris neutro de siempre y uno cálido tiñe la sombra hacia el naranja.
        b = self.ambient_brightness
        piso = (
            int(self.ambient_color[0] * b),
            int(self.ambient_color[1] * b),
            int(self.ambient_color[2] * b),
        )
        self._multiplier.fill(piso)

        # AUD-302 — los degradados van en un lote, uno por foco.
        #
        # **Salvo con sombras proyectadas.** Con obstáculos, la sombra de cada
        # luz se resta justo después de sumarla y antes de la siguiente
        # (AUD-278): agruparlas rompería ese orden y las sombras de un muro
        # borrarían la luz de focos que ese muro no tapa. Con obstáculos se
        # dibuja como siempre, uno por uno.
        por_lotes = not self._obstaculos
        lote = SpriteBatch() if por_lotes else None

        for light in self.lights:
            screen_pos = (
                int(light.position.x - camera_offset.x),
                int(light.position.y - camera_offset.y),
            )
            gradient = light.get_cached_gradient()
            gw, gh = gradient.get_size()
            blit_x = screen_pos[0] - gw // 2
            blit_y = screen_pos[1] - gh // 2
            if lote is not None:
                lote.dibujar(gradient, (blit_x, blit_y), None,
                             pygame.BLEND_RGBA_MAX)
                continue
            self._multiplier.blit(gradient, (blit_x, blit_y), special_flags=pygame.BLEND_RGBA_MAX)
            # AUD-278 — la sombra se resta **de esta luz**, justo después de
            # sumarla y antes de la siguiente. Hacerlo al final, sobre la
            # máscara ya compuesta, borraría también la luz de los focos que no
            # están tapados por ese muro.
            if self._obstaculos:
                self._proyector.proyectar(
                    self._multiplier, light.position,
                    light.get_current_radius(), self._obstaculos, camera_offset,
                    piso_ambiente=piso)

        if lote is not None:
            lote.volcar(self._multiplier)

        return self._multiplier

    def mapa_de_luz(self) -> pygame.Surface | None:
        """El último multiplicador compuesto, o `None` si nadie compuso aún.

        AUD-343 — el documento que una escena con la ruta de GPU expone por
        su propiedad `light_surface`: es el mapa del fotograma actual, no una
        copia, así que sólo se puede leer después de `render_map`. Antes de
        eso devuelve `None`, que es lo que `App` necesita para saber que no
        hay nada que subir a la tarjeta.
        """
        return self._multiplier

    def get_player_light(self, player_pos: pygame.Vector2, is_combat: bool) -> LightSource:
        """Create/return a dynamic light for the player."""
        radius = 100 if is_combat else 60
        intensity = 0.9 if is_combat else 0.6
        color = (255, 220, 180) if not is_combat else (255, 200, 100)
        return LightSource(
            position=player_pos,
            radius=radius,
            color=color,
            intensity=intensity,
            flicker=True,
            flicker_speed=3.0,
            flicker_amount=0.1,
        )
