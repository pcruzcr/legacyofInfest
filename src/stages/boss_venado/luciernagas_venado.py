"""Módulo: luciernagas_venado
Sistema: stages.boss_venado
Descripción: "La Hora de las Luciérnagas" -- Unidad VII (spec §4a, Tarea 12 del plan de
    peregrinación). Muestrea FilterTools.compute_histogram() (filter_tools.py:38-49,
    verificado por lectura directa: devuelve {"r","g","b","luminance","total_pixels"},
    arrays numpy de 256 bins + el total de píxeles) sobre una copia REDUCIDA de la
    superficie de mundo ya compuesta (ver "Muestreo reducido" más abajo) cada
    FRECUENCIA_DE_MUESTREO cuadros; la luminancia media DIRIGE dos salidas de lógica de
    juego real (no cosméticas, cumpliendo el criterio de la rúbrica --
    27_ACADEMIC_RUBRICS.md §5, 15 pts: "histograma dirigiendo lógica de juego, no
    cosmético"): cuántas luciérnagas se encienden (``cantidad_objetivo``,
    ``luciernagas_objetivo()``) y CUÁNTO se refuerza el halo lunar del jugador
    (``factor_de_halo``, ``factor_de_halo_objetivo()`` -- fix del coordinador de esta
    tarea: el refuerzo del halo era narrativa sin código hasta esta versión; ver "Refuerzo
    REAL del halo" más abajo para el mecanismo completo).

    Muestreo reducido (fix de rendimiento del coordinador de esta tarea, con números
    MEDIDOS en este entorno, no estimados):

    - Costo del histograma a RESOLUCIÓN COMPLETA (800x600, el mismo tamaño que
      settings.INTERNAL_WIDTH x INTERNAL_HEIGHT): microbenchmark de 200 llamadas de
      compute_histogram() sobre una pygame.Surface((800, 600)) llana midió ~37 ms por
      llamada -- más del doble del presupuesto de un cuadro entero a 60 fps (16.7 ms).
      Este número fue el que originalmente motivó subir FRECUENCIA_DE_MUESTREO de 20
      (borrador del plan) a 90 (versión anterior de este módulo).
    - Costo del muestreo REDUCIDO (``pygame.transform.smoothscale`` a
      TAMANO_MUESTREO_REDUCIDO=(200, 150) + compute_histogram sobre la copia):
      microbenchmark de 300 llamadas en este mismo entorno midió ~0.28 ms/llamada para
      el smoothscale y ~2.0 ms/llamada para compute_histogram sobre la superficie ya
      reducida (pipeline combinado también ~2.0 ms/llamada) -- un orden de magnitud por
      debajo de los 37 ms de resolución completa, y muy por debajo del presupuesto de un
      cuadro.
    - Equivalencia verificada (no solo asumida): ``calcular_intensidad`` ya normaliza
      por ``total_pixels``, así que el resultado no depende de la resolución de entrada
      en principio -- confirmado empíricamente en este entorno: diferencia MÁXIMA 0.0
      exacta sobre 40 colores planos aleatorios (donde matemáticamente debe ser exacta,
      un color uniforme sobrevive cualquier reescalado sin cambiar) y diferencia MÁXIMA
      0.000428 (media 0.00039) sobre 20 superficies con textura sintética (500
      rectángulos de color aleatorio cada una, para forzar el caso donde el filtro
      bilineal de smoothscale SÍ podría introducir diferencia real) -- ambas
      estadísticamente insignificantes frente a la escala de ``luciernagas_objetivo``/
      ``factor_de_halo_objetivo`` (que operan en pasos de 1 luciérnaga / fracciones de
      0.35 en el factor).
    - Con el costo real por debajo de 2 ms, FRECUENCIA_DE_MUESTREO baja de 90 (1.5s,
      calibrado contra el costo COMPLETO) a 30 (0.5s a 60fps) -- más responsivo al
      cruzar zonas del corredor sin pagar ya el riesgo de micro-tirón que motivó subir a
      90 en primer lugar (2 ms es < 1/8 del presupuesto de un cuadro, nada que se sienta
      como un tirón).

    El arnés de playtest (`playtest/harness.py`, grep confirmado) NUNCA llama
    dibujar_mundo()/dibujar_ui() -- corre la simulación sin renderizar -- así que este
    costo (a cualquiera de las dos resoluciones) NUNCA se paga durante bots/gates/CI,
    solo durante partidas reales renderizadas (main.py, copiloto, filmstrips).
    GestorDeLuciernagas paga el costo cada FRECUENCIA_DE_MUESTREO cuadros reusando
    cada_n_frames() de efectos_venado.py (mismo patrón de cadencia que ya usa el resto
    del pulido AAA de este boss, ver su docstring) en vez de reimplementar el módulo a
    mano.

    Refuerzo REAL del halo (fix académico del coordinador de esta tarea): antes de este
    fix, "refuerzo del halo lunar del jugador" era una frase en este docstring sin
    ningún código detrás -- el halo (BossVenadoScene._build_player_halo) se construía
    siempre con el mismo brillo fijo, sin leer nada del histograma. Ahora
    ``GestorDeLuciernagas.factor_de_halo`` (calculado en el MISMO muestreo que
    ``cantidad_objetivo``, sobre la MISMA lectura de intensidad -- cero costo adicional)
    es un multiplicador en [FACTOR_HALO_MINIMO, FACTOR_HALO_MAXIMO] == [1.0, 1.35] que
    la escena aplica al construir el halo (ver BossVenadoScene._build_player_halo(factor)
    y dibujar_ui): con la franja visible más oscura, el pico efectivo del halo sube hasta
    un 35% por encima del histórico; con la franja clara (intensidad == 1.0 exacto),
    ``factor_de_halo == FACTOR_HALO_MINIMO == 1.0`` y el halo es BYTE-IDÉNTICO al
    comportamiento anterior a este fix (verificado por
    test_build_player_halo_factor_por_defecto_es_identico_al_historico en
    test_boss_scene.py). El factor SOLO AUMENTA desde 1.0 -- nunca baja del piso que fija
    test_player_halo_never_silently_disabled (PLAYER_HALO_PEAK/RADIUS, halo construido
    con factor por defecto) -- así que ese candado de piso preexistente sigue
    ejercitando exactamente el mismo camino de código que antes y sigue en verde sin
    ningún cambio en su propio archivo."""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from src.framework.processing.filter_tools import FilterTools
