"""Módulo: test_gaussian_blur_bgfar
Sistema: tests
Descripción: Unidad VII -- profundidad de campo barata sobre BG_Far vía
    FilterTools.gaussian_blur, aplicada UNA VEZ al generar el tileset (coste
    cero en runtime)."""
from __future__ import annotations

import numpy as np
import pygame

from src.stages.boss_venado.tools.gen_tileset_bgfar_blur import (
    NOMBRES_BG_FAR,
    generar_tileset_borroso,
)

# NOTA: sin pygame.init() propio -- conftest.py de este directorio ya lo hace
# (más pygame.display.set_mode) a nivel de sesión, antes de recolectar
# cualquier módulo de prueba; repetirlo aquí solo forzaba un import fuera de
# orden (E402) sin cambiar el comportamiento.


def test_nombres_bg_far_no_esta_vacio_y_coincide_con_compose_sky():
    """compose_sky() es la ÚNICA función que escribe en bg_far -- ver
    gen_level_residencias.py:255. Este test fija que la detección automática
    encuentra al menos los nombres de banda conocidos."""
    assert "sky_top" in NOMBRES_BG_FAR
    assert "sky_horizon" in NOMBRES_BG_FAR
    assert "cloud_l" in NOMBRES_BG_FAR
    assert len(NOMBRES_BG_FAR) >= 15


def test_nombres_bg_far_coincide_con_gen_level_residencias():
    """Blindaje mecánico (sugerencia del coordinador tras la revisión de la
    Tarea 13) de la garantía que hoy solo sostiene la CONSTRUCCIÓN: el
    docstring de ``gen_level_residencias._nombres_bg_far()`` explica que ese
    conjunto y ``NOMBRES_BG_FAR`` (este módulo) son iguales porque ambos
    invocan la MISMA ``compose_sky``/``_blank`` -- pero eso no estaba
    verificado en tiempo de ejecución en ningún test. Si algún día los dos
    conjuntos discreparan (p. ej. alguien reintrodujera una copia de
    ``compose_sky`` en vez de reusar la real), el ``mapping_blur`` que
    ``build_tmx()`` calcula apuntaría a un tile equivocado del atlas
    borroso -- exactamente el escenario que ese docstring advierte, y que
    hasta ahora ningún test fallaba ante un `KeyError` silencioso.

    Importar ``gen_level_residencias`` aquí NO reintroduce el ciclo que
    forzó la Tarea 13 a evitar el import en el otro sentido: ese ciclo era
    ``gen_level_residencias -> gen_tileset_bgfar_blur -> gen_level_residencias``
    (un módulo de herramienta importándose a sí mismo indirectamente). Un
    módulo de TEST que importa a los dos no participa en ese grafo -- ni
    ``gen_tileset_bgfar_blur`` ni ``gen_level_residencias`` importan nada
    de ningún archivo bajo ``tests/``, así que no hay ciclo posible.
    Verificado además de forma independiente (no solo razonado): importando
    ambos módulos en un intérprete nuevo, en este orden, sin error.

    Comparación por IGUALDAD DE CONJUNTOS (``==`` entre dos ``frozenset``),
    no convertidos a tupla/lista: dos frozensets con el mismo contenido son
    iguales sin importar el orden de iteración interno de cada uno, que no
    está garantizado a coincidir entre dos construcciones independientes
    aunque el contenido sea idéntico -- convertir a tupla antes de comparar
    haría el test dependiente de ese orden y potencialmente inestable.
    """
    from src.stages.boss_venado.tools import gen_level_residencias
    assert NOMBRES_BG_FAR == gen_level_residencias._nombres_bg_far()


def test_generar_tileset_borroso_produce_un_png_distinto_del_original(tmp_path):
    from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX
    ruta_original = tmp_path / "orig.png"
    _fabricar_tileset_de_prueba(ruta_original)
    destino = tmp_path / "blur.png"
    mapping = generar_tileset_borroso(ruta_original, destino)
    assert destino.exists()
    assert set(mapping) == NOMBRES_BG_FAR
    original = pygame.image.load(str(ruta_original))
    borroso = pygame.image.load(str(destino))
    # el tile borroso NO debe ser pixel-idéntico al original -- si lo fuera,
    # el blur no se aplicó de verdad.
    nombre = next(iter(NOMBRES_BG_FAR))
    from src.stages.boss_venado.tools.gen_level_residencias import COLUMNS, TILE
    idx = NAME_TO_INDEX[nombre]
    col, row = idx % COLUMNS, idx // COLUMNS
    original_tile = original.subsurface((col * TILE, row * TILE, TILE, TILE))
    idx_b = mapping[nombre]
    col_b, row_b = idx_b % COLUMNS, idx_b // COLUMNS
    borroso_tile = borroso.subsurface((col_b * TILE, row_b * TILE, TILE, TILE))
    # AU-20260826-03: tostring esta deprecado desde pygame 2.3.0; tobytes es el reemplazo directo
    assert pygame.image.tobytes(original_tile, "RGB") != pygame.image.tobytes(borroso_tile, "RGB")


