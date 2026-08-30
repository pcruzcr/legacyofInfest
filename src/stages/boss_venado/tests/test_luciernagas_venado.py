"""Módulo: test_luciernagas_venado
Sistema: tests
Descripción: Unidad VII -- el histograma de luminancia (FilterTools.compute_histogram,
    filter_tools.py:38-49) dirige la cantidad de luciérnagas del corredor (más oscuro ->
    más luciérnagas), Tarea 12 del plan de peregrinación. Estas pruebas cubren solo la
    lógica PURA de luciernagas_venado.py (funciones de mapeo + el gestor con su cadencia
    de muestreo) -- el candado de wiring dentro de la escena real vive en
    test_boss_scene.py (Paso 6 del plan) y el de despacho real bajo App._draw()/
    composición por alfa de GPU vive en test_despacho_real_overlays.py (ver su docstring
    para el porqué de un candado aparte).

    DESVIACIÓN del borrador literal del plan (Paso 1): el borrador incluía un fixture
    autouse ``pygame.init()``/``pygame.quit()`` por prueba. Se retira aquí -- conftest.py
    (línea 15-16) ya llama ``pygame.init()`` + ``pygame.display.set_mode((320, 224))`` UNA
    vez a nivel de sesión, y ningún otro archivo de esta suite llama ``pygame.quit()``
    (verificado por grep). Confirmado empíricamente: con el fixture puesto,
    ``pygame.quit()`` tras cada prueba de este módulo tumbaba el display de sesión, y
    cualquier archivo de pruebas que corriera después alfabéticamente (p. ej.
    test_map_residencias.py, que carga el TMX real con pixelalpha=True vía pytmx, que
    exige pygame.display inicializado para poder llamar Surface.convert()) fallaba
    con ``pygame.error`` (superficie sin formato porque el display ya no existe)
    -- 5 pruebas rojas en un archivo hermano sin relación con esta tarea.
    Ninguna prueba de aquí necesita pygame.init()/quit() propios: solo crean
    pygame.Surface llanas, que ya funcionan con el pygame.init() de sesión."""
from __future__ import annotations

import pygame

from src.stages.boss_venado.luciernagas_venado import (
    FACTOR_HALO_MAXIMO,
    FACTOR_HALO_MINIMO,
    FRECUENCIA_DE_MUESTREO,
    TAMANO_MUESTREO_REDUCIDO,
    GestorDeLuciernagas,
    calcular_intensidad,
    factor_de_halo_objetivo,
    luciernagas_objetivo,
)


def _superficie(color: tuple[int, int, int]) -> pygame.Surface:
    s = pygame.Surface((64, 48))
    s.fill(color)
    return s


def test_calcular_intensidad_superficie_oscura_da_valor_bajo():
    intensidad = calcular_intensidad(_superficie((10, 10, 10)))
    assert 0.0 <= intensidad < 0.15


def test_calcular_intensidad_superficie_clara_da_valor_alto():
    intensidad = calcular_intensidad(_superficie((240, 240, 240)))
    assert 0.85 < intensidad <= 1.0


def test_luciernagas_objetivo_es_inversamente_proporcional_a_la_intensidad():
    oscuro = luciernagas_objetivo(0.05)
    claro = luciernagas_objetivo(0.95)
    assert oscuro > claro
    assert luciernagas_objetivo(0.0) == 14   # MAXIMO_LUCIERNAGAS
    assert luciernagas_objetivo(1.0) == 0    # MINIMO_LUCIERNAGAS


