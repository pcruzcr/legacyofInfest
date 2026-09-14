"""Objetivos declarados en el mapa, y su seguimiento — AUD-400. Cierra GAP-047.

Qué no había
============
`GAP-047` lo dice con una búsqueda: cero coincidencias de `mision`, `objective`
o `quest` en `src/`. `progression_system.py` lleva el avance **entre**
escenarios y las banderas de zona en la partida, que es otra cosa: no había
objetivos declarados, ni seguimiento, ni estado de completado por objetivo.

El hueco estaba parado por decisión del dueño —la fase 7, reconstrucción de
contenido, estaba suspendida (`docs/87` §27)—. El dueño la levantó el
2026-08-11 y pidió cerrarlo.

Cómo encaja con lo que ya existe
================================
Casi todo el trabajo estaba hecho y disperso, que es el motivo de que esto sean
pocas líneas:

* El **bus de eventos** ya emite lo que hay que contar: `ENEMY_DIED`,
  `ITEM_COLLECTED`, `FLAG_SET`, `CHECKPOINT_REACHED`, `DIALOGUE_FINISHED`.
* El **diálogo** ya ejecuta acciones (`DialogueSystem._execute_action`), así que
  un guion puede completar un objetivo sin que haya que inventar un enganche.
* El **TMX** ya sabe declarar objetos con propiedades.

Lo que faltaba era quién lleva la cuenta. Esto no inventa fuentes de verdad
nuevas: escucha las que ya hay.

Por qué el sistema se suscribe y no pregunta
============================================
El bus guarda referencias **débiles**, así que quien se suscribe tiene que
seguir vivo. `StageScene` guarda el sistema durante toda la escena, que es
exactamente lo que dura un objetivo: al cambiar de mapa se construye otro, como
con el mundo ECS.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.engine.core.events import Events

logger = logging.getLogger(__name__)

__all__ = ["TIPOS_DE_OBJETIVO", "Objetivo", "SistemaDeObjetivos"]

#: Qué se puede pedir, y de qué evento se entera cada uno.
#:
#: Son cinco y no veinte a propósito: cada tipo tiene que corresponder a algo
#: que el motor **ya emite**. Un tipo que no se pueda contar con los eventos
#: existentes sería un objetivo que nunca se completa, y un objetivo que no se
#: puede terminar es peor que no tener objetivos.
TIPOS_DE_OBJETIVO: dict[str, str] = {
    "derrotar": Events.ENEMY_DIED,
    "recoger": Events.ITEM_COLLECTED,
    "bandera": Events.FLAG_SET,
    "hablar": Events.DIALOGUE_FINISHED,
    "llegar": Events.CHECKPOINT_REACHED,
}


@dataclass
class Objetivo:
    """Una cosa que el jugador tiene que hacer.

    `objetivo` es contra qué se compara lo que trae el evento: el `enemy_type`
    que murió, el `item_id` recogido, la bandera puesta. **Vacío significa
    «cualquiera»**, que es lo que hace que «derrota a cinco enemigos» se pueda
    escribir sin enumerar especies.
    """

    id: str
    texto: str
    tipo: str
    objetivo: str = ""
    cantidad: int = 1
    #: Un objetivo opcional no impide terminar el nivel. Es la diferencia entre
    #: la misión y el coleccionable, y sin ella todo secreto se vuelve
    #: obligatorio.
    opcional: bool = False
    progreso: int = 0
    #: Se marca a mano con `completar()` — lo usan el guion de diálogo y el
    #: código de escenario. Separado del progreso para que un objetivo se pueda
    #: dar por bueno sin fingir un recuento.
    forzado: bool = False

    @property
    def completado(self) -> bool:
        return self.forzado or self.progreso >= self.cantidad

    @property
    def restante(self) -> int:
        return max(0, self.cantidad - self.progreso)

    def describir(self) -> str:
        """Cómo se lee en el HUD."""
        marca = "[x]" if self.completado else "[ ]"
        if self.cantidad > 1 and not self.forzado:
            return f"{marca} {self.texto} ({min(self.progreso, self.cantidad)}/{self.cantidad})"
        return f"{marca} {self.texto}"


class SistemaDeObjetivos:
    """Lleva la cuenta de los objetivos de un escenario.

    Se suscribe a los eventos que ya emite el juego y avanza lo que
    corresponda. No decide nada del nivel: cuando todo lo obligatorio está
    hecho lo **anuncia**, y quien quiera actuar sobre eso —abrir una puerta,
    permitir la salida— lo escucha. La misma división que `Contacto` en la
    física: hechos, no reglas.
    """

    def __init__(self, bus: Any = None) -> None:
        self._objetivos: dict[str, Objetivo] = {}
        self._bus = bus
        self._anunciado = False
        if bus is not None:
            # Un manejador por tipo de evento, todos apuntando al mismo sitio.
            # Se guardan en el objeto porque el bus tiene referencias débiles:
            # una lambda suelta se recogería antes del primer disparo.
            for evento in set(TIPOS_DE_OBJETIVO.values()):
                bus.subscribe(evento, self._al_ocurrir)
            # AUD-OBJ: tambien escuchar recogidas por InteractableSystem
            # (EVENTO_RECOGIDO) que emite item_id pero no ITEM_COLLECTED.
            try:
                from src.framework.stage.interactable_system import EVENTO_RECOGIDO
                bus.subscribe(EVENTO_RECOGIDO, self._al_ocurrir)
            except Exception:
                pass
            # La entrada por guion: `complete_objective:` desde un diálogo.
            bus.subscribe(Events.OBJECTIVE_REQUESTED, self._al_pedir)

    # -- alta -------------------------------------------------------
    def declarar(self, objetivo: Objetivo) -> None:
        """Da de alta un objetivo. Repetir el id reemplaza."""
        if objetivo.tipo not in TIPOS_DE_OBJETIVO:
            logger.warning(
                "SistemaDeObjetivos: tipo %r desconocido en el objetivo %r — se "
                "ignora. Válidos: %s",
                objetivo.tipo, objetivo.id, ", ".join(sorted(TIPOS_DE_OBJETIVO)),
            )
            return
        self._objetivos[objetivo.id] = objetivo

    # -- avance -----------------------------------------------------
    def _al_ocurrir(self, **datos: Any) -> None:
        """Un evento del juego. Avanza los objetivos a los que le corresponda.

        El bus no dice qué evento fue, así que se mira por lo que trae: cada
        tipo de objetivo sabe de qué clave suya se entera. Es menos elegante
        que un manejador por evento y evita el problema que lo haría necesario
        —cinco métodos casi idénticos que hay que acordarse de mantener a la
        vez—.

        AUD-OBJ: `derrotar` acepta tanto `enemy_type` (sintetico/tests) como
        `entity_id` (EnemyBase._die real) usando _tipo_de; `recoger` acepta
        `item_id` de cualquier evento (ITEM_COLLECTED o INTERACT_ITEM_PICKED).
        """
        for objetivo in self._objetivos.values():
            if objetivo.completado:
                continue
            # Caso especial derrotar: puede venir como entity_id y se deriva tipo
            if objetivo.tipo == "derrotar":
                valor = ""
                if "enemy_type" in datos:
                    valor = str(datos.get("enemy_type", ""))
                elif "entity_id" in datos:
                    try:
                        from src.engine.core.score_system import _tipo_de
                        valor = _tipo_de(str(datos.get("entity_id", "")))
                    except Exception:
                        valor = str(datos.get("entity_id", ""))
                else:
                    continue
                # Si objetivo vacio cuenta cualquiera, si no comparar case-insensitive
                eid_raw = str(datos.get("entity_id", ""))
                if (objetivo.objetivo
                        and objetivo.objetivo.lower() != valor.lower()
                        and objetivo.objetivo != eid_raw):
                    # tambien aceptar substring para compatibilidad (boss)
                    low_obj = objetivo.objetivo.lower()
                    low_val = valor.lower()
                    if low_obj not in low_val and low_val not in low_obj:
                        # comparar contra entity_id raw tambien
                        raw = eid_raw.lower()
                        if low_obj not in raw:
                            continue
                self.avanzar(objetivo.id)
                continue
            clave = _CLAVE_DEL_TIPO.get(objetivo.tipo, "")
            if clave not in datos:
                continue
            valor = str(datos.get(clave, ""))
            if objetivo.objetivo and objetivo.objetivo != valor:
                # para recoger permitir match parcial case-insensitive?
                if objetivo.objetivo.lower() != valor.lower():
                    continue
            self.avanzar(objetivo.id)

    def _al_pedir(self, objective_id: str = "", **_: Any) -> None:
        """`complete_objective:` desde un guion de diálogo."""
        if objective_id:
            self.completar(objective_id)

    def avanzar(self, id_objetivo: str, cuanto: int = 1) -> None:
        objetivo = self._objetivos.get(id_objetivo)
        if objetivo is None or objetivo.completado:
            return
        objetivo.progreso += cuanto
        if objetivo.completado:
            self._anunciar_uno(objetivo)

    def completar(self, id_objetivo: str) -> None:
        """Lo da por hecho sin contar. Lo usa `complete_objective:` del guion."""
        objetivo = self._objetivos.get(id_objetivo)
        if objetivo is None or objetivo.completado:
            return
        objetivo.forzado = True
        self._anunciar_uno(objetivo)

    def _anunciar_uno(self, objetivo: Objetivo) -> None:
        if self._bus is not None:
            self._bus.emit(Events.OBJECTIVE_COMPLETED,
                           objective_id=objetivo.id, text=objetivo.texto)
        if self.todo_hecho and not self._anunciado:
            self._anunciado = True
            if self._bus is not None:
                self._bus.emit(Events.OBJECTIVES_COMPLETED)

    # -- lectura ----------------------------------------------------
    @property
    def objetivos(self) -> list[Objetivo]:
        return list(self._objetivos.values())

    @property
    def pendientes(self) -> list[Objetivo]:
        return [o for o in self._objetivos.values() if not o.completado]

    @property
    def todo_hecho(self) -> bool:
        """¿Están hechos todos los **obligatorios**?

        Los opcionales no cuentan, y por eso existen: si contaran, cada secreto
        del mapa bloquearía el final del nivel. Sin ningún objetivo declarado
        devuelve `True` — un mapa que no pide nada no tiene nada pendiente, que
        es lo que mantiene intactos los mapas que no declaran objetivos.
        """
        return all(o.completado for o in self._objetivos.values() if not o.opcional)

    def resumen(self) -> list[str]:
        """Las líneas para el HUD, obligatorios primero."""
        ordenados = sorted(self._objetivos.values(), key=lambda o: (o.opcional, o.id))
        return [o.describir() for o in ordenados]

    def reiniciar(self) -> None:
        """Vuelve a empezar. Lo llama el respawn, como el resto del escenario."""
        for objetivo in self._objetivos.values():
            objetivo.progreso = 0
            objetivo.forzado = False
        self._anunciado = False


#: De qué clave del evento se entera cada tipo. Va aparte de
#: `TIPOS_DE_OBJETIVO` porque son dos cosas distintas —qué evento escucho y qué
#: campo suyo comparo— y juntarlas en una tupla haría el diccionario ilegible.
_CLAVE_DEL_TIPO: dict[str, str] = {
    "derrotar": "enemy_type",
    "recoger": "item_id",
    "bandera": "flag",
    "hablar": "tree_id",
    "llegar": "checkpoint_id",
}


def objetivo_desde_tiled(props: dict[str, Any], nombre: str = "") -> Objetivo | None:
    """Construye un `Objetivo` desde las propiedades de un objeto de Tiled.

    Devuelve `None` y avisa si le falta lo imprescindible, en vez de construir
    un objetivo a medias: uno sin `id` no se puede completar desde un guion, y
    uno sin texto sale en blanco en el HUD. Es el mismo trato que el resto del
    cargador da al dato incompleto — se queja y sigue, no revienta el nivel.
    """
    id_objetivo = str(props.get("objective_id") or nombre or "").strip()
    texto = str(props.get("text") or "").strip()
    if not id_objetivo or not texto:
        logger.warning(
            "StageLoader: objetivo sin 'objective_id' o sin 'text' — se ignora "
            "(id=%r, text=%r)", id_objetivo, texto,
        )
        return None
    tipo = str(props.get("kind") or "bandera").strip().lower()
    try:
        cantidad = max(1, int(props.get("count", 1)))
    except (TypeError, ValueError):
        cantidad = 1
    return Objetivo(
        id=id_objetivo,
        texto=texto,
        tipo=tipo,
        objetivo=str(props.get("target") or "").strip(),
        cantidad=cantidad,
        opcional=str(props.get("optional", "")).strip().lower() in ("true", "1"),
    )
