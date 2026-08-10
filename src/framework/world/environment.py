"""
Module: environment
System: framework.world
Description: AUD-358 — `EnvironmentState`, la foto del mundo en un fotograma.

Por qué existe esto
===================

Hasta ahora el ambiente de un escenario lo producían **tres sistemas
independientes que escribían directamente sobre sus consumidores**:

    RelojDeMundo ──→ _lighting.ambient_brightness, _post_processing
    Estacion ─────→ el mismo sitio, multiplicando
    WeatherSystem ─→ sus partículas, su capa, su clave de audio ambiente

Funciona, y tiene dos costes que se pagan cada vez que se añade algo. El
primero es que **nadie puede preguntar por el ambiente**: para saber si está
lloviendo hay que ir a buscar `_weather._climate`, un privado de la escena; el
enemigo que quisiera comportarse distinto de noche tendría que conocer el
reloj del escenario. El segundo es que el ambiente **sólo puede ser
decoración**: los tres sistemas terminan en el renderizador, así que nada de
lo que ocurre en el mundo puede cambiar una regla del juego.

`EnvironmentState` es la respuesta a las dos cosas: un **valor inmutable** que
`WorldSimulation` compone una vez por fotograma y que cualquiera puede leer.

    WorldSimulation ──→ EnvironmentState ──→ render / audio / gameplay

Reglas del contrato, y el porqué de cada una
============================================

1. **Es un valor, no un sistema.** `frozen=True`. Un consumidor no puede
   escribir en él, así que no puede haber dos sistemas discutiéndose el
   ambiente — que es exactamente el modo de fallo que este módulo viene a
   cerrar. Si algo tiene que cambiar el mundo, se lo pide a la simulación.

2. **Rango declarado, siempre.** Cada campo dice qué unidad y qué rango tiene.
   Un `0.5` sin rango obliga al consumidor a adivinar, y dos consumidores
   adivinan distinto.

3. **Lo derivado se deriva aquí, una vez.** `es_de_noche`, `suelo_mojado` o
   `factor_friccion` son propiedades de este objeto y no cuentas que cada
   consumidor repita. Tres copias de «¿está mojado?» con tres umbrales es
   cómo se acaba con lluvia que resbala en la física y no en el sonido.

4. **`neutro()` en vez de `None`.** Una escena sin simulación —un menú, un
   escenario que no pidió ciclo— devuelve el estado neutro, no `None`. Así
   ningún consumidor necesita una rama `if estado is None`, que es la rama
   que nunca se prueba.

Lo que este módulo NO hace
==========================

No simula: eso es `simulation.py`. No dibuja, no suena y no conoce a pygame.
Se puede construir, comparar e imprimir en una prueba sin arrancar SDL, y esa
es la propiedad que lo hace utilizable como contrato.
"""
from __future__ import annotations

from dataclasses import dataclass

#: Humedad a partir de la cual el suelo cuenta como mojado. No es un número
#: físico: es el punto en el que el jugador **debe notar** que llueve. Por
#: debajo, la lluvia es decoración; por encima, cambia cómo se frena.
UMBRAL_SUELO_MOJADO: float = 0.55

#: Cuánto se pierde de frenado con el suelo empapado, como fracción. 0,40
#: significa que en tormenta se frena al 60 % — se derrapa, pero el jugador
#: sigue pudiendo pararse donde quiere. Un suelo que quita el 80 % se lee como
#: un control roto, no como lluvia.
PERDIDA_MAXIMA_DE_FRICCION: float = 0.40

#: Ritmo de frenado horizontal en el suelo mojado, px/s², justo al cruzar el
#: umbral de humedad. A la velocidad de paseo (200 px/s) son ~0,09 s de
#: derrape; con la humedad al máximo, `factor_friccion` lo baja a 1.320 y el
#: derrape sube a ~0,15 s. Se busca que el jugador **note** la lluvia sin
#: perder el control: un frenado de 400 px/s² sería hielo, y el hielo ya tiene
#: su propio sistema (`ZonaDeFriccion` del TMX, AUD-236).
FRENADO_EN_MOJADO: float = 2_200.0

