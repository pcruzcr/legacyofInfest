"""El panel de pausa — AUD-555.

Qué pedía el dueño y qué había antes
======================================
"Al presionar el botón de Pausa, se abrirá un menú principal con pestañas
(tabs) inspirado en el estilo de The Legend of Zelda: Ocarina of Time, donde
el jugador podrá gestionar su equipo, revisar el árbol de habilidades y ver
el mapa general con total comodidad."

Lo que había (AUD-533/549/550) resolvía la mitad del pedido — Inventario,
Árbol de habilidades, Mapa y Tienda eran alcanzables desde la pausa — pero
como una **lista vertical** que empuja una escena nueva por cada opción:
elegir "Inventario" apilaba `InventoryScene` encima del `StageScene`
pausado, cancelar la sacaba, y se volvía a ver la lista. Cuatro pantallas
separadas, no un panel con pestañas.

Cómo se resuelve sin reescribir las cuatro pantallas
=======================================================
`InventoryScene`, `SkillTreeScene` y `WorldMapScene` (de sólo lectura,
AUD-549) ya están completas, probadas y usadas también desde el título —
reescribirlas arriesgaría esos otros caminos por ganar una presentación
distinta. En vez de eso, este panel las **embebe por composición**:
construye una instancia de cada una y llama a su `update()`/`draw()`
directamente, con una tira de pestañas propia por encima que decide cuál
está activa.

El obstáculo real de embeber así: las tres cancelan con
`self.context.scene_manager.pop()`, que asume ser el tope de la pila. Aquí
nunca lo son — el tope sigue siendo el `StageScene` pausado, que las dibuja
y actualiza a mano. Por eso las tres ganaron un parámetro `standalone`
(`False` aquí): con él en `False`, Cancelar no hace nada dentro de la
pestaña, y es este panel quien decide qué significa Cancelar — cerrar el
panel entero, sea cual sea la pestaña activa, que es como cancela Ocarina
of Time.

La Tienda queda fuera del anillo de pestañas a propósito: tiene una
interacción propia de comprar/vender que no es "consultar", como las otras
tres, y el pedido no la menciona junto a "equipo, habilidades, mapa". Vive
en una cuarta pestaña, "Menú", como una lista corta junto a Guardar y
salir / Salir al título — al elegir Tienda desde ahí se empuja `ShopScene`
de siempre (AUD-550), sin cambios.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.engine.core.events import Events
from src.engine.input.action_map import Action

if TYPE_CHECKING:
    from src.engine.scene.base_scene import BaseScene


class PausaDeEscenario:
    """Espera de la escena: `_paused`, `input`, `context`, `_dt`,
    `_abrir_tienda`, `_save_and_quit`, `_quit_to_title`,
    `_set_paused_side_effects`. No instanciar solo: ver
    `stage_parts/__init__.py`."""

    #: Las tres primeras son paneles de consulta embebidos; la cuarta es
    #: una lista de acciones (comprar, guardar, salir).
    PESTANAS_DE_PAUSA: tuple[str, ...] = (
        "Equipo", "Habilidades", "Mapa", "Menú",
    )
    OPCIONES_DEL_MENU_DE_PAUSA: tuple[str, ...] = (
        "Tienda", "Guardar y salir", "Salir al título",
    )

    def _abrir_panel_de_pausa(self) -> None:
        """Construye las tres pestañas frescas cada vez que se pausa: el
        saldo, el inventario o el progreso del mapa pueden haber cambiado
        desde la última pausa, y una instancia vieja los mostraría
        atrasados."""
        from src.engine.scenes.inventory_scene import InventoryScene
        from src.engine.scenes.skill_tree_scene import SkillTreeScene
        from src.engine.scenes.world_map_scene import WorldMapScene

        self._pausa_tab: int = 0
        self._pausa_menu_seleccion: int = 0
        self._pausa_equipo: BaseScene = InventoryScene(
            self.context, standalone=False)
        self._pausa_habilidades: BaseScene = SkillTreeScene(
            self.context, standalone=False)
        self._pausa_mapa: BaseScene = WorldMapScene(
            self.context, permitir_viajar=False, standalone=False)
        # `on_enter()` de las tres es lo que carga sus datos (el mapa lee
        # la partida guardada y construye sus nodos ahí, no en `__init__`)
        # — sin esto la pestaña "Mapa" se abriría vacía. El fundido que
        # también dispara es inofensivo: `TransitionManager.start_fade_in`
        # sólo reinicia su propio temporizador, así que las tres llamadas
        # seguidas no se pisan.
        for pestana in (self._pausa_equipo, self._pausa_habilidades, self._pausa_mapa):
            pestana.awake()
            pestana.start()
            pestana.on_enter()

    def _cerrar_panel_de_pausa(self) -> None:
        for pestana in (
            getattr(self, "_pausa_equipo", None),
            getattr(self, "_pausa_habilidades", None),
            getattr(self, "_pausa_mapa", None),
        ):
            if pestana is not None:
                pestana.on_exit()
                pestana.destroy()
        self._pausa_equipo = None
        self._pausa_habilidades = None
        self._pausa_mapa = None

    def _pestana_de_consulta_activa(self) -> BaseScene | None:
        """La pestaña embebida activa, o `None` en la pestaña "Menú"
        (índice 3), que no es una de las tres consultas."""
        tab = getattr(self, "_pausa_tab", 0)
        if tab >= 3:
            return None
        return (self._pausa_equipo, self._pausa_habilidades, self._pausa_mapa)[tab]

    def _handle_pause_input(self) -> None:
        im = self.input
        if im is None:
            return
        if im.is_action_just_pressed(Action.CANCEL):
            # Cierra el panel entero sea cual sea la pestaña activa — así
            # cancela Ocarina of Time: un botón, no uno por pestaña.
            self._paused = False
            self._set_paused_side_effects(False)
            self._cerrar_panel_de_pausa()
            return
        if im.is_action_just_pressed(Action.TAB_NEXT):
            self._pausa_tab = (self._pausa_tab + 1) % len(self.PESTANAS_DE_PAUSA)
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
            return
        if im.is_action_just_pressed(Action.TAB_PREV):
            self._pausa_tab = (self._pausa_tab - 1) % len(self.PESTANAS_DE_PAUSA)
            self.context.event_bus.emit(Events.SFX_MENU_HOVER)
            return
        if self._pausa_tab == 3:
            self._actualizar_menu_de_pausa(im)
            return
        pestana = self._pestana_de_consulta_activa()
        if pestana is not None:
            pestana.update(self._dt)

    def _actualizar_menu_de_pausa(self, im: Any) -> None:
        opciones = self.OPCIONES_DEL_MENU_DE_PAUSA
        if im.is_action_just_pressed(Action.MOVE_DOWN):
            self._pausa_menu_seleccion = (self._pausa_menu_seleccion + 1) % len(opciones)
        if im.is_action_just_pressed(Action.MOVE_UP):
            self._pausa_menu_seleccion = (self._pausa_menu_seleccion - 1) % len(opciones)
        if im.is_action_just_pressed(Action.CONFIRM):
            opcion = opciones[self._pausa_menu_seleccion]
            if opcion == "Tienda":
                # AUD-550 — sin cambios: la Tienda sigue empujándose como
                # una escena aparte, no embebida como las otras tres.
                self._abrir_tienda()
            elif opcion == "Guardar y salir":
                self._save_and_quit()
            elif opcion == "Salir al título":
                self._quit_to_title()