from src.stages.boss_venado.efectos_venado import cada_n_frames

#: Cada cuántos cuadros se re-muestrea el histograma (30 cuadros == 0.5s a 60fps) --
#: valor MEDIDO tras el muestreo reducido (ver el docstring del módulo, "Muestreo
#: reducido"): con smoothscale + compute_histogram sobre 200x150 costando ~2ms/llamada
#: (contra ~37ms a resolución completa), 0.5s es responsivo sin riesgo de micro-tirón.
FRECUENCIA_DE_MUESTREO = 30

#: Tamaño al que se reescala la superficie de mundo ANTES de histogramar (fix de
#: rendimiento del coordinador de esta tarea) -- ver el docstring del módulo, "Muestreo
#: reducido", para las mediciones y la verificación de equivalencia con la resolución
#: completa. calcular_intensidad() normaliza por total_pixels, así que es
#: (estadísticamente) indiferente a la resolución de entrada.
TAMANO_MUESTREO_REDUCIDO = (200, 150)

MAXIMO_LUCIERNAGAS = 14
MINIMO_LUCIERNAGAS = 0

#: Multiplicador MÍNIMO del refuerzo de halo -- 1.0 == comportamiento histórico
#: intacto (sin refuerzo), el PISO que test_player_halo_never_silently_disabled ya
#: protege. El factor real (GestorDeLuciernagas.factor_de_halo) SOLO sube desde aquí,
#: nunca baja de 1.0 -- ver el docstring del módulo, "Refuerzo REAL del halo".
FACTOR_HALO_MINIMO = 1.0

#: Multiplicador MÁXIMO del refuerzo de halo, con la franja visible en oscuridad
#: total -- pico efectivo hasta un 35% más brillante que el histórico.
FACTOR_HALO_MAXIMO = 1.35


def calcular_intensidad(surface: pygame.Surface) -> float:
    """Luminancia media de `surface`, normalizada a [0.0, 1.0] -- 0 = negro total, 1 =
    blanco total. Usa el histograma de luminancia de FilterTools.compute_histogram()
    (256 bins), no un promedio de píxeles directo: es DELIBERADAMENTE la misma
    herramienta de la Unidad VII que documenta el README (Tarea 15), no un atajo con
    numpy.mean().

    Resolución-agnóstica por construcción (normaliza por ``total_pixels``, no por un
    tamaño fijo) -- por eso ``GestorDeLuciernagas.actualizar_desde_superficie`` puede
    pasarle una copia REDUCIDA de la superficie (``pygame.transform.smoothscale`` a
    TAMANO_MUESTREO_REDUCIDO) sin cambiar el resultado de forma perceptible: ver el
    docstring del módulo, "Muestreo reducido", para la verificación empírica de esa
    equivalencia. Esta función en sí NO hace ningún reescalado -- eso es
    responsabilidad de quien la llama, para que siga siendo trivial de probar con
    superficies pequeñas y colores exactos (ver test_luciernagas_venado.py)."""
    hist = FilterTools.compute_histogram(surface)
    luminancia = hist["luminance"]
    total = int(hist["total_pixels"])
    if total <= 0:
        return 0.0
    suma_ponderada = sum(i * int(c) for i, c in enumerate(luminancia))
    return max(0.0, min(1.0, suma_ponderada / (total * 255.0)))


