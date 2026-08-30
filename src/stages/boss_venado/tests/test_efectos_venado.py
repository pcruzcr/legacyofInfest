"""Tests del módulo efectos_venado: puerto EfectosDelEscenario + implementaciones
de prueba (EfectosNulos/EfectosRegistrados) + configs BurstConfig propias del boss +
utilidad de cadencia cada_n_frames (pulido AAA, spec 2026-08-21 §3.1)."""
import itertools

import pygame
import pytest

from src.framework.vfx.particle_system import BurstConfig
from src.stages.boss_venado import efectos_venado as ev


def test_efectos_nulos_no_hace_nada_y_no_lanza():
    """EfectosNulos es el valor por defecto del boss (tests sin escena, grader,
    arnés headless, entity_factory): las cuatro operaciones del puerto deben
    poder llamarse con argumentos cualquiera sin lanzar y sin devolver nada
    observable."""
    nulos = ev.EfectosNulos()
    config = BurstConfig(count=1, speed=1.0, lifetime=0.1, size=(1, 1), color=(1, 2, 3))
    assert nulos.particulas(0.0, 0.0, config) is None
    assert nulos.particulas_dirigidas(0.0, 0.0, -90.0, config) is None
    assert nulos.sacudir(1.0, 0.1, (0.0, 1.0)) is None
    assert nulos.sacudir(1.0, 0.1, None) is None
    assert nulos.estela(0.0, 0.0, (4, 4), (1, 2, 3, 4)) is None


def test_efectos_registrados_registra_las_cuatro_llamadas():
    """EfectosRegistrados (solo tests) guarda cada llamada en su lista propia,
    con los argumentos EXACTOS recibidos -- así un test puede verificar QUÉ se
    pidió sin arrancar el motor real."""
    reg = ev.EfectosRegistrados()
    config = BurstConfig(count=2, speed=3.0, lifetime=0.2, size=(1, 2), color=(9, 9, 9))

    reg.particulas(10.0, 20.0, config)
    assert reg.particulas_emitidas == [(10.0, 20.0, config)]

    reg.particulas_dirigidas(11.0, 21.0, -90.0, config)
    assert reg.particulas_dirigidas_emitidas == [(11.0, 21.0, -90.0, config)]

    reg.sacudir(4.0, 0.2, (1.0, 0.0))
    assert reg.sacudidas == [(4.0, 0.2, (1.0, 0.0))]

    reg.estela(12.0, 22.0, (8, 8), (1, 2, 3, 4))
    assert reg.estelas == [(12.0, 22.0, (8, 8), (1, 2, 3, 4))]

    # cada lista es independiente -- una segunda llamada se ACUMULA, no reemplaza.
    reg.particulas(30.0, 40.0, config)
    assert len(reg.particulas_emitidas) == 2


def test_cada_n_frames_dispara_en_multiplos_exactos():
    assert ev.cada_n_frames(0, 4) is True     # frame 0 cuenta como múltiplo de 4
    assert ev.cada_n_frames(4, 4) is True
    assert ev.cada_n_frames(8, 4) is True
    assert ev.cada_n_frames(1, 4) is False
    assert ev.cada_n_frames(3, 4) is False
    assert ev.cada_n_frames(5, 4) is False


def test_cada_n_frames_n_cero_o_negativo_nunca_dispara():
    assert ev.cada_n_frames(0, 0) is False
    assert ev.cada_n_frames(4, 0) is False
    assert ev.cada_n_frames(0, -1) is False


def test_polvo_aterrizaje_valores_del_spec():
    """Valores fijados por el spec 2026-08-21 §3.1 -- candado de regresión
    numérica, para que nadie los "ajuste" sin darse cuenta al tocar otra
    config vecina."""
    c = ev.POLVO_ATERRIZAJE
    assert (c.count, c.speed, c.lifetime) == (8, 90.0, 0.4)
    assert (c.size_min, c.size_max) == (2, 4)
    assert c.color == (180, 150, 110)
    assert (c.spread, c.gravity, c.friction) == (160.0, 300.0, 0.85)


def test_tierra_oleada_valores_del_spec():
    c = ev.TIERRA_OLEADA
    assert (c.count, c.speed, c.lifetime) == (3, 70.0, 0.35)
    assert (c.size_min, c.size_max) == (2, 3)
    assert c.color == (120, 95, 70)
    assert (c.spread, c.gravity, c.friction) == (140.0, 300.0, 0.9)


def _oleada_de_prueba(x: float = 2872.0, direccion: int = 1) -> "ev.OleadaDeLianas":
    return ev.OleadaDeLianas(x, direccion, y_suelo=560.0, x_min=2480.0, x_max=3264.0)


def test_oleada_avanza_a_velocidad_constante_segun_direccion():
    """OLEADA_VEL=380 px/s -- ida (direccion=1) suma, vuelta (direccion=-1) resta.

    Task 9 (revisión final 2026-08-21): dt=0.1 (antes 1.0) -- con el blindaje
    de pared del Step 9.3, un dt de 1.0s completo desde el centro (2872.0)
    YA CRUZA la pared derecha (tope real en x=3244.0, a solo 372px) en este
    único salto, así que ese dt disparaba la muerte en pared y recolocaba
    `x` tangente a la pared en vez de la suma cruda que este test quiere
    verificar -- 0.1s (38px de desplazamiento) queda cómodamente lejos de
    ambas paredes y sigue probando exactamente la misma fórmula de signo."""
    ida = _oleada_de_prueba(direccion=1)
    ida.update(0.1)
    assert ida.x == pytest.approx(2872.0 + ev.OLEADA_VEL * 0.1)

    vuelta = _oleada_de_prueba(direccion=-1)
    vuelta.update(0.1)
    assert vuelta.x == pytest.approx(2872.0 - ev.OLEADA_VEL * 0.1)


