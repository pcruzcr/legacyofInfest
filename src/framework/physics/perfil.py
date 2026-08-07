"""
Module: perfil
System: framework.physics
Description: AUD-333 — la física de un contexto, declarada en un solo sitio.

Por qué existe esto
===================
Hasta ahora la física de locomoción vivía **dentro** de los integradores de
cada entidad: `Player.update` leía `settings.GRAVITY`, `EnemyBase.update`
otra copia de las mismas cuentas, y el modo cenital era una bandera booleana
con sus propias ramas por todos lados. Eso sirve para un juego; no sirve
para un motor que quiere ser usado en **contextos y modos de juego**
distintos, porque el contexto —plataformas, planta, vuelo, tanque— tiene que
ser un dato que la escena o el modo eligen, no un `if` en el integrador.

`PhysicsProfile` es ese dato: todos los números de la física de un modo,
juntos, con los valores actuales del juego como preset `plataformas()`. Un
contexto nuevo —un nivel de hielo, un modo de vuelo, un minijuego de vista
cenital— es un perfil, y el integrador lo consume sin ramas propias.

Qué está cableado hoy (AUD-333) y qué falta
============================================
Cableado: la gravedad, la caída máxima y los factores de muro del bloque de
física del jugador; la velocidad de suelo (`walk_speed`); el impulso de
salto, el coyote y los saltos aéreos de la máquina de estados; el margen de
pegado y la velocidad de deslizamiento de las pendientes; y el modo cenital,
que ahora es el preset `cenital()` en vez de una bandera suelta.

Pendiente (próxima fase): el modo `vuelo` — el perfil lo declara, pero el
integrador del jugador aún no tiene una integración de vuelo que lo
consuma. Mientras no exista, el preset `vuelo()` no se publica: un modo sin
comportamiento es código muerto, y este repositorio lo persigue.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.engine.core import settings

#: Los modos que la física sabe nombrar. Los integrados hoy son
#: `plataformas` (el juego actual) y `cenital` (AUD-328, sin gravedad y
#: movimiento en dos ejes). `vuelo` es el siguiente, con su integración.
PLATAFORMAS = "plataformas"
CENITAL = "cenital"
VUELO = "vuelo"


@dataclass
class Muro:
    """Cómo se comporta la gravedad al rozar una pared vertical en el aire.

    En el juego son los factores fijos 0,3 (gravedad) y 0,5 (caída máxima)
    del deslizamiento por la pared; aquí son datos del perfil para que un
    contexto pueda declararlos sin tocar el integrador.
    """

    factor_gravedad: float = 0.3
    factor_max_caida: float = 0.5


@dataclass
class Cuestas:
    """Los números del suelo inclinado, hoy constantes en `pendientes.py`.

    `margen_pegado` es `MARGEN_DE_PEGADO` — los píxeles que el jugador puede
    «caer» de golpe siguiendo la cuesta al bajar sin que se le vea el
    traqueteo. `velocidad_deslizamiento` es `settings.PLAYER_SLOPE_SLIDE_SPEED`
    — la velocidad acotada a la que la gravedad desliza a quien se queda
    quieto en una cuesta (AUD-326).
    """

    margen_pegado: float = 8.0
    velocidad_deslizamiento: float = 90.0


@dataclass
class PhysicsProfile:
    """Toda la física de un contexto de juego, en un solo objeto.

    Los valores por defecto son exactamente los del juego actual — leídos de
    `settings` en el momento de construir el perfil, para que un
    `monkeypatch` de `settings` antes de construir a la entidad siga
    funcionando y el trinquete de calibración (`test_calibracion_del_salto`)
    siga midiendo lo mismo.
    """

    modo: str = PLATAFORMAS
    gravedad: float = settings.GRAVITY
    max_caida: float = settings.PLAYER_MAX_FALL_SPEED
    velocidad_suelo: float = settings.PLAYER_WALK_SPEED
    salto_impulso: float = settings.PLAYER_JUMP_FORCE
    coyote_frames: int = settings.PLAYER_COYOTE_FRAMES
    saltos_aereos: int = settings.PLAYER_AIR_JUMPS
    muro: Muro = field(default_factory=Muro)
    cuestas: Cuestas = field(default_factory=Cuestas)

    @classmethod
    def plataformas(cls) -> PhysicsProfile:
        """El contexto del juego actual: todo sale de `settings`."""
        return cls()

    @classmethod
    def cenital(cls) -> PhysicsProfile:
        """AUD-328 como perfil: sin gravedad, sin caída, sin salto.

        Es el mismo contenido que la vieja bandera `vista_cenital` — con la
        bandera, un contexto nuevo tenía que acordarse de ponerla y las
        ramas del integrador decidían por él; con el perfil, el modo es el
        dato y el integrador lo lee.
        """
        return cls(
            modo=CENITAL,
            gravedad=0.0,
            max_caida=0.0,
            salto_impulso=0.0,
            coyote_frames=0,
            saltos_aereos=0,
        )
