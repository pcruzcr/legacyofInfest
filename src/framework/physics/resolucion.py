"""
Module: resolucion
System: framework.physics
Description: AUD-334 — el resolutor de mundo compartido.

Por qué existe esto
===================
La resolución de colisión del motor vivía como métodos del jugador
(`_resolve_collision`, `_resolver_pendientes`, `_resolve_one_way_collision`),
con los comentarios auditados repartidos entre ellos. Un contexto de juego
nuevo —un minijuego, un modo, un jefe que también se mueve contra el
escenario— tenía dos opciones: heredar del jugador (arrastrando la máquina
de estados) o copiar los métodos (duplicando en cada copia las trampas que
costaron AUD-130, AUD-297, AUD-323, AUD-324 y AUD-326).

Este módulo es la resolución entera como **pasos puros** sobre un
`EstadoDeMovimiento` — qué sabe la entidad este fotograma — que devuelven
`Contacto` — los **hechos**, no las reglas: a qué posición llegó, a qué
velocidad, si aterrizó, contra qué lado de pared quedó, si hay borde libre
para el ledge grab. La entidad decide qué hacer con los hechos: sonar el
aterrizaje, recargar el doble salto, permitir el wall jump.

Cómo lo consume el jugador
==========================
El jugador conserva sus métodos con los mismos nombres y firmas —los
llaman directamente las pruebas y el material que se copia—, pero ahora son
adaptadores delgados: traducen sus atributos a `EstadoDeMovimiento`,
llaman al paso correspondiente y aplican el `Contacto` de vuelta. Las
entidades y modos nuevos pueden llamar directamente a `resolver_movimiento`,
que compone los cinco pasos en el orden auditado.

El orden importa y es el que AUD-297 fijó: eje X → pared lateral de las
cuestas → eje Y → cuestas → repisas de un sentido. Las cuestas van después
del eje Y porque la pendiente corrige la altura que la caja acaba de dejar,
y antes de las repisas porque una repisa atravesable por encima de una
cuesta tiene que poder atrapar al jugador ya colocado en la cuesta.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.framework.physics.perfil import CENITAL, Cuestas, PhysicsProfile
from src.framework.stage.pendientes import (
    MARGEN_DE_PEGADO,
    Pendiente,
    componente_de_deslizamiento,
    resolver_con_ganadora,
    resolver_lateral,
)


@dataclass
class EstadoDeMovimiento:
    """Lo que el resolutor necesita saber de la entidad en un fotograma.

    El resolutor muta `posicion` y `velocidad` y va dejando el resto de
    campos como huella para los pasos siguientes.
    """

    posicion: pygame.Vector2
    velocidad: pygame.Vector2
    ancho: float
    alto: float
    en_el_suelo: bool = False
    #: Dónde estaban los pies el fotograma anterior: las repisas de un
    #: sentido sólo atrapan a quien estaba a la altura del borde.
    prev_foot_y: float = 0.0
    #: ¿Pisaba suelo antes del paso Y? Lo escribe `resolver_eje_y` y lo
    #: consume `resolver_cuestas` — AUD-297: leer `en_el_suelo` allí no
    #: vale, porque el paso Y lo pone a False.
    venia_del_suelo: bool = False


@dataclass
class Contacto:
    """Los hechos del fotograma. Sin reglas: la entidad decide.

    `aterrizo_en` vale "", "suelo", "cuesta" o "repisa" — según dónde
    aterrizó. `aterrizo_desde_el_aire` sólo es significativo en el caso
    «repisa»: es el dato que AUD-255 necesitaba para sonar sólo al llegar
    desde el aire y no cada fotograma de pie encima.
    """

    posicion: pygame.Vector2
    velocidad: pygame.Vector2
    en_el_suelo: bool = False
    aterrizo: bool = False
    aterrizo_en: str = ""
    aterrizo_desde_el_aire: bool = False
    topo: bool = False
    lado_de_pared: int = 0
    pared_en_el_aire: bool = False
    repisa_libre: bool = False
    venia_del_suelo: bool = False


def resolver_eje_x(
    estado: EstadoDeMovimiento,
    dt: float,
    solidos: list[pygame.Rect],
) -> Contacto:
    """Integra y resuelve el eje X contra los sólidos.

    AUD-130 — este paso también **integra**, y ahí estaba el defecto: la
    resolución vivía en un método que salía temprano si `collision_rects`
    estaba vacío, y un escenario sin cajas de colisión —un error
    frecuentísimo en la primera capa `Collision` de un estudiante— dejaba
    la velocidad creciendo y la posición congelada. Contrato: **integrar
    siempre, resolver sólo si hay contra qué**.

    El umbral `v_overlap <= 2` es la tolerancia al redondeo a entero del
    rect: dos píxeles separan «estoy de pie encima» de «me estoy dando
    contra ello». Subirlo haría atravesable un escalón bajo; bajarlo a
    cero engancharía al jugador con el suelo sobre el que está de pie.
    """
    w, h = estado.ancho, estado.alto
    contacto = Contacto(
        posicion=estado.posicion, velocidad=estado.velocidad,
        en_el_suelo=estado.en_el_suelo)
    lado: int = 0
    pared_en_el_aire = False
    repisa_libre = False

    estado.posicion.x += estado.velocidad.x * dt
    if solidos:
        for tile in solidos:
            px = pygame.Rect(int(estado.posicion.x), int(estado.posicion.y), w, h)
            if px.colliderect(tile):
                # BUG-003 FIX: save pre-mutation top for ledge grab check.
                pre_mutate_top = px.top
                pre_px = pygame.Rect(
                    int(estado.posicion.x - estado.velocidad.x * dt),
                    int(estado.posicion.y), w, h)
                v_overlap = min(pre_px.bottom, tile.bottom) - max(pre_px.top, tile.top)
                if v_overlap <= 2:
                    continue
                if estado.velocidad.x > 0:
                    px.right = tile.left
                    lado = 1
                elif estado.velocidad.x < 0:
                    px.left = tile.right
                    lado = -1
                else:
                    if (px.right - tile.left) < (tile.right - px.left):
                        px.right = tile.left
                        lado = 1
                    else:
                        px.left = tile.right
                        lado = -1
                if lado != 0 and not estado.en_el_suelo:
                    pared_en_el_aire = True
                    ledge_check = pygame.Rect(
                        tile.left if lado == 1 else tile.right - 2,
                        tile.top - 16,
                        max(tile.width, 2),
                        16,
                    )
                    ledge_found = False
                    for t2 in solidos:
                        if ledge_check.colliderect(t2):
                            ledge_found = True
                            break
                    repisa_libre = (
                        not ledge_found
                        and pre_mutate_top <= tile.top + 8
                        and pre_mutate_top >= tile.top - 16
                    )
                estado.velocidad.x = 0.0
                estado.posicion.x = float(px.x)

    contacto.lado_de_pared = lado
    contacto.pared_en_el_aire = pared_en_el_aire
    contacto.repisa_libre = repisa_libre
    return contacto


def resolver_paredes_de_pendientes(
    estado: EstadoDeMovimiento,
    pendientes: list[Pendiente],
    margen: float = MARGEN_DE_PEGADO,
) -> None:
    """Frena la entrada lateral a la rampa — AUD-323.

    El eje X se mueve libre y el eje Y coloca sobre la hipotenusa; eso
    dejaba dos entradas laterales abiertas — la cara empinada del extremo
    alto y la hipotenusa a media altura — por las que el jugador cruzaba
    la roca y luego era absorbido hacia la superficie. `resolver_lateral`
    devuelve la `x` corregida y esto la aplica, con la velocidad frenada
    igual que contra una pared normal.
    """
    if not pendientes:
        return
    rect = pygame.Rect(
        int(estado.posicion.x), int(estado.posicion.y),
        int(estado.ancho), int(estado.alto))
    x = resolver_lateral(rect, pendientes, margen=margen)
    if x is None:
        return
    if x != estado.posicion.x:
        estado.velocidad.x = 0.0
    estado.posicion.x = x


def resolver_eje_y(
    estado: EstadoDeMovimiento,
    dt: float,
    solidos: list[pygame.Rect],
) -> Contacto:
    """Integra y resuelve el eje Y, por dirección de movimiento.

    El que venía de arriba aterriza (`prev_bottom <= tile.top + 1`) y el
    que venía de abajo topa (`prev_top >= tile.bottom - 1`): cada eje sólo
    ve la penetración que causó su propio movimiento.

    AUD-297 — `venia_del_suelo` se guarda aquí, antes de poner
    `en_el_suelo` a False, para el paso de cuestas que corre después.
    """
    w, h = estado.ancho, estado.alto
    contacto = Contacto(
        posicion=estado.posicion, velocidad=estado.velocidad,
        en_el_suelo=estado.en_el_suelo)

    prev_bottom = estado.posicion.y + h
    prev_top = estado.posicion.y
    estado.posicion.y += estado.velocidad.y * dt
    was_grounded = estado.en_el_suelo
    estado.venia_del_suelo = was_grounded
    contacto.venia_del_suelo = was_grounded
    estado.en_el_suelo = False
    if solidos:
        py = pygame.Rect(int(estado.posicion.x), int(estado.posicion.y), w, h)
        check = py.inflate(0, 2)
        check.y = py.y - 1
        for tile in solidos:
            if check.colliderect(tile):
                if estado.velocidad.y >= 0 and prev_bottom <= tile.top + 1:
                    # Came from above: land.
                    if not was_grounded and estado.velocidad.y > 0:
                        contacto.aterrizo = True
                        contacto.aterrizo_en = "suelo"
                    py.bottom = tile.top
                    estado.velocidad.y = 0.0
                    estado.en_el_suelo = True
                elif estado.velocidad.y < 0 and prev_top >= tile.bottom - 1:
                    # Came from below: bonk.
                    py.top = tile.bottom
                    estado.velocidad.y = 0.0
                    contacto.topo = True
                estado.posicion.y = float(py.y)
                check.y = py.y - 1
                check.height = py.height + 2
    return contacto


def resolver_cuestas(
    estado: EstadoDeMovimiento,
    dt: float,
    pendientes: list[Pendiente],
    cuestas: Cuestas,
) -> Contacto:
    """Coloca los pies sobre la cuesta que se esté pisando — AUD-297.

    Los pasos de AUD-324 (la proyección del impulso de caída sobre la
    hipotenusa) y AUD-326 (el deslizamiento sostenido de quien se queda
    quieto) viven aquí. La geometría está en `pendientes.py`, que no toca
    entidades: devuelve una `y` y esto la aplica.
    """
    contacto = Contacto(
        posicion=estado.posicion, velocidad=estado.velocidad,
        en_el_suelo=estado.en_el_suelo)
    if not pendientes:
        return contacto

    rect = pygame.Rect(
        int(estado.posicion.x), int(estado.posicion.y),
        int(estado.ancho), int(estado.alto))
    superficie, ganadora = resolver_con_ganadora(
        rect, estado.velocidad.y,
        estado.venia_del_suelo or estado.en_el_suelo,
        pendientes,
        margen=cuestas.margen_pegado)
    if superficie is None:
        return contacto

    if not estado.en_el_suelo and estado.velocidad.y > 0:
        contacto.aterrizo = True
        contacto.aterrizo_en = "cuesta"
        # AUD-324 — la proyección de velocidad que `docs/87` §11 pidió:
        # caer en vertical sobre una cuesta no debe parar al jugador en
        # seco; el impulso de la caída se proyecta sobre la hipotenusa y
        # lo empuja cuesta abajo.
        if ganadora is not None:
            estado.velocidad.x += componente_de_deslizamiento(
                ganadora, estado.velocidad.y)
    elif ganadora is not None and estado.velocidad.x == 0.0:
        # AUD-326 — el deslizamiento sostenido. El aterrizaje ya proyectó
        # el impulso (AUD-324); aquí, estando ya en el suelo y sin entrada
        # horizontal, la gravedad desliza al jugador cuesta abajo a
        # velocidad constante y acotada, sin aceleración en fuga. Andar
        # manda: la entrada ya puso `velocity.x` y esto no se la discute.
        desliz = componente_de_deslizamiento(
            ganadora, cuestas.velocidad_deslizamiento)
        estado.velocidad.x = desliz
        # Este paso corre después de integrar el eje Y: la velocidad que se
        # ponga aquí no se integra este fotograma, así que el
        # deslizamiento se aplica sobre la posición directamente.
        estado.posicion.x += desliz * dt
    estado.posicion.y = float(superficie) - estado.alto
    estado.velocidad.y = 0.0
    estado.en_el_suelo = True
    return contacto


def resolver_repisas(
    estado: EstadoDeMovimiento,
    repisas: list[pygame.Rect],
) -> Contacto:
    """Resuelve las plataformas de un solo sentido (atravesables desde abajo).

    Sólo resuelve cayendo (`velocidad.y >= 0`) **y** si los pies estaban a
    la altura del borde el fotograma anterior (`prev_foot_y <= plat.top + 1`):
    andar hacia una plataforma desde un suelo más bajo la atraviesa (la
    semántica de un solo sentido del prólogo — saltar a través, caer encima).
    """
    contacto = Contacto(
        posicion=estado.posicion, velocidad=estado.velocidad,
        en_el_suelo=estado.en_el_suelo)
    if not repisas or estado.velocidad.y < 0:
        return contacto

    player_rect = pygame.Rect(
        int(estado.posicion.x), int(estado.posicion.y),
        int(estado.ancho), int(estado.alto))
    # Inflate by 2px so edge-aligned platforms (player bottom == plat top)
    # are detected via colliderect's strict comparison.
    collision_check_rect = player_rect.inflate(0, 2)
    estaba_en_el_aire = not estado.en_el_suelo
    for plat in repisas:
        if (collision_check_rect.colliderect(plat)
                and estado.prev_foot_y <= plat.top + 1):
            contacto.aterrizo = True
            contacto.aterrizo_en = "repisa"
            contacto.aterrizo_desde_el_aire = estaba_en_el_aire
            player_rect.bottom = plat.top
            estado.velocidad.y = 0.0
            estado.en_el_suelo = True
            estado.posicion.y = float(player_rect.y)
            if estado.posicion.y + estado.alto > plat.top + 4:
                estado.posicion.y = float(plat.top - estado.alto)
            break
    return contacto


def resolver_movimiento(
    estado: EstadoDeMovimiento,
    dt: float,
    solidos: list[pygame.Rect],
    repisas: list[pygame.Rect] | None = None,
    pendientes: list[Pendiente] | None = None,
    perfil: PhysicsProfile | None = None,
) -> Contacto:
    """La resolución entera, compuesta en el orden auditado.

    Es la puerta de entrada para las entidades y modos nuevos: un contexto
    que no es el jugador llama a esto una vez por fotograma y consume el
    `Contacto`. El perfil decide el comportamiento — con `modo ==
    "cenital"` no hay cuestas ni repisas que resolver (AUD-328 y AUD-129) —
    y sin perfil se asume el contexto de plataformas con los valores por
    defecto.
    """
    solidos = solidos or []
    repisas = repisas or []
    pendientes = pendientes or []
    cuestas = perfil.cuestas if perfil is not None else Cuestas()
    activas = perfil is None or perfil.modo != CENITAL

    eje_x = resolver_eje_x(estado, dt, solidos)
    eje_cuestas: Contacto | None = None
    eje_repisas: Contacto | None = None
    if activas:
        resolver_paredes_de_pendientes(
            estado, pendientes, margen=cuestas.margen_pegado)
    eje_y = resolver_eje_y(estado, dt, solidos)
    if activas:
        eje_cuestas = resolver_cuestas(estado, dt, pendientes, cuestas)
        eje_repisas = resolver_repisas(estado, repisas)

    aterrizo_en = (
        eje_y.aterrizo_en
        or (eje_cuestas.aterrizo_en if eje_cuestas else "")
        or (eje_repisas.aterrizo_en if eje_repisas else "")
    )
    return Contacto(
        posicion=estado.posicion,
        velocidad=estado.velocidad,
        en_el_suelo=estado.en_el_suelo,
        aterrizo=bool(aterrizo_en),
        aterrizo_en=aterrizo_en,
        topo=eje_y.topo,
        lado_de_pared=eje_x.lado_de_pared,
        pared_en_el_aire=eje_x.pared_en_el_aire,
        repisa_libre=eje_x.repisa_libre,
        venia_del_suelo=estado.venia_del_suelo,
    )