def test_oleada_rect_a_ras_de_suelo_ancho_40_alto_24():
    o = _oleada_de_prueba(x=2872.0)
    r = o.rect
    assert (r.width, r.height) == (ev.OLEADA_ANCHO, ev.OLEADA_ALTO) == (40, 24)
    assert r.bottom == 560          # a ras del suelo (y_suelo)
    assert r.centerx == 2872        # centrado en x


def test_oleada_muere_al_salir_por_la_derecha():
    """Task 9 (revisión final 2026-08-21): blindaje de pared -- la oleada
    muere en el PRIMER fotograma en que su borde delantero TOCA la pared
    (``rect.right >= x_max``), no cuando termina de salir por completo (el
    bug viejo dejaba hasta 40px de la cresta sobresaliendo de la arena en su
    último fotograma vivo). Se parte del CENTRO (no ya pegada a la pared)
    para recorrer varios fotogramas y verificar el invariante en TODOS,
    no solo en el de la muerte."""
    o = ev.OleadaDeLianas(2872.0, 1, y_suelo=560.0, x_min=2480.0, x_max=3264.0)
    rects_vivos = []
    for _ in range(120):            # 2s: de sobra a 380px/s desde el centro (~392px de recorrido)
        if not o.viva:
            break
        o.update(1.0 / 60.0)
        if o.viva:
            rects_vivos.append(o.rect)
    assert o.viva is False
    assert o.murio_en_pared is True
    assert o.consumida is False
    assert all(r.right <= o.x_max for r in rects_vivos), (
        "la oleada sobresalió por la pared derecha en algún fotograma VIVO")
    assert o.rect.right == int(o.x_max), (
        "el fotograma de muerte no quedó tangente a la pared derecha")


def test_oleada_muere_al_salir_por_la_izquierda():
    """Espejo izquierdo del test anterior -- ver su docstring."""
    o = ev.OleadaDeLianas(2872.0, -1, y_suelo=560.0, x_min=2480.0, x_max=3264.0)
    rects_vivos = []
    for _ in range(120):
        if not o.viva:
            break
        o.update(1.0 / 60.0)
        if o.viva:
            rects_vivos.append(o.rect)
    assert o.viva is False
    assert o.murio_en_pared is True
    assert all(r.left >= o.x_min for r in rects_vivos), (
        "la oleada sobresalió por la pared izquierda en algún fotograma VIVO")
    assert o.rect.left == int(o.x_min), (
        "el fotograma de muerte no quedó tangente a la pared izquierda")


def test_oleada_golpeada_consume_y_no_marca_murio_en_pared():
    o = _oleada_de_prueba()
    o.golpeada()
    assert o.viva is False
    assert o.consumida is True
    assert o.murio_en_pared is False   # murió por golpe, no por pared -- distinción que el boss usa para las ráfagas de tierra


def test_oleada_dibujar_mundo_pinta_algo():
    o = _oleada_de_prueba(x=100.0)
    # Ratificado por el coordinador 2026-08-21: el (0,0) literal del plan
    # dejaba la cresta fuera del lienzo. Con y_suelo=560.0 fijo del helper
    # _oleada_de_prueba y un lienzo de 200x200, la cresta (rect.top=536,
    # rect.bottom=560) cae fuera del lienzo con offset=(0,0) -- ningún test
    # de pintado podría pasar nunca, con NINGUNA implementación correcta de
    # dibujar_mundo. offset.y=460.0 desplaza el y_suelo=560 (mundo) a la fila
    # 100 del lienzo, visible, sin tocar OleadaDeLianas ni el contrato de los
    # otros 5 tests de este Step (mismo criterio que usan los tests de la
    # escena real en Task 5: offset = y_suelo - punto_en_pantalla).
    offset = pygame.Vector2(0.0, 460.0)
    limpia = pygame.Surface((200, 200))
    limpia.fill((10, 10, 10))
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    o.dibujar_mundo(surface, offset, t=0.0)
    assert pygame.image.tobytes(surface, "RGB") != pygame.image.tobytes(limpia, "RGB"), (
        "dibujar_mundo no pintó ningún píxel distinguible")


def test_oleada_dibujar_overlay_pinta_el_color_recibido():
    o = _oleada_de_prueba(x=100.0)
    # Ratificado por el coordinador 2026-08-21: el (0,0) literal del plan
    # dejaba la cresta fuera del lienzo (misma razón geométrica que el test
    # anterior -- ver su comentario).
    offset = pygame.Vector2(0.0, 460.0)
    surface = pygame.Surface((200, 200))
    surface.fill((10, 10, 10))
    color = (230, 90, 60)
    o.dibujar_overlay(surface, offset, color)

    import numpy as np
    arr = pygame.surfarray.array3d(surface)
    objetivo = np.array(color, dtype=arr.dtype)
    assert bool(np.all(arr == objetivo, axis=-1).any()), (
        f"dibujar_overlay no pintó ningún píxel {color!r} exacto")


