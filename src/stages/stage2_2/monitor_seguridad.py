"""
Module: monitor_seguridad
System: stage (student assignment — entrada_antenas)
Academic Unit: Unidad VII — Procesamiento digital de imagen

Monitor CRT de la caseta de seguridad del Stage 2-2.

Captura lo que ve la cámara de vigilancia, lo procesa con `FilterTools` y lo
dibuja como una pantalla de circuito cerrado, con su histograma debajo.

El efecto es **diegético**: el escenario ya tenía cámaras de seguridad, así que
mostrar su señal procesada pertenece a la ficción en vez de superponerse a
ella. Y el resultado del histograma no es decorativo — decide el alcance de
detección de la cámara.

La cadena de procesamiento
--------------------------
Se aplica en este orden, y el orden importa:

1. **Reducción a 128 × 96.** Todo el coste de un filtro convolutivo es
   proporcional al número de píxeles. Procesar la pantalla completa
   (800 × 600 = 480 000 px) costaría unas 39 veces más que procesar el
   recorte reducido (12 288 px), para un resultado que se muestra en una
   ventana de 128 px de ancho.

2. **`gaussian_blur(sigma=1.2)`.** Un filtro de suavizado gaussiano antes de
   derivar. No es opcional ni estético: **la derivada de una señal amplifica
   su ruido**. Un píxel aislado que difiera de sus vecinos produce un gradiente
   enorme, y sin pre-suavizado el mapa de bordes sale lleno de puntos sueltos.
   Es el mismo paso que Canny incorpora internamente.

   El núcleo gaussiano bidimensional es::

       G(x, y) = (1 / 2πσ²) · e^(−(x² + y²) / 2σ²)

   con σ = 1.2 px. Un sigma menor deja pasar ruido; uno mayor difumina los
   bordes que se quieren detectar. A esta escala de tile (16 px) 1.2 conserva
   las siluetas y borra el granulado del asfalto.

3. **`sobel_edge()`.** Magnitud del gradiente por convolución con dos núcleos
   de 3 × 3, uno por eje::

       Gx = [-1  0  1]        Gy = [-1 -2 -1]
            [-2  0  2]             [ 0  0  0]
            [-1  0  1]             [ 1  2  1]

   Cada uno es el producto exterior de una derivada central `[-1 0 1]` por un
   suavizado binomial `[1 2 1]` en el eje perpendicular: derivan en una
   dirección y promedian en la otra. La magnitud del gradiente es::

       |∇I| = √(Gx² + Gy²)

   Son los que devuelve `FilterTools.get_standard_kernel("sobel_x")` y
   `("sobel_y")`, verificado.

4. **`adjust_contrast(factor=1.9)`.** El mapa de magnitudes queda concentrado
   en valores bajos: la mayoría de los píxeles no son borde. Un estiramiento
   alrededor del punto medio separa el borde real del fondo::

       I' = clip((I − 128) · 1.9 + 128,  0, 255)

   Sin este paso la pantalla se ve gris uniforme a 128 px de ancho.

5. **Tinte de fósforo verde y líneas de barrido**, para que lea como monitor
   CRT y no como una imagen recortada.

El histograma que decide la lógica
----------------------------------
`FilterTools.compute_histogram()` devuelve, entre otros, un canal
``"luminance"``: 256 casillas con el conteo de píxeles de cada nivel, donde la
luminancia es la combinación estándar de la recomendación ITU-R BT.601::

    Y = 0.299·R + 0.587·G + 0.114·B

Los coeficientes no son iguales porque el ojo humano no es igual de sensible a
los tres primarios: el verde aporta más de la mitad de la luminancia percibida
y el azul apenas un 11 %.

De ese histograma se calcula la luminancia media como esperanza discreta::

    Y_media = Σ (i · h[i]) / Σ h[i]        para i = 0..255

y se convierte en el multiplicador de alcance de la cámara. En el asfalto
soleado el jugador se recorta contra un fondo claro y lo ven de lejos; bajo la
sombra de un árbol o contra el edificio gris, el alcance cae casi a la mitad.
Es sigilo emergente que sale de una medición real de la imagen, no de una
bandera puesta a mano en el mapa.
"""
from __future__ import annotations

import numpy as np
import pygame

from src.framework.processing.color_tools import ColorTools
from src.framework.processing.filter_tools import FilterTools

