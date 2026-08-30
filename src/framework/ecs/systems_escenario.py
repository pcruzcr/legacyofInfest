"""
Fase ESCENARIO y ARRASTRE — las superficies se mueven y llevan a su pasajero.

Extraído de `systems.py` monolítico por Fase, no por mecánica.
Plataformas móviles, bloques rítmicos, hundibles, lianas y el arrastre
comparten ventana ESCENARIO→ARRASTRE porque todas mueven geometría antes de
que el jugador resuelva colisiones. El orden plataforma → arrastre → colisión
es el que evita el hundimiento de un fotograma.
"""
from __future__ import annotations

import pygame

from src.framework.ecs.components import (
    BloqueRitmico,
    EsJugador,
    Liana,
    LianaSalto,
    PlataformaHundible,
    PlataformaMovil,
    Solido,
    Transform,
    Velocidad,
)
from src.framework.ecs.world import EntityId, World

# ══════════════════════════════════════════════════════════════
# Fase ESCENARIO — las superficies se mueven
# ══════════════════════════════════════════════════════════════


def sistema_plataformas_moviles(mundo: World, dt: float) -> None:
    """Mueve las plataformas y **anota cuánto se movieron**.

    El `delta` no es un dato de conveniencia: es lo único que permite al sistema
    de arrastre saber cuánto llevar al pasajero. Calcularlo allí obligaría a
    recordar la posición anterior de cada plataforma, que es guardar el mismo
    dato dos veces.
    """
    for entidad, plat in mundo.cada(PlataformaMovil):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue
        antes = pygame.Vector2(t.posicion)

        if plat._espera_restante > 0.0:
            plat._espera_restante -= dt
            plat.delta.update(0, 0)
            continue

        objetivo = plat.destino if plat._hacia_destino else plat.origen
        hacia = objetivo - t.posicion
        distancia = hacia.length()
        paso = plat.velocidad * dt
        if distancia <= paso or distancia == 0.0:
            t.posicion.update(objetivo)
            plat._hacia_destino = not plat._hacia_destino
            plat._espera_restante = plat.espera
        else:
            t.posicion += hacia.normalize() * paso

        t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))
        plat.delta.update(t.posicion - antes)


def sistema_bloques_ritmicos(mundo: World, dt: float) -> None:
    """Aparecen y desaparecen a compás.

    Quitar y poner el componente `Solido` es todo lo que hace falta: el sistema
    de colisión consulta quién es sólido cada fotograma, así que un bloque que
    deja de serlo deja de sostener a quien tenga encima **en el mismo
    fotograma**, y el jugador cae. Con herencia habría que avisar a alguien; con
    componentes, la ausencia del dato es el aviso.
    """
    reloj = mundo.recurso("reloj_musical")
    for entidad, bloque in mundo.cada(BloqueRitmico):
        bloque._t += dt
        # AUD-137 (F6): con patrón, el bloque **pregunta a la música** en qué
        # pulso va en vez de contar sus propios segundos. Contando segundos,
        # el bloque y la canción llevan relojes distintos y a los cinco
        # minutos van medio compás desfasados: es la razón por la que hasta
        # ahora no se podía hacer un nivel rítmico de verdad.
        if bloque.sigue_la_musica and reloj is not None:
            # AUD-250: el `desfase` se pasa también aquí. Antes sólo contaba en
            # el modo por segundos, así que escribir un `patron` hacía que todos
            # los bloques con el mismo ritmo entraran y salieran a la vez — un
            # semáforo en lugar de un ritmo.
            presente = reloj.presente_en_patron(bloque.patron, bloque.desfase)
        else:
            presente = bloque.presente
        tiene = mundo.tiene(entidad, Solido)
        if presente and not tiene:
            mundo.poner(entidad, Solido())
        elif not presente and tiene:
            mundo.quitar(entidad, Solido)


