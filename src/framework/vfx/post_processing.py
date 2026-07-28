from __future__ import annotations

import numpy as np
import pygame

from src.engine.core import settings


class PostProcessing:
    """Screen-space post-processing effects: vignette, flash, tint, bloom, motion blur, color grading."""

    def __init__(self) -> None:
        self._vignette_strength: float = 0.4
        self._flash_color: tuple[int, int, int] = (0, 0, 0)
        self._flash_alpha: float = 0.0
        self._flash_duration: float = 0.0
        self._flash_timer: float = 0.0
        self._tint_color: tuple[int, int, int] = (0, 0, 0)
        self._tint_alpha: float = 0.0
        self._damage_vignette: float = 0.0
        # Pre-build vignette surface to avoid first-frame penalty (AUD-052).
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        self._vignette_surf: pygame.Surface | None = self._build_vignette(w, h)
        self._last_vignette_strength: float = self._vignette_strength
        self._bloom_intensity: float = 0.0
        #: Bloom permanente del escenario, sin decaimiento. `_bloom_intensity`
        #: es la ráfaga con temporizador; en cada fotograma se usa el mayor.
        self._bloom_base: float = 0.0
        self._bloom_target: float = 0.0
        #: Fotogramas desde el último recálculo del halo, y la intensidad con
        #: la que se calculó. Ver `_apply_bloom`.
        self._bloom_age: int = 0
        self._bloom_cached_intensity: float = -1.0
        self._bloom_decay: float = 0.0
        self._bloom_threshold: int = 80
        self._motion_blur_strength: float = 0.0
        self._prev_frame: pygame.Surface | None = None
        self._color_grading: tuple[int, int, int, int, int, int, int, int, int] | None = None
        self._flash_surf: pygame.Surface | None = None
        self._tint_surf: pygame.Surface | None = None
        self._blur_surf: pygame.Surface | None = None
        self._bloom_down: pygame.Surface | None = None
        self._bloom_up: pygame.Surface | None = None
        self._highlight_surf: pygame.Surface | None = None
        self._motion_up: pygame.Surface | None = None
        #: Modo de daltonismo — se carga una vez (lazy) para no hacer I/O
        #: (user_settings.get()) en cada fotograma (AUD-052).
        self._cb_mode: str | None = None

    def set_motion_blur(self, strength: float = 0.3) -> None:
        self._motion_blur_strength = max(0.0, min(1.0, strength))

    def clear_motion_blur(self) -> None:
        self._motion_blur_strength = 0.0
        self._prev_frame = None

    def set_color_grading(
        self, r: int, g: int, b: int,
        rr: int, gg: int, bb: int,
        rrr: int, ggg: int, bbb: int
    ) -> None:
        self._color_grading = (r, g, b, rr, gg, bb, rrr, ggg, bbb)

    def clear_color_grading(self) -> None:
        self._color_grading = None

    def set_bloom(self, intensity: float, duration: float = 0.3) -> None:
        self._bloom_target = max(0.0, min(1.0, intensity))
        self._bloom_intensity = self._bloom_target
        self._bloom_decay = 1.0 / max(0.01, duration)

    def flash(self, color: tuple[int, int, int], alpha: float = 200, duration: float = 0.1) -> None:
        self._flash_color = color
        self._flash_alpha = alpha
        self._flash_duration = duration
        self._flash_timer = duration

    def set_damage_vignette(self, strength: float) -> None:
        self._damage_vignette = max(0.0, min(0.6, strength))

    def set_tint(self, color: tuple[int, int, int], alpha: float) -> None:
        self._tint_color = color
        self._tint_alpha = alpha

    def clear_tint(self) -> None:
        self._tint_alpha = 0.0

    def update(self, dt: float) -> None:
        if self._flash_timer > 0:
            self._flash_timer -= dt
            if self._flash_timer <= 0:
                self._flash_alpha = 0.0
        if self._bloom_intensity > 0.001:
            self._bloom_intensity -= self._bloom_decay * dt
        else:
            self._bloom_intensity = 0.0

    def _apply_colorblind_filter(self, surface: pygame.Surface) -> None:
        # AUD-036: this used to read settings.COLORBLIND_MODE, a module global
        # that nothing ever assigned to. The options screen persisted the
        # player's choice to config.json and this filter read a different,
        # always-"off" variable, so selecting a colourblind mode had no effect
        # on a single rendered frame. Both sides now use user_settings.
        # AUD-052: Load mode once (lazy) and cache it to avoid hitting
        # user_settings.get() (which may do I/O on first call) every frame.
        if self._cb_mode is None:
            from src.engine.core import user_settings
            self._cb_mode = user_settings.get().colorblind_mode
        if self._cb_mode == "off":
            return
        arr = pygame.surfarray.pixels3d(surface)
        try:
            r = arr[:,:,0].astype(np.float32)
            g = arr[:,:,1].astype(np.float32)
            b = arr[:,:,2].astype(np.float32)
            if self._cb_mode == "protanopia":
                arr[:,:,0] = np.clip(r * 0.57 + g * 0.43, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.86, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.86, 0, 255).astype(np.uint8)
            elif self._cb_mode == "deuteranopia":
                arr[:,:,0] = np.clip(r * 0.63, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.78 + r * 0.22, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.86, 0, 255).astype(np.uint8)
            elif self._cb_mode == "tritanopia":
                arr[:,:,0] = np.clip(r * 0.95, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip(g * 0.43 + b * 0.57, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip(b * 0.43, 0, 255).astype(np.uint8)
        finally:
            del arr

    #: Factor de reducción para el bloom. A 1/4 de lado son 1/16 de los
    #: píxeles, y el desenfoque hace el resto: nadie distingue un halo
    #: calculado a 200x150 de uno calculado a 800x600.
    _BLOOM_DOWNSCALE = 6

    def _apply_bloom(self, surface: pygame.Surface, w: int, h: int, intensidad: float) -> None:
        """Añade el halo de las zonas brillantes.

        F1.2 — por qué esto se calcula en pequeño
        -----------------------------------------
        La versión anterior hacía dos cosas: un halo difuso barato (1,72 ms) y
        una **capa de realce** que recorría los 480.000 píxeles de la pantalla
        con numpy para hallar la luminancia. Medido: **12,08 ms**, o el 72 % del
        presupuesto de fotograma, cada fotograma que el bloom estuviera activo.

        Como el bloom sólo se activaba en ráfagas de 0,15 a 0,6 s, el efecto era
        que recoger un objeto o cambiar de fase el jefe **tiraba la tasa de
        refresco a la mitad** justo en el momento más vistoso del juego.

        Ahora la luminancia se calcula sobre la superficie ya reducida que el
        halo difuso necesita de todos modos: 30.000 píxeles en vez de 480.000,
        y una sola llamada a `smoothscale` para las dos cosas. El resultado es
        visualmente equivalente —un halo es información de baja frecuencia por
        definición— y permite dejar el bloom encendido de forma permanente.
        """
        pequeno = (max(1, w // self._BLOOM_DOWNSCALE), max(1, h // self._BLOOM_DOWNSCALE))
        if self._bloom_down is None or self._bloom_down.get_size() != pequeno:
            self._bloom_down = pygame.Surface(pequeno)
            self._highlight_surf = pygame.Surface(pequeno)
            self._bloom_up = None

        # El halo se recalcula cada N fotogramas y se reutiliza en los demás.
        #
        # Medido: con el halo recalculado en cada fotograma, la mediana de
        # Stage 0 subía de 5,25 a 9,88 ms y el p95 a 20,09 —fuera de
        # presupuesto—. Un halo es información de baja frecuencia y muy
        # difuminada: refrescarlo a 30 Hz en vez de 60 es invisible, y el resto
        # de los fotogramas sólo pagan un `blit`.
        self._bloom_age += 1
        reutilizable = (
            self._bloom_up is not None
            and self._bloom_up.get_size() == (w, h)
            and self._bloom_age < self._BLOOM_REFRESH_EVERY
            and abs(intensidad - self._bloom_cached_intensity) < 0.02
        )
        if reutilizable:
            surface.blit(self._bloom_up, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            return
        self._bloom_age = 0
        self._bloom_cached_intensity = intensidad

        pygame.transform.smoothscale(surface, pequeno, self._bloom_down)

        # Sólo lo que pasa del umbral de luminancia, en color. El halo difuso
        # que había antes sumaba la escena **entera** con `set_alpha`, y
        # `set_alpha` **no tiene efecto con BLEND_RGB_ADD**: el fondo oscuro
        # recibía la suma completa. Medido: un fondo de valor 43 subía a 239 y
        # una zona brillante de 208 subía a 234, es decir, el efecto aclaraba
        # más lo oscuro que lo iluminado, que es exactamente lo contrario de un
        # bloom. Aquí la atenuación va dentro de la aritmética de numpy, donde
        # sí surte efecto, y el umbral garantiza que las sombras no se toquen.
        realce = self._highlight_surf
        harr = pygame.surfarray.pixels3d(realce)
        try:
            arr = pygame.surfarray.pixels3d(self._bloom_down)
            try:
                rgb = arr.astype(np.float32)
                # Coeficientes de luma ITU-R BT.601.
                lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
            finally:
                del arr
            # Cuánto sobresale cada píxel del umbral, de 0 a 1.
            exceso = np.clip((lum - self._bloom_threshold) / 175.0, 0.0, 1.0)
            # El halo conserva el color de lo que brilla: una antorcha irradia
            # naranja y unas esporas verde. Un realce gris los volvería a todos
            # del mismo color.
            peso = (exceso * intensidad)[:, :, None]
            harr[:] = self._difuminar(rgb * peso, self._BLOOM_BLUR_RADIUS)
        finally:
            del harr

        self._bloom_up = pygame.transform.smoothscale(realce, (w, h))
        surface.blit(self._bloom_up, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

    #: Cada cuántos fotogramas se recalcula el halo. 2 significa 30 Hz.
    _BLOOM_REFRESH_EVERY = 2

    #: Radio del desenfoque del halo, en píxeles de la imagen reducida. Con
    #: reducción de 4, un radio de 6 equivale a ~24 px de pantalla por lado.
    _BLOOM_BLUR_RADIUS = 9

    @staticmethod
    def _difuminar(imagen: np.ndarray, radio: int) -> np.ndarray:
        """Desenfoque de caja separable, en dos pasadas de sumas acumuladas.

        F1.2 — por qué no basta reducir y volver a ampliar
        -------------------------------------------------
        El primer intento difuminaba el halo con dos `smoothscale`
        —reducir a un tercio y volver a ampliar—. No funcionó, y la razón es
        instructiva: el remuestreo bilineal interpola *entre* téxeles, así que
        una mancha luminosa reaparece con el mismo tamaño, sólo con los bordes
        suavizados. Medido: a 5, 20, 50, 90 y 150 px del borde del foco, el
        aporte del halo era exactamente **+0,0** en todos los casos. El halo
        tenía la misma silueta que la fuente, que es decir que no había halo.

        Un desenfoque de caja sí ensancha, porque cada píxel de salida es la
        media de una ventana de entrada. Separable en horizontal y vertical, y
        con sumas acumuladas, cuesta O(n) por eje independientemente del radio:
        sobre 200x150 son unas décimas de milisegundo.

        Es además el algoritmo de la Unidad VII —convolución con núcleo
        uniforme— resuelto con la optimización clásica de la imagen integral,
        así que el archivo sirve de ejemplo además de funcionar.
        """
        resultado = imagen.astype(np.float32)
        ventana = 2 * radio + 1
        for eje in (0, 1):
            # Se replica el borde para que el desenfoque no oscurezca los
            # extremos, que es lo que pasaría rellenando con ceros.
            relleno = [(0, 0)] * resultado.ndim
            relleno[eje] = (radio + 1, radio)
            acumulado = np.cumsum(
                np.pad(resultado, relleno, mode="edge"), axis=eje, dtype=np.float32)
            inicio = [slice(None)] * resultado.ndim
            fin = [slice(None)] * resultado.ndim
            n = resultado.shape[eje]
            inicio[eje] = slice(0, n)
            fin[eje] = slice(ventana, ventana + n)
            resultado = (acumulado[tuple(fin)] - acumulado[tuple(inicio)]) / ventana
        return np.clip(resultado, 0, 255).astype(np.uint8)

    def set_base_bloom(self, intensity: float) -> None:
        """Fija el bloom permanente del escenario, sin decaimiento.

        Se distingue de `set_bloom`, que es una ráfaga con temporizador: el
        bloom base es una decisión de dirección artística del nivel y no debe
        apagarse solo. En cada fotograma se usa el mayor de los dos, así que
        una ráfaga puede subir por encima del base y luego volver a él.
        """
        self._bloom_base = max(0.0, min(1.0, intensity))

    def set_vignette(self, strength: float) -> None:
        """Fija la intensidad de la viñeta base del escenario (0 a 0,6)."""
        self._vignette_strength = max(0.0, min(0.6, strength))

    def apply(self, surface: pygame.Surface) -> None:
        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT

        # Flash overlay
        if self._flash_alpha > 0:
            alpha = int(self._flash_alpha * (self._flash_timer / max(self._flash_duration, 0.01)))
            if self._flash_surf is None or self._flash_surf.get_size() != (w, h):
                self._flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self._flash_surf.fill((*self._flash_color, min(255, alpha)))
            surface.blit(self._flash_surf, (0, 0))

        # Damage + base vignette
        if self._damage_vignette > 0 or self._vignette_strength > 0:
            total_v = min(0.6, self._vignette_strength + self._damage_vignette)
            if (self._vignette_surf is None
                or self._vignette_surf.get_size() != (w, h)
                or abs(total_v - self._last_vignette_strength) > 0.01):
                self._vignette_surf = self._build_vignette(w, h)
                self._last_vignette_strength = total_v
            self._vignette_surf.set_alpha(int(total_v * 255))
            surface.blit(self._vignette_surf, (0, 0))

        # Bloom — downsample bright areas for a glow
        intensidad = max(self._bloom_intensity, self._bloom_base)
        if intensidad > 0.01:
            self._apply_bloom(surface, w, h, intensidad)

        # Tint overlay
        if self._tint_alpha > 0:
            if self._tint_surf is None or self._tint_surf.get_size() != (w, h):
                self._tint_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            self._tint_surf.fill((*self._tint_color, int(self._tint_alpha * 255)))
            surface.blit(self._tint_surf, (0, 0))

        # Motion blur — blend current frame with previous frame (1/4 res buffer)
        if self._motion_blur_strength > 0.01:
            sw, sh = max(1, w // 4), max(1, h // 4)
            down_size = (sw, sh)
            up_size = (w, h)
            if self._prev_frame is None:
                self._prev_frame = pygame.Surface(down_size)
                pygame.transform.smoothscale(surface, down_size, self._prev_frame)
            else:
                if self._blur_surf is None or self._blur_surf.get_size() != up_size:
                    self._blur_surf = pygame.Surface(up_size, pygame.SRCALPHA)
                if self._motion_up is None or self._motion_up.get_size() != up_size:
                    self._motion_up = pygame.Surface(up_size)
                prev_up = self._motion_up
                pygame.transform.smoothscale(self._prev_frame, up_size, prev_up)
                self._blur_surf.blit(prev_up, (0, 0))
                self._blur_surf.set_alpha(int(self._motion_blur_strength * 128))
                surface.blit(self._blur_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                pygame.transform.smoothscale(surface, down_size, self._prev_frame)

        # Color grading — 3x3 color matrix applied per pixel
        if self._color_grading is not None:
            cr, cg, cb, crr, cgg, cbb, crrr, cggg, cbbb = self._color_grading
            arr = pygame.surfarray.pixels3d(surface)
            try:
                pr = arr[:,:,0].astype(np.int32)
                pg = arr[:,:,1].astype(np.int32)
                pb = arr[:,:,2].astype(np.int32)
                arr[:,:,0] = np.clip((pr * cr + pg * cg + pb * cb) // 255, 0, 255).astype(np.uint8)
                arr[:,:,1] = np.clip((pr * crr + pg * cgg + pb * cbb) // 255, 0, 255).astype(np.uint8)
                arr[:,:,2] = np.clip((pr * crrr + pg * cggg + pb * cbbb) // 255, 0, 255).astype(np.uint8)
            finally:
                del arr

        # Colorblind filter (last, on top of everything)
        self._apply_colorblind_filter(surface)

    def _build_vignette(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        max_dist_sq = cx * cx + cy * cy
        arr = pygame.surfarray.pixels_alpha(surf)
        try:
            xs, ys = np.ogrid[:w, :h]
            dist_sq = (xs - cx) ** 2 + (ys - cy) ** 2
            dist = np.sqrt(dist_sq / max_dist_sq)
            alpha = np.clip((dist - 0.3) / 0.7 * 200, 0, 200).astype(np.uint8)
            arr[:, :] = alpha
        finally:
            del arr
        return surf
