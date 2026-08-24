"""
Las cinemáticas del escenario: montar el director y dejarle parar el juego.

Extraído de `stage_scene.py` en AUD-290 sin cambiar una línea de lógica.

Por qué es un grupo cohesivo
============================
Los dos métodos son el sistema de escenas entero visto desde la escena: uno lo
construye a partir de lo que declaró el TMX y el otro lo corre cada fotograma y
responde a la única pregunta que el resto del juego necesita —«¿me toca estar
quieto?»—. Fuera de ellos, `StageScene` no sabe nada de guiones.

Y salen juntos por lo que comparten: `_escenas_vistas` vive en la escena y no en
el director para que sobreviva a las muertes; recargar el mapa crea un director
nuevo y sin esa memoria la introducción se repetiría en cada intento.
"""
from __future__ import annotations

import logging

from src.engine.core import settings
from src.engine.input.action_map import Action


class CinematicasDeEscenario:
    """El director de escenas, montado y conducido.

    Espera de la escena: `_cutscenes`, `_escenas_vistas`, `_player`, `_camera`,
    `_stage_data`, `_dialogue` y la entrada.
    """

    def _actualizar_escenas(self, dt: float) -> bool:
        """Corre el director. Devuelve `True` si el juego debe quedarse quieto.

        El salto se lee con CANCEL, la misma tecla con la que stage 0 lo hacía
        a mano, pero ahora saltar **ejecuta el final** del guion en vez de
        tirarlo a medias (`CutsceneScript.saltar`).
        """
        director = self._cutscenes
        if director is None or self._player is None:
            return False
        im = self.input
        saltar = bool(im is not None and im.is_action_just_pressed(Action.CANCEL))
        director.update(dt, self._player.rect, saltar=saltar)
        return bool(director.bloquea)

    def _montar_director_de_escenas(self) -> None:
        """AUD-136 (D3) — conecta las escenas del TMX con el motor.

        Antes de esto, el único escenario del proyecto que reproducía una
        cutscene era stage 0, a mano, apagando el guion desde fuera tocando un
        atributo privado. El sistema de escenas estaba escrito, probado y sin
        nadie que lo ejecutara: la novena vez este mes que aparece el mismo
        patrón —código correcto que no llega al jugador—.
        """
        from src.framework.stage.cutscene_director import CutsceneDirector
        from src.framework.stage.cutscene_guion import ContextoDeGuion

        stage = self._stage_data
        if stage is None:
            self._cutscenes = None
            return
        entidades = {
            nombre: e for e in stage.entity_list
            if (nombre := getattr(e, "name", "") or getattr(e, "entity_id", ""))
        }
        contexto = ContextoDeGuion(
            camara=self._camera,
            jugador=self._player,
            bus=self.context.event_bus,
            dialogo=self._dialogue,
            entidades=entidades,
        )
        self._cutscenes = CutsceneDirector(
            contexto,
            getattr(stage, "escenas", []),
            bus=self.context.event_bus,
            vistas=self._escenas_vistas,
        )
        if self._cutscenes.errores:
            # Los errores de guion no cancelan la escena —se ignora la línea y
            # se sigue—, pero tienen que verse: un guion que calla es un guion
            # que el estudiante da por bueno.
            registro = logging.getLogger(__name__)
            for error in self._cutscenes.errores:
                registro.warning("guion de escena en %s: %s", stage.stage_id, error)

    def _cargar_los_arboles_de_dialogo(self) -> None:
        """Lee las conversaciones del escenario de `data/dialogues/<id>.json`.

        AUD-244 — `DialogueTree.desde_datos` existe desde AUD-127, escrita para
        que un diseñador que no programa pueda escribir un diálogo en un fichero
        de datos en vez de instanciar `DialogueNode` en Python. No la llamaba
        nadie: la única forma de tener conversación seguía siendo escribirla en
        el código del escenario, que es exactamente lo que aquello quería
        evitar. `stage0` lo hace así y por eso era el único que las tenía.

        Un escenario sin fichero no es un error: la inmensa mayoría no habla.
        Un fichero ilegible **sí** se avisa, porque el diseñador lo escribió
        esperando que se leyera.
        """
        import json

        from src.framework.stage.stage_data import slug_de_stage_id
        from src.framework.ui.dialogue_system import DialogueTree

        self._arboles_de_dialogo = {}
        stage_id = str(getattr(self._stage_data, "stage_id", "") or "")
        if not stage_id:
            return
        ruta = settings.PROJECT_ROOT / "data" / "dialogues" / f"{slug_de_stage_id(stage_id)}.json"
        if not ruta.is_file():
            return
        try:
            crudo = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logging.getLogger(__name__).warning(
                "diálogo: %s no se puede leer; el escenario se juega sin "
                "conversaciones", ruta, exc_info=True)
            return

        arboles = crudo if isinstance(crudo, list) else [crudo]
        for datos in arboles:
            if not isinstance(datos, dict):
                continue
            arbol = DialogueTree.desde_datos(datos)
            if arbol.tree_id:
                self._arboles_de_dialogo[arbol.tree_id] = arbol