def sistema_plataformas_hundibles(mundo: World, dt: float) -> None:
    """Se hunden al pisarlas y vuelven solas.

    AUD-507 — `marcar_pisada` existía desde que existe esta mecánica, con un
    docstring que decía «lo llama el sistema de colisión», y nadie la
    llamaba: sólo la usaba `tests/test_ecs.py` invocándola a mano. Ninguna
    hundible del juego llegó a hundirse nunca pisándola. El sensor de abajo
    es el mismo patrón que `sistema_arrastre_de_plataformas` —un rectángulo
    fino sobre la superficie, `colliderect` contra quien tenga `Transform` y
    `Velocidad`—, así que detecta al jugador y a cualquier otra cosa capaz de
    pisar, no sólo a quien tenga la marca `EsJugador`.
    """
    for entidad, hund in mundo.cada(PlataformaHundible):
        t = mundo.obtener(entidad, Transform)
        if t is None:
            continue

        if (hund._ausente <= 0.0 and not hund._cayendo and hund._pisada <= 0.0):
            sensor = pygame.Rect(
                t.rect.x, t.rect.y - MARGEN_PASAJERO,
                t.rect.width, MARGEN_PASAJERO + 1,
            )
            for pisador in mundo.con(Transform, Velocidad):
                if pisador == entidad:
                    continue
                tp = mundo.obtener(pisador, Transform)
                if tp is not None and sensor.colliderect(tp.rect):
                    marcar_pisada(mundo, entidad)
                    break

        if hund._ausente > 0.0:
            hund._ausente -= dt
            if hund._ausente <= 0.0:
                t.posicion.y = hund.y_original
                t.rect.y = int(hund.y_original)
                hund._cayendo = False
                hund._pisada = 0.0
                mundo.poner(entidad, Solido(atravesable_desde_abajo=True))
            continue

        if hund._cayendo:
            t.posicion.y += hund.velocidad_caida * dt
            t.rect.y = int(t.posicion.y)
            if t.posicion.y > hund.y_original + 120:
                mundo.quitar(entidad, Solido)
                hund._ausente = hund.reaparece_en
        elif hund._pisada > 0.0:
            hund._pisada -= dt
            if hund._pisada <= 0.0:
                hund._cayendo = True


def marcar_pisada(mundo: World, plataforma: EntityId) -> None:
    """Avisa de que alguien pisó una hundible. Lo llama el sistema de colisión.

    Es una función y no un componente `Pisado` porque el dato vive un solo
    fotograma. Un componente que se pone y se quita cada fotograma ensucia el
    censo y no aporta nada que no aporte una llamada.
    """
    hund = mundo.obtener(plataforma, PlataformaHundible)
    if hund is not None and not hund._cayendo and hund._ausente <= 0.0 and hund._pisada <= 0.0:
        hund._pisada = hund.retraso


# ══════════════════════════════════════════════════════════════
# Fase ARRASTRE — las plataformas llevan a su pasajero
# ══════════════════════════════════════════════════════════════

#: Margen en px para considerar que algo va «encima» de una plataforma.
#:
#: Cero no vale: tras resolver la colisión el pasajero queda apoyado, con su
#: borde inferior exactamente en el borde superior de la plataforma, y un
#: `colliderect` de rectángulos que sólo se tocan da **False**. Con un píxel de
#: margen el apoyo se detecta, y con más de tres se detectaría a quien pasa
#: saltando por encima.
MARGEN_PASAJERO = 2


def sistema_arrastre_de_plataformas(mundo: World, _dt: float) -> None:
    """Mueve con la plataforma a quien va encima.

    **Esto es lo que casi nadie implementa**, y el motivo por el que las
    plataformas móviles «no funcionan» en la mitad de los proyectos: sin
    arrastre, el jugador se queda clavado en el aire mientras la plataforma se
    va, y parece un fallo de colisión cuando es un sistema que falta.

    Corre entre el movimiento de la plataforma y la resolución de colisiones,
    y no después. Después, el pasajero pasaría un fotograma hundido en la
    plataforma y saldría expulsado al siguiente.
    """
    for entidad, plat in mundo.cada(PlataformaMovil):
        if plat.delta.length_squared() == 0.0:
            continue
        tp = mundo.obtener(entidad, Transform)
        if tp is None:
            continue
        sensor = pygame.Rect(
            tp.rect.x, tp.rect.y - MARGEN_PASAJERO, tp.rect.width, MARGEN_PASAJERO + 1,
        )
        for pasajero in mundo.con(Transform, Velocidad):
            if pasajero == entidad:
                continue
            t = mundo.obtener(pasajero, Transform)
            if t is None or not sensor.colliderect(t.rect):
                continue
            t.posicion += plat.delta
            t.rect.topleft = (int(t.posicion.x), int(t.posicion.y))


