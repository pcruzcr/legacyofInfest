"""
Module: guard_system
System: stage (student assignment) — stage1_1 «La Entrada»
Academic Unit: N/A
Description: Guardia mantenida. Mientras se tenga pulsada la tecla de
defensa, el jugador no recibe daño.

POR QUÉ EXISTE
--------------
El motor solo trae un PARRY con ventana de 0,2 s que hay que atinar en el
instante justo (`_handle_parry_input`, player_states.py:113, y
`_PARRY_DURATION`, línea 954). No existe ninguna postura de bloqueo que se
mantenga pulsada.

Este módulo añade esa defensa sencilla sin tocar un solo archivo del
profesor: envuelve `player.apply_damage` en tiempo de ejecución. Como TODO
el daño al jugador pasa por ahí —contacto con enemigos
(`enemy_base.py:529`), proyectiles (`enemy_shooter.py:206`, y el escupitajo
de la rana), zonas de peligro— con un único punto de intercepción la
guardia protege de todo por igual.

CÓMO SE USA
-----------
Mantener pulsada `CTRL izquierdo` o `Q`. En el suelo. Ya está.

DECISIONES DE EQUILIBRIO
------------------------
· **Defenderse inmoviliza.** Con la guardia puesta el jugador queda clavado
  en el sitio; para caminar hay que soltar la tecla. Es lo que le da un
  precio al bloqueo: si no, se avanzaría por todo el nivel siendo inmune.
· Solo funciona con los pies en el suelo. Bloquear mientras se cae dejaría
  el nivel sin ninguna tensión.
· No hay medidor ni desgaste: se pidió algo simple, no un sistema de
  resistencia. Si más adelante hiciera falta, `REDUCCION` permite pasar de
  inmunidad total a daño reducido cambiando un número.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

# Fracción del daño que absorbe la guardia.
#   1.0 = inmunidad total mientras se bloquea
#   0.5 = se recibe la mitad
REDUCCION: float = 1.0


class GuardSystem:
    """Bloqueo mantenido, sin ventana de tiempo."""

    # Teclas libres: ninguna de estas aparece en
    # src/engine/input/action_map.py, así que no pisa nada del motor.
    TECLAS: tuple[int, ...] = (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_q)

    #: Bloquear en el aire trivializaría el nivel.
    SOLO_EN_SUELO: bool = True

    def __init__(self) -> None:
        self.activo: bool = False
        self.bloqueos: int = 0
        self._player: Any = None
        self._original: Callable[..., None] | None = None
        self._era_de_instancia: bool = False

    # ── Lectura del teclado ─────────────────────────────────────────

    @classmethod
    def hay_tecla_de_guardia(cls, esta_pulsada: Callable[[int], bool]) -> bool:
        """¿Está pulsada alguna de las teclas de defensa?

        Recibe la función de consulta en vez de leer el teclado directo,
        para poder probarlo sin depender de un teclado real.
        """
        return any(esta_pulsada(tecla) for tecla in cls.TECLAS)

    @classmethod
    def leer_teclado(cls) -> bool:
        """Consulta el teclado físico. `is_raw_key_held` devuelve True en
        CADA fotograma mientras la tecla siga abajo (input_manager.py:183),
        que es justo lo que necesita una guardia mantenida."""
        from src.engine.input.input_manager import InputManager
        return cls.hay_tecla_de_guardia(InputManager.is_raw_key_held)

    # ── Enganche del interceptor de daño ────────────────────────────

    def enganchar(self, player: Any) -> None:
        # ── Enganche idempotente de `apply_damage` ────────
        # Se envuelve `player.apply_damage` porque es el único punto (cuello de botella)
        # por donde entra TODO el daño al jugador en el motor (ya sea por contacto con 
        # enemigos, proyectiles o zonas de peligro). Al interceptar esta única función, 
        # la guardia protege de cualquier fuente de daño sin tener que modificar cada 
        # entidad del juego.
        # 
        # El método es IDEMPOTENTE: si se llama múltiples veces, primero se desengancha 
        # el envoltorio anterior (`self.desenganchar()`) antes de poner uno nuevo. Esto 
        # evita apilar múltiples filtros (lo que causaría recursión infinita o pérdida 
        # del método original) si la escena llamara a `enganchar()` varias veces.
        if self._original is not None:
            self.desenganchar()

        original = player.apply_damage
        self._player = player
        self._original = original
        # ¿`apply_damage` ya era un atributo de instancia antes de envolverlo?
        # Si no lo era, desenganchar debe BORRAR el atributo para que vuelva a
        # resolverse contra la clase, no dejar pegado un método enlazado.
        self._era_de_instancia = "apply_damage" in vars(player)

        def apply_damage_con_guardia(amount, source_position,
                                     knockback_force=150.0):
            if self.activo:
                self.bloqueos += 1
                restante = amount * (1.0 - REDUCCION)
                if restante <= 0.0:
                    return
                return original(restante, source_position, knockback_force)
            return original(amount, source_position, knockback_force)

        player.apply_damage = apply_damage_con_guardia

    def desenganchar(self) -> None:
        # ── Desenganche y limpieza del diccionario de instancia ────────
        # Restaura el comportamiento original. 
        # Si `apply_damage` no era originalmente un atributo de la instancia (sino 
        # un método heredado de la clase BaseEntity/Player), asignarlo durante el 
        # enganche lo metió en el diccionario `__dict__` (`vars(player)`) de la instancia. 
        # Si al desenganchar simplemente reasignáramos `self._original`, estaríamos 
        # dejando un método enlazado pegado a la instancia, enmascarando el de la clase.
        # Por eso, si no era de instancia, se debe BORRAR con `vars().pop()` para que 
        # la resolución de métodos vuelva a buscarlo en la clase.
        if self._player is not None and self._original is not None:
            if self._era_de_instancia:
                self._player.apply_damage = self._original
            else:
                vars(self._player).pop("apply_damage", None)
        self._player = None
        self._original = None
        self._era_de_instancia = False
        self.activo = False

    # ── Ciclo por fotograma ─────────────────────────────────────────

    def actualizar(self, player: Any, tecla_pulsada: bool) -> None:
        """Decide si la guardia queda activa este fotograma."""
        if not tecla_pulsada:
            self.activo = False
            return
        if self.SOLO_EN_SUELO and not getattr(player, "is_grounded", False):
            self.activo = False
            return
        self.activo = True

    # ── Inmovilidad mientras se defiende ────────────────────────────

    def congelar(self, player: Any, x_previa: float) -> None:
        # ── Inmovilidad al bloquear (y por qué guardar X) ────────
        # Devuelve al jugador a su X anterior mientras tenga la guardia.
        # 
        # POR QUÉ SE HACE ASÍ Y NO PONIENDO velocity.x = 0:
        # La máquina de estados del jugador procesa el input y sobreescribe 
        # `velocity.x` DENTRO de `player.update()`, y en ese mismo método 
        # integra la posición. No hay un punto intermedio accesible desde 
        # fuera (como este overlay) para interceptarlo:
        # - Anular la velocidad ANTES de `update()` no sirve porque la 
        #   máquina de estados la vuelve a fijar leyendo las flechas.
        # - Anularla DESPUÉS no sirve porque ya se integró y la posición cambió.
        # Por eso el escenario guarda la posición X antes del update y la 
        # restaura aquí.
        # 
        # SOLO SE CONGELA LA HORIZONTAL: La vertical se deja intacta para que 
        # la gravedad y las caídas sigan aplicándose normalmente. Si también 
        # congeláramos Y, el jugador podría quedarse flotando en el aire al 
        # asomarse por un borde y bloquear.
        if player is None or not self.activo:
            return
        player.position.x = x_previa
        player.velocity.x = 0.0
        if hasattr(player, "rect"):
            player.rect.x = int(x_previa)

    # ── Dibujo del indicador ────────────────────────────────────────

    def draw(self, surface: pygame.Surface, player: Any,
             camera_offset: pygame.Vector2) -> None:
        """Escudo sencillo delante del jugador, para que se vea que bloquea."""
        if not self.activo or player is None:
            return
        x = int(player.rect.centerx - camera_offset.x)
        y = int(player.rect.centery - camera_offset.y)
        lado = 1 if getattr(player, "facing_direction", 1) >= 0 else -1
        cx = x + lado * (player.rect.width // 2 + 4)

        pygame.draw.ellipse(surface, (120, 200, 255),
                            (cx - 4, y - 14, 9, 28), 2)
        pygame.draw.ellipse(surface, (220, 245, 255),
                            (cx - 2, y - 9, 4, 18), 1)