def test_oleada_dibujar_overlay_recorta_la_grieta_al_rango_de_la_arena():
    """B-036 (revisor #2, addenda Task 1 punto 1): la grieta de 32px por
    delante de la cresta se proyectaba en línea recta desde el borde
    delantero sin comprobar los límites de la arena -- con la oleada cerca
    de una pared, hasta 32px de la grieta caían fuera de [x_min, x_max]
    (cosmético, pero visible). Colocamos la oleada a solo 10px de la pared
    derecha (todavía viva) para que, SIN el recorte, la grieta se
    proyectara 22px más allá de x_max."""
    x_min, x_max = 2480.0, 3264.0
    o = ev.OleadaDeLianas(0.0, 1, y_suelo=560.0, x_min=x_min, x_max=x_max)
    o.x = x_max - 10.0 - ev.OLEADA_ANCHO / 2.0   # rect.right queda a 10px de x_max
    assert o.rect.right == pytest.approx(x_max - 10.0)

    offset = pygame.Vector2(2400.0, 460.0)   # mapea [x_min, x_max] dentro del lienzo
    surface = pygame.Surface((900, 200))
    surface.fill((10, 10, 10))
    color = (230, 90, 60)
    o.dibujar_overlay(surface, offset, color)

    import numpy as np
    arr = pygame.surfarray.array3d(surface)
    objetivo = np.array(color, dtype=arr.dtype)
    pintado = np.all(arr == objetivo, axis=-1)
    limite_derecho_pantalla = int(x_max - offset.x)
    assert pintado[:limite_derecho_pantalla + 1, :].any(), (
        "dibujar_overlay no pintó ninguna grieta dentro del rango esperado")
    assert not pintado[limite_derecho_pantalla + 1:, :].any(), (
        "la grieta se pintó más allá de x_max -- debe recortarse a "
        "[x_min, x_max] (B-036)")


# ──────────────────────────────────────────────
# Pulido AAA fase 2 (diseño 2026-08-21) — configs de partículas
# ──────────────────────────────────────────────

def test_configs_de_particulas_del_pulido_aaa_fase2():
    """Valores exactos de las 9 BurstConfig nuevas (§2.2-2.4 del diseño) —
    un solo test tabular en vez de 9 duplicados, porque todas comprueban lo
    mismo: que la constante llegó tal cual la fijó el diseño."""
    from src.stages.boss_venado import efectos_venado as ev

    tabla = {
        "POLVO_PISOTON": (18, 140.0, 0.45, (2, 5), (180, 150, 110), 160.0, 320.0, 0.85),
        "HOJAS": (6, 30.0, 1.2, (2, 3), (110, 160, 90), 120.0, 60.0, 0.95),
        "POLVO_ASENTANDOSE": (4, 25.0, 0.5, (1, 3), (170, 145, 110), 360.0, 40.0, 0.9),
        "MOTAS": (2, 20.0, 0.6, (1, 2), (200, 230, 160), 60.0, -40.0, 0.95),
        "POLEN": (1, 10.0, 0.35, (1, 2), (200, 230, 160), 360.0, 0.0, 0.9),
        "NUBE_ESPORA": (6, 40.0, 0.3, (2, 3), (190, 220, 150), 360.0, 0.0, 0.85),
        "POLVO_RASPADO": (3, 60.0, 0.3, (2, 3), (170, 145, 110), 50.0, 200.0, 0.9),
        "POLVO_PEZUNAS": (2, 40.0, 0.3, (2, 3), (170, 145, 110), 60.0, 250.0, 0.9),
        "ESCOMBROS": (10, 110.0, 0.5, (2, 4), (150, 140, 130), 120.0, 400.0, 0.85),
    }
    for nombre, (count, speed, lifetime, size, color, spread, gravity, friction) in tabla.items():
        cfg = getattr(ev, nombre)
        assert (cfg.count, cfg.speed, cfg.lifetime, (cfg.size_min, cfg.size_max),
                cfg.color, cfg.spread, cfg.gravity, cfg.friction) == (
            count, speed, lifetime, size, color, spread, gravity, friction), nombre


def test_cresta_de_pisoton_ease_out_monotono_y_expira():
    from src.stages.boss_venado.efectos_venado import CrestaDePisoton, STOMP_WINDOW_VISUAL

    cresta = CrestaDePisoton(centro_x=100.0, y_suelo=560.0)
    assert cresta.duracion == STOMP_WINDOW_VISUAL
    assert cresta.viva
    assert cresta.desplazamiento == 0.0
    anterior = 0.0
    dt = STOMP_WINDOW_VISUAL / 20.0
    for _ in range(20):
        cresta.update(dt)
        actual = cresta.desplazamiento
        assert actual >= anterior - 1e-9, "el ease-out debe ser monótono no decreciente"
        anterior = actual
    assert cresta.desplazamiento == 48.0
    assert not cresta.viva


def test_cresta_de_pisoton_dibuja_dos_monticulos_separados():
    import pygame
    from src.stages.boss_venado.efectos_venado import CrestaDePisoton

    pygame.init()
    cresta = CrestaDePisoton(centro_x=100.0, y_suelo=100.0)
    cresta.update(CrestaDePisoton(100.0, 100.0).duracion)  # desplazamiento máximo (48px)
    surface = pygame.Surface((300, 120))
    surface.fill((10, 10, 10))
    cresta.dibujar_mundo(surface, pygame.Vector2(0, 0))
    color_relleno = (120, 95, 70)
    izquierda_pintada = surface.get_at((int(100 - 48), 95))[:3] == color_relleno
    derecha_pintada = surface.get_at((int(100 + 48), 95))[:3] == color_relleno
    assert izquierda_pintada and derecha_pintada, (
        "los dos montículos deben aparecer a ±48px del centro cuando el "
        "desplazamiento ya llegó a su máximo")