#: Las bandas del día, de la más luminosa a la más oscura. Son las que usa la
#: astronomía de verdad —los tres crepúsculos se definen por la altura del sol
#: bajo el horizonte— y aquí sirven para lo mismo que allí: nombrar los tramos
#: donde el cielo cambia deprisa. Un consumidor que sólo distinga `dia` y
#: `noche` no puede pintar la diferencia entre las 18:20 y las 19:00, que es
#: justo donde está el color.
FASES_DEL_DIA: tuple[str, ...] = (
    "dia",
    "crepusculo_civil",       # el sol acaba de ponerse; aún se lee un libro
    "crepusculo_nautico",     # se distingue el horizonte del mar
    "crepusculo_astronomico",  # ya se ven estrellas, queda claridad
    "noche",
)

#: Periodo sinódico lunar en días. El de verdad (29,530588…), no uno redondo:
#: el ciclo de la luna es material del curso de gráficas y un número inventado
#: aquí se copiaría en la práctica del alumno.
DIAS_DEL_MES_LUNAR: float = 29.530588


@dataclass(frozen=True, slots=True)
class EnvironmentState:
    """El ambiente del mundo en un fotograma. Inmutable, sin dependencias."""

    # ── Tiempo ────────────────────────────────────────────────────────
    #: Hora del día, 0 a 24. 12,0 es mediodía.
    hora: float = 12.0
    #: Días completos transcurridos desde que arrancó la simulación, 0-based.
    #: Es el calendario: la luna y las estaciones se cuentan con esto.
    dia: int = 0
    #: Clave de estación, de `framework.stage.seasons.ESTACIONES`.
    estacion: str = "summer"

    # ── Luz, ya compuesta (hora × estación) ───────────────────────────
    #: Multiplicador del `ambient_light` del mapa, 0 a 1.
    factor_ambiente: float = 1.0
    #: Tinte de la luz ambiente. (255, 255, 255) es «sin teñir».
    color_ambiente: tuple[int, int, int] = (255, 255, 255)
    #: Cuánto sumar al bloom base del escenario.
    bloom_extra: float = 0.0

    # ── Atmósfera ─────────────────────────────────────────────────────
    #: Clave de clima, de `WeatherSystem.CLIMATE_PARAMS`.
    clima: str = "clear"
    #: Cuánto cae, 0 (nada) a 1 (tormenta cerrada).
    precipitacion: float = 0.0
    #: Cuánta agua hay en el aire y en el suelo, 0 a 1. Sube con la lluvia y
    #: con la niebla, y es lo que consulta la física, no `clima`: preguntar
    #: por el nombre del clima obliga a cada consumidor a mantener su propia
    #: lista de «cuáles mojan».
    humedad: float = 0.0
    #: Viento lateral en px/s, con signo (negativo = hacia la izquierda).
    viento: float = 0.0
    #: Cuánto se ve, 1 (nítido) a 0 (nada). La niebla y la tormenta la bajan.
    visibilidad: float = 1.0

    #: Cobertura de nubes, 0 (cielo raso) a 1 (cerrado). Atenúa el sol, la
    #: luna y las estrellas, y ablanda las sombras.
    cobertura_nubes: float = 0.0

    # ── Astronomía ────────────────────────────────────────────────────
    #: Altura del sol sobre el horizonte, -1 (medianoche) a 1 (mediodía).
    #: 0 es el horizonte: amanecer subiendo, ocaso bajando.
    altura_solar: float = 1.0
    #: Fase lunar, 0 a 1. 0 y 1 son luna nueva; 0,5, llena.
    fase_lunar: float = 0.0
    #: Banda del día, de `FASES_DEL_DIA`. No es `día`/`noche`: el crepúsculo
    #: es donde ocurren los mejores cambios atmosféricos y merece nombre
    #: propio, porque un consumidor que sólo distinga dos casos no puede
    #: pintar la diferencia entre las 18:20 y las 19:00.
    fase_del_dia: str = "dia"

    # ── Derivados: se calculan aquí y en ningún otro sitio ────────────

    @property
    def es_de_noche(self) -> bool:
        """El sol está bajo el horizonte."""
        return self.altura_solar <= 0.0

    @property
    def luz_lunar(self) -> float:
        """Cuánta luna hay iluminando ahora mismo, 0 a 1.

        Cero de día — la luna se ve, pero no ilumina nada que importe— y de
        noche, la fracción del disco visible. Es lo que un escenario nocturno
        usa para que la noche de luna llena sea jugable y la de luna nueva
        dé miedo, sin que el escenario tenga que saber qué día es.
        """
        if not self.es_de_noche:
            return 0.0
        return 1.0 - abs(self.fase_lunar * 2.0 - 1.0)

    @property
    def suelo_mojado(self) -> bool:
        """Un solo umbral, aquí, para la física, el audio y el render."""
        return self.humedad >= UMBRAL_SUELO_MOJADO

    @property
    def factor_friccion(self) -> float:
        """Multiplicador del frenado del suelo, de 0,6 a 1,0.

        Éste es el campo que convierte el ambiente en jugabilidad y no en
        decoración: `lluvia → humedad → suelo mojado → fricción → control`.
        Es lineal a partir del umbral y está acotado por
        `PERDIDA_MAXIMA_DE_FRICCION` para que la tormenta más cerrada siga
        dejando el juego jugable — la misma decisión que `MIN_AMBIENTE` tomó
        con la noche.
        """
        if not self.suelo_mojado:
            return 1.0
        exceso = (self.humedad - UMBRAL_SUELO_MOJADO) / (1.0 - UMBRAL_SUELO_MOJADO)
        return 1.0 - PERDIDA_MAXIMA_DE_FRICCION * min(1.0, max(0.0, exceso))

    @property
    def frenado_del_suelo(self) -> float:
        """Ritmo de frenado horizontal, en px/s², para `PhysicsProfile.friccion`.

        Cero con el suelo seco, y cero significa **instantáneo**: es lo que
        hacen hoy los tres presets y lo que sienten los dieciséis escenarios
        existentes. Soltar el mando para en seco.

        Con el suelo mojado pasa a ser un ritmo finito y el jugador **derrapa**
        al soltar. Ése es el hilo entero del sistema —lluvia → humedad → suelo
        mojado → frenado → control— y es la primera vez que
        `PhysicsProfile.friccion` (AUD-336) tiene un consumidor: se escribió,
        se probó, y los tres presets la dejaban en 0.

        Sí, hay un salto: de instantáneo a `FRENADO_EN_MOJADO` en cuanto se
        cruza el umbral. Es deliberado y es la consecuencia de que
        `suelo_mojado` sea un booleano: el jugador tiene que **notar** que
        empezó a llover. Una rampa continua desde el suelo seco haría el
        cambio imperceptible, que es justo lo que este sistema viene a evitar.
        """
        if not self.suelo_mojado:
            return 0.0
        return FRENADO_EN_MOJADO * self.factor_friccion

    @classmethod
    def neutro(cls) -> EnvironmentState:
        """Mediodía de verano despejado: el mundo que no interfiere.

        Es lo que devuelve una escena sin simulación, y está elegido para que
        **todos los derivados sean la identidad**: factor de ambiente 1,
        tinte blanco, bloom extra 0, fricción ×1. Un consumidor que aplique
        el estado neutro obtiene exactamente el comportamiento de antes de
        que existiera este módulo, y eso es lo que permite conectarlo sin
        cambiar ni un escenario.
        """
        return cls()