#: Tamaño de la imagen procesada, a la mitad de la versión anterior.
#:
#: 64 × 48 en vez de 128 × 96. El panel completo pasa de 138 × 163 px a
#: 74 × 98 sobre una pantalla de 800 × 600, así que deja de comer esquina.
#: Como los filtros se aplican DESPUÉS de reducir, procesar 3 072 px en vez
#: de 12 288 abarata la cadena por cuatro.
_ANCHO, _ALTO = 64, 48

#: Lado del recorte del mundo que alimenta al monitor, en píxeles de pantalla.
#:
#: Se mantiene en 128 × 96 aunque la pantalla se muestre a 64 × 48, por dos
#: razones. La calibración de `_Y_OSCURO`/`_Y_CLARO` se midió con este recorte,
#: y cambiarlo la invalidaría. Y reducir 2:1 con `smoothscale` promedia cuatro
#: píxeles en uno, lo que actúa como un antialias previo que le viene bien al
#: detector de bordes.
#:
#: Medido antes: con 256 × 192 el recorte abarcaba tanto cielo que la
#: luminancia media apenas variaba entre 118 y 133 en todo el nivel, y el
#: alcance de la cámara cambiaba 12 px de 190 — indistinguible.
_RECORTE_W, _RECORTE_H = 128, 96

#: Parámetros de la cadena. Justificados en el encabezado del módulo.
#:
#: Sigma bajado de 1.2 a 0.8: con 1.2 las siluetas salían blandas porque el
#: suavizado previo se comía detalle del mismo orden que el tile (16 px). 0.8
#: sigue eliminando el granulado del asfalto sin redondear los contornos.
_SIGMA_GAUSS: float = 0.8
_FACTOR_CONTRASTE: float = 1.5

#: Núcleo de engrosado. Cruz de 5 vecinos con peso 0.30::
#:
#:      ⎡  0   0.30   0  ⎤
#:      ⎢0.30  0.30  0.30⎥
#:      ⎣  0   0.30   0  ⎦
#:
#: El peso bajó dos veces al mirar el resultado. De 0.7 a 0.45 porque las
#: líneas se fundían entre sí y las siluetas salían como manchas rellenas. Y de
#: 0.45 a 0.30 al reducir la pantalla a 64 × 48: a menor resolución una línea
#: de 1 px ocupa proporcionalmente el doble, así que necesita la mitad de
#: engrosado para leerse igual.
#:
#: Cada píxel suma 0.30 de sí mismo y de sus cuatro vecinos ortogonales. Sobre
#: un mapa de bordes —líneas claras sobre fondo negro— eso **dilata** las
#: líneas: una línea de 1 px pasa a 3 px y se satura contra el tope de 255,
#: mientras el fondo negro sigue en 0 porque 0.30 × 0 = 0. Es la razón por la
#: que la cruz y no un cuadrado 3×3 completo: la cruz engrosa sin redondear
#: las esquinas.
_KERNEL_ENGROSADO = np.array(
    [[0.00, 0.30, 0.00],
     [0.30, 0.30, 0.30],
     [0.00, 0.30, 0.00]], dtype=np.float32,
)

#: Fósforo verde del CRT, y ámbar para la etiqueta de zona. El ámbar es el otro
#: color clásico de monitor monocromo, así que contrasta con el verde sin
#: salirse del lenguaje visual de una pantalla de vigilancia.
_FOSFORO: tuple[int, int, int] = (120, 255, 150)
_AMBAR: tuple[int, int, int] = (255, 186, 66)
_ROJO_ALERTA: tuple[int, int, int] = (255, 82, 68)

#: Zonas del nivel, en coordenadas de mundo. Se evalúan en orden y gana la
#: primera que contenga al jugador.
_ZONAS: tuple[tuple[str, float, float, float, float], ...] = (
    #  etiqueta      x_min   x_max   y_min   y_max
    ("AZOTEA",       1280.0, 1980.0,   0.0,  300.0),
    ("ESCALADA",     1040.0, 1300.0,   0.0,  640.0),
    ("CASETA",        980.0, 1300.0, 640.0,  820.0),
    ("ENTRADA",         0.0,  480.0,   0.0,  820.0),
    ("PARQUEO",       480.0, 1040.0,   0.0,  820.0),
)

#: Alto del minimapa del motor (`Minimap._minimap_h`), en píxeles. Se usa para
#: colocar el monitor debajo cuando se ancla arriba a la derecha.
_ALTO_MINIMAPA: int = 56

#: Alto del bloque de vida del HUD (retrato de 34 px desde y=2, más corazones y
#: barra de combo). Se usa para colgar el monitor justo debajo.
_ALTO_HUD_VIDA: int = 40