def test_cresta_de_pisoton_no_rebasa_la_pared_en_ambos_clamps_reales():
    """Candado de contención (campaña bughunt_20260823, evidencia en
    reports/bughunt_20260823/claude_bordes_camara/geometria_bordes.json,
    sonda_geometria_bordes.py::probar_stomp) -- mismo criterio que
    test_oleada_muere_al_salir_por_la_* de arriba, pero para CrestaDePisoton:
    ``_do_stomp`` (boss_venado.py:1090-1104) planta la cresta en
    ``self.rect.centerx`` sin conocer ARENA_X0/ARENA_X1 -- su única defensa
    es que el jefe nunca puede estar más cerca de una pared que su propio
    clamp de movimiento real (``ARENA_X0+32`` / ``ARENA_X1-32-rect.width``,
    boss_venado.py:724-726 y 1683-1684; STOMP solo existe en fase 0, donde
    ``rect.width==48`` -- boss_venado.py:279/285).

    La coincidencia de constantes es AJUSTADA: el alcance máximo de UN lado
    de la cresta es ``ANCHO/2 + DESPLAZAMIENTO_MAXIMO = 7+48 = 55px``, contra
    un hueco real de ``32 + rect.width/2 = 32+24 = 56px`` entre el clamp y la
    pared -- sobra apenas 1px teórico (la sonda midió empíricamente
    1.1088px, porque el muestreo por fotogramas no alcanza el desplazamiento
    máximo EXACTO en el último frame vivo; este test usa el máximo TEÓRICO,
    así que el margen que verifica es el más estrecho posible: 1.0px exacto).

    Este test fuerza AMBOS clamps reales (izquierdo y derecho) y deja crecer
    la cresta hasta su desplazamiento máximo (48px) para comprobar que el
    alcance nunca cruza [ARENA_X0, ARENA_X1] -- si alguien mueve ANCHO,
    DESPLAZAMIENTO_MAXIMO o el margen de 32px del clamp de pared sin revisar
    esta coincidencia, este candado debe reventar."""
    from src.stages.boss_venado.boss_venado import ARENA_X0, ARENA_X1
    from src.stages.boss_venado.efectos_venado import CrestaDePisoton

    ancho_rect_boss = 48.0  # boss_venado.py:285 (self.rect.width = 48) -- fase 0, STOMP no existe en fase 2
    mitad_ancho_boss = ancho_rect_boss / 2.0
    alcance_maximo_cresta = CrestaDePisoton.ANCHO / 2.0 + CrestaDePisoton.DESPLAZAMIENTO_MAXIMO

    # clamp izquierdo real de _update_movement: position.x == ARENA_X0 + 32
    cx_clamp_izq = (ARENA_X0 + 32.0) + mitad_ancho_boss
    cresta_izq = CrestaDePisoton(cx_clamp_izq, y_suelo=560.0)
    cresta_izq.update(cresta_izq.duracion)   # desplazamiento al máximo exacto (48px)
    assert cresta_izq.desplazamiento == CrestaDePisoton.DESPLAZAMIENTO_MAXIMO
    borde_izq_peor = cx_clamp_izq - alcance_maximo_cresta
    assert borde_izq_peor >= ARENA_X0, (
        f"la cresta del STOMP en el clamp de pared izquierdo sobresale "
        f"{ARENA_X0 - borde_izq_peor}px de ARENA_X0={ARENA_X0} "
        f"(borde_izq_peor={borde_izq_peor})")

    # clamp derecho real de _update_movement: position.x == ARENA_X1 - 32 - rect.width
    cx_clamp_der = (ARENA_X1 - 32.0 - ancho_rect_boss) + mitad_ancho_boss
    cresta_der = CrestaDePisoton(cx_clamp_der, y_suelo=560.0)
    cresta_der.update(cresta_der.duracion)
    assert cresta_der.desplazamiento == CrestaDePisoton.DESPLAZAMIENTO_MAXIMO
    borde_der_peor = cx_clamp_der + alcance_maximo_cresta
    assert borde_der_peor <= ARENA_X1, (
        f"la cresta del STOMP en el clamp de pared derecho sobresale "
        f"{borde_der_peor - ARENA_X1}px de ARENA_X1={ARENA_X1} "
        f"(borde_der_peor={borde_der_peor})")

    # margen exacto que este candado protege en cada lado -- el peor caso
    # posible del diseño actual, documentado para que una futura sesión no
    # tenga que re-derivarlo: 1.0px, ni un fotograma de sobra.
    margen_izq = borde_izq_peor - ARENA_X0
    margen_der = ARENA_X1 - borde_der_peor
    assert margen_izq == pytest.approx(1.0)
    assert margen_der == pytest.approx(1.0)


def test_anillo_de_caida_se_contrae_de_48_a_8():
    import pygame
    from src.stages.boss_venado.efectos_venado import AnilloDeCaida

    pygame.init()
    surface = pygame.Surface((200, 200))
    surface.fill((5, 5, 5))
    color = (230, 90, 60)
    AnilloDeCaida.dibujar_overlay(surface, (100, 100), 0.0, color)
    # progreso 0.0 -> radio 48: debe haber un punto pintado a distancia ~48 del centro
    hay_radio_48 = any(
        surface.get_at((100 + 48, 100 + dy))[:3] == color for dy in (-1, 0, 1))
    surface.fill((5, 5, 5))
    AnilloDeCaida.dibujar_overlay(surface, (100, 100), 1.0, color)
    hay_radio_8 = any(
        surface.get_at((100 + 8, 100 + dy))[:3] == color for dy in (-1, 0, 1))
    assert hay_radio_48, "progreso=0.0 debe pintar puntos a radio 48"
    assert hay_radio_8, "progreso=1.0 debe pintar puntos a radio 8 (ease-in)"


def test_corona_de_esporas_crece_de_6_a_14():
    import pygame
    from src.stages.boss_venado.efectos_venado import CoronaDeEsporas

    pygame.init()
    surface = pygame.Surface((60, 60))
    surface.fill((5, 5, 5))
    color = (230, 90, 60)
    CoronaDeEsporas.dibujar_overlay(surface, (30, 30), 0.0, color)
    radio_min_pintado = surface.get_at((30 + 6, 30))[:3] == color
    surface.fill((5, 5, 5))
    CoronaDeEsporas.dibujar_overlay(surface, (30, 30), 1.0, color)
    radio_max_pintado = surface.get_at((30 + 14, 30))[:3] == color
    assert radio_min_pintado and radio_max_pintado


