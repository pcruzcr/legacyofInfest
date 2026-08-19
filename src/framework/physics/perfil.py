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
pegado y la velocidad de deslizamiento de las pendientes; el modo cenital,
que ahora es el preset `cenital()` en vez de una bandera suelta; y el modo
`vuelo` (AUD-335), el preset que los contextos de vuelo eligen para
heredar la integración sin gravedad con su propia velocidad.

AUD-336 cerró lo que quedaba de la fase: `aceleracion` y `friccion` (px/s²)
declaran cómo se acerca la velocidad horizontal a la que fija la máquina de
estados, y el jugador las consume en `_aplicar_friccion_y_aceleracion`. Con
las dos en 0 —los presets `plataformas()`, `cenital()` y `vuelo()`— el
comportamiento es el de siempre: la velocidad ES la del estado. La fricción
por superficie desde el TMX ya vivía en el ECS (`ZonaDeFriccion` +
`sistema_friccion`, AUD-236): recorta la velocidad que el integrador acaba
de producir, así que compone con la aceleración del perfil sin tocarse.
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


@dataclass(frozen=True)
class Material:
    """Una superficie con nombre: cuánto frena y cuánto devuelve — AUD-396.

    Cierra GAP-039. La fricción por superficie ya existía desde AUD-236
    (`ZonaDeFriccion` + `sistema_friccion`) y el perfil ya declaraba
    `friccion` desde AUD-336. Lo que no había era el **material** como cosa
    nombrada que agrupe las dos propiedades, y por eso faltaba la segunda:
    sin restitución no hay rebote, así que el hielo y el musgo se podían
    expresar y la goma no.

    `frozen=True` porque un material es una constante del mundo, no un estado:
    dos plataformas de goma comparten la misma instancia y nadie debe poder
    ablandar una de ellas por accidente desde otro sitio.

    `restitucion` es la fracción de velocidad vertical que se devuelve al
    chocar: 0 se queda pegado —lo de siempre—, 1 rebotaría para siempre.
    """

    nombre: str = "roca"
    #: Multiplicador de la fricción del perfil. 1 = la de siempre.
    friccion: float = 1.0
    #: Fracción de la velocidad de impacto que se devuelve. 0 = sin rebote.
    restitucion: float = 0.0


#: El suelo normal: no rebota. Es el material por defecto **a propósito**, para
#: que los mapas que ya existen se jueguen exactamente igual que antes.
ROCA = Material("roca")
#: Resbala. La fricción baja ya se podía expresar con `ZonaDeFriccion`; aquí
#: está por completar el catálogo con un nombre en vez de con un número suelto.
HIELO = Material("hielo", friccion=0.15)
#: Frena mucho.
MUSGO = Material("musgo", friccion=2.5)
#: La que no se podía expresar hasta ahora, y el motivo del hueco.
#:
#: 0,6 y no más: por encima de ~0,8 el rebote tarda tanto en amortiguarse que
#: el jugador pierde el control del personaje varios segundos, que se lee como
#: un fallo y no como una mecánica.
GOMA = Material("goma", restitucion=0.6)
#: AUD-551 — GAP-070 punto 1: el freno del lodo de la Fase 2 del 4-1 ya
#: existía (`ZonaDeFriccion.multiplicador`, AUD-522), pero la zona nunca
#: declaraba `material="lodo"` — sólo `musgo` lo hacía — así que
#: `Transform.material_actual` nunca valía "lodo" y la pisada distinta
#: (`states/grounded.py`) no tenía forma de encenderse. Fricción y
#: restitución en su valor de fábrica a propósito: este material existe
#: sólo para nombrar la zona, no para cambiar cómo frena (eso ya lo hace
#: `multiplicador`, sin tocar).
LODO = Material("lodo")
#: AUD-554 — GAP-070 "Pasos sobre Tierra/Grava": la Fase 1 del 4-1 pisa
#: suelo normal (sin `ZonaDeFriccion` propia, hasta ahora) y sonaba con el
#: genérico `sfx_step` que comparten los otros 25 escenarios. Igual que
#: `LODO`, existe sólo para nombrar la zona y encender la pisada propia —
#: no cambia fricción ni restitución, el terreno se sigue jugando igual.
GRAVA = Material("grava")
#: AUD-554 — GAP-070 "Pasos Ahogados": la Fase 5 pide que los pasos del
#: jugador bajen de volumen y cedan protagonismo al ambiente nocturno. Mismo
#: criterio que `GRAVA`/`LODO`: la zona sólo nombra el terreno.
AHOGADO = Material("ahogado")

#: Los materiales que el motor conoce, por su nombre. Es lo que permite
#: declararlos desde datos —un TMX, un tileset— sin que el cargador tenga que
#: importar cada constante.
MATERIALES: dict[str, Material] = {
    m.nombre: m for m in (ROCA, HIELO, MUSGO, GOMA, LODO, GRAVA, AHOGADO)
}


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
    #: Aceleración horizontal hacia la velocidad que fija la máquina de
    #: estados, en px/s². Con 0 (el juego actual) la velocidad es la del
    #: estado, al instante; con más de 0, ésa pasa a ser el **objetivo** y la
    #: velocidad real se acerca a él a ritmo acotado (AUD-336).
    aceleracion: float = 0.0
    #: Frenado sin entrada, en px/s². Con 0 se frena a ritmo de
    #: `aceleracion`; con las dos en 0 el juego actual no frena porque no
    #: tiene inercia que disipar.
    friccion: float = 0.0
    #: AUD-396 — la superficie sobre la que se cae (GAP-039).
    #:
    #: `ROCA` por defecto: restitución 0, o sea el comportamiento de siempre
    #: —tocar suelo pone la velocidad vertical a cero—. Los dieciséis mapas
    #: entregados no cambian.
    material: Material = field(default_factory=lambda: ROCA)

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

    @classmethod
    def vuelo(cls) -> PhysicsProfile:
        """AUD-335 — el modo vuelo: sin gravedad, movimiento en dos ejes.

        La integración es la misma que la cenital — sin gravedad, sin
        caída, sin salto, velocidad desde la entrada — porque la física
        del vuelo ES esa: el modo la declara y hereda el comportamiento.
        Un contexto de vuelo construye el suyo propio con la velocidad que
        quiera; las repisas de un sentido y las cuestas no se resuelven en
        vuelo, son semántica de plataformas (ver `resolucion.py`).
        """
        return cls(
            modo=VUELO,
            gravedad=0.0,
            max_caida=0.0,
            salto_impulso=0.0,
            coyote_frames=0,
            saltos_aereos=0,
        )