def sistema_lianas_moviles(mundo: World, dt: float) -> None:
    """Liana que se balancea — amplitud>0 oscila como péndulo y arrastra al trepador.

    PSX HQ 2.5D: una liana estática es un palo; una que se mueve es un reto de
    timing y una lectura de física. Usa _origen_x + sin(t*2π/periodo)*amplitud,
    con periodo 0 = estática. Arrastra a quien esté en TrepandoState agarrado a
    esa liana (delta x aplicado a su Transform y a su rect).
    """
    import math as _math
    for _, liana in mundo.cada(Liana):
        if liana.amplitud <= 0.0 or liana.periodo <= 0.0:
            continue
        # Guarda origen la primera vez
        if abs(liana._origen_x) < 0.5 and liana._origen_x == 0.0:
            # Si rect.x es 0 por casualidad, no confundir con no inicializado
            # Usa flag: si _t==0 y amplitud>0, inicializa
            if liana._t == 0.0:
                liana._origen_x = float(liana.rect.x)
        liana._t += dt
        nuevo_x = liana._origen_x + _math.sin(liana._t * 2 * _math.pi / liana.periodo) * liana.amplitud
        delta = int(nuevo_x) - liana.rect.x
        if delta != 0:
            liana.rect.x = int(nuevo_x)
            # Arrastra a trepadores agarrados a esta liana
            from src.framework.entities.states.rope import TrepandoState
            for eid in mundo.con(Transform, EsJugador):
                t = mundo.obtener(eid, Transform)
                if t is None:
                    continue
                # Busca si el jugador está trepando esta liana (via estado)
                # Accede al Player real si es vista
                duenio = getattr(t, "_duenio", None)
                if duenio is not None:
                    estado = getattr(duenio, "_state_instance", None)
                    if isinstance(estado, TrepandoState) and getattr(estado, "liana", None) is liana:
                        # Mueve al jugador con la liana
                        duenio.position.x += float(delta)
                        duenio.rect.x += delta
                        # También mueve su Transform vista
                        t.posicion.x += float(delta)
                        t.rect.x += delta


def sistema_lianas_salto(mundo: World, dt: float) -> None:
    """Liana de salto — colgante con pendulo para saltar de una a otra.

    Distinta a Vine de trepar: aquí te cuelgas y te balanceas, no subes.
    Usa _origen_x + sin(t*2π/periodo)*amplitud, periodo 0 = fija colgante.
    Arrastra a quien esté en BalanceoEnLianaSaltoState.
    """
    import math as _math
    for _, ls in mundo.cada(LianaSalto):
        if ls.amplitud <= 0.0 or ls.periodo <= 0.0:
            continue
        if ls._t == 0.0 and ls._origen_x == 0.0:
            ls._origen_x = float(ls.rect.x)
        ls._t += dt
        nuevo_x = ls._origen_x + _math.sin(ls._t * 2 * _math.pi / ls.periodo) * ls.amplitud
        delta = int(nuevo_x) - ls.rect.x
        if delta != 0:
            ls.rect.x = int(nuevo_x)
            from src.framework.entities.states.rope import BalanceoEnLianaSaltoState
            for eid in mundo.con(Transform, EsJugador):
                t = mundo.obtener(eid, Transform)
                if t is None:
                    continue
                duenio = getattr(t, "_duenio", None)
                if duenio is not None:
                    estado = getattr(duenio, "_state_instance", None)
                    if isinstance(estado, BalanceoEnLianaSaltoState) and getattr(estado, "_liana_salto", None) is ls:
                        duenio.position.x += float(delta)
                        duenio.rect.x += delta
                        t.posicion.x += float(delta)
                        t.rect.x += delta