def test_gestor_dark_surface_produce_mas_luciernagas_que_clara():
    """DESVIACIÓN del borrador literal del plan (Paso 1): el borrador llamaba
    ``actualizar_desde_superficie`` UNA sola vez por gestor y esperaba una
    diferencia inmediata -- eso contradice la cadencia de
    FRECUENCIA_DE_MUESTREO que el propio Paso 3 del plan implementa (contador
    post-incremento + módulo, el MISMO patrón que ``cada_n_frames`` ya usa en
    ~15 sitios de boss_venado.py: la primera muestra real cae en el cuadro N,
    nunca en el cuadro 1 -- verificado corriendo el borrador literal, que hace
    fallar este mismo test con ``7 > 7`` porque ninguno de los dos gestores
    llega a muestrear). El propio Paso 6 del plan (más abajo, en
    test_boss_scene.py) ya usa el patrón correcto -- ``for _ in range(25):``,
    "supera FRECUENCIA_DE_MUESTREO" (el 25 quedó por debajo del valor final
    de 90 tras la revisión de costo de esta tarea -- ver luciernagas_venado.py
    -- así que ese Paso 6 usa ``range(FRECUENCIA_DE_MUESTREO)`` real, no 25
    fijo; ver test_boss_scene.py) -- así que este test se alinea con ESE
    precedente en vez de con el borrador inconsistente de este mismo Paso."""
    g_oscuro = GestorDeLuciernagas()
    g_claro = GestorDeLuciernagas()
    for _ in range(FRECUENCIA_DE_MUESTREO):   # garantiza al menos un muestreo real
        g_oscuro.actualizar_desde_superficie(_superficie((10, 10, 10)))
        g_claro.actualizar_desde_superficie(_superficie((240, 240, 240)))
    assert g_oscuro.cantidad_objetivo > g_claro.cantidad_objetivo


def test_gestor_no_remuestrea_fuera_de_la_cadencia():
    """Candado de determinismo/costo (revisión de calidad de esta tarea): dentro
    de la misma ventana de FRECUENCIA_DE_MUESTREO cuadros, cantidad_objetivo NO
    cambia sin importar cuanto cambie la superficie de entrada -- el costo real
    (numpy sobre 800x600 en la escena real, ver el docstring del módulo) solo se
    paga cada FRECUENCIA_DE_MUESTREO cuadros, nunca cuadro a cuadro."""
    g = GestorDeLuciernagas()
    oscuro = _superficie((10, 10, 10))
    claro = _superficie((240, 240, 240))
    # cuadro 1: no dispara muestreo (1 % FRECUENCIA_DE_MUESTREO != 0 -- ver
    # cada_n_frames en efectos_venado.py).
    g.actualizar_desde_superficie(oscuro)
    objetivo_tras_cuadro_1 = g.cantidad_objetivo
    # cuadros 2..(N-1): tampoco disparan.
    for _ in range(FRECUENCIA_DE_MUESTREO - 2):
        g.actualizar_desde_superficie(claro)
        assert g.cantidad_objetivo == objetivo_tras_cuadro_1
    # cuadro N: SI dispara (N % FRECUENCIA_DE_MUESTREO == 0).
    g.actualizar_desde_superficie(claro)
    # calcular_intensidad(claro) SIN reescalar == la lectura real del gestor: para
    # un color PLANO, pygame.transform.smoothscale es matemáticamente exacto (todo
    # píxel de origen es idéntico, cualquier promedio bilineal reproduce el mismo
    # valor) -- verificado empíricamente en la revisión de rendimiento de esta
    # tarea (diff máxima 0.0 exacta sobre 40 colores planos aleatorios, ver el
    # docstring de luciernagas_venado.py, "Muestreo reducido").
    assert g.cantidad_objetivo == luciernagas_objetivo(calcular_intensidad(claro))
    assert g.cantidad_objetivo != objetivo_tras_cuadro_1


def test_frecuencia_de_muestreo_es_30():
    """Canario del fix de rendimiento del coordinador (Tarea 12): con el
    muestreo reducido (smoothscale a TAMANO_MUESTREO_REDUCIDO antes de
    histogramar, ~2ms/llamada medido) la cadencia baja de 90 (1.5s, calibrada
    contra el costo de resolución completa, ~37ms/llamada) a 30 (0.5s) -- ver
    el docstring del módulo, "Muestreo reducido", para ambas mediciones. Este
    test fija el valor exacto para que un cambio futuro sea deliberado, no un
    despiste -- las demás pruebas de este archivo usan la constante
    simbólicamente y seguirían pasando con cualquier N, así que sin este
    candado un retroceso accidental a 90 (o cualquier otro valor) no se
    notaría en ningún otro lado."""
    assert FRECUENCIA_DE_MUESTREO == 30


