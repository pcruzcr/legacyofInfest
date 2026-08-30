"""Módulo: test_presencias_venado
Sistema: tests
Descripción: fauna decorativa del corredor -- daño 0, sin ECS, ventanas aleatorias."""
from __future__ import annotations

import pytest

from src.stages.boss_venado.presencias_venado import (
    LIMITE_X0,
    LIMITE_X1,
    LIMITE_Y0,
    LIMITE_Y1,
    PRESENCIAS,
    X_EMISOR_BRAMIDO,
    EventoSombraQueCruza,
    GestorDePresencias,
    PresenciaVenado,
    _clamp,
    columna_de_patrullaje,
    fila_de_presencia,
)


def test_presencias_no_tienen_rect_ni_damage_on_contact():
    """Candado arquitectónico: ninguna PresenciaVenado puede dañar al
    jugador porque el dataclass no expone ni rect de colisión ni
    damage_on_contact -- es geometría+temporizador, no una entidad ECS."""
    for p in PRESENCIAS:
        assert not hasattr(p, "rect")
        assert not hasattr(p, "damage_on_contact")


def test_gestor_actualizar_no_recibe_ni_toca_al_jugador():
    """GestorDePresencias.actualizar() solo toma dt -- prueba por firma que
    es imposible que lea o modifique al jugador."""
    import inspect
    firma = inspect.signature(GestorDePresencias.actualizar)
    assert list(firma.parameters) == ["self", "dt"]


def test_ventanas_deterministas_con_la_misma_semilla():
    g1 = GestorDePresencias(semilla=42)
    g2 = GestorDePresencias(semilla=42)
    visibles_1, visibles_2 = [], []
    for _ in range(600):   # 10s a 60fps
        g1.actualizar(1 / 60)
        g2.actualizar(1 / 60)
        visibles_1.append(dict(g1.visibles))
        visibles_2.append(dict(g2.visibles))
    assert visibles_1 == visibles_2


def test_visibles_filtra_por_tramo_activo():
    """GestorDePresencias.actualizar() solo procesa (abre/cierra ventana de)
    las presencias del tramo activo -- las de otros tramos ni siquiera
    entran en el diccionario interno mientras su tramo no está activo, así
    que g.visibles nunca se contamina con ids ajenos al tramo que se ha
    recorrido. Reemplaza a test_columna_actual_filtra_presencias_por_tramo
    (candado inerte: el campo columna_actual nunca se leía en ningún lado
    -- decisión YAGNI del coordinador, ver presencias_venado.py).

    Nota de verificación empírica (corrida a mano antes de escribir esta
    prueba): una presencia que queda visible (timer positivo) justo antes
    de cambiar de tramo se CONGELA en ese valor -- actualizar() la salta
    por completo mientras su tramo no sea el activo, así que NO decae a
    0.0 solo por cambiar de tramo. Por eso esta prueba no afirma que una
    presencia "desaparece" al cambiar de tramo -- lo que sí es cierto, y lo
    que se prueba aquí, es que una presencia de un tramo nunca ABRE una
    ventana nueva mientras ese tramo no está activo."""
    ids_por_tramo = {t: {p.id for p in PRESENCIAS if p.tramo == t} for t in (1, 2, 3)}

    g = GestorDePresencias(semilla=3)
    g.tramo_actual = 1
    vistos_tramo1 = set()
    for _ in range(20 * 60):   # 20s a 60fps: cubre la espera máxima (15.0s) del tramo 1
        g.actualizar(1 / 60)
        vistos_tramo1 |= set(g.visibles)
    assert vistos_tramo1, "el tramo 1 debió abrir al menos una ventana visible en 20s"
    assert vistos_tramo1 <= ids_por_tramo[1]
    # Mientras el tramo 1 estuvo activo, ninguna presencia de otro tramo
    # entró siquiera al diccionario interno (ni con valor 0.0).
    assert not (set(g._visible) & (ids_por_tramo[2] | ids_por_tramo[3]))

    g.tramo_actual = 2
    congelado_del_tramo1 = set(g.visibles) & ids_por_tramo[1]   # lo que haya quedado congelado, si algo
    vistos_tramo2 = set()
    for _ in range(20 * 60):   # 20s a 60fps: cubre la espera máxima (16.0s) del tramo 2
        g.actualizar(1 / 60)
        vistos_tramo2 |= set(g.visibles) - congelado_del_tramo1
    assert vistos_tramo2, "el tramo 2 debió abrir al menos una ventana visible en 20s"
    assert vistos_tramo2 <= ids_por_tramo[2]
    # El tramo 3 tampoco se contaminó mientras el tramo 2 estuvo activo.
    assert not (set(g._visible) & ids_por_tramo[3])


def test_columna_de_patrullaje_oscila_con_el_tiempo_no_con_la_posicion():
    """Candado de la auto-revisión de este plan: la fase del vaivén depende
    de tiempo_total (segundos reales), NUNCA de la posición del jugador --
    dos tiempos distintos deben dar columnas distintas incluso si el
    'periodo' cabe varias veces en un rango de píxeles similar."""
    p = PRESENCIAS[0]
    c0 = columna_de_patrullaje(p, 0.0)
    c_mitad = columna_de_patrullaje(p, p.periodo_patrullaje / 2.0)
    c_periodo_completo = columna_de_patrullaje(p, p.periodo_patrullaje)
    assert c0 == pytest.approx(p.columna_centro, abs=0.5)
    assert c_mitad == pytest.approx(p.columna_centro, abs=0.5)
    assert c0 == pytest.approx(c_periodo_completo, abs=1e-6)   # periódica
    assert abs(c0 - columna_de_patrullaje(p, p.periodo_patrullaje / 4.0)) > 1.0


