"""
Los componentes: datos, sin comportamiento.

F5.1 — la regla que hay que respetar
====================================
Un componente **no tiene métodos que cambien el juego**. Puede tener una
propiedad calculada o un `rect_actual()` que derive datos de los suyos, pero en
cuanto uno empieza a llamar al bus de eventos o a mover a otra entidad, deja de
ser un dato y vuelve a ser un objeto con comportamiento, que es justo lo que se
estaba intentando dejar atrás.

Todo componente es un `@dataclass` con `slots=True`. Los slots no son
microoptimización: impiden crear atributos por error. Sin ellos, un
`viento.fuerza = 100` con la propiedad mal escrita —`furza`— crea el atributo,
no falla, y el viento deja de soplar sin que nada avise. Es exactamente el tipo
de fallo silencioso que este proyecto lleva un mes cazando.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pygame

# ══════════════════════════════════════════════════════════════
# Núcleo: lo que casi todo tiene
# ══════════════════════════════════════════════════════════════


class Transform:
    """Dónde está y hacia dónde mira.

    Es el único componente que **no** es un `dataclass`, y la razón es de
    rendimiento medida, no de estilo.

    Las dos formas de un Transform
    -------------------------------
    * **Propio** — lo usan las entidades que sólo existen en el ECS: plataformas
      móviles, bloques rítmicos, guardias. Guarda su posición y su rect.
    * **Vista** — lo usan las entidades de la jerarquía (`BaseEntity` y sus 26
      subclases de estudiantes). No guarda nada: **lee del dueño**.

    Por qué la vista, con los números
    ----------------------------------
    Se intentaron las dos alternativas obvias y las dos costaron caro:

    1. `rect` como **propiedad** en `BaseEntity`: el motor lee `rect` y
       `position` 255 veces por fotograma, y a 404 ns contra 66 el prólogo pasó
       de 18,36 ms a 21,36 ms por fotograma. Un 16 % del presupuesto en
       indirección.
    2. `rect` como atributo normal más `__setattr__` para vigilar las
       reasignaciones: **34,58 ms**, casi el doble. `__setattr__` se dispara en
       *cada* escritura de atributo de la entidad —temporizadores, banderas,
       velocidades— y el motor escribe muchísimos por fotograma.

    La vista invierte la dirección: el dueño tiene `rect` y `position` como
    atributos normales —lectura a 66 ns, exactamente como antes de la fase 5— y
    es el **componente** el que hace la indirección. Se paga donde es barato:
    los sistemas recorren decenas de entidades, no miles de veces por fotograma.

    Y resuelve gratis el problema que motivó todo esto: si un estudiante
    reasigna `self.rect = otro_rect` —ocurre 14 veces en las entregas—, la vista
    lo ve al instante, porque no guardaba una copia que pudiera quedarse vieja.
    """

    __slots__ = ("_duenio", "_facing", "_posicion", "_rect")

    def __init__(
        self,
        posicion: pygame.Vector2 | None = None,
        rect: pygame.Rect | None = None,
        facing: int = 1,
        duenio: object | None = None,
    ) -> None:
        self._posicion = posicion if posicion is not None else pygame.Vector2(0, 0)
        self._rect = rect if rect is not None else pygame.Rect(0, 0, 0, 0)
        self._facing = facing
        #: Si no es `None`, este Transform es una vista sobre esa entidad.
        self._duenio = duenio

    @property
    def posicion(self) -> pygame.Vector2:
        d = self._duenio
        return d.position if d is not None else self._posicion  # type: ignore[union-attr]

    @posicion.setter
    def posicion(self, valor: pygame.Vector2) -> None:
        self.posicion.update(valor)

    @property
    def rect(self) -> pygame.Rect:
        d = self._duenio
        return d.rect if d is not None else self._rect  # type: ignore[union-attr]

    @rect.setter
    def rect(self, valor: pygame.Rect) -> None:
        if self._duenio is not None:
            self._duenio.rect = valor  # type: ignore[union-attr]
        else:
            self._rect = valor

    @property
    def facing(self) -> int:
        d = self._duenio
        return getattr(d, "facing_direction", self._facing) if d is not None else self._facing

    @facing.setter
    def facing(self, valor: int) -> None:
        valor = -1 if valor < 0 else 1
        self._facing = valor
        if self._duenio is not None and hasattr(self._duenio, "facing_direction"):
            self._duenio.facing_direction = valor  # type: ignore[union-attr]

    def __repr__(self) -> str:
        clase = "vista" if self._duenio is not None else "propio"
        return f"Transform({clase}, pos={tuple(self.posicion)}, rect={tuple(self.rect)})"


@dataclass(slots=True)
class Velocidad:
    v: pygame.Vector2


@dataclass(slots=True)
class Gravedad:
    """Sin este componente una entidad no cae. Flotar es no tenerlo."""

    multiplicador: float = 1.0


@dataclass(slots=True)
class Solido:
    """Bloquea el paso. La geometría del escenario y las puertas cerradas."""

    atravesable_desde_abajo: bool = False


class Salud:
    """Vida, y quién es su dueño.

    F5.12 — la segunda deuda declarada de la fase 5, saldada
    --------------------------------------------------------
    Nació como un `dataclass` con sus propios `actual` y `maxima`, y la escena
    los **sincronizaba** con `current_health` de `EnemyBase` en cada golpe. Dos
    copias del mismo dato, y quedó escrito como deuda: *«el día que ninguna
    entrega dependa de `current_health`, el componente pasa a ser la única
    verdad»*.

    Ese día no va a llegar: hay **48 referencias** a `current_health` y
    `max_health` en el código de los estudiantes, incluyendo escrituras
    (`boss.current_health = boss.phase_max_health` en Paburu). Esperar a que
    desaparezcan es esperar a reescribir su trabajo.

    Así que se resuelve al revés, con la misma solución que `Transform`: el
    componente es una **vista** sobre el dueño. `current_health` sigue siendo el
    atributo normal de siempre —su código no cambia y no paga indirección— y el
    componente lee de ahí. No hay dos copias porque no hay copia: hay un dato y
    una ventana a él.

    Sincronizar dos copias siempre acaba mal. La pregunta correcta no era
    «¿cuándo puedo borrar la otra?» sino «¿por qué hay dos?».
    """

    __slots__ = ("_actual", "_duenio", "_invulnerable", "_maxima")

    def __init__(
        self,
        actual: float = 0.0,
        maxima: float = 0.0,
        invulnerable: bool = False,
        duenio: object | None = None,
    ) -> None:
        self._actual = actual
        self._maxima = maxima
        self._invulnerable = invulnerable
        self._duenio = duenio

    @property
    def actual(self) -> float:
        d = self._duenio
        return float(d.current_health) if d is not None else self._actual  # type: ignore[union-attr]

    @actual.setter
    def actual(self, valor: float) -> None:
        if self._duenio is not None:
            self._duenio.current_health = valor  # type: ignore[union-attr]
        else:
            self._actual = valor

    @property
    def maxima(self) -> float:
        d = self._duenio
        return float(d.max_health) if d is not None else self._maxima  # type: ignore[union-attr]

    @maxima.setter
    def maxima(self, valor: float) -> None:
        if self._duenio is not None:
            self._duenio.max_health = valor  # type: ignore[union-attr]
        else:
            self._maxima = valor

    @property
    def invulnerable(self) -> bool:
        d = self._duenio
        if d is not None and hasattr(d, "_invincibility_timer"):
            return self._invulnerable or d._invincibility_timer > 0  # type: ignore[union-attr]
        return self._invulnerable

    @invulnerable.setter
    def invulnerable(self, valor: bool) -> None:
        self._invulnerable = valor

    @property
    def fraccion(self) -> float:
        return self.actual / self.maxima if self.maxima > 0 else 0.0

    def __repr__(self) -> str:
        clase = "vista" if self._duenio is not None else "propia"
        return f"Salud({clase}, {self.actual}/{self.maxima})"


@dataclass(slots=True)
class Renderizable:
    """Qué dibujar y en qué capa. El dibujado lo hace un sistema, no la entidad."""

    surface: pygame.Surface | None = None
    capa: int = 4
    visible: bool = True


@dataclass(slots=True)
class Etiqueta:
    """Marca legible. Para depurar y para que los sistemas filtren por rol."""

    nombre: str


@dataclass(slots=True)
class EsJugador:
    """Marca sin datos: esta entidad es **el** jugador.

    F5.11 — la pieza que permitió jubilar `_mundo_ecs_paso`
    -------------------------------------------------------
    Los sistemas de sigilo necesitan saber dónde está el jugador. La primera
    versión se lo pasaba por parámetro::

        sistema_conos_de_vision(mundo, dt, rect_del_jugador)

    Y eso rompía la firma `Sistema = Callable[[World, float], None]`, así que
    esos dos sistemas no cabían en el `Planificador` y la escena tenía que
    llamar a los once a mano, en orden, sin equivocarse.

    Con una marca, el sistema lo busca él: `mundo.con(EsJugador, Transform)`.
    La firma vuelve a ser uniforme, los once entran en el planificador y el
    orden deja de estar escrito a mano en la escena para estar declarado en un
    solo sitio con su motivo.

    Es un componente vacío a propósito. En ECS, «qué eres» se dice teniendo o
    no teniendo un componente, no con un campo `tipo` que haya que comparar.
    """


# ══════════════════════════════════════════════════════════════
# F5.3 — zonas con efecto físico
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class ZonaDeViento:
    """Empuja a quien esté dentro. Mega Man 2 (Air Man), Celeste (Golden Ridge).

    Es el mismo rectángulo que una `HazardZone`, con una diferencia de fondo:
    la zona de daño **quita algo**, y ésta **cambia cómo te mueves**. Diseñar
    con la segunda es más interesante porque el jugador puede aprovecharla —un
    viento a favor alarga el salto— y por eso se separan.
    """

    rect: pygame.Rect
    #: Aceleración en px/s². Positiva empuja a la derecha o hacia abajo.
    fuerza: pygame.Vector2
    #: Segundos de ciclo. 0 = constante. Con ciclo, sopla la mitad del tiempo.
    periodo: float = 0.0
    _t: float = 0.0

    @property
    def soplando(self) -> bool:
        return self.periodo <= 0.0 or (self._t % self.periodo) < (self.periodo / 2.0)


@dataclass(slots=True)
class ZonaDeFriccion:
    """Cambia el agarre del suelo. La miel de The Hive, el hielo, las cintas.

    `multiplicador` < 1 resbala, > 1 frena antes. `arrastre` mueve solo, que es
    lo que convierte esto en una cinta transportadora.
    """

    rect: pygame.Rect
    multiplicador: float = 1.0
    arrastre: float = 0.0


@dataclass(slots=True)
class ZonaLetalTemporizada:
    """Mata, pero sólo mientras está encendida.

    MGS (los láseres del almacén), Mega Man 2 (Quick Man), Celeste (los
    buscadores del Templo de los Espejos), Inside (las ondas de choque).

    `desfase` existe para poder colocar cinco láseres que se encienden en
    cascada en vez de todos a la vez, que es la diferencia entre un obstáculo y
    un patrón.
    """

    rect: pygame.Rect
    dano: float = 99.0
    encendido: float = 1.0
    apagado: float = 1.0
    desfase: float = 0.0
    _t: float = 0.0

    @property
    def activa(self) -> bool:
        ciclo = self.encendido + self.apagado
        if ciclo <= 0.0:
            return True
        return ((self._t + self.desfase) % ciclo) < self.encendido

    @property
    def aviso(self) -> float:
        """0→1 en el medio segundo previo a encenderse. Para el parpadeo.

        Sin aviso, una zona letal que aparece de golpe no es un obstáculo: es
        una emboscada. Media clase de diseño cabe en esta propiedad.
        """
        ciclo = self.encendido + self.apagado
        if ciclo <= 0.0 or self.activa:
            return 0.0
        restante = self.encendido + self.apagado - ((self._t + self.desfase) % ciclo)
        return max(0.0, 1.0 - restante / 0.5) if restante < 0.5 else 0.0


@dataclass(slots=True)
class ZonaDeAgua:
    """F5.6 — el disparador que le faltaba a `SwimmingState`.

    El estado de nado estaba escrito, completo y era **inalcanzable**: cero
    transiciones en todo `src/`. Y `docs/45_SWIMMING_SPEC.md` lo decía desde el
    14 de julio: «No dedicated water zone detection».

    Esto es esa detección.
    """

    rect: pygame.Rect
    #: Con corriente el agua además arrastra. SMB3 (Water Land).
    corriente: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))


# ══════════════════════════════════════════════════════════════
# F5.4 — superficies que se mueven
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class PlataformaMovil:
    """Va y viene entre dos puntos, y **arrastra a quien lleva encima**.

    Lo segundo es la parte que se olvida siempre, y por eso está escrito aquí
    arriba: sin arrastre el jugador se queda flotando en el aire mientras la
    plataforma se va, y parece un fallo de colisión cuando es un fallo de
    diseño del sistema.
    """

    origen: pygame.Vector2
    destino: pygame.Vector2
    velocidad: float = 40.0
    #: Segundos de pausa en cada extremo. Un ir y venir sin pausa no se puede
    #: leer: el jugador no sabe cuándo saltar.
    espera: float = 0.5
    _hacia_destino: bool = True
    _espera_restante: float = 0.0
    #: Cuánto se movió en el último fotograma. Lo lee el sistema de arrastre.
    delta: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))


@dataclass(slots=True)
class BloqueRitmico:
    """Aparece y desaparece a compás. Mega Man 2 (Wily 1), Celeste (cassette).

    Un bloque que desaparece **con el jugador encima** tiene que dejarlo caer,
    no atraparlo. El sistema de colisión lo consigue solo, porque el bloque
    deja de estar en la lista de sólidos.
    """

    visible_seg: float = 1.0
    oculto_seg: float = 1.0
    desfase: float = 0.0
    _t: float = 0.0

    @property
    def presente(self) -> bool:
        ciclo = self.visible_seg + self.oculto_seg
        if ciclo <= 0.0:
            return True
        return ((self._t + self.desfase) % ciclo) < self.visible_seg


@dataclass(slots=True)
class PlataformaHundible:
    """Se hunde al pisarla y vuelve sola. Cuphead (Perilous Piers).

    `retraso` es la ventana de decisión: si fuera cero, pisar sería morir y no
    habría nada que jugar.
    """

    retraso: float = 0.4
    velocidad_caida: float = 90.0
    reaparece_en: float = 3.0
    y_original: float = 0.0
    _pisada: float = 0.0
    _cayendo: bool = False
    _ausente: float = 0.0


# ══════════════════════════════════════════════════════════════
# F5.9 — sigilo
# ══════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════
# F5.14 — lianas y tirolesas
# ══════════════════════════════════════════════════════════════


@dataclass(slots=True)
class Liana:
    """Cuerda o enredadera por la que se sube y se baja.

    Donkey Kong Country (Ropey Rampage), Zelda, Spelunky, Castlevania.

    Por qué no es una plataforma vertical
    --------------------------------------
    Se podría simular con `Solido` estrechos apilados y dejar que el jugador
    salte entre ellos, y es lo que un estudiante intentaría primero. No
    funciona: sobre una columna de sólidos el jugador queda *al lado*, no
    *dentro*, y no puede subir sin saltar.

    Una liana necesita suspender la gravedad y dar movimiento vertical libre
    mientras se está agarrado, y eso es un **estado del jugador**, no geometría.
    De ahí `TrepandoState`.

    `ancho_de_agarre` es generoso a propósito. Con la anchura exacta de la
    cuerda —dos o tres píxeles— agarrarse sería un acto de puntería, y saltar
    hacia una liana y fallar por un píxel se lee como que el juego no responde.
    """

    rect: pygame.Rect
    #: Píxeles de margen a cada lado para poder agarrarse.
    ancho_de_agarre: int = 10
    #: Velocidad de subida y bajada, px/s.
    velocidad: float = 70.0


@dataclass(slots=True)
class Tirolesa:
    """Cable en diagonal por el que se desliza. DKC, Rayman, Ori.

    Se declara con dos puntos y no con un rectángulo porque **la pendiente es
    la mecánica**: una tirolesa horizontal es un pasillo, y una casi vertical es
    una caída. El ángulo decide si el tramo es un descanso o una carrera.

    `solo_de_bajada` está por defecto porque una tirolesa que sube gratis
    rompe cualquier nivel construido alrededor de saltos: el jugador la usa para
    llegar donde el diseñador no quería. Quien la quiera bidireccional puede
    pedirla, pero que no sea el descuido por omisión.
    """

    origen: pygame.Vector2
    destino: pygame.Vector2
    velocidad: float = 190.0
    #: Radio de enganche alrededor del cable, en píxeles.
    radio_de_enganche: float = 14.0
    solo_de_bajada: bool = True

    def punto_mas_cercano(self, p: pygame.Vector2) -> pygame.Vector2:
        """Proyección de `p` sobre el segmento, recortada a sus extremos.

        Recortada y no sobre la recta infinita: sin el recorte, un jugador que
        pasa por debajo del extremo se engancharía a un cable que no está ahí,
        y es de los fallos que más desconciertan porque el cable *se ve* lejos.
        """
        d = self.destino - self.origen
        largo2 = d.length_squared()
        if largo2 == 0.0:
            return pygame.Vector2(self.origen)
        t = max(0.0, min(1.0, (p - self.origen).dot(d) / largo2))
        return self.origen + d * t

    def progreso(self, p: pygame.Vector2) -> float:
        """0 en el origen, 1 en el destino."""
        d = self.destino - self.origen
        largo2 = d.length_squared()
        if largo2 == 0.0:
            return 1.0
        return max(0.0, min(1.0, (p - self.origen).dot(d) / largo2))


@dataclass(slots=True)
class ConoDeVision:
    """Detección por ángulo y distancia. MGS, Inside, Metroid Dread.

    Generaliza lo que César Ubáu escribió en `stage2_2/camara_seguridad.py`
    para su cámara de seguridad. Se sube al framework para que no tenga que
    reescribirlo cada estudiante que quiera un guardia, y se cita en el
    material de clase como Unidad II: es álgebra vectorial de las que se ven.
    """

    #: Vector unitario de mira.
    mira: pygame.Vector2
    alcance: float = 160.0
    #: Semiángulo del cono en grados. 30 da un cono de 60.
    semiangulo: float = 30.0
    #: Barrido: grados a cada lado y velocidad. 0 = fijo.
    barrido: float = 0.0
    velocidad_barrido: float = 45.0
    _fase: float = 0.0
    #: Lo escribe el sistema; lo leen la IA y el dibujado.
    ve_al_jugador: bool = False


@dataclass(slots=True)
class Alerta:
    """Normal → sospecha → alerta, y la vuelta lenta.

    La vuelta es lenta a propósito. Un guardia que olvida al instante convierte
    el sigilo en prueba y error sin coste; uno que no olvida nunca lo convierte
    en una partida perdida. Los segundos de memoria son la palanca de
    dificultad de todo el sistema.
    """

    nivel: float = 0.0
    subida_por_segundo: float = 2.0
    bajada_por_segundo: float = 0.35
    umbral_sospecha: float = 0.4
    umbral_alerta: float = 1.0

    @property
    def estado(self) -> str:
        if self.nivel >= self.umbral_alerta:
            return "alerta"
        if self.nivel >= self.umbral_sospecha:
            return "sospecha"
        return "tranquilo"


@dataclass(slots=True)
class Acosador:
    """Persigue y **no se puede matar**. Nemesis, SA-X, E.M.M.I., el conserje.

    `Salud.invulnerable` ya existiría para esto, pero un acosador necesita algo
    más: reaparecer. Retirarlo cuando el jugador lo pierde y devolverlo después
    es lo que produce la sensación de que sigue ahí fuera, y es más barato que
    simularlo fuera de pantalla.
    """

    velocidad: float = 55.0
    #: Distancia a la que se retira si lo pierde de vista.
    distancia_retirada: float = 480.0
    #: Segundos hasta volver a aparecer.
    reaparicion: float = 6.0
    _fuera: float = 0.0
