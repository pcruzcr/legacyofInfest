"""
Module: simulation
System: framework.world
Description: AUD-358 — `WorldSimulation`: la autoridad del ambiente del mundo.

Qué es, en una frase
====================

El productor de `EnvironmentState`. Compone el reloj, el calendario, la
estación, la astronomía y el clima en **una** foto por fotograma, y a partir
de ahí el renderizador, el audio y la jugabilidad leen esa foto en vez de
hablar entre ellos.

    reloj → calendario → estación ─┐
                       astronomía ─┼→ EnvironmentState → render / audio / juego
                            clima ─┘

Qué cambia respecto a lo que había
==================================

Nada de lo que hay se tira. `RelojDeMundo` (`stage/day_night.py`), `Estacion`
(`stage/seasons.py`) y los climas de `WeatherSystem` siguen siendo los mismos
y siguen siendo la fuente de verdad de lo suyo. Lo que cambia es **quién habla
con quién**: hasta ahora los tres escribían directamente sobre `_lighting` y
`_post_processing` (`stage_parts/ambiente.py`), y por eso nadie podía
*preguntar* por el ambiente y el ambiente sólo podía ser decoración.

Tres decisiones que conviene no deshacer
========================================

**1. El mapa configura, no simula.** Un escenario declara `start_hour`,
`season` y `climate` y la simulación calcula el resto. Un mapa que escribiera
`ambient_light = 0.18`, `sun_angle = 37` y `fog_density = 0.6` a mano es un
mapa imposible de mantener: el día que se toque la curva de luz hay que
revisar los dieciséis. Y como el realismo y el diseño no siempre coinciden,
hay `forzar()`, que sustituye un campo del estado sin tocar la simulación —
ahí es donde un nivel narrativo rompe el realismo a propósito.

**2. Las cuentas caras no se hacen a 60 Hz.** La fase lunar no cambia dentro
de un fotograma ni dentro de un minuto. `update()` recalcula la parte astral
sólo cuando el **día** cambia, y la parte del día sólo cuando la **hora**
cambia lo bastante. Lo que sí es continuo —la luz, el viento— se interpola.

**3. La astronomía es un modelo, y se dice cuál.** No hay efemérides aquí: la
altura solar es un armónico y la fase lunar es el periodo sinódico real sobre
el contador de días. Es suficiente para que el mundo sea **coherente** —el sol
sale por donde salió ayer, la luna crece— y es honesto llamarlo modelo. Un
comentario que prometiera precisión astronómica sería una mentira que alguien
copiaría a su práctica.

Lo que este módulo NO hace
==========================

No dibuja nubes, no pinta auroras y no simula huracanes. Produce el **estado**
del que todo eso se alimentaría. La diferencia importa: los fenómenos son
consumidores del estado y se pueden añadir de uno en uno sin tocar esto, que
es exactamente lo que hace que la lista larga de fenómenos sea abordable.
Catálogo y prioridades en `docs/92_CATALOGO_DE_FENOMENOS.md`.
"""
from __future__ import annotations

import math
import random

from src.framework.stage.day_night import HORAS_POR_DIA, RelojDeMundo, luz_a_las
from src.framework.stage.seasons import POR_DEFECTO, aplicar_tinte, estacion
from src.framework.world.environment import DIAS_DEL_MES_LUNAR, EnvironmentState