def test_presencias_jamas_salen_del_corredor():
    """Candado (dictamen doc-guardian, riesgo #6, precedente B-035 -- el
    venado se salía de la arena en SEARCH; la geometría nueva sin control
    de límites se escapa): con dt grande y varias semillas, ninguna
    presencia debe calcular una posición fuera de los límites REALES del
    corredor, sin importar cuánto empuje el vaivén senoidal."""
    for semilla in (1, 2, 3, 17, 999):
        g = GestorDePresencias(semilla=semilla)
        for _ in range(50):
            g.actualizar(37.0)   # dt grande a propósito: estresa el vaivén
        for p in PRESENCIAS:
            x = columna_de_patrullaje(p, g.tiempo_total)
            y = fila_de_presencia(p)
            assert LIMITE_X0 <= x <= LIMITE_X1
            assert LIMITE_Y0 <= y <= LIMITE_Y1


def test_clamp_recorta_fuera_de_rango():
    """_clamp() directo con valores fuera de rango, y una PresenciaVenado
    sintética cuyo columna_centro +- rango_columnas excedería LIMITE_X0/X1
    sin el clamp -- verifica que columna_de_patrullaje() recorta EXACTO al
    límite en vez de dejar pasar el valor crudo del vaivén senoidal (el
    candado de arriba, test_presencias_jamas_salen_del_corredor, prueba
    esto solo indirectamente contra las 3 presencias reales, que hoy no
    llegan a excederse; este ejercita el propio mecanismo del clamp)."""
    assert _clamp(100.0, 0.0, 50.0) == 50.0
    assert _clamp(-10.0, 0.0, 50.0) == 0.0
    assert _clamp(25.0, 0.0, 50.0) == 25.0

    # columna_centro=2450 + rango_columnas=200 excede LIMITE_X1=2480 en el
    # pico del vaivén (periodo_patrullaje=4.0, t=1.0 -> avance=0.25 ->
    # sin(0.25*tau)=1.0 exacto -> x_crudo = 2650 sin clamp).
    p_alta = PresenciaVenado(
        "sintetica_alta", tramo=1, columna_centro=2450.0, rango_columnas=200.0,
        periodo_patrullaje=4.0, color=(0, 0, 0), alto=10,
        espera=(1.0, 1.0), duracion=(1.0, 1.0),
    )
    assert columna_de_patrullaje(p_alta, 1.0) == LIMITE_X1

    # columna_centro=30 - rango_columnas=200 cae bajo LIMITE_X0=0 en el
    # valle del vaivén (t=3.0 -> avance=0.75 -> sin(0.75*tau)=-1.0 exacto ->
    # x_crudo = -170 sin clamp).
    p_baja = PresenciaVenado(
        "sintetica_baja", tramo=1, columna_centro=30.0, rango_columnas=200.0,
        periodo_patrullaje=4.0, color=(0, 0, 0), alto=10,
        espera=(1.0, 1.0), duracion=(1.0, 1.0),
    )
    assert columna_de_patrullaje(p_baja, 3.0) == LIMITE_X0


def test_sombra_que_cruza_dispara_solo_una_vez_por_episodio_en_su_ventana():
    disparos = []
    evento = EventoSombraQueCruza(reproducir_sfx=lambda x: disparos.append(x))
    for x in (0.0, 2100.0, 2250.0, 2400.0, 2470.0, 2480.0):
        evento.actualizar(x)
    assert len(disparos) == 1
    # CORRECCIÓN post-revisión de spec: el callback NO recibe la columna del
    # jugador (2250.0, la primera x dentro de [SOMBRA_X0, ARENA_X0) que
    # abrió la ventana) -- recibe siempre X_EMISOR_BRAMIDO (el gazebo del
    # Venado, x=3168), para que _play_sfx_spatial produzca paneo/atenuación
    # reales en vez de un sonido centrado en el propio jugador (ver el
    # docstring de X_EMISOR_BRAMIDO en presencias_venado.py).
    assert disparos[0] == X_EMISOR_BRAMIDO


def test_sombra_que_cruza_no_dispara_fuera_de_su_ventana():
    disparos = []
    evento = EventoSombraQueCruza(reproducir_sfx=lambda x: disparos.append(x))
    for x in (0.0, 500.0, 1900.0):
        evento.actualizar(x)
    assert disparos == []


def test_sombra_que_cruza_se_puede_reiniciar_para_otro_episodio():
    disparos = []
    evento = EventoSombraQueCruza(reproducir_sfx=lambda x: disparos.append(x))
    evento.actualizar(2300.0)
    evento.reiniciar()
    evento.actualizar(2300.0)
    assert len(disparos) == 2
    # Ambos disparos vienen del gazebo, nunca de 2300.0 (la columna del
    # jugador que abrió la ventana) -- ver X_EMISOR_BRAMIDO.
    assert disparos == [X_EMISOR_BRAMIDO, X_EMISOR_BRAMIDO]