def test_estrellas_de_aturdimiento_orbitan_sobre_la_cabeza():
    import math
    import pygame
    from src.stages.boss_venado.efectos_venado import EstrellasDeAturdimiento

    pygame.init()
    surface = pygame.Surface((60, 60))
    surface.fill((5, 5, 5))
    color = (230, 90, 60)
    centro_cabeza = (30, 40)
    EstrellasDeAturdimiento.dibujar_overlay(surface, centro_cabeza, t=0.0, color=color)
    # en t=0 la primera estrella (k=0) cae en angulo=0 -> (cx+10, cy-10)
    cx, cy = centro_cabeza[0], centro_cabeza[1] - EstrellasDeAturdimiento.ALTURA_SOBRE_CABEZA
    px, py = int(cx + 10.0), int(cy)
    assert surface.get_at((px, py))[:3] == color


# ──────────────────────────────────────────────
# Task 2: SenalDeCastigo -- señal universal de ventana de castigo (§2.5)
# ──────────────────────────────────────────────

def _frame_de_prueba() -> "pygame.Surface":
    import pygame
    frame = pygame.Surface((16, 16), pygame.SRCALPHA)
    frame.fill((0, 0, 0, 0))
    pygame.draw.rect(frame, (40, 60, 30, 255), (2, 2, 12, 12))  # "cuerpo" opaco
    return frame


def test_senal_de_castigo_cachea_el_anillo_por_clave():
    """(A) del coordinador, Task 14 (2026-08-22): ``silueta()`` se renombra
    a ``anillo()`` -- ya no cachea la silueta completa, cachea el anillo de
    contorno de 1px -- pero el contrato de caché por clave (misma clave ->
    misma Surface) no cambia."""
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    senal = SenalDeCastigo()
    frame = _frame_de_prueba()
    clave = ("drift", 0, 1, 1.0)
    s1 = senal.anillo(frame, clave)
    s2 = senal.anillo(frame, clave)
    assert s1 is s2, "la misma clave debe devolver la MISMA superficie cacheada"
    assert senal.tamano_cache() == 1


def test_senal_de_castigo_anillo_es_el_borde_exterior_no_la_silueta():
    """(A) del coordinador, Task 14 -- Test 1 de la tarea: con un frame
    sintético (cuadrado opaco 10x10 en un lienzo 20x20) el anillo tiene
    píxeles encendidos en el borde EXTERIOR del cuadrado y CERO en su
    interior (el bug viejo: silueta completa dorada -- ver
    zoom_stomp.png f1790/f1840, el venado como silueta blanca sólida) y
    CERO lejos de cualquier borde (el anillo no se extiende más de 1px)."""
    import pygame
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    senal = SenalDeCastigo(color=(250, 220, 120))
    frame = pygame.Surface((20, 20), pygame.SRCALPHA)
    frame.fill((0, 0, 0, 0))
    pygame.draw.rect(frame, (40, 60, 30, 255), (5, 5, 10, 10))  # cuadrado opaco, x/y en [5,14]
    anillo = senal.anillo(frame, ("drift", 0, 1, 1.0))

    def px(frame_x: int, frame_y: int) -> tuple[int, int, int, int]:
        # la superficie del anillo es frame+2 (1px de margen a cada lado):
        # anillo-local (i,j) == frame-local (i-1, j-1).
        return tuple(anillo.get_at((frame_x + 1, frame_y + 1)))

    for fx, fy in ((4, 9), (15, 9), (9, 4), (9, 15)):  # borde exterior (ortogonal)
        color = px(fx, fy)
        assert color[3] == 255 and color[:3] == (250, 220, 120), (
            f"el borde exterior ({fx},{fy}) del cuadrado debería estar en el anillo: {color}")

    for fx, fy in ((9, 9), (5, 5), (14, 14)):  # interior/borde del propio cuadrado
        color = px(fx, fy)
        assert color[3] == 0, f"el interior ({fx},{fy}) no debe formar parte del anillo: {color}"

    color = px(0, 0)  # lejos de cualquier borde
    assert color[3] == 0, f"un pixel lejos del cuadrado no debe formar parte del anillo: {color}"


def test_senal_de_castigo_brillo_nunca_toca_cero():
    """(A) del coordinador, Task 14 -- Test 2 de la tarea: el pulso viejo
    (0.35+0.35*sin, 5Hz) tocaba 0 y apagaba la señal un instante de cada
    ciclo (zoom_stomp.png f1856, zoom_sweep.png f5889: "vuelve a verde").
    El nuevo vive en [0.2, 1.0] a 3Hz y NUNCA debe caer por debajo de 0.2
    en 600 muestras de t."""
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    for i in range(600):
        t = i * 0.0037
        b = SenalDeCastigo.brillo(t)
        assert b >= 0.2, f"brillo por debajo de 0.2 en t={t}: {b}"
        assert b <= 1.0 + 1e-9, f"brillo por encima de 1.0 en t={t}: {b}"


def test_senal_de_castigo_cache_de_anillos_acotada_tras_600_frames_fase2():
    """§9 del diseño: la caché de ANILLOS (no la de brillo) está acotada
    por combinaciones de (anim_key, frame_idx, facing, escala) — nunca por
    id(frame), que crecería sin límite porque BossBase.draw() escala una
    Surface NUEVA cada fotograma en fase 2."""
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    senal = SenalDeCastigo()
    frame_base = _frame_de_prueba()
    combinaciones_posibles = 0
    for anim_key in ("drift", "frenzy_drift", "stomp", "charge", "vine"):
        for frame_idx in range(2):
            for facing in (1, -1):
                for escala in (1.0, 1.25):
                    combinaciones_posibles += 1
    contador = 0
    for _ in range(600):
        anim_key = ("drift", "frenzy_drift", "stomp", "charge", "vine")[contador % 5]
        frame_idx = contador % 2
        facing = 1 if contador % 2 == 0 else -1
        escala = 1.0 if contador % 3 == 0 else 1.25
        clave = (anim_key, frame_idx, facing, escala)
        # cada llamada crea una Surface "nueva" (como haría BossBase.draw en
        # fase 2) -- lo que importa es que la caché indexe por CLAVE, no por
        # identidad de objeto.
        senal.anillo(frame_base.copy(), clave)
        contador += 1
    assert senal.tamano_cache() <= combinaciones_posibles