#: Frecuencia de refresco del monitor, en Hz. A 60 fps sería malgastar: una
#: cámara de circuito cerrado real ronda los 8-12 cuadros por segundo, y bajar
#: a 8 divide el coste del procesado por siete.
_HZ: float = 8.0

#: Extremos de luminancia media que mapean al alcance mínimo y máximo.
#:
#: Calibrados contra el nivel real, no elegidos a ojo. Recorriendo el escenario
#: y midiendo la luminancia media en siete puntos representativos, el rango
#: observado va de **118.1** (bajo la sombra proyectada de un árbol) a **167.3**
#: (azotea contra el cielo abierto). Los extremos se fijan un poco por fuera de
#: ese intervalo para que ninguna zona real quede saturada contra el tope.
_Y_OSCURO, _Y_CLARO = 115.0, 170.0
_FACTOR_MIN, _FACTOR_MAX = 0.55, 1.00


class MonitorSeguridad:
    """Pantalla de circuito cerrado con la señal de la cámara procesada."""

    def __init__(self, ancla: str = "arriba_izquierda", margen: int = 10) -> None:
        """
        Args:
            ancla: `arriba_derecha`, `abajo_derecha`, `abajo_izquierda` o
                `arriba_izquierda`. Por defecto arriba a la derecha, debajo
                del minimapa del motor: los dos paneles de información
                comparten la columna derecha y dejan libre la zona donde
                aparece el jugador.
            margen: separación al borde de pantalla, en píxeles.
        """
        self.ancla = ancla
        self.margen = margen

        self._acum = 0.0
        self._t = 0.0

        #: Última imagen procesada, lista para dibujar.
        self.imagen: pygame.Surface | None = None

        #: Zona del nivel donde está el jugador y si alguna cámara lo ve.
        self.zona: str = "ENTRADA"
        self.alertado: bool = False

        # Fuentes creadas UNA vez. Construir un `pygame.font.Font` cuesta
        # milisegundos: hacerlo dentro de `draw()` añadía ~13 ms por fotograma,
        # más que toda la cadena de filtros junta (2.95 ms medidos).
        self._f_cabecera = pygame.font.Font(None, 12)
        self._f_zona = pygame.font.Font(None, 13)
        self._f_lectura = pygame.font.Font(None, 11)

        # Estado observable, para la lógica de juego y para el README.
        self.luminancia_media: float = 128.0
        self.factor_visibilidad: float = 1.0
        self.histograma: dict | None = None
        self.ms_ultimo_proceso: float = 0.0

    # ── Ciclo de vida ───────────────────────────────────────────────

    def update(self, dt: float, pantalla: pygame.Surface,
               centro_interes: tuple[int, int],
               pos_mundo: tuple[float, float] | None = None,
               alertado: bool = False) -> None:
        """Refresca el monitor a `_HZ`, no cada fotograma.

        Args:
            pantalla: la superficie ya renderizada del mundo.
            centro_interes: punto en coordenadas de **pantalla** alrededor del
                cual se recorta la señal — normalmente el jugador.
            pos_mundo: posición del jugador en coordenadas de mundo, para
                resolver la etiqueta de zona.
            alertado: si alguna cámara lo está detectando en este momento.
        """
        self._t += dt

        # La cabecera y la etiqueta se actualizan **cada fotograma**, aunque la
        # imagen solo se procese a 8 Hz: un aviso de detección que tarda hasta
        # 125 ms en encenderse se siente roto.
        self.alertado = alertado
        if pos_mundo is not None:
            self.zona = self._zona_de(pos_mundo)

        self._acum += dt
        if self._acum < 1.0 / _HZ:
            return
        self._acum = 0.0

        recorte = self._recortar(pantalla, centro_interes)
        if recorte is None:
            return

        import time
        t0 = time.perf_counter()

        # ── Histograma: mide ANTES de procesar ─────────────────────
        # Se calcula sobre el recorte crudo, no sobre el mapa de bordes: lo que
        # interesa es cuánta luz hay en la escena, no cuántos bordes tiene.
        self.histograma = FilterTools.compute_histogram(recorte)
        self.luminancia_media = self._media_luminancia(self.histograma)
        self.factor_visibilidad = self._a_factor(self.luminancia_media)

        # ── Cadena de filtros ──────────────────────────────────────
        pequeno = pygame.transform.smoothscale(recorte, (_ANCHO, _ALTO))
        suavizado = FilterTools.gaussian_blur(pequeno, _SIGMA_GAUSS)
        bordes = FilterTools.sobel_edge(suavizado)
        # `stretch_contrast` normaliza cada canal a todo el rango [0, 255]. Sin
        # este paso, una escena de poco contraste —el asfalto contra su propia
        # sombra— produce un mapa de bordes tenue que el factor fijo de
        # contraste no logra levantar. Estirando primero, el borde más fuerte
        # de cada cuadro llega siempre a blanco, sea cual sea la escena.
        normalizado = FilterTools.stretch_contrast(bordes)
        # Engrosado: dilata las líneas para que las siluetas se lean a 64 px.
        engrosado = FilterTools.apply_kernel(normalizado, _KERNEL_ENGROSADO)
        realzado = FilterTools.adjust_contrast(engrosado, _FACTOR_CONTRASTE)
        self.imagen = ColorTools.apply_tint(realzado, _FOSFORO)

        self.ms_ultimo_proceso = (time.perf_counter() - t0) * 1000.0

    # ── Cálculo ─────────────────────────────────────────────────────

    @staticmethod
    def _recortar(pantalla: pygame.Surface,
                  centro: tuple[int, int]) -> pygame.Surface | None:
        """Recorte centrado, recortado a los límites de la pantalla."""
        w, h = pantalla.get_size()
        x = max(0, min(w - _RECORTE_W, centro[0] - _RECORTE_W // 2))
        y = max(0, min(h - _RECORTE_H, centro[1] - _RECORTE_H // 2))
        rect = pygame.Rect(x, y, min(_RECORTE_W, w), min(_RECORTE_H, h))
        if rect.width < 8 or rect.height < 8:
            return None
        # `.copy()` y no `subsurface()`: la subsuperficie comparte memoria con
        # la pantalla, y `surfarray` sobre ella bloquearía la superficie padre
        # mientras el resto del dibujado sigue en curso.
        return pantalla.subsurface(rect).copy()

    @staticmethod
    def _zona_de(pos: tuple[float, float]) -> str:
        """Etiqueta de la zona que contiene al jugador.

        Se recorre `_ZONAS` en orden y gana la primera que lo contenga, así que
        las zonas más específicas van declaradas antes que las generales.
        """
        x, y = pos
        for etiqueta, x0, x1, y0, y1 in _ZONAS:
            if x0 <= x < x1 and y0 <= y < y1:
                return etiqueta
        return "EXTERIOR"

    @staticmethod
    def _media_luminancia(hist: dict) -> float:
        """Esperanza discreta del histograma de luminancia."""
        lum = hist["luminance"]
        total = int(lum.sum())
        if total <= 0:
            return 128.0
        return float(sum(i * int(lum[i]) for i in range(256)) / total)

    @staticmethod
    def _a_factor(y_media: float) -> float:
        """Mapea luminancia media a multiplicador de alcance, con recorte."""
        t = (y_media - _Y_OSCURO) / (_Y_CLARO - _Y_OSCURO)
        t = max(0.0, min(1.0, t))
        return _FACTOR_MIN + (_FACTOR_MAX - _FACTOR_MIN) * t

    # ── Dibujado ────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        if self.imagen is None:
            return

        w, h = surface.get_size()
        # imagen + separación + histograma (14) + línea de lectura (11).
        alto_total = _ALTO + 32
        if self.ancla == "arriba_izquierda":
            # Debajo del HUD de vida: el retrato ocupa Rect(2, 2, 34, 34) y los
            # corazones empiezan en y = 6, así que el bloque superior izquierdo
            # termina cerca de y = 40. Se deja margen hasta 48.
            ox = self.margen - 2
            oy = _ALTO_HUD_VIDA + 14
        elif self.ancla == "arriba_derecha":
            # Debajo del minimapa del motor, que ocupa (716, 4) a (796, 60) en
            # una pantalla de 800 × 600. `_ALTO_MINIMAPA` deja el hueco justo
            # para que los dos paneles compartan la columna derecha sin
            # solaparse ni tocarse.
            ox = w - _ANCHO - self.margen - 6
            oy = self.margen + _ALTO_MINIMAPA + 18
        elif self.ancla == "abajo_derecha":
            ox = w - _ANCHO - self.margen - 6
            oy = h - alto_total - self.margen - 6
        elif self.ancla == "abajo_izquierda":
            ox = self.margen + 6
            oy = h - alto_total - self.margen - 6
        else:
            ox, oy = self.margen + 6, self.margen + 16

        # Carcasa. Se tiñe de rojo apagado durante la alerta, para que el
        # estado se lea de reojo sin tener que fijar la vista en el texto.
        parpadeo = int(self._t * 3.0) % 2 == 0
        borde = _ROJO_ALERTA if (self.alertado and parpadeo) else (78, 84, 96)
        fondo = (44, 26, 28) if self.alertado else (26, 28, 34)
        marco = pygame.Rect(ox - 4, oy - 13, _ANCHO + 8, alto_total + 16)
        pygame.draw.rect(surface, fondo, marco, border_radius=4)
        pygame.draw.rect(surface, borde, marco, 1, border_radius=4)

        # ── Cabecera: cambia de estado ─────────────────────────────
        # A 64 px de ancho no cabe "o MONITOREADO": se acorta a la palabra que
        # lleva el significado. La cabecera se recorta al ancho del panel para
        # que ningún idioma futuro la desborde.
        if self.alertado:
            texto, color = "! DETECTADO", _ROJO_ALERTA if parpadeo else (150, 60, 55)
        else:
            texto, color = "o VIGILADO", (150, 205, 165)
        cab = self._f_cabecera.render(texto, True, color)
        surface.blit(cab, (ox - 1, oy - 12), pygame.Rect(0, 0, _ANCHO + 2, 12))

        # Testigo de grabación: 1 Hz en reposo, 3 Hz en alerta
        ritmo = 3.0 if self.alertado else 1.0
        if int(self._t * ritmo * 2.0) % 2 == 0:
            pygame.draw.circle(surface, _ROJO_ALERTA,
                               (ox + _ANCHO - 3, oy - 7), 2)

        # ── Señal ──────────────────────────────────────────────────
        surface.blit(self.imagen, (ox, oy))

        # Líneas de barrido: una de cada tres filas, oscurecida
        barrido = pygame.Surface((_ANCHO, _ALTO), pygame.SRCALPHA)
        for y in range(0, _ALTO, 3):
            pygame.draw.line(barrido, (0, 0, 0, 58), (0, y), (_ANCHO, y))
        surface.blit(barrido, (ox, oy))

        # ── Etiqueta de zona, en ámbar sobre fondo oscuro ──────────
        etiqueta = self._f_zona.render(self.zona, True, _AMBAR)
        ew, eh = etiqueta.get_size()
        # Esquina superior derecha, no la inferior izquierda: abajo tapaba el
        # suelo, que es donde está casi toda la información útil de la señal.
        # Arriba a la derecha casi siempre hay cielo.
        caja = pygame.Rect(ox + _ANCHO - ew - 6, oy + 2, ew + 4, eh)
        fondo_etq = pygame.Surface(caja.size, pygame.SRCALPHA)
        fondo_etq.fill((0, 0, 0, 185))
        surface.blit(fondo_etq, caja.topleft)
        pygame.draw.rect(surface, (140, 100, 40), caja, 1)
        surface.blit(etiqueta, (caja.x + 2, caja.y))

        pygame.draw.rect(surface, borde if self.alertado else (60, 120, 80),
                         (ox, oy, _ANCHO, _ALTO), 1)

        self._dibujar_histograma(surface, ox, oy + _ALTO + 3)

    def _dibujar_histograma(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        """Histograma de luminancia en 16 columnas, con la media marcada.

        Se agrupan las 256 casillas de 16 en 16 —antes de 8 en 8— porque con
        64 px de ancho solo caben 16 barras de 4 px.
        """
        if self.histograma is None:
            return
        alto = 14
        pygame.draw.rect(surface, (18, 20, 24), (ox, oy, _ANCHO, alto))

        lum = self.histograma["luminance"]
        # 256 casillas en 32 columnas: se agrupan de ocho en ocho para que cada
        # barra tenga 4 px de ancho y el gráfico siga siendo legible.
        grupos = [int(lum[i * 16:(i + 1) * 16].sum()) for i in range(16)]
        techo = max(grupos) or 1
        for i, v in enumerate(grupos):
            altura = int(alto * v / techo)
            if altura <= 0:
                continue
            pygame.draw.rect(surface, (95, 190, 120),
                             (ox + i * 4, oy + alto - altura, 3, altura))

        # Marca de la luminancia media
        mx = ox + int(_ANCHO * self.luminancia_media / 255.0)
        pygame.draw.line(surface, (255, 210, 90), (mx, oy), (mx, oy + alto))
        surface.blit(
            self._f_lectura.render("Y=%3.0f vis=%.2f" % (self.luminancia_media,
                                                        self.factor_visibilidad),
                                   True, (150, 205, 165)),
            (ox, oy + alto + 1))
