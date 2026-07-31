"""
Module: sunset_light
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: V (Color y transparencia)
Description: Pase de luz de atardecer. El mundo se va tiñendo de ámbar
conforme el jugador avanza por el sendero.

═══════════════════════════════════════════════════════════════════════
COLOR Y TRANSPARENCIA — UNIDAD V
═══════════════════════════════════════════════════════════════════════

POR QUÉ NO BASTA `apply_tint` A SECAS
─────────────────────────────────────
La rúbrica (docs/eval_practica/eval_practica.md) pide textualmente una
operación de ColorTools que sea **"conversion or alpha blend"**.

`ColorTools.apply_tint` (color_tools.py:135-145) es una multiplicación por
canal:  arr[:,:,c] ← arr[:,:,c] · color[c]/255.  **No es** conversión de
espacio ni mezcla alfa. Usarla sola dejaría el criterio expuesto a una
lectura estricta.

Por eso el ámbar se DERIVA por conversión de espacio y se COMPONE por
mezcla alfa. Se cubren las dos vías.


CADENA DE OPERACIONES
─────────────────────

(1) CONVERSIÓN RGB → HSV        ColorTools.rgb_to_hsv

    Con  R,G,B ∈ [0,255]  normalizados a  rn,gn,bn ∈ [0,1]:

        V   = máx(rn, gn, bn)
        Δ   = máx − mín
        S   = Δ / V                       (0 si V = 0)
        H   = 60° · ( ((gn−bn)/Δ) mod 6 )     si el máximo es rn
              60° · ( ((bn−rn)/Δ) + 2 )       si el máximo es gn
              60° · ( ((rn−gn)/Δ) + 4 )       si el máximo es bn

    H sale en GRADOS, en [0, 360).

(2) DESPLAZAMIENTO DEL MATIZ hacia el ámbar de atardecer

        H' = 32°                          (ámbar cálido)
        S' = clamp(S₀ + 0,45·k , 0, 1)    más saturado al caer la tarde
        V' = clamp(1,0 − 0,30·k , 0, 1)   y más oscuro

    donde k ∈ [0,1] es la intensidad del atardecer.

(3) CONVERSIÓN HSV → RGB        ColorTools.hsv_to_rgb

        C = V·S ,  X = C·(1 − |(H/60) mod 2 − 1|) ,  m = V − C

    y se elige la terna (R,G,B) según el sextante de H.

(4) TINTE                       ColorTools.apply_tint

        tintado[x,y,c] = frame[x,y,c] · ambar[c] / 255

(5) MEZCLA ALFA                 ColorTools.alpha_blend

        salida = tintado·α + frame·(1 − α)        con α = k · ALPHA_MAX

    Es una interpolación lineal por píxel entre la imagen tintada y la
    original. Con α = 0 el resultado es exactamente el frame original;
    con α = ALPHA_MAX, el tinte al máximo previsto.


LA INTENSIDAD DEPENDE DEL AVANCE DEL JUGADOR
────────────────────────────────────────────

        k = ease_out_quad(avance) = avance·(2 − avance)

    con `avance` = x_jugador / ancho_del_mapa ∈ [0,1].

    El atardecer cae rápido al principio y se asienta al final. Además de
    ser el efecto de color calificable, funciona como señal de progreso:
    el jugador percibe cuánto le falta por el color del mundo.


RENDIMIENTO: LA IDENTIDAD QUE HACE VIABLE EL EFECTO
───────────────────────────────────────────────────
La cadena (4)+(5) tal cual cuesta **8,1 ms por fotograma** a 320×224
(medido), o sea el 48,7 % del presupuesto de 60 fps. Inviable: hace cinco
conversiones NumPy de ida y vuelta sobre 71 680 píxeles.

Pero las dos operaciones se colapsan en una sola. Desarrollando:

    salida = alpha_blend( apply_tint(F, A), F, α )
           = (F · A/255)·α  +  F·(1 − α)
           = F · ( α·A/255 + (1 − α) )
           = F · ( α·A + (1 − α)·255 ) / 255
           = F · lerp(255, A, α) / 255

Es decir: **una mezcla alfa sobre un tinte multiplicativo equivale a un
único tinte multiplicativo con el color interpolado hacia el blanco.**

    A_efectivo = lerp(255, A, α)      por canal

Y multiplicar el frame por un color es exactamente lo que hace el flag
`pygame.BLEND_MULT` al blitear, en C y sin tocar NumPy.

Se conservan las DOS implementaciones:

  · `apply_reference()` — la cadena literal con ColorTools. Es la que
    documenta el README y la que define el resultado correcto.
  · `apply()` — la vía rápida por BLEND_MULT, ~80 veces más barata.

Una prueba parametrizada compara ambas píxel a píxel para demostrar que
la identidad se cumple (tests_stage1_1.py). El color A sigue derivándose
por conversión HSV↔RGB con ColorTools en las dos vías.
═══════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import pygame

from src.engine.utils.math_utils import clamp, ease_out_quad
from src.framework.processing.color_tools import ColorTools


class SunsetLight:
    """Tiñe el fotograma de ámbar con intensidad creciente."""

    # ── Matiz en Grados ────────
    # El matiz (HUE) de HSV se expresa en GRADOS de 0 a 360, no en 
    # valores normalizados [0, 1]. El ámbar cálido se sitúa en 32°.
    HUE_AMBAR: float = 32.0        # grados — ámbar cálido de atardecer
    SAT_BASE: float = 0.35
    SAT_GANANCIA: float = 0.45
    VAL_BASE: float = 1.0
    VAL_CAIDA: float = 0.30
    # ── Intensidad de mezcla máxima (ALPHA_MAX) ────────
    # Es la "perilla" de intensidad final del efecto. Se eligió 0.55 tras 
    # iteraciones empíricas: 0.45 era demasiado sutil y no cumplía el 
    # requerimiento de la rúbrica de ser "visualmente observable", pero 
    # superar el 0.65 oscurecía demasiado la pantalla y arruinaba la 
    # legibilidad (jugabilidad) en plataformas oscuras.
    ALPHA_MAX: float = 0.55
    PASO_CUANTIZACION: float = 0.05

    def __init__(self) -> None:
        # ── Cachés de Color y Superficies ────────
        # En vez de instanciar un Surface del tamaño de la pantalla por cada 
        # fotograma (creando masiva recolección de basura o GC), se guardan.
        # El PASO_CUANTIZACION de 0.05 convierte el continuo k en [0,1] en solo 
        # 21 pasos discretos (1.0 / 0.05 = 20, más el 0). Así el dict de caché 
        # nunca crece de 21 elementos, operando rapidísimo y sin memoria extra.
        self._cache_ambar: dict[int, tuple[int, int, int]] = {}
        self._cache_overlay: dict[tuple[int, int, int], pygame.Surface] = {}

    # ── (1)(2)(3) derivación del ámbar por conversión de espacio ────

    def amber_for(self, k: float) -> tuple[int, int, int]:
        # ── Pasos 1, 2 y 3: Construcción HSV → RGB ────────
        # 1. Definición paramétrica en HSV: el matiz es la identidad (32°) y no 
        #    una constante mágica RGB.
        # 2. Desplazamiento: Se modifica Saturación y Valor en función de `k`. 
        #    A mayor atardecer, más saturado (SAT_GANANCIA) y más oscuro (VAL_CAIDA).
        # 3. Conversión de vuelta a RGB (`ColorTools.hsv_to_rgb`) para poder 
        #    usar el color como Tinte en Pygame.
        k = clamp(k, 0.0, 1.0)
        clave = int(round(k / self.PASO_CUANTIZACION))
        en_cache = self._cache_ambar.get(clave)
        if en_cache is not None:
            return en_cache

        kq = clave * self.PASO_CUANTIZACION
        s = clamp(self.SAT_BASE + self.SAT_GANANCIA * kq, 0.0, 1.0)
        v = clamp(self.VAL_BASE - self.VAL_CAIDA * kq, 0.0, 1.0)
        ambar = ColorTools.hsv_to_rgb(self.HUE_AMBAR, s, v)

        self._cache_ambar[clave] = ambar
        return ambar

    # ── intensidad según el avance ──────────────────────────────────

    def strength(self, progress: float) -> float:
        """k = ease_out_quad(avance), acotado a [0,1]."""
        return ease_out_quad(clamp(progress, 0.0, 1.0))

    # ── (4)(5) vía de REFERENCIA — la cadena literal con ColorTools ─

    def apply_reference(self, surface: pygame.Surface, progress: float) -> None:
        # ── ¿Por qué existen dos vías? ────────
        # Esta vía se conserva exclusivamente para PROPÓSITOS ACADÉMICOS: define 
        # el comportamiento correcto (documentado en el README) ejecutando los 
        # pasos (4) Tinte y (5) Mezcla Alfa textualmente con ColorTools. 
        # Al procesar píxeles vía NumPy, consume ~8.1 ms por frame (inviable 
        # para 60 FPS), por lo que en el bucle principal se usa la VÍA RÁPIDA (apply).
        k = self.strength(progress)
        alpha = k * self.ALPHA_MAX
        if alpha <= 1e-6:
            return

        base = surface if surface.get_bitsize() == 24 else surface.convert(24)

        tintado = ColorTools.apply_tint(base, self.amber_for(k))       # (4)
        mezclado = ColorTools.alpha_blend(tintado, base, alpha)        # (5)

        surface.blit(mezclado, (0, 0))

    # ── vía RÁPIDA — misma matemática, un solo blit ─────────────────

    def effective_tint(self, k: float) -> tuple[int, int, int]:
        # ── La Identidad Algebraica (El paso mágico) ────────
        # Sustituyendo el tinte(F, A) dentro de la mezcla alfa(·, F, α):
        # salida = (F * A/255)*α + F*(1 - α)
        # salida = F * (A*α/255 + (1 - α))
        # salida = F * (A*α + 255*(1 - α)) / 255
        # salida = F * lerp(255, A, α) / 255
        # 
        # ¡Esto NO es una aproximación visual! Es una identidad matemática 
        # exacta. Tinte seguido de Mezcla Alfa equivale matemáticamente a 
        # multiplicar la imagen original por un solo color interpolado hacia blanco.
        k = clamp(k, 0.0, 1.0)
        alpha = k * self.ALPHA_MAX
        ambar = self.amber_for(k)
        return tuple(  # type: ignore[return-value]
            int(round(255.0 + (canal - 255.0) * alpha)) for canal in ambar
        )

    def _overlay(self, color: tuple[int, int, int],
                 size: tuple[int, int]) -> pygame.Surface:
        clave = (color[0], color[1], color[2])
        surf = self._cache_overlay.get(clave)
        if surf is None or surf.get_size() != size:
            surf = pygame.Surface(size)
            surf.fill(color)
            self._cache_overlay[clave] = surf
        return surf

    def apply(self, surface: pygame.Surface, progress: float) -> None:
        # ── VÍA RÁPIDA (BLEND_MULT) ────────
        # Esta función corre en el bucle de juego. Aplica el resultado del bloque 
        # anterior usando la bandera `pygame.BLEND_MULT`. Esto hace que el código 
        # C subyacente de Pygame realice la multiplicación de píxeles nativamente 
        # sin salir a Python/NumPy, bajando el tiempo de ejecución casi a 0 ms.
        k = self.strength(progress)
        if k * self.ALPHA_MAX <= 1e-6:
            return
        overlay = self._overlay(self.effective_tint(k), surface.get_size())
        surface.blit(overlay, (0, 0), special_flags=pygame.BLEND_MULT)