def test_senal_de_castigo_cache_de_brillo_acotada_tras_600_frames_fase2():
    """Addenda del revisor #2, punto 2 (rango de brillo actualizado por la
    corrección visual del coordinador, Task 14-A, 2026-08-22): la caché de
    BRILLO (``self._cache_brillo``) también debe quedar acotada, igual que
    la de anillos -- indexada por (clave, nivel_de_brillo_cuantizado). Con
    ``round(b, 2)`` crudo la cota sería ~81 valores de brillo por clave (b
    vive en [0.2, 1.0]): demasiado alta para una técnica que solo necesita
    verse fluida a 3 Hz, así que se cuantiza a ``NIVELES_BRILLO_CACHE`` (16)
    niveles -- la cota real queda en combinaciones_de_clave * 16, no * 81."""
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo, NIVELES_BRILLO_CACHE

    senal = SenalDeCastigo()
    frame_base = _frame_de_prueba()
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    combinaciones_posibles = 0
    for anim_key in ("drift", "frenzy_drift", "stomp", "charge", "vine"):
        for frame_idx in range(2):
            for facing in (1, -1):
                for escala in (1.0, 1.25):
                    combinaciones_posibles += 1
    contador = 0
    for _ in range(600):
        anim_key = ("drift", "frenzy_drift", "stomp", "charge", "vine")[contador % 5]
        frame_idx = contador % 2
        facing = 1 if contador % 2 == 0 else -1
        escala = 1.0 if contador % 3 == 0 else 1.25
        clave = (anim_key, frame_idx, facing, escala)
        # barre t sobre varios ciclos completos del seno (5Hz) para que el
        # brillo cuantizado toque, en la práctica, sus 16 niveles posibles.
        t = contador * 0.0037
        surface.fill((0, 0, 0, 0))
        senal.dibujar_overlay(surface, frame_base.copy(), clave, (16, 16), t)
        contador += 1
    assert senal.tamano_cache_brillo() <= combinaciones_posibles * NIVELES_BRILLO_CACHE


def test_senal_de_castigo_jamas_usa_set_alpha():
    """Riesgo 2 del dictamen: set_alpha es ignorado bajo BLEND_RGBA_ADD y
    dejaría la señal invisible en la ruta GL real -- este candado revienta
    si cualquier implementación futura lo reintroduce.

    Alcance ESTRECHADO a la clase (Task 14-B, 2026-08-22): antes el candado
    inspeccionaba el MÓDULO entero (``inspect.getsource(ev)``), lo cual era
    correcto mientras ``SenalDeCastigo`` era la única pieza del archivo que
    tocaba alfa/blending -- pero ``EstelaDeFantasmas`` (Task 14-B) SÍ
    necesita ``set_alpha``: pinta en el PASE DE MUNDO (``draw()``, compuesto
    por software contra ``internal_surface`` ANTES de subir la textura GL),
    no en el overlay post-luz de ``dibujar_ui()`` donde vive el problema de
    H-28/riesgo 2 -- ahí la composición por alfa estándar de pygame funciona
    sin trampas. Acotar el candado a la clase que sí tiene el riesgo evita
    un falso positivo contra una pieza que no lo tiene.

    Reescrito respecto al plan original (nota 5 del coordinador): el plan
    proponía interceptar la llamada con
    ``monkeypatch.setattr(pygame.Surface, "set_alpha", ...)``, pero en
    pygame-ce 2.5.7 (la versión instalada en el lab) ``pygame.Surface`` es
    un tipo C marcado inmutable y esa línea lanza
    ``TypeError: cannot set 'set_alpha' attribute of immutable type``,
    ANTES de ejercitar el código bajo prueba -- no es un fallo de
    ``SenalDeCastigo``, es que el candado nunca llega a montarse. Se
    verifica la misma garantía por inspección estática del código fuente
    de la CLASE (no del módulo entero, ver el párrafo anterior)."""
    import inspect
    from src.stages.boss_venado import efectos_venado as ev

    fuente = inspect.getsource(ev.SenalDeCastigo)
    # "set_alpha(" (con paréntesis pegado) es la LLAMADA real.
    assert "set_alpha(" not in fuente, (
        "SenalDeCastigo no debe llamar Surface.set_alpha jamás -- "
        "BLEND_RGBA_ADD lo ignora en la ruta GL real (ver H-28)")


def test_senal_de_castigo_pulsa_de_brillo_con_el_tiempo():
    """b = 0.6 + 0.4*sin(2*pi*3*t) (Task 14-A, 3Hz): en t=1/12s (cuarto de
    período) el brillo llega a su pico (1.0), distinto del valle de t=0
    (0.6) -- dibujar_overlay() en dos instantes distintos debe componer
    resultados distintos."""
    import pygame
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    senal = SenalDeCastigo()
    frame = _frame_de_prueba()
    clave = ("drift", 0, 1, 1.0)
    surface_a = pygame.Surface((32, 32), pygame.SRCALPHA)
    surface_a.fill((0, 0, 0, 0))
    senal.dibujar_overlay(surface_a, frame, clave, (16, 16), t=0.0)
    surface_b = pygame.Surface((32, 32), pygame.SRCALPHA)
    surface_b.fill((0, 0, 0, 0))
    senal.dibujar_overlay(surface_b, frame, clave, (16, 16), t=1.0 / 12.0)
    arr_a = pygame.surfarray.array3d(surface_a)
    arr_b = pygame.surfarray.array3d(surface_b)
    assert arr_a.sum() != arr_b.sum(), "el brillo debe variar con t"