# ──────────────────────────────────────────────
# TAREA (2026-08-27): "bruma" -- perspectiva atmosferica sobre el tileset
# BG_Far ya borroso. Ademas del gaussian_blur (TAREA 13, arriba), cada tile
# pasa por FilterTools.adjust_contrast con un factor < 1.0: los planos
# lejanos, ademas de perder nitidez, pierden CONTRASTE LOCAL -- asi es como
# el ojo humano lee "esto esta lejos" (perspectiva atmosferica real). Este
# bloque es la mitad ROJA del TDD: generar_tileset_bruma/CONTRASTE_BRUMA/
# TILESET_BRUMA todavia NO EXISTEN en gen_tileset_bgfar_blur.py -- cada test
# los importa DENTRO de su propio cuerpo (no arriba, a nivel de modulo) para
# que la ausencia de esos nombres falle ESE test en particular con un
# ImportError legible, sin tumbar la recoleccion del resto del archivo (los
# tres tests de blur de arriba deben seguir corriendo intactos).
# ──────────────────────────────────────────────

def test_contraste_bruma_es_reduccion():
    """Candado del SENTIDO del parametro, antes de que exista quien lo
    consuma: la bruma es perspectiva atmosferica -- los planos lejanos
    PIERDEN contraste, nunca lo ganan. Si algun dia CONTRASTE_BRUMA se
    pusiera en 1.0 (sin efecto), <= 0.0 (degenerado/invertido segun la
    formula de FilterTools.adjust_contrast) o >= 1.0 (aumento, el sentido
    opuesto al diseño aprobado), este test lo atrapa aqui -- no jugando."""
    from src.stages.boss_venado.tools.gen_tileset_bgfar_blur import CONTRASTE_BRUMA
    assert 0.0 < CONTRASTE_BRUMA < 1.0


def test_generar_tileset_bruma_reduce_el_contraste(tmp_path):
    """Evidencia de MUTACION (regla de oro, manual QA Sec 3.5): compara el
    atlas SOLO-BLUR (generar_tileset_borroso) contra el atlas BRUMA
    (generar_tileset_bruma = blur + adjust_contrast) sobre el MISMO
    tileset sintetico de origen. Si algun dia la pasada de
    ``FilterTools.adjust_contrast`` se eliminara de ``generar_tileset_bruma``
    (p. ej. alguien la comenta "para probar algo" y se le olvida
    descomentarla), ``generar_tileset_bruma`` quedaria bit a bit igual a
    ``generar_tileset_borroso`` sobre el mismo tile y este test fallaria de
    inmediato -- no puede ponerse en verde por accidente ni quedar verde
    con el contraste retirado.

    La metrica es la desviacion estandar de la LUMINANCIA (formula
    perceptual estandar, la misma que usa
    ``FilterTools.compute_histogram``): un contraste local mas bajo
    comprime los valores hacia la media y por lo tanto reduce esa
    desviacion. Se recorre el tileset sintetico buscando el primer tile con
    varianza real tras el blur (la mayoria deberia calificar, dado el ruido
    de ``_fabricar_tileset_de_prueba``, pero un tile que el blur aplano del
    todo -- std 0 -- no sirve de evidencia: no hay contraste que reducir)."""
    from src.stages.boss_venado.tools.gen_tileset_bgfar_blur import generar_tileset_bruma
    from src.stages.boss_venado.tools.gen_level_residencias import COLUMNS, TILE

    ruta_original = tmp_path / "orig.png"
    _fabricar_tileset_de_prueba(ruta_original)
    destino_blur = tmp_path / "blur.png"
    destino_bruma = tmp_path / "bruma.png"
    mapping_blur = generar_tileset_borroso(ruta_original, destino_blur)
    mapping_bruma = generar_tileset_bruma(ruta_original, destino_bruma)
    blur = pygame.image.load(str(destino_blur))
    bruma = pygame.image.load(str(destino_bruma))

    def _tile(atlas, mapping, nombre):
        idx = mapping[nombre]
        col, row = idx % COLUMNS, idx // COLUMNS
        return atlas.subsurface((col * TILE, row * TILE, TILE, TILE))

    for nombre in sorted(set(mapping_blur) & set(mapping_bruma)):
        tile_blur = _tile(blur, mapping_blur, nombre)
        std_blur = _desviacion_estandar_luminancia(tile_blur)
        if std_blur <= 0.0:
            continue  # tile plano tras el blur -- sin contraste que reducir, sigue buscando
        tile_bruma = _tile(bruma, mapping_bruma, nombre)
        std_bruma = _desviacion_estandar_luminancia(tile_bruma)
        assert std_bruma < std_blur
        assert pygame.image.tobytes(tile_blur, "RGB") != pygame.image.tobytes(tile_bruma, "RGB")
        break
    else:
        assert False, "ningun tile del tileset sintetico conservo varianza tras el blur"


