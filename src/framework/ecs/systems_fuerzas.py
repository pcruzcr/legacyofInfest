"""
Fase FUERZAS — modifican la velocidad antes de integrarla.

Extraído de `systems.py` monolítico (770 líneas) por Fase, no por mecánica.
Viento, fricción/arrastre, corriente de agua y resortes comparten fase porque
todos escriben `Velocidad` antes de que se integre a `Transform`. El orden
entre ellos importa más que la separación por mecánica.
"""
from __future__ import annotations

from src.framework.ecs.components import (
    Resorte,
    Transform,
    Velocidad,
    ZonaDeAgua,
    ZonaDeFriccion,
    ZonaDeViento,
)
from src.framework.ecs.world import World
from src.framework.physics.perfil import MATERIALES, ROCA


def sistema_resortes(mundo: World, dt: float) -> None:
    """Rebota a quien cae sobre un resorte.

    AUD-131 — corre en la fase de FUERZAS, **antes** de que el jugador
    resuelva su colisión, para que el impulso ya esté puesto cuando se
    integra. Si corriera después, el jugador aterrizaría sobre el resorte, la
    colisión le pondría la velocidad vertical a cero, y el rebote se perdería
    en el mismo fotograma en que se disparó.

    Sólo rebota quien **baja**: `v.v.y > 0`. Tocar el resorte de lado o desde
    abajo no hace nada, que es lo que el jugador espera al verlo.
    """
    for _, muelle in mundo.cada(Resorte):
        if muelle._espera > 0.0:
            muelle._espera = max(0.0, muelle._espera - dt)
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not muelle.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is None or v.v.y <= 0.0 or not muelle.listo:
                continue
            v.v.y = muelle.impulso
            muelle._espera = muelle.rearme


def sistema_viento(mundo: World, dt: float) -> None:
    """Empuja a todo lo que esté dentro de una zona de viento.

    Es aceleración y no velocidad fija a propósito. Fijar la velocidad haría
    que el viento **anulara** el movimiento del jugador —dentro de la zona daría
    igual lo que pulses—, y eso no es un obstáculo: es una pausa. Acelerando, el
    jugador puede luchar contra el viento, y esa lucha es la mecánica.
    """
    for _, zona in mundo.cada(ZonaDeViento):
        zona._t += dt
        if not zona.soplando:
            continue
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not zona.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is not None:
                v.v += zona.fuerza * dt


def sistema_friccion(mundo: World, dt: float) -> None:
    """Cambia el agarre y arrastra. Hielo, miel y cintas transportadoras.

    El arrastre se aplica **a la posición** y no a la velocidad. Si se sumara a
    la velocidad, saltar desde una cinta conservaría todo su empuje y saldrías
    disparado; sumándolo a la posición, la cinta te lleva mientras la pisas y te
    suelta al saltar, que es lo que hace Mega Man 2.

    AUD-490 — también deja el material de la zona en el dueño del `Transform`
    (`GAP-039`, la restitución por región). Se limpia **antes** de recorrer las
    zonas, en su propia pasada: quien salió de una zona de goma el fotograma
    pasado no debe seguir rebotando como si siguiera dentro, y una entidad
    puede solapar más de una zona a la vez sólo por accidente de diseño de
    nivel — la última zona que la toque manda, no la primera.

    AUD-655 — este *clear* global es intencional: el material por defecto es
    `None` → `ROCA` en el resolutor. Limpiar solo entidades que estuvieron en
    zona dejaría material pegado al salir; limpiar todas garantiza *reset*
    determinista. El coste es O(n) con n = entidades con Transform+Velocidad,
    típicamente <30, despreciable frente a físicas/colisiones.
    """
    for entidad in mundo.con(Transform, Velocidad):
        t = mundo.obtener(entidad, Transform)
        if t is not None:
            t.material_actual = None
    for _, zona in mundo.cada(ZonaDeFriccion):
        tocando_ahora: set[int] = set()
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not zona.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is None:
                continue
            tocando_ahora.add(entidad)
            if zona.inercia > 0.0:
                # AUD-522 — resbalar de verdad: la velocidad de este
                # fotograma (ya fijada por la entrada) es el objetivo, no
                # el resultado. Amortiguación exponencial acotada — mismo
                # patrón que `ChaseFlight.DRAG` (AUD-046) — así que nunca
                # se aleja del objetivo, sólo tarda en llegar.
                anterior = zona._vx_mezclada.get(entidad, v.v.x)
                objetivo = v.v.x
                tasa = zona.inercia ** dt
                mezclada = objetivo + (anterior - objetivo) * tasa
                zona._vx_mezclada[entidad] = mezclada
                v.v.x = mezclada
            elif zona.multiplicador != 1.0:
                v.v.x *= zona.multiplicador
            if zona.arrastre:
                t.posicion.x += zona.arrastre * dt
                t.rect.x = int(t.posicion.x)
            if zona.material != "roca":
                t.material_actual = MATERIALES.get(zona.material, ROCA)
        if zona.inercia > 0.0 and zona._vx_mezclada:
            # Quien ya no toca la zona deja de resbalar — sin esto, una
            # entidad que vuelve a entrar mucho después reanudaría desde
            # la velocidad con la que salió en vez de desde la de ahora.
            for entidad in list(zona._vx_mezclada):
                if entidad not in tocando_ahora:
                    del zona._vx_mezclada[entidad]


def sistema_corriente_de_agua(mundo: World, dt: float) -> None:
    """El agua frena y arrastra. La parte de nado la lleva `SwimmingState`."""
    for _, agua in mundo.cada(ZonaDeAgua):
        if agua.corriente.length_squared() == 0.0:
            continue
        for entidad in mundo.con(Transform, Velocidad):
            t = mundo.obtener(entidad, Transform)
            if t is None or not agua.rect.colliderect(t.rect):
                continue
            v = mundo.obtener(entidad, Velocidad)
            if v is not None:
                v.v += agua.corriente * dt