def test_senal_de_castigo_sobre_overlay_negro_solo_ilumina_el_anillo():
    """(A) del coordinador, Task 14 -- Test 3 de la tarea (reemplaza al
    hallazgo de la Task 9 sobre "fantasma de RGB": con la técnica de anillo
    ese problema queda resuelto por diseño, no por premultiplicación).
    Dibujar sobre un overlay negro deja el píxel del CENTRO del cuerpo en
    (0,0,0) -- el anillo NUNCA pinta el interior, a diferencia del bug
    viejo que blanqueaba el cuerpo entero (zoom_stomp.png f1790/f1840) -- y
    un píxel del anillo por encima de (60,50,25)."""
    import pygame
    from src.stages.boss_venado.efectos_venado import SenalDeCastigo

    senal = SenalDeCastigo()
    frame = _frame_de_prueba()          # 16x16, "cuerpo" opaco en (2,2,12,12)
    surface = pygame.Surface((32, 32), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 255))
    destino = (8, 8)
    senal.dibujar_overlay(surface, frame, ("drift", 0, 1, 1.0), destino, t=0.0)
    # centro del cuerpo: frame-local (8,8) -> superficie destino+frame = (16,16)
    centro_cuerpo = surface.get_at((16, 16))[:3]
    assert centro_cuerpo == (0, 0, 0), (
        f"el interior del cuerpo no debe iluminarse: {centro_cuerpo}")
    # un pixel del anillo, justo a la izquierda del borde del cuerpo:
    # frame-local (1,8) -> superficie (9,16)
    anillo_pixel = surface.get_at((9, 16))[:3]
    assert anillo_pixel[0] > 60 and anillo_pixel[1] > 50 and anillo_pixel[2] > 25, (
        f"el anillo de contorno no se iluminó lo suficiente: {anillo_pixel}")


# ──────────────────────────────────────────────
# (B) del coordinador, Task 14 (2026-08-22) — EstelaDeFantasmas: fantasmas
# del sprite (nunca los rectángulos verdes de TrailSystem.capture_at)
# ──────────────────────────────────────────────

def test_estela_de_fantasmas_capacidad_acotada():
    """agregar() más allá de la capacidad descarta el fantasma MÁS VIEJO
    (FIFO) -- nunca crece sin límite."""
    from src.stages.boss_venado.efectos_venado import EstelaDeFantasmas

    estela = EstelaDeFantasmas(capacidad=6, vida=0.22)
    frame = _frame_de_prueba()
    for i in range(10):
        estela.agregar(frame, (float(i), 0.0))
    assert estela.cantidad() == 6


def test_estela_de_fantasmas_ttl_expira_y_purga():
    from src.stages.boss_venado.efectos_venado import EstelaDeFantasmas

    estela = EstelaDeFantasmas(capacidad=6, vida=0.22)
    frame = _frame_de_prueba()
    estela.agregar(frame, (0.0, 0.0))
    assert estela.cantidad() == 1
    estela.update(0.10)
    assert estela.cantidad() == 1, "0.10s < 0.22s de vida -- todavía no debe purgar"
    estela.update(0.20)               # acumulado 0.30s > 0.22s de vida
    assert estela.cantidad() == 0, "el fantasma debió expirar y purgarse"


def test_estela_de_fantasmas_alfa_decrece_con_el_ttl():
    """dibujar_mundo() modula el alfa con ``ttl/vida`` -- se verifica por
    diferencia empírica: un fantasma recién agregado (ttl==vida) debe verse
    MÁS visible que el mismo fantasma ya envejecido (ttl menor), midiendo
    el brillo compuesto sobre un lienzo negro."""
    import pygame
    from src.stages.boss_venado.efectos_venado import EstelaDeFantasmas

    estela = EstelaDeFantasmas(capacidad=6, vida=0.22)
    frame = _frame_de_prueba()
    estela.agregar(frame, (4.0, 4.0))

    surface_nuevo = pygame.Surface((20, 20))
    surface_nuevo.fill((0, 0, 0))
    estela.dibujar_mundo(surface_nuevo, pygame.Vector2(0, 0))
    brillo_nuevo = int(pygame.surfarray.array3d(surface_nuevo).sum())

    estela.update(0.18)                 # ttl baja a ~0.04 (~18% de vida)
    surface_viejo = pygame.Surface((20, 20))
    surface_viejo.fill((0, 0, 0))
    estela.dibujar_mundo(surface_viejo, pygame.Vector2(0, 0))
    brillo_viejo = int(pygame.surfarray.array3d(surface_viejo).sum())

    assert 0 < brillo_viejo < brillo_nuevo, (
        f"el fantasma envejecido ({brillo_viejo}) debe verse más tenue que "
        f"el recién agregado ({brillo_nuevo}), nunca invisible de golpe ni "
        f"igual de brillante")


def test_estela_de_fantasmas_agregar_tiñe_verde_liana_conserva_el_alfa():
    """agregar() copia el frame y lo tiñe con BLEND_RGB_MULT (verde liana,
    §2.1) -- el canal alfa original del sprite (recortado a su silueta) se
    conserva intacto, solo cambia el RGB."""
    from src.stages.boss_venado.efectos_venado import EstelaDeFantasmas

    estela = EstelaDeFantasmas()
    frame = _frame_de_prueba()          # cuerpo opaco (2,2,12,12), resto alfa 0
    estela.agregar(frame, (0.0, 0.0))
    fantasma = estela._fantasmas[0]["surface"]
    assert fantasma.get_at((0, 0))[3] == 0, "el fondo transparente debe seguir transparente"
    assert fantasma.get_at((8, 8))[3] == 255, "el cuerpo opaco debe seguir opaco"
    assert fantasma.get_at((8, 8))[:3] != frame.get_at((8, 8))[:3], (
        "el cuerpo debe quedar teñido -- no es una copia sin cambios del frame")