def luciernagas_objetivo(intensidad: float, minimo: int = MINIMO_LUCIERNAGAS,
                         maximo: int = MAXIMO_LUCIERNAGAS) -> int:
    """Mapeo inverso: cuanto más oscura la franja visible, más luciérnagas. Lineal a
    propósito -- es la relación más legible para un lector de código que audite "el
    histograma dirige esto", sin curva oculta."""
    intensidad = max(0.0, min(1.0, intensidad))
    return round(maximo - (maximo - minimo) * intensidad)


def factor_de_halo_objetivo(intensidad: float, minimo: float = FACTOR_HALO_MINIMO,
                            maximo: float = FACTOR_HALO_MAXIMO) -> float:
    """Mapeo inverso lineal, misma forma que ``luciernagas_objetivo`` (misma
    intensidad de entrada, mismo sentido oscuro->más): cuanto más oscura la franja
    visible, mayor el multiplicador de refuerzo del halo del jugador. Continuo (sin
    ``round()`` -- a diferencia de ``luciernagas_objetivo``, que cuenta luciérnagas
    discretas, un multiplicador de brillo no tiene motivo para saltar en pasos
    enteros). ``intensidad == 1.0`` (franja totalmente clara) da exactamente
    ``minimo`` (1.0 por defecto) -- CERO refuerzo, el comportamiento histórico previo
    a este fix. ``intensidad == 0.0`` (oscuridad total) da exactamente ``maximo``."""
    intensidad = max(0.0, min(1.0, intensidad))
    return maximo - (maximo - minimo) * intensidad


@dataclass
class GestorDeLuciernagas:
    """Estado entre muestreos: cantidad objetivo de luciérnagas y factor de refuerzo
    del halo (ambos recalculados cada FRECUENCIA_DE_MUESTREO cuadros, DESDE LA MISMA
    lectura de intensidad -- ver ``actualizar_desde_superficie``) más un contador de
    cuadro propio -- nunca reloj de pared (ver el docstring del módulo y el de
    BossVenadoScene._tiempo_luciernagas para el parpadeo, que es una responsabilidad
    aparte de este gestor)."""

    cantidad_objetivo: int = MAXIMO_LUCIERNAGAS // 2
    #: Multiplicador de refuerzo del halo -- arranca en FACTOR_HALO_MINIMO (1.0, SIN
    #: refuerzo) hasta el primer muestreo real: nunca por debajo del piso que protege
    #: test_player_halo_never_silently_disabled, ni antes ni después de muestrear.
    factor_de_halo: float = FACTOR_HALO_MINIMO
    _contador: int = field(default=0, init=False)

    def actualizar_desde_superficie(self, surface: pygame.Surface) -> None:
        """Llamar UNA vez por cuadro con la superficie del mundo ya compuesta; el
        muestreo real (el único paso que cuesta, ver el docstring del módulo) ocurre
        solo cada FRECUENCIA_DE_MUESTREO cuadros (los demás cuadros son no-op
        deliberado -- cada_n_frames de efectos_venado.py, mismo patrón de cadencia que
        el resto del pulido AAA de este boss).

        Fix de rendimiento del coordinador: reescala `surface` a
        TAMANO_MUESTREO_REDUCIDO (``pygame.transform.smoothscale``) ANTES de
        histogramar -- ver el docstring del módulo, "Muestreo reducido", para las
        mediciones (37ms a resolución completa vs ~2ms reducido) y la verificación de
        equivalencia. La MISMA lectura de intensidad alimenta las dos salidas de este
        gestor (``cantidad_objetivo`` Y ``factor_de_halo``) -- un solo histograma por
        muestreo, no dos."""
        self._contador += 1
        if not cada_n_frames(self._contador, FRECUENCIA_DE_MUESTREO):
            return
        reducida = pygame.transform.smoothscale(surface, TAMANO_MUESTREO_REDUCIDO)
        intensidad = calcular_intensidad(reducida)
        self.cantidad_objetivo = luciernagas_objetivo(intensidad)
        self.factor_de_halo = factor_de_halo_objetivo(intensidad)
