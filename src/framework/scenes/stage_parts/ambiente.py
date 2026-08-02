"""
El ambiente del escenario: luz, bloom, viñeta, partículas, estación y hora.

Extraído de `stage_scene.py` en AUD-152 sin cambiar una línea de lógica. Ver
`stage_parts/__init__.py` para por qué es un mixin y no un colaborador.

Todo lo de aquí comparte una misma regla de precedencia, y por eso está junto:

    propiedad del TMX  >  tabla por zona  >  valor por defecto del motor

Esa regla es el contrato con el estudiante: lo que escribe en Tiled manda, y
el motor sólo rellena lo que no dijo. Si cada sistema la resolviera a su
manera, un mapa se vería distinto según qué propiedad usara.
"""
from __future__ import annotations

import pygame

from src.framework.vfx.lighting import LightSource


class MezclaDeAmbiente:
    """Luz, post-procesado, partículas, estación y ciclo día/noche.

    Espera de la escena: `_stage_data`, `_lighting`, `_post_processing`,
    `_ambient_particles`, `_estacion`, `_reloj`, y el atributo de clase `ZONE`.
    """

    #: Brillo ambiente por zona cuando el TMX no declara `ambient_light`.
    #:
    #: F1.1 — antes esto era una cadena `if/elif` que además creaba las luces
    #: con coordenadas fijas escritas en el motor. Un estudiante que
    #: construyera su escenario en Tiled heredaba las dos luces del zone 0, en
    #: (80, 80) y (240, 80), estuviera ahí su nivel o no. Ahora las luces se
    #: colocan en el mapa y esta tabla sólo decide **cuánta oscuridad** hay si
    #: nadie lo dijo.
    #:
    #: El zone 0 valía 1.0 —sin oscurecer—, así que todo el sistema de
    #: iluminación era invisible en el único escenario terminado del juego.
    AMBIENT_BY_ZONE: dict[int, float] = {
        0: 0.62,   # prólogo: exterior nublado, se ve todo pero la luz se nota
        1: 0.50,
        2: 0.32,
        3: 0.22,
    }
    AMBIENT_DEFAULT: float = 0.55

    def _setup_lighting(self) -> None:
        """Prepara la iluminación del escenario a partir del TMX.

        Orden de precedencia, del más específico al más general:

        1. `ambient_light` en las propiedades del mapa.
        2. `AMBIENT_BY_ZONE[zone]`.
        3. `AMBIENT_DEFAULT`.

        Los focos vienen siempre del mapa (objetos de tipo `Light` en la capa
        `Objects`). Si el mapa no declara ninguno, el escenario queda iluminado
        sólo por la luz que acompaña al jugador, que es un resultado legítimo
        y además una pista visual clara de que faltan focos.
        """
        self._lighting.clear()
        self._player_light = None

        # BUG-075: si el TMX no declara zona, cae al atributo ZONE de la escena.
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        declarado = getattr(self._stage_data, "ambient_light", None)
        if declarado is not None:
            self._lighting.ambient_brightness = declarado
        else:
            self._lighting.ambient_brightness = self.AMBIENT_BY_ZONE.get(
                zone, self.AMBIENT_DEFAULT)

        self._stage_lights = [
            LightSource(
                position=pygame.Vector2(*spec.position),
                radius=spec.radius,
                color=spec.color,
                intensity=spec.intensity,
                flicker=spec.flicker,
                flicker_speed=spec.flicker_speed,
                flicker_amount=spec.flicker_amount,
            )
            for spec in getattr(self._stage_data, "lights", [])
        ]

    #: Bloom permanente por zona cuando el TMX no declara `bloom`.
    #:
    #: F1.2 — el bloom existía y sólo se encendía en ráfagas de 0,15 a 0,6 s al
    #: recoger un objeto o cambiar de fase el jefe. El resto del tiempo, cero.
    #: Un halo permanente y suave es lo que hace que la iluminación de F1.1 se
    #: lea como luz y no como manchas.
    BLOOM_BY_ZONE: dict[int, float] = {
        0: 0.18,   # prólogo: bruma tenue
        1: 0.22,
        2: 0.30,   # zonas de fuego: el halo hace el trabajo
        3: 0.35,
    }
    BLOOM_DEFAULT: float = 0.20

    #: Viñeta por zona. Sube al bajar la luz ambiente: cuanto más oscuro el
    #: nivel, más cerrado el encuadre.
    VIGNETTE_BY_ZONE: dict[int, float] = {0: 0.30, 1: 0.36, 2: 0.44, 3: 0.50}
    VIGNETTE_DEFAULT: float = 0.35

    def _setup_post_processing(self) -> None:
        """Fija bloom y viñeta del escenario a partir del TMX.

        Misma precedencia que la iluminación: propiedad del mapa, luego tabla
        por zona, luego valor por defecto. Así un estudiante puede escribir
        `bloom = 0.4` en Tiled y verlo, sin tocar una línea de Python.
        """
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        bloom = getattr(self._stage_data, "bloom", None)
        if bloom is None:
            bloom = self.BLOOM_BY_ZONE.get(zone, self.BLOOM_DEFAULT)
        self._post_processing.set_base_bloom(bloom)

        vineta = getattr(self._stage_data, "vignette", None)
        if vineta is None:
            vineta = self.VIGNETTE_BY_ZONE.get(zone, self.VIGNETTE_DEFAULT)
        self._post_processing.set_vignette(vineta)

    #: Partículas de ambiente por zona: (tipo, partículas por segundo).
    #:
    #: F1.3 — `AmbientParticleSystem.set_effect` no la llamaba nadie, así que
    #: el ritmo se quedaba en cero toda la partida. Medido en Stage 0 tras tres
    #: segundos de juego: 0 partículas. El sistema existía, se actualizaba y se
    #: dibujaba; no tenía nada que dibujar.
    AMBIENT_FX_BY_ZONE: dict[int, tuple[str, float]] = {
        0: ("spores", 14.0),   # prólogo: bosque infestado
        1: ("leaves", 10.0),
        2: ("embers", 18.0),
        3: ("ash", 22.0),
    }
    AMBIENT_FX_DEFAULT: tuple[str, float] = ("dust", 8.0)

    def _setup_ambient_particles(self) -> None:
        """Enciende las partículas de ambiente del escenario.

        Misma precedencia que la luz y el post-procesado: propiedad del mapa
        (`ambient_fx`, `ambient_fx_rate`), luego tabla por zona, luego valor por
        defecto. Un `ambient_fx` de `none` en el TMX apaga el efecto de forma
        explícita, que es distinto de no declararlo.
        """
        zone = self._stage_data.zone
        if zone is None:
            zone = getattr(self, "ZONE", 0)

        tipo = getattr(self._stage_data, "ambient_fx", "")
        ritmo = getattr(self._stage_data, "ambient_fx_rate", None)
        if not tipo:
            # Precedencia: mapa > estación > zona. La estación va antes que la
            # zona porque es una decisión explícita del autor del mapa y la
            # tabla por zona es sólo un respaldo del motor.
            if getattr(self._stage_data, "season", ""):
                tipo, ritmo_estacion = self._estacion.particulas
            else:
                tipo, ritmo_estacion = self.AMBIENT_FX_BY_ZONE.get(
                    zone, self.AMBIENT_FX_DEFAULT)
            if ritmo is None:
                ritmo = ritmo_estacion
        elif ritmo is None:
            ritmo = self.AMBIENT_FX_DEFAULT[1]

        self._ambient_particles.set_effect(tipo, ritmo)

    def _clima_efectivo(self) -> str:
        """Qué clima usa el escenario: el del mapa, o el que sugiere la estación.

        F2.2 — el orden importa y por eso vive en un método propio. Un autor
        que escribe `climate = fog` en un mapa de otoño quiere niebla, no la
        lluvia que trae la estación. La estación **sugiere**; no manda.

        Está extraído en vez de en línea dentro de `on_enter` porque una regla
        de precedencia que sólo se puede probar recargando un TMX entero se
        acaba probando de mentira: la primera versión de su prueba
        reimplementaba la regla en el propio test y por tanto no podía fallar.
        """
        declarado = getattr(self._stage_data, "climate", "")
        return declarado or self._estacion.clima

    def _setup_season(self) -> None:
        """Resuelve la estación del escenario. Ver `framework.stage.seasons`."""
        from src.framework.stage.seasons import estacion

        self._estacion = estacion(getattr(self._stage_data, "season", ""))

    def _setup_day_night(self) -> None:
        """Arranca el reloj del escenario a partir del TMX.

        F2.1: sin `day_length` el reloj queda congelado en su hora inicial y el
        escenario se comporta exactamente como antes de esta fase. Es
        deliberado: un prólogo de tres minutos no gana nada con un ciclo, y
        obligar a todos los mapas a tener uno sería imponer una decisión de
        diseño desde el motor.
        """
        from src.framework.stage.day_night import RelojDeMundo

        hora = getattr(self._stage_data, "start_hour", None)
        if hora is None:
            hora = self.HORA_POR_DEFECTO
        self._reloj = RelojDeMundo(
            hora_inicial=hora,
            duracion_dia=getattr(self._stage_data, "day_length", 0.0) or 0.0,
        )
        # Se guardan los valores base del escenario porque el ciclo los
        # **modula**: si se sobrescribieran, cada fotograma partiría del
        # resultado del anterior y la luz se iría a cero en unos segundos.
        self._ambiente_base = self._lighting.ambient_brightness
        self._bloom_base_escenario = self._post_processing._bloom_base
        self._aplicar_hora()

    #: Hora que se usa cuando el mapa no declara `start_hour`. Mediodía, es
    #: decir, el factor de ambiente 1.0: un escenario que no pide ciclo se ve
    #: exactamente con el `ambient_light` que escribió su autor.
    HORA_POR_DEFECTO = 12.0

    #: Suelo de luz ambiente aplicada. Por debajo de esto el nivel deja de ser
    #: jugable.
    #:
    #: F2.1: el ciclo **multiplica** el ambiente del escenario, así que los dos
    #: factores se componen. Medido en Stage 0, que declara `ambient_light`
    #: 0,70: a medianoche el factor 0,35 daba un ambiente aplicado de 0,245 y
    #: un brillo de pantalla de 12,7 sobre 255. El jugador no ve los enemigos.
    #: Una noche realista que impide jugar es un defecto, no una decisión
    #: artística: la hora se comunica con el color, que sí cambia por completo.
    MIN_AMBIENTE = 0.45

    def _aplicar_hora(self) -> None:
        """Traduce la hora actual, y la estación, a luz ambiente y bloom."""
        from src.framework.stage.seasons import aplicar_tinte

        luz = self._reloj.luz()
        self._lighting.ambient_brightness = max(
            self.MIN_AMBIENTE,
            self._ambiente_base * luz.factor_ambiente * self._estacion.factor_luz,
        )
        self._post_processing.set_base_bloom(
            self._bloom_base_escenario + luz.bloom_extra)
        # El tinte de la hora se aplica como color de la luz ambiente, y la
        # estación lo modula. Los dos son multiplicadores, así que se componen
        # sin que ninguno tenga que conocer al otro: a mediodía en verano el
        # resultado es casi blanco, y de madrugada en invierno, azul doble.
        self._lighting.ambient_color = aplicar_tinte(luz.color, self._estacion)

