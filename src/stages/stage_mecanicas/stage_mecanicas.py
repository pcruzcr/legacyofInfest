"""
Module: stage_mecanicas
System: stage (escenario de referencia del profesor)
Academic Unit: II (vectores), IV (arquitectura)

El laboratorio de mecánicas: siete salas, once mecánicas, un ejemplo de cada.

F5.13 — por qué existe este escenario
======================================
Las once mecánicas de la fase 5 estaban en el motor, probadas, documentadas y
declaradas en la guía del estudiante. **Ninguna entrega usaba una sola.**

Es la misma forma de fallo que este proyecto lleva un mes cazando —la
iluminación que no iluminaba un píxel, el nado inalcanzable, el ultimate cuyo
medidor nadie subía— sólo que un paso más allá: aquí el camino existe, está
abierto y no hay nadie andándolo.

Y la causa es conocida: nadie adopta una mecánica leyendo su tabla de
propiedades. Se adopta viéndola funcionar, abriendo el mapa en Tiled y copiando
el objeto. Este escenario es ese mapa.

Cómo está construido, y por qué así
------------------------------------
Una mecánica por sala, en un sitio donde equivocarse no mata, y la siguiente
combina con la anterior. Es lo que hace Mario 1-1 —enseñar por colocación, sin
texto— y lo que las secciones 2 y 4 del dossier del Top 200 describen en sus
193 análisis.

Entre sala y sala hay una repisa de descanso. Sin ellas, siete mecánicas
seguidas se leen como una sola cuesta arriba: son las «válvulas de escape» que
el dossier menciona en cada nivel bueno de la historia.

La clase no tiene lógica propia
--------------------------------
No sobreescribe `update` ni `draw`, y eso es deliberado: **todo lo que hace este
escenario está en su TMX**. Si hiciera falta código para que las mecánicas
funcionen, no serían usables desde Tiled y el escenario no demostraría lo que
pretende demostrar.

Un estudiante puede reproducir cualquier sala sin escribir una línea de Python.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class StageMecanicas(StageScene):
    """Escenario de referencia de las once mecánicas de la fase 5."""

    STAGE_ID: str = "stage_mecanicas"
    STAGE_NAME: str = "LABORATORIO DE MECANICAS"
    ZONE: int = 0

    TMX_PATH = settings.ASSETS_DIR / "maps/stage_mecanicas/stage_mecanicas.tmx"

    #: Qué enseña cada sala, en orden. Lo lee la prueba que comprueba que el
    #: mapa sigue conteniendo las once, para que nadie las borre sin enterarse.
    SALAS: tuple[tuple[str, str], ...] = (
        ("WindZone", "el viento empuja mientras saltas"),
        ("Conveyor", "el suelo se mueve bajo los pies"),
        ("MovingPlatform", "la plataforma te lleva encima"),
        ("RhythmBlock", "los bloques aparecen a compás"),
        ("LaserZone", "los láseres se encienden en cascada"),
        ("SinkingPlatform", "la plataforma se hunde al pisarla"),
        ("WaterZone", "bajo el agua se acaba el aire"),
        ("Guard", "el cono de visión y el estado de alerta"),
        ("Stalker", "el perseguidor al que no se puede matar"),
    )

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