# ──────────────────────────────────────────────
# Velo de niebla del corredor (Tarea 8, B-046 en REGISTRO-DE-BUGS.md)
# ──────────────────────────────────────────────

def test_velo_x_inicio_y_x_fin_se_derivan_de_tabla():
    """Candado anti-magia: las constantes del velo NO son números repetidos
    a mano -- están tomadas literalmente de `tramos_venado.TABLA`. Si algún
    día el diseño narrativo mueve el Acto 3 ("El umbral", clima fog) o el
    Acto 4 ("Lo sagrado", == ARENA_X0), este velo se mueve solo con ellos."""
    from src.stages.boss_venado.tramos_venado import TABLA

    assert TABLA[2].numero == 3
    assert TABLA[2].clima == "fog"
    assert ev.VELO_X_INICIO == TABLA[2].x_inicio == 1520.0
    assert TABLA[3].numero == 4
    assert ev.VELO_X_FIN == TABLA[3].x_inicio == 2480.0


def test_velo_x_fin_coincide_con_el_inicio_de_la_arena():
    """Candado de calidad (revisión de spec T8, 2026-08-25): el test de
    arriba fija VELO_X_FIN contra TABLA, pero no contra la arena en sí --
    este candado cierra esa garantía comparando directamente contra la
    constante canónica del boss (`boss_venado.ARENA_X0`, no la copia local
    de `boss_venado_scene.py`, que solo se mantiene sincronizada a mano por
    convención): si la arena se mueve, el velo debe moverse con ella."""
    from src.stages.boss_venado.boss_venado import ARENA_X0

    assert ev.VELO_X_FIN == ARENA_X0


def test_alfa_de_niebla_es_cero_fuera_del_acto_3():
    """0 en Actos 1-2 (antes del umbral) y 0 en el Acto 4/arena (después del
    umbral) -- la niebla existe SOLO donde `tramo_en(x).clima == "fog"`."""
    assert ev.alfa_de_niebla(0.0) == 0
    assert ev.alfa_de_niebla(800.0) == 0            # Acto 1
    assert ev.alfa_de_niebla(1300.0) == 0            # Acto 2
    assert ev.alfa_de_niebla(2500.0) == 0            # Acto 4 (arena)
    assert ev.alfa_de_niebla(10_000.0) == 0          # bien dentro de la arena


def test_alfa_de_niebla_valores_exactos_en_los_bordes():
    """Los cuatro bordes de la función por tramos, con el valor EXACTO que
    describe el diseño (0 al entrar, VELO_ALFA_MAX en todo el sostenido,
    0 al llegar a la arena) -- fija la continuidad en los dos empalmes
    internos (1720 y 2380), donde la rampa y el sostenido deben coincidir
    sin salto."""
    assert ev.alfa_de_niebla(1520.0) == 0                     # VELO_X_INICIO: arranca la rampa de entrada
    assert ev.alfa_de_niebla(1720.0) == ev.VELO_ALFA_MAX       # fin de la rampa de entrada == inicio del sostenido
    assert ev.alfa_de_niebla(2380.0) == ev.VELO_ALFA_MAX       # fin del sostenido == inicio de la rampa de salida
    assert ev.alfa_de_niebla(2480.0) == 0                     # VELO_X_FIN: la niebla ya se disipó del todo


def test_alfa_de_niebla_sostenido_en_todo_el_tramo_medio():
    """[1720, 2380] completo debe valer VELO_ALFA_MAX, no solo los bordes."""
    for x in (1720.0, 1900.0, 2100.0, 2200.0, 2380.0):
        assert ev.alfa_de_niebla(x) == ev.VELO_ALFA_MAX


def test_alfa_de_niebla_rampa_de_entrada_es_monotona_creciente():
    """[1520, 1720): cada paso hacia adelante debe subir el alfa (o
    quedarse igual por redondeo), nunca bajar -- nunca "parpadea"."""
    xs = [1520.0 + i * 20.0 for i in range(11)]   # 1520, 1540, ..., 1720
    alfas = [ev.alfa_de_niebla(x) for x in xs]
    assert alfas[0] == 0
    assert alfas[-1] == ev.VELO_ALFA_MAX
    assert all(a <= b for a, b in itertools.pairwise(alfas)), (
        f"la rampa de entrada no es monótona: {alfas}")


def test_alfa_de_niebla_rampa_de_salida_es_monotona_decreciente():
    """(2380, 2480]: cada paso hacia adelante debe bajar el alfa (o
    quedarse igual por redondeo), nunca subir."""
    xs = [2380.0 + i * 10.0 for i in range(11)]   # 2380, 2390, ..., 2480
    alfas = [ev.alfa_de_niebla(x) for x in xs]
    assert alfas[0] == ev.VELO_ALFA_MAX
    assert alfas[-1] == 0
    assert all(a >= b for a, b in itertools.pairwise(alfas)), (
        f"la rampa de salida no es monótona: {alfas}")


def test_alfa_de_niebla_devuelve_int_en_rango_valido():
    """Contrato de tipo: `alfa_de_niebla` alimenta `Surface.set_alpha()`
    directamente (ver `boss_venado_scene._dibujar_velo_de_niebla`), que
    exige un entero 0-255 -- nunca un float ni un valor fuera de rango."""
    for x in (0.0, 1520.0, 1600.0, 1720.0, 2000.0, 2380.0, 2450.0, 2480.0, 5000.0):
        alfa = ev.alfa_de_niebla(x)
        assert isinstance(alfa, int)
        assert 0 <= alfa <= 255