def test_mapping_bruma_coincide_con_nombres_bg_far(tmp_path):
    """Mismo contrato que ``generar_tileset_borroso``: el mapping devuelto
    cubre EXACTAMENTE ``NOMBRES_BG_FAR`` (ni un tile de mas ni de menos).
    De paso, candado de contrato de firma: el destino por defecto de
    ``generar_tileset_bruma`` es la constante publica ``TILESET_BRUMA``
    (mismo patron que ``generar_tileset_borroso``/``TILESET_BLUR``) -- para
    que nadie olvide re-exportar la ruta real del atlas."""
    import inspect
    from src.stages.boss_venado.tools.gen_tileset_bgfar_blur import (
        TILESET_BRUMA,
        generar_tileset_bruma,
    )
    firma = inspect.signature(generar_tileset_bruma)
    assert firma.parameters["destino"].default == TILESET_BRUMA

    ruta_original = tmp_path / "orig.png"
    _fabricar_tileset_de_prueba(ruta_original)
    destino = tmp_path / "bruma.png"
    mapping = generar_tileset_bruma(ruta_original, destino)
    assert set(mapping) == NOMBRES_BG_FAR


def test_bruma_no_toca_el_png_blur_viejo(tmp_path):
    """CLAUDE.md, ZONAS EDITABLES punto 3: 'solo CREAR archivos nuevos,
    jamas sobrescribir existentes'. Este candado prueba que generar el
    atlas bruma sobre el sintetico no toca EN ABSOLUTO el archivo del atlas
    blur viejo -- ni sus bytes ni su mtime -- cuando a ambas funciones se
    les pasan destinos explicitos distintos (el patron real que usara
    ``gen_level_residencias.py``: dos rutas de salida separadas, nunca la
    misma)."""
    from src.stages.boss_venado.tools.gen_tileset_bgfar_blur import generar_tileset_bruma

    ruta_original = tmp_path / "orig.png"
    _fabricar_tileset_de_prueba(ruta_original)
    destino_blur = tmp_path / "blur.png"
    generar_tileset_borroso(ruta_original, destino_blur)
    contenido_blur_antes = destino_blur.read_bytes()
    mtime_antes = destino_blur.stat().st_mtime_ns

    destino_bruma = tmp_path / "bruma.png"
    generar_tileset_bruma(ruta_original, destino_bruma)

    assert destino_blur.read_bytes() == contenido_blur_antes
    assert destino_blur.stat().st_mtime_ns == mtime_antes
    assert destino_bruma.exists()
    assert destino_bruma.read_bytes() != contenido_blur_antes


def _desviacion_estandar_luminancia(tile: pygame.Surface) -> float:
    """Desviacion estandar de la luminancia (formula perceptual estandar,
    la misma que usa ``FilterTools.compute_histogram``) de un tile --
    metrica de CONTRASTE LOCAL: bajar el contraste comprime los valores
    hacia la media y por lo tanto reduce esta desviacion."""
    arr = pygame.surfarray.array3d(tile).astype(np.float64)
    luminancia = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    return float(luminancia.std())


def _fabricar_tileset_de_prueba(ruta) -> None:
    """Tileset sintético mínimo, con ruido (no color plano) para que el
    blur produzca una diferencia medible -- el atlas REAL se usa en el
    Paso 3, esto solo prueba el mecanismo de blureo+empaquetado."""
    from src.stages.boss_venado.tools.gen_level_residencias import COLUMNS, TILE
    from src.stages.boss_venado.tools.gen_tileset_residencias import NAME_TO_INDEX
    filas = (max(NAME_TO_INDEX.values()) + COLUMNS) // COLUMNS
    surf = pygame.Surface((COLUMNS * TILE, filas * TILE))
    surf.fill((0, 0, 0))
    import random
    rng = random.Random(1)
    for _name, idx in NAME_TO_INDEX.items():
        col, row = idx % COLUMNS, idx // COLUMNS
        for _ in range(40):
            x = col * TILE + rng.randrange(TILE)
            y = row * TILE + rng.randrange(TILE)
            surf.set_at((x, y), (rng.randrange(256), rng.randrange(256), rng.randrange(256)))
    pygame.image.save(surf, str(ruta))
