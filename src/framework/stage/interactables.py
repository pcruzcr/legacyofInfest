"""
Objetos con los que el jugador interactúa: recogibles, cerraduras, cofres y disparadores.

F4.1 — de dónde sale esto
=========================
Petición literal de los estudiantes tras jugar la fase 1: *«si se podía agarrar
objetos y llevar[los], abrir jaulas o puertas, además de abrir cofres
misteriosos o activar eventos»*.

El motor ya tenía un `Inventory` con seis mejoras permanentes —vasija de
corazón, pluma veloz— pero **nada recogible en el mapa**: no había forma de
poner un objeto en Tiled y que el jugador lo cogiera. Tampoco había puertas,
ni cofres, ni manera de disparar un evento desde el escenario.

Qué se añade, y por qué estas cuatro cosas
-------------------------------------------
Son las cuatro piezas mínimas con las que se puede construir cualquier
puzle de llave y puerta, que es el patrón que pedían:

- `Recogible` — algo que se coge al pasar por encima o con el botón de agarrar.
- `Cerradura` — puerta o jaula que se abre con una llave concreta.
- `Cofre` — se abre con el botón y entrega su contenido una sola vez.
- `Disparador` — emite un evento del bus; el escenario decide qué significa.

Deliberadamente **no** se añade un sistema de diálogo, ni de comercio, ni de
crafteo. Cada uno de esos exige interfaz propia y ninguno hace falta para lo
que se pidió.

Dónde vive el estado
--------------------
Aquí sólo hay datos y reglas. Ni se dibuja ni se leen teclas: eso lo hace
`InteractableSystem`, que la escena actualiza. La razón es la de siempre en
este proyecto —que el estudiante pueda leer estas reglas sin pelearse con
pygame— y una práctica: así se pueden probar sin abrir una ventana.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from src.framework.entities.player import Player

#: Distancia, en píxeles, a la que el jugador puede accionar algo con el botón
#: de agarrar. Generosa a propósito: obligar a la precisión de un píxel para
#: abrir una puerta no añade dificultad, añade frustración.
ALCANCE_DE_USO: int = 24


@dataclass
class Recogible:
    """Un objeto en el suelo. Al cogerlo entra en el llavero o en el inventario.

    `item_id` es libre: `"llave_roja"`, `"heart_vessel"`, `"tuerca"`. Si
    coincide con un objeto de `engine.core.inventory` se aplica su efecto; si
    no, se guarda como llave, que es lo que hace útil el sistema sin obligar
    al estudiante a registrar nada en Python.
    """

    rect: pygame.Rect
    item_id: str
    #: Con `False` hay que pulsar el botón de agarrar. Con `True` basta pasar
    #: por encima, que es lo natural para monedas y objetos menores.
    automatico: bool = True
    #: Texto que se muestra al recogerlo. Vacío = el motor compone uno.
    mensaje: str = ""
    #: Cuántas unidades entrega (AUD-218). Con `1` —lo de siempre— nada cambia
    #: para las entregas existentes. Sirve para una bolsa de monedas sin tener
    #: que poner veinte objetos en el suelo, que es como suelta el botín un
    #: enemigo al morir.
    cantidad: int = 1
    recogido: bool = False


@dataclass
class Cerradura:
    """Puerta o jaula. Se abre con `key_id` y deja de bloquear el paso.

    Mientras está cerrada, su rectángulo es sólido: el jugador choca. Al
    abrirse deja de estarlo, y ahí está toda la mecánica.

    `consume_llave` decide si la llave desaparece al usarse. Por defecto no:
    una llave que se gasta obliga al estudiante a contar cuántas puso, y el
    fallo típico —dejar una puerta imposible— no se ve hasta que alguien juega
    el nivel entero.
    """

    rect: pygame.Rect
    key_id: str
    #: `"puerta"` o `"jaula"`. Sólo cambia el mensaje y el color; se separan
    #: porque una jaula suele contener algo y una puerta da paso.
    clase: str = "puerta"
    consume_llave: bool = False
    mensaje_bloqueado: str = ""
    abierta: bool = False
    #: Evento del bus que se emite al abrirla, si el escenario quiere reaccionar.
    evento_al_abrir: str = ""

    # ── AUD-132 — interruptores y puertas que se cierran solas ──
    #
    # `Disparador` emitía su evento al bus y **nadie escuchaba**. Un estudiante
    # podía poner un interruptor en Tiled, verlo funcionar en el registro, y no
    # conseguir que abriera nada sin escribir Python. La pieza que faltaba era
    # el receptor, y el receptor natural es la propia cerradura.
    #
    #: Nombre de evento que abre esta cerradura sin llave. El mismo que se
    #: escribe en el `EventTrigger`, y con eso queda el circuito completo:
    #: interruptor -> bus -> puerta, sin una línea de código.
    abre_con_evento: str = ""
    #: Segundos que permanece abierta antes de cerrarse sola. `0` = para
    #: siempre. Es lo que convierte un interruptor en una carrera contra el
    #: tiempo, que es el 90 % de lo que se hace con un interruptor.
    cierra_en: float = 0.0
    _cierre: float = 0.0

    #: AUD-635 — skill_id requerido para abrir la cerradura.
    requires_skill: str = ""

    def abrir(self, temporal: bool = True) -> None:
        """Abre la cerradura y arranca el temporizador si lo tiene."""
        self.abierta = True
        self._cierre = self.cierra_en if (temporal and self.cierra_en > 0.0) else 0.0

    def avanzar(self, dt: float) -> bool:
        """Un fotograma del temporizador. Devuelve `True` si se acaba de cerrar.

        Cerrar con el jugador dentro sería aplastarlo contra la geometría, así
        que el llamante comprueba el solapamiento antes de hacer caso. Aquí
        sólo se cuenta el tiempo: la decisión es del sistema, que es quien
        sabe dónde está el jugador.
        """
        if not self.abierta or self._cierre <= 0.0:
            return False
        self._cierre -= dt
        if self._cierre > 0.0:
            return False
        self._cierre = 0.0
        self.abierta = False
        return True


@dataclass
class Cofre:
    """Se abre con el botón de agarrar y entrega su contenido una sola vez."""

    rect: pygame.Rect
    contenido: str = ""
    #: Si no está vacío, hace falta esta llave para abrirlo.
    key_id: str = ""
    mensaje: str = ""
    abierto: bool = False
    evento_al_abrir: str = ""


@dataclass
class Disparador:
    """Emite un evento del bus. El escenario decide qué significa.

    Es la pieza que convierte el resto en un sistema abierto: un estudiante
    puede poner un `Disparador` con `evento="ABRIR_COMPUERTA"` y escuchar ese
    nombre desde su escena sin tocar el motor.
    """

    rect: pygame.Rect
    evento: str
    #: Con `True` se dispara al entrar; con `False`, al pulsar el botón.
    automatico: bool = True
    una_vez: bool = True
    #: Si no está vacío, hace falta esta llave para activarlo.
    key_id: str = ""
    disparado: bool = False


@dataclass
class ZonaDeWarp:
    """Teletransporta al jugador a otro punto **del mismo mapa** — AUD-287.

    Zelda (las cuevas), Metroid (los ascensores), Hollow Knight (los bancos de
    los Stagways), Super Metroid (los tubos). Lo que hasta ahora no se podía
    declarar desde Tiled: `NextTrigger` cambia de escenario y `Door` abre un
    paso, pero mover al jugador de una punta del mapa a otra **no existía**, ni
    con propiedad ni con tipo de objeto. Un mapa grande no tenía forma de
    conectar sus extremos sin obligar a recorrerlo entero.

    Por qué el enfriamiento
    -----------------------
    Sin él, un warp cuyo destino cae dentro de otra zona de warp —o dentro de sí
    mismo, que es el error de colocación más fácil de cometer en Tiled— entra en
    un bucle: el jugador aparece dentro del disparador, salta, aparece otra vez.
    A 60 fps eso no es un fallo visible, es una pantalla epiléptica. Medio
    segundo basta para salir andando de cualquier rectángulo razonable.

    `una_vez` está para los pasadizos de ida sin vuelta, y `key_id` para los que
    hay que ganarse: los dos siguen el mismo contrato que `Disparador`, para que
    quien ya sepa poner un disparador sepa poner un warp.
    """

    rect: pygame.Rect
    #: Adónde va el **centro inferior** del jugador, en píxeles de mundo.
    destino: pygame.Vector2
    #: Con `True` se cruza al tocarlo; con `False`, pulsando el botón de usar.
    automatico: bool = True
    una_vez: bool = False
    #: Si no está vacío, hace falta esta llave.
    key_id: str = ""
    #: Segundos que tarda en poder volver a usarse.
    enfriamiento: float = 0.5
    #: Texto que se enseña al cruzar. Vacío = ninguno.
    mensaje: str = ""
    #: AUD-635 — skill_id requerido para usar el warp.
    requires_skill: str = ""
    usado: bool = False
    _espera: float = 0.0


@dataclass
class Llavero:
    """Lo que el jugador lleva encima durante el escenario.

    Es un conjunto, no una lista: llevar dos llaves rojas no abre dos puertas
    rojas, y contar duplicados sólo daría oportunidades de equivocarse.
    """

    llaves: set[str] = field(default_factory=set)

    def tiene(self, key_id: str) -> bool:
        return not key_id or key_id in self.llaves

    def coger(self, key_id: str) -> None:
        if key_id:
            self.llaves.add(key_id)

    def gastar(self, key_id: str) -> None:
        self.llaves.discard(key_id)


# ──────────────────────────────────────────────────────────────────────
# AUD-625 — Salidas secretas y salas secretas (SecretExit / SecretRoom)
# ──────────────────────────────────────────────────────────────────────

@dataclass
class SecretExit:
    """Salida oculta que revela un nuevo nodo en el mapa del mundo.

    No se dibuja: es un disparador invisible. Cuando el jugador lo toca,
    emite el evento `SECRET_FOUND` con el ID del secreto, y el mapa del
    mundo revela el nuevo nodo. El diseñador controla la recompensa
    (ítem, atajo, lore) vía el manejador del evento en su escena.
    """

    rect: pygame.Rect
    secret_id: str
    #: Si `True`, el secreto se revela al tocarlo. Si `False`, al pulsar
    #: el botón de usar (para secretos que requieren acción deliberada).
    automatico: bool = True
    #: Si `True`, el secreto solo se puede descubrir una vez por partida.
    una_vez: bool = True
    #: Si no está vacío, hace falta esta llave/ítem para revelarlo.
    key_id: str = ""
    descubierto: bool = False

    def revelar(self, player: Player) -> bool:
        """Intenta revelar el secreto. Devuelve True si se revela ahora."""
        if self.descubierto:
            return False
        if self.key_id and not self._tiene_llave(player, self.key_id):
            return False
        self.descubierto = True
        return True

    @staticmethod
    def _tiene_llave(player: Player, key_id: str) -> bool:
        if not key_id:
            return True
        from src.engine.core.inventory import get_inventory
        return get_inventory().has_skill(key_id) or getattr(player, "_habilidades_libres", False)


@dataclass
class SecretRoom:
    """Sala oculta con tell visual sutil (sparkle cada 3s).

    Se dibuja como un rectángulo invisible con tell visual. Al entrar,
    emite `SECRET_FOUND` y puede dar un recogible o activar algo.
    """

    rect: pygame.Rect
    secret_id: str
    #: Ítem que se otorga al descubrirla (opcional).
    recompensa: str = ""
    #: Tell visual: "sparkle" (default), "particles", "sound", "none".
    tell: str = "sparkle"
    descubierto: bool = False

    def intentar_descubrir(self, player: Player) -> bool:
        """Si el jugador entra en el rectángulo y no está descubierto, lo revela."""
        if self.descubierto or not self.rect.colliderect(player.rect):
            return False
        self.descubierto = True
        return True


# ──────────────────────────────────────────────────────────────────────
# AUD-XXX — Placa de presión (PressurePlate)
# ──────────────────────────────────────────────────────────────────────

@dataclass
class PlacaDePresion:
    """Boton en el suelo que se activa con peso y abre puertas mientras esta pisada.

    Es el eslabon que faltaba entre ``BloqueEmpujable`` (AUD-140) y
    ``Cerradura.abre_con_evento`` (AUD-132): un ``PushBlock`` encima de la
    placa abre la puerta cuyo ``abre_con`` coincide con ``evento``, y al
    quitar el bloque la puerta se cierra (si ``mantener`` es ``True``, el
    comportamiento de puzzle Sokoban).

    Por que no es un ``Disparador``
    --------------------------------
    ``Disparador`` solo mira al jugador y dispara una vez. La placa mira a
    **bloques empujables** (y opcionalmente al jugador) cada fotograma, y su
    estado es continuo: ``activa`` mientras haya peso encima. Sin esto, un
    puzzle de "pon el bloque en el boton" no se podia declarar desde Tiled y
    obligaba a escribir Python en cada nivel (GAP del usuario 2026-08-26).

    Modos de ``requiere``
    ----------------------
    * ``"bloque"`` (defecto) — cualquier ``BloqueEmpujable``.
    * ``"jugador"`` — el jugador.
    * ``"ambos"`` — bloque Y jugador a la vez.
    * ``"cualquiera"`` — bloque O jugador.

    ``mantener`` decide si la puerta se cierra al liberar la placa. Con
    ``False`` la placa es un interruptor que queda enclavado.
    """

    rect: pygame.Rect
    evento: str
    requiere: str = "bloque"
    mantener: bool = True
    una_vez: bool = False
    mensaje: str = ""
    activa: bool = False
    disparada: bool = False
    # Estado del fotograma anterior — para detectar flancos sin bus.
    _activa_previa: bool = False


def alcanza(jugador: pygame.Rect, objetivo: pygame.Rect, margen: int = ALCANCE_DE_USO) -> bool:
    """¿Está el jugador lo bastante cerca para accionar esto?

    Se infla el rectángulo del objetivo en vez del del jugador porque así el
    alcance no depende del tamaño del personaje, que cambia al agacharse.
    """
    return objetivo.inflate(margen * 2, margen * 2).colliderect(jugador)
