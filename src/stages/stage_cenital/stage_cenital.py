"""
Module: stage_cenital
System: stage (escenario de referencia del profesor)
Academic Unit: II (vectores), IV (arquitectura)

El laboratorio de la vista cenital: tres salas, un modo de juego.

AUD-383 — por qué existe este escenario
=======================================
El motor sabe jugar desde arriba desde AUD-129. `vista=cenital` quita la
gravedad, deja el movimiento en dos ejes y trae los tres modos de cámara, con
su preset de física (`PhysicsProfile.cenital()`), sus pruebas y su
documentación.

**Ningún mapa lo declaraba.** Un modo de juego entero que el estudiante no
podía descubrir: no lo ve jugando, no lo encuentra abriendo un mapa en Tiled, y
sólo podía enterarse leyendo la especificación — que es justo lo que no se
hace. Es la misma forma de fallo que `stage_mecanicas` vino a cerrar para las
once mecánicas de la fase 5, un escalón más arriba: allí faltaban mecánicas,
aquí faltaba una **vista**.

Lo destapó AUD-378, al arreglar el punto ciego del guardián de cobertura de
TMX, que llevaba sin mirar veinte de las treinta y ocho propiedades del motor.

Qué demuestra, y qué no
------------------------
Cuatro propiedades que ningún otro mapa declara: `vista`, `camara`,
`profundidad_min` y `profundidad_max`. **No es un nivel.** Es la respuesta a
«¿cómo se hace un mapa cenital?», y por eso cabe en pantalla y media.

Tres salas porque `camara` tiene tres modos y el mapa existe para enseñarlos:
`seguir` va pegada, `zona_muerta` deja moverse sin que la cámara reaccione y
`sala` encuadra el recinto. El TMX declara `sala` y lleva los otros dos
comentados al lado, a un cambio de palabra de probarse.

Sin enemigos, a propósito: los arquetipos actuales asumen plataformas, y
mezclar esa conversación aquí convertiría «así se declara una vista cenital» en
«así se hace un nivel cenital». Lo que faltaba era lo primero.

La clase no tiene lógica propia
--------------------------------
Igual que `stage_mecanicas`, y por el mismo motivo: **todo lo que hace este
escenario está en su TMX**. Si hiciera falta código para que la vista cenital
funcione, no sería usable desde Tiled y el escenario no demostraría lo que
pretende demostrar. Un estudiante puede reproducirlo sin escribir una línea de
Python.

El mapa lo genera `tools/generate_stage_cenital.py`. Editar el `.tmx` a mano se
pierde en la siguiente regeneración.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.engine.core import settings
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class StageCenital(StageScene):
    """Escenario de referencia de la vista cenital."""

    STAGE_ID: str = "stage_cenital"
    STAGE_NAME: str = "LABORATORIO DE VISTA CENITAL"
    ZONE: int = 0

    TMX_PATH = settings.ASSETS_DIR / "maps/stage_cenital/stage_cenital.tmx"

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