def test_muestreo_reducido_preserva_oscuro_mas_luciernagas_en_superficie_grande():
    """Fix de rendimiento del coordinador: actualizar_desde_superficie hace
    ``pygame.transform.smoothscale(surface, TAMANO_MUESTREO_REDUCIDO)`` antes
    de histogramar. Las pruebas de arriba usan superficies de 64x48 --
    MENORES que TAMANO_MUESTREO_REDUCIDO=(200,150) en ambos ejes, así que
    smoothscale las ESCALA HACIA ARRIBA ahí, sin ejercitar el camino de
    reducción real (el que de verdad importa en la escena, donde la
    superficie de entrada es 800x600). Este test usa una superficie del
    tamaño REAL de pantalla para probar la reducción de verdad de punta a
    punta a través de GestorDeLuciernagas (no solo de calcular_intensidad
    aislada)."""
    g_oscuro = GestorDeLuciernagas()
    g_claro = GestorDeLuciernagas()
    oscura = pygame.Surface((800, 600))
    oscura.fill((10, 10, 10))
    clara = pygame.Surface((800, 600))
    clara.fill((240, 240, 240))
    for _ in range(FRECUENCIA_DE_MUESTREO):
        g_oscuro.actualizar_desde_superficie(oscura)
        g_claro.actualizar_desde_superficie(clara)
    assert g_oscuro.cantidad_objetivo > g_claro.cantidad_objetivo


def test_factor_de_halo_objetivo_extremos():
    """Fix académico del coordinador (Tarea 12, "refuerzo REAL del halo"):
    mismo mapeo inverso lineal que luciernagas_objetivo, pero continuo (sin
    round()) y en el rango [FACTOR_HALO_MINIMO, FACTOR_HALO_MAXIMO] ==
    [1.0, 1.35]. intensidad==1.0 (franja totalmente clara) debe dar
    EXACTAMENTE FACTOR_HALO_MINIMO -- CERO refuerzo, el comportamiento
    histórico previo a este fix."""
    assert factor_de_halo_objetivo(0.0) == FACTOR_HALO_MAXIMO
    assert factor_de_halo_objetivo(1.0) == FACTOR_HALO_MINIMO
    oscuro = factor_de_halo_objetivo(0.05)
    claro = factor_de_halo_objetivo(0.95)
    assert oscuro > claro


def test_gestor_factor_de_halo_sube_con_oscuridad_real():
    """El histograma DIRIGE de verdad el refuerzo del halo: una franja
    oscura real (no un intensidad inventada a mano) debe hacer que
    GestorDeLuciernagas.factor_de_halo suba por encima del piso
    FACTOR_HALO_MINIMO tras al menos un muestreo real."""
    g = GestorDeLuciernagas()
    oscura = pygame.Surface((800, 600))
    oscura.fill((5, 5, 8))
    for _ in range(FRECUENCIA_DE_MUESTREO):
        g.actualizar_desde_superficie(oscura)
    assert g.factor_de_halo > FACTOR_HALO_MINIMO


def test_gestor_factor_de_halo_con_blanco_puro_es_historico():
    """intensidad exactamente 1.0 (blanco puro, no un gris claro) debe dejar
    factor_de_halo en EXACTAMENTE FACTOR_HALO_MINIMO (1.0) -- el
    comportamiento histórico intacto, sin ningún refuerzo. Blanco puro
    (255,255,255), no un gris claro como (240,240,240): calcular_intensidad
    normaliza por 255, así que solo el blanco puro da intensidad == 1.0
    exacto (necesario para == exacto en el assert, no solo "cerca de")."""
    g = GestorDeLuciernagas()
    blanca = pygame.Surface((800, 600))
    blanca.fill((255, 255, 255))
    for _ in range(FRECUENCIA_DE_MUESTREO):
        g.actualizar_desde_superficie(blanca)
    assert g.factor_de_halo == FACTOR_HALO_MINIMO


def test_tamano_muestreo_reducido_es_menor_que_pantalla_completa():
    """Candado de sentido: TAMANO_MUESTREO_REDUCIDO debe ser estrictamente
    menor que 800x600 (settings.INTERNAL_WIDTH x INTERNAL_HEIGHT) en ambos
    ejes -- si no, el fix de rendimiento del coordinador no reduciría nada."""
    ancho, alto = TAMANO_MUESTREO_REDUCIDO
    assert ancho < 800
    assert alto < 600
