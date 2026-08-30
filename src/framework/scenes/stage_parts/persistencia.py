"""
Persistencia del escenario — banderas, diálogo y guardado.

Extraído de `senales.py` en AUD-733 sin cambiar una línea de lógica.

Por qué existe
==============
`senales.py` llegó a 441 líneas y su presupuesto es 400. El corte no es
arbitrario: las tres piezas que salen —banderas (`FLAG_SET`), diálogo
(`SHOW_DIALOGUE`) y guardado (`SAVE_REQUESTED` + `abre_con` de cerraduras)—
son el *estado que sobrevive* a la escena, no el efecto que se ve en el
fotograma. Las partículas, la sacudida y el bloom se quedan en `senales.py`,
que es lo que el jugador *ve*; aquí queda lo que el jugador *conserva*.

Es un mixin, no un colaborador, por la misma razón que los otros: las
entregas sobreescriben `_subscribe_event_handlers` y con un colaborador
dejarían de tener efecto en silencio. Ver `stage_parts/__init__.py`.
"""

from __future__ import annotations

import logging
from typing import Any

from src.engine.core.events import Events
from src.engine.core.experience import ExperienceSystem


class PersistenciaDeEscenario:
    """Banderas, diálogo y guardado del escenario.

    Espera de la escena: `context`, `context.banderas`, `context.event_bus`,
    `context.save_manager`, `_interactables`, `_dialogue`,
    `_arboles_de_dialogo`, `_stage_data`, `_vfx_handlers`.
    """

    def _suscribir_persistencia(self) -> None:
        """Suscribe banderas, diálogo, cerraduras por evento y guardado.

        Lo llama `SenalesDeEscenario._subscribe_event_handlers` al final,
        cuando ya están arriba los VFX y el sonido. El orden importa sólo
        para que `cerraduras` vea los eventos que ya existen.
        """

        def _on_flag_set(**data: Any) -> None:
            flag = str(data.get("flag", ""))
            if flag:
                self.context.banderas[flag] = True  # type: ignore[attr-defined]

        self.context.event_bus.subscribe(Events.FLAG_SET, _on_flag_set)  # type: ignore[attr-defined]
        self._vfx_handlers[Events.FLAG_SET] = _on_flag_set  # type: ignore[attr-defined]

        def _on_show_dialogue(**data: Any) -> None:
            tree_id = str(data.get("tree_id", ""))
            arbol = self._arboles_de_dialogo.get(tree_id)  # type: ignore[attr-defined]
            if arbol is None:
                if tree_id:
                    logging.getLogger(__name__).warning(
                        "diálogo: el mapa pide el árbol '%s' y no está en "
                        "data/dialogues/%s.json",
                        tree_id,
                        getattr(self._stage_data, "stage_id", "?"),  # type: ignore[attr-defined]
                    )
                return
            if not self._dialogue.active:  # type: ignore[attr-defined]
                self._dialogue.start_dialogue(arbol)  # type: ignore[attr-defined]

        self._vfx_handlers[Events.SHOW_DIALOGUE] = _on_show_dialogue  # type: ignore[attr-defined]

        # Fix reporte Guillermo 7c: cerraduras con `abre_con` por evento del mapa
        for cerradura in getattr(self._interactables, "cerraduras", []):  # type: ignore[attr-defined]
            evt = str(getattr(cerradura, "abre_con_evento", "") or "")
            if evt and evt not in self._vfx_handlers and evt not in self._sfx_handlers:  # type: ignore[attr-defined]
                def _make_opener(ev: str = evt) -> Any:
                    def _opener(**_data: Any) -> None:
                        try:
                            self._interactables.abrir_por_evento(ev)  # type: ignore[attr-defined]
                        except Exception:
                            pass
                    return _opener
                handler = _make_opener()
                self.context.event_bus.subscribe(evt, handler)  # type: ignore[attr-defined]
                self._vfx_handlers[evt] = handler  # type: ignore[attr-defined]

        def _on_save_requested(**data: Any) -> None:
            sm = self.context.save_manager  # type: ignore[attr-defined]
            if sm is not None:
                sm.auto_save(
                    stage_id=data.get("stage_id", ""),
                    stage_index=data.get("stage_index", 0),
                    checkpoint_x=data.get("checkpoint_x", 0),
                    checkpoint_y=data.get("checkpoint_y", 0),
                    health=data.get("health", 100),
                    max_health=data.get("max_health", 100),
                    zone_flags=dict(getattr(self.context, "banderas", {})),  # type: ignore[attr-defined]
                    exp_total=ExperienceSystem.get_instance().exp,
                )

        self.context.event_bus.subscribe(Events.SAVE_REQUESTED, _on_save_requested)  # type: ignore[attr-defined]
        self._vfx_handlers[Events.SAVE_REQUESTED] = _on_save_requested  # type: ignore[attr-defined]