#: Humedad, viento (px/s), cobertura de nubes, precipitación y visibilidad de
#: cada clima. Las cinco claves son las de `WeatherSystem.CLIMATE_PARAMS`, y
#: `test_la_tabla_cubre_los_climas_del_motor` falla si alguien añade un clima
#: allí y no aquí: dos tablas que se desincronizan en silencio son cómo un
#: clima nuevo acaba sin humedad y la lluvia deja de resbalar.
#:
#: La visibilidad sale de `overlay_alpha` del sistema de clima (`1 - a/255`),
#: no de un número nuevo: la capa gris que ya se pinta ES cuánto se deja de
#: ver, y tener dos fuentes para el mismo hecho garantiza que se separen.
CLIMAS: dict[str, dict[str, float]] = {
    #                humedad  viento  nubes  precipitación  visibilidad
    "clear": {"humedad": 0.15, "viento": 0.0, "nubes": 0.05,
              "precipitacion": 0.0, "visibilidad": 1.00},
    "rain":  {"humedad": 0.85, "viento": 15.0, "nubes": 0.80,
              "precipitacion": 0.60, "visibilidad": 0.88},
    "snow":  {"humedad": 0.45, "viento": 12.0, "nubes": 0.75,
              "precipitacion": 0.40, "visibilidad": 0.80},
    # La niebla no llueve: moja el aire, no el suelo. Por eso humedad alta y
    # precipitación cero — y por eso el suelo NO resbala con niebla, que es la
    # clase de distinción que se pierde si la física pregunta por el nombre
    # del clima en vez de por la humedad.
    "fog":   {"humedad": 0.50, "viento": 0.0, "nubes": 0.60,
              "precipitacion": 0.0, "visibilidad": 0.69},
    "storm": {"humedad": 1.00, "viento": 75.0, "nubes": 1.00,
              "precipitacion": 1.00, "visibilidad": 0.76},
}

def viento_de(clima: str, rng: random.Random) -> float:
    """Viento **con signo** del clima, en px/s. Negativo = hacia la izquierda.

    AUD-374 — existía por duplicado. `CLIMAS` daba la magnitud y
    `WeatherSystem._set_climate_params` sorteaba su propia tabla con
    `random.uniform`; que los números coincidieran —75 aquí frente al centro
    del `uniform(50, 100)` de allí, 15 frente a `uniform(-15, 15)`, 12 frente
    a `uniform(-12, 12)`— delata que era una decisión copiada, no dos.

    Vive aquí, con la tabla, porque el viento es un hecho del mundo: la
    dirección en la que sopla no puede depender de quién pregunte. El sistema
    de clima lo consume; ya no lo inventa.

    El signo lo pone quien llama y **se queda**: sortearlo en cada consulta
    del estado haría que la lluvia cambiase de lado por fotograma.
    """
    magnitud = CLIMAS.get(clima, CLIMAS["clear"])["viento"]
    if magnitud == 0.0:
        return 0.0
    return rng.choice((-1.0, 1.0)) * magnitud


#: Altura solar por debajo de la cual empieza cada banda. Los tres crepúsculos
#: de verdad se definen por grados bajo el horizonte (-6, -12, -18); aquí el
#: equivalente sobre la altura normalizada de `_altura_solar`.
_BANDAS: tuple[tuple[float, str], ...] = (
    (0.0, "dia"),
    (-0.10, "crepusculo_civil"),
    (-0.21, "crepusculo_nautico"),
    (-0.31, "crepusculo_astronomico"),
)


def _altura_solar(hora: float) -> float:
    """Altura del sol, -1 a 1, con un armónico sobre la hora.

    Cero a las 6 y a las 18 (el horizonte), 1 a mediodía y -1 a medianoche.
    Es un modelo, no una efeméride: no depende de la latitud ni del día del
    año, así que el sol sale siempre a la misma hora. A cambio es exacto,
    barato y reproducible, que es lo que un escenario necesita para que su
    iluminación sea la misma cada vez que se juega.
    """
    return math.sin(2.0 * math.pi * (hora - 6.0) / HORAS_POR_DIA)


def _azimut_solar(hora: float) -> float:
    """De qué lado viene la luz, -1 (este) a 1 (oeste) — AUD-399.

    Es el coseno del mismo ángulo del que `_altura_solar` toma el seno, o sea
    la otra proyección del mismo sol: a las 6 vale -1 (sale por el este y la
    sombra se alarga hacia el oeste), 0 a mediodía —sol arriba, sombra a
    plomo— y 1 a las 18.

    Se saca del mismo ángulo a propósito. Calcularlo con su propia fórmula
    dejaría dos modelos del sol que se pueden desincronizar, que es el defecto
    que GAP-050 documentó cuando había dos autoridades sobre un mismo dato.
    """
    return -math.cos(2.0 * math.pi * (hora - 6.0) / HORAS_POR_DIA)


