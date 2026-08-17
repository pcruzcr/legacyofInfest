"""Banco de calibración del salto: cuántas baldosas cruza el jugador de verdad.

Por qué medir algo que ya hay una fórmula para calcular (AUD-204, AUD-504)
----------------------------------------------------------------------------
`src/framework/stage/level_metrics.py` deriva la envolvente de salto
integrando la misma física a paso fijo que usa `Player._apply_physics`
(Euler semi-implícito, ``dt = 1/60``), no la fórmula continua del proyectil
(``v²/2g``). Con eso califica los huecos de los mapas de los estudiantes y
decide si un nivel es transitable.

Aun así sigue siendo un modelo, no el jugador. El jugador tiene estados, corta
el salto si sueltas el botón, cambia de velocidad horizontal al despegar y
resuelve colisiones por ejes con rectángulos enteros. Ninguna de esas cosas
aparece en la integración aislada, y todas mueven el resultado — por eso este
banco sigue existiendo después de AUD-504: la fórmula corregida se acerca
mucho más a lo medido, pero "se acerca" no es "es".

Este banco no calcula: **ejecuta**. Construye un hueco de N baldosas, pone al
`Player` real encima con el `InputManager` de prueba, y prueba a saltarlo desde
cada píxel del tramo de despegue. Lo que devuelve no es una predicción sino un
recuento: de cuántas posiciones de despegue se cruza el hueco, y desde cuántas
no.

Qué NO hace
-----------
No toca la física ni propone tocarla. `GRAVITY` y `PLAYER_JUMP_FORCE` recalibran
los 17 mapas de golpe y afectan a entregas ya calificadas, así que cambiarlas es
una decisión de diseño con coste académico, no un ajuste. Este módulo sólo pone
el número encima de la mesa para que esa decisión se tome con un dato medido.

Las dos técnicas
----------------
Se mide con dos formas de jugar porque el motor las trata distinto, y la
diferencia no es pequeña:

* **natural** — se mantiene la dirección pulsada durante todo el vuelo. Es lo
  que hace cualquiera que no se haya leído el código.
* **experta** — se suelta la dirección al despegar. `AirborneState` sólo escribe
  ``velocity.x`` cuando ``move_x != 0`` (`states/airborne.py`), así que soltar
  la tecla **conserva** la velocidad del suelo (90 px/s) en lugar de bajar a la
  aérea (45 px/s). Es contraintuitivo —soltar el mando te lleva más lejos— pero
  es lo que hace el motor.

El botón de salto se mantiene pulsado en ambas: soltarlo activa el corte de
salto (``velocity.y *= 0.5``) y recorta el arco.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.framework.entities.player import Player
from tests.playtest.bot import _StubInput

#: Paso de simulación. Fijo a propósito: el banco mide diseño de nivel, no
#: comportamiento bajo carga, y un dt variable metería ruido en la medida.
DT: float = 1.0 / 60.0

#: Tope de fotogramas por intento. A 60 fps son 10 s, de sobra para un salto de
#: 0,95 s más la carrerilla; si un intento llega aquí es que el jugador se quedó
#: atascado y el intento cuenta como fallido.
_MAX_FOTOGRAMAS: int = 600

_ALTO_JUGADOR: int = 32
_ANCHO_JUGADOR: int = 20

_SUELO_Y: int = 300
_BORDE_X: int = 320
_INICIO_X: float = 100.0

#: Tramo de despegue que se barre, en píxeles desde el borde del vacío. Empieza
#: en negativo para incluir los saltos lanzados **después** de pisar el aire:
#: `PLAYER_COYOTE_FRAMES` los permite y son parte legítima de la técnica.
_DESPEGUE_MIN: int = -8
_DESPEGUE_MAX: int = 40


@dataclass(frozen=True)
class Medicion:
    """Resultado de barrer un obstáculo desde todas las posiciones de despegue."""

    baldosas: int
    ancho_px: int
    despegues_validos: int
    despegues_probados: int

    @property
    def superable(self) -> bool:
        return self.despegues_validos > 0

    @property
    def margen(self) -> float:
        """Fracción del tramo de despegue desde la que sale bien (0-1).

        Es el número que de verdad importa para diseñar un nivel. Un hueco que
        sólo se cruza desde el 8 % de las posiciones es *técnicamente* posible y
        en la práctica es un muro: el jugador lo intentará doce veces y
        concluirá que el juego está roto. «Superable» y «justo» no son lo mismo,
        y una sola columna de sí/no los confunde.
        """
        if not self.despegues_probados:
            return 0.0
        return self.despegues_validos / self.despegues_probados


def _jugador_en_suelo(y_suelo: int) -> Player:
    jugador = Player(pygame.Vector2(_INICIO_X, float(y_suelo - _ALTO_JUGADOR)))
    jugador.is_grounded = True
    return jugador


def _intento(
    rects: list[pygame.Rect],
    despegue_px: int,
    *,
    soltar_direccion: bool,
    exito,
    y_muerte: float,
) -> bool:
    """Una carrerilla y un salto. True si `exito(jugador)` se cumple."""
    jugador = _jugador_en_suelo(_SUELO_Y)
    mando = _StubInput()
    saltado = False
    en_vuelo = False

    for _ in range(_MAX_FOTOGRAMAS):
        pulsadas: set[Action] = set()
        if not saltado:
            pulsadas.add(Action.MOVE_RIGHT)
            distancia = _BORDE_X - (jugador.position.x + _ANCHO_JUGADOR)
            if distancia <= despegue_px:
                pulsadas.add(Action.JUMP)
                saltado = True
        else:
            # Mantener saltar: soltarlo dispara el corte de salto y acorta
            # el arco, que es una técnica distinta y no la que se mide aquí.
            pulsadas.add(Action.JUMP)
            if not soltar_direccion:
                pulsadas.add(Action.MOVE_RIGHT)

        mando.set_actions(pulsadas)
        jugador.update(DT, rects, mando)

        if jugador.position.y > y_muerte:
            return False

        # El veredicto se emite al **aterrizar**, no al agotar el reloj. Sin
        # esto, un salto que vuelve a caer en la plataforma de salida seguía
        # simulando 600 fotogramas de un jugador quieto: el barrido completo
        # costaba 17 s y casi todo era eso.
        if saltado:
            if not jugador.is_grounded:
                en_vuelo = True
            elif en_vuelo:
                return exito(jugador)

    return False


def medir_hueco(baldosas: int, *, soltar_direccion: bool = False) -> Medicion:
    """¿Se cruza un vacío de `baldosas` baldosas, y desde cuántos despegues?"""
    ancho = baldosas * settings.TILE_SIZE
    rects = [
        pygame.Rect(0, _SUELO_Y, _BORDE_X, 64),
        pygame.Rect(_BORDE_X + ancho, _SUELO_Y, 400, 64),
    ]
    validos = sum(
        _intento(
            rects,
            despegue,
            soltar_direccion=soltar_direccion,
            exito=lambda j: j.position.x > _BORDE_X,
            y_muerte=_SUELO_Y + 80,
        )
        for despegue in range(_DESPEGUE_MIN, _DESPEGUE_MAX + 1)
    )
    return Medicion(
        baldosas=baldosas,
        ancho_px=ancho,
        despegues_validos=validos,
        despegues_probados=_DESPEGUE_MAX - _DESPEGUE_MIN + 1,
    )


def medir_repecho(baldosas: int, *, soltar_direccion: bool = False) -> Medicion:
    """¿Se sube un escalón de `baldosas` baldosas de alto?"""
    alto = baldosas * settings.TILE_SIZE
    cima = _SUELO_Y - alto
    rects = [
        pygame.Rect(0, _SUELO_Y, _BORDE_X, 64),
        pygame.Rect(_BORDE_X, cima, 400, 64 + alto),
    ]
    validos = sum(
        _intento(
            rects,
            despegue,
            soltar_direccion=soltar_direccion,
            # Subido = los pies quedan a la altura de la cima. El +1 absorbe el
            # redondeo a entero del rect de colisión.
            exito=lambda j: j.position.y + _ALTO_JUGADOR <= cima + 1,
            y_muerte=_SUELO_Y + 80,
        )
        for despegue in range(_DESPEGUE_MIN, _DESPEGUE_MAX + 1)
    )
    return Medicion(
        baldosas=baldosas,
        ancho_px=alto,
        despegues_validos=validos,
        despegues_probados=_DESPEGUE_MAX - _DESPEGUE_MIN + 1,
    )


def barrido_huecos(
    maximo: int = 12, *, soltar_direccion: bool = False,
) -> list[Medicion]:
    return [
        medir_hueco(n, soltar_direccion=soltar_direccion)
        for n in range(1, maximo + 1)
    ]


def barrido_repechos(maximo: int = 8) -> list[Medicion]:
    return [medir_repecho(n) for n in range(1, maximo + 1)]


def maximo_superable(mediciones: list[Medicion]) -> int:
    """La mayor talla superable. 0 si ninguna lo es."""
    superables = [m.baldosas for m in mediciones if m.superable]
    return max(superables) if superables else 0


def tabla() -> str:
    """El informe que se lee a ojo, para pegarlo en una auditoría."""
    from src.framework.stage.level_metrics import JumpEnvelope

    env = JumpEnvelope.from_settings()
    tile = settings.TILE_SIZE
    lineas = [
        "Calibración del salto — medido sobre el Player real, no calculado",
        "",
        f"  GRAVITY={settings.GRAVITY}  PLAYER_JUMP_FORCE={settings.PLAYER_JUMP_FORCE}"
        f"  PLAYER_WALK_SPEED={settings.PLAYER_WALK_SPEED}",
        f"  envolvente calculada: hueco natural {env.max_gap:.1f}px"
        f" ({env.max_gap / tile:.2f} bald.)"
        f", hueco experto {env.max_gap_expert:.1f}px"
        f" ({env.max_gap_expert / tile:.2f} bald.)"
        f", repecho {env.max_height:.1f}px ({env.max_height / tile:.2f} bald.)",
        "",
        "  HUECOS            natural            experta",
        "  bald.  px    despegues  margen   despegues  margen",
    ]
    for nat, exp in zip(
        barrido_huecos(), barrido_huecos(soltar_direccion=True), strict=True,
    ):
        lineas.append(
            f"  {nat.baldosas:5d} {nat.ancho_px:4d}"
            f"   {nat.despegues_validos:4d}/{nat.despegues_probados:<3d}"
            f" {nat.margen:6.0%}"
            f"    {exp.despegues_validos:4d}/{exp.despegues_probados:<3d}"
            f" {exp.margen:6.0%}"
        )

    lineas += ["", "  REPECHOS", "  bald.  px    despegues  margen"]
    for med in barrido_repechos():
        lineas.append(
            f"  {med.baldosas:5d} {med.ancho_px:4d}"
            f"   {med.despegues_validos:4d}/{med.despegues_probados:<3d}"
            f" {med.margen:6.0%}"
        )
    return "\n".join(lineas)


if __name__ == "__main__":  # pragma: no cover - herramienta de línea de órdenes
    import os

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    pygame.init()
    print(tabla())