def _fase_del_dia(altura: float) -> str:
    for umbral, nombre in _BANDAS:
        if altura >= umbral:
            return nombre
    return "noche"


def _fase_lunar(dia: int, desfase: float = 0.0) -> float:
    """Fase lunar 0-1 desde el contador de días. 0 nueva, 0,5 llena.

    El periodo es el sinódico real (29,530588 días) porque el ciclo de la luna
    es material del curso: un número redondo inventado aquí se copiaría a la
    práctica del alumno como si fuera el bueno.
    """
    return ((dia + desfase) % DIAS_DEL_MES_LUNAR) / DIAS_DEL_MES_LUNAR


class WorldSimulation:
    """La autoridad del ambiente. Un escenario la configura; ella calcula.

    Uso mínimo::

        mundo = WorldSimulation(hora_inicial=19.0, duracion_dia=240.0,
                                estacion="autumn", clima="storm")
        mundo.update(dt)
        estado = mundo.estado()      # EnvironmentState, listo para consumir
    """

    def __init__(
        self,
        hora_inicial: float = 12.0,
        duracion_dia: float = 0.0,
        estacion: str = POR_DEFECTO,
        clima: str = "clear",
        dia_inicial: int = 0,
        desfase_lunar: float = 0.0,
        rng: random.Random | None = None,
    ) -> None:
        # El reloj no se reimplementa: es el de `day_night.py`, con su curva de
        # luz medida en Stage 0 y su prueba de jugabilidad nocturna detrás.
        self._reloj = RelojDeMundo(
            hora_inicial=hora_inicial, duracion_dia=duracion_dia)
        self._estacion_nombre = str(estacion or POR_DEFECTO)
        self._clima = str(clima or "clear")
        self._dia = int(dia_inicial)
        self._desfase_lunar = float(desfase_lunar)
        self._hora_previa = self._reloj.hora
        #: Sustituciones del diseñador, por nombre de campo. Ver `forzar`.
        self._forzados: dict[str, object] = {}
        # AUD-374 — el azar de la simulación es suyo, no el global. Sembrarlo
        # es lo que permite repetir una tormenta en una prueba, y es el primer
        # trozo de GAP-042: un `Random` propio se puede fijar; el módulo
        # `random` lo comparte todo el proceso y no se puede aislar.
        self._rng = rng if rng is not None else random.Random()
        self._viento = viento_de(self._clima, self._rng)

    # ── Configuración ─────────────────────────────────────────────────

    @property
    def reloj(self) -> RelojDeMundo:
        """El reloj, para quien ya lo usaba. No se rompe a nadie."""
        return self._reloj

    @property
    def dia(self) -> int:
        return self._dia

    @property
    def clima(self) -> str:
        return self._clima

    def set_clima(self, nombre: str) -> None:
        self._clima = str(nombre or "clear")
        # La dirección se sortea **aquí** y no en `estado()`: el estado se
        # consulta por fotograma, así que sortear allí haría que la lluvia
        # cambiara de lado sesenta veces por segundo.
        self._viento = viento_de(self._clima, self._rng)

    def set_estacion(self, nombre: str) -> None:
        self._estacion_nombre = str(nombre or POR_DEFECTO)

    def forzar(self, **campos: object) -> None:
        """Sustituye campos del estado sin tocar la simulación.

        Es la válvula que el diseño necesita y que el realismo no da: la
        fase 5 de un nivel puede querer luna llena a las 22:00 de un día en
        que tocaría luna nueva, porque la escena se sostiene sobre esa luz.
        Forzar un campo **no** altera el reloj ni el calendario, así que
        quitar la sustitución devuelve el mundo coherente a donde estaba.

        `forzar(fase_lunar=0.5)` fija la luna; `forzar(fase_lunar=None)` la
        suelta.
        """
        for nombre, valor in campos.items():
            if valor is None:
                self._forzados.pop(nombre, None)
            else:
                self._forzados[nombre] = valor

    # ── Simulación ────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Avanza el mundo. Lo caro sólo se recalcula cuando cambia el día.

        El calendario se lleva detectando la vuelta del reloj: si la hora
        **retrocede** entre dos fotogramas es que pasó la medianoche. Contar
        con un acumulador aparte daría dos relojes que se desincronizan, que
        es el defecto que este módulo entero viene a evitar.
        """
        if self._reloj.congelado:
            return
        self._reloj.update(dt)
        hora = self._reloj.hora
        if hora < self._hora_previa:
            self._dia += 1
        self._hora_previa = hora

    def estado(self) -> EnvironmentState:
        """La foto del fotograma. Es lo único que los consumidores necesitan."""
        hora = self._reloj.hora
        est = estacion(self._estacion_nombre)
        luz = luz_a_las(hora)
        tiempo = CLIMAS.get(self._clima, CLIMAS["clear"])
        altura = _altura_solar(hora)

        # La luz compuesta es EXACTAMENTE la cuenta que `_aplicar_hora` hace
        # hoy en `stage_parts/ambiente.py`: hora × estación para el factor, y
        # el tinte de la estación sobre el color de la hora. Se replica aquí
        # —en vez de inventar una nueva— para que conectar la simulación no
        # cambie ni un píxel de los dieciséis escenarios existentes.
        factor = luz.factor_ambiente * est.factor_luz
        color = aplicar_tinte(luz.color, est)

        crudo = EnvironmentState(
            hora=hora,
            dia=self._dia,
            estacion=self._estacion_nombre,
            factor_ambiente=factor,
            color_ambiente=color,
            bloom_extra=luz.bloom_extra,
            clima=self._clima,
            precipitacion=tiempo["precipitacion"],
            humedad=tiempo["humedad"],
            # AUD-374 — el viento sale del atributo, no de la tabla: la tabla
            # sólo tiene magnitudes y el campo declara signo. La dirección se
            # decidió al fijar el clima y se mantiene hasta que cambie.
            viento=self._viento,
            visibilidad=tiempo["visibilidad"],
            cobertura_nubes=tiempo["nubes"],
            altura_solar=altura,
            azimut_solar=_azimut_solar(hora),
            fase_lunar=_fase_lunar(self._dia, self._desfase_lunar),
            fase_del_dia=_fase_del_dia(altura),
        )
        if not self._forzados:
            return crudo
        return self._sustituir(crudo)

    def _sustituir(self, crudo: EnvironmentState) -> EnvironmentState:
        """Aplica las sustituciones del diseñador sobre el estado calculado.

        Se ignoran en silencio los nombres que no son campos del estado: un
        `forzar(lluvia_de_ranas=1)` no debe tumbar el nivel de nadie a mitad
        de una demo de clase. Si el campo no existe, no hay nada que
        sustituir y la simulación sigue siendo coherente.
        """
        validos = {
            k: v for k, v in self._forzados.items()
            if k in EnvironmentState.__dataclass_fields__
        }
        return EnvironmentState(**{**_como_dict(crudo), **validos})  # type: ignore[arg-type]


def _como_dict(estado: EnvironmentState) -> dict[str, object]:
    """Los campos del estado como diccionario.

    `dataclasses.asdict` no vale: recorre en profundidad y convertiría la
    tupla del color en lista, así que el estado reconstruido dejaría de ser
    igual al original y las pruebas de igualdad mentirían.
    """
    return {n: getattr(estado, n) for n in EnvironmentState.__dataclass_fields__}
