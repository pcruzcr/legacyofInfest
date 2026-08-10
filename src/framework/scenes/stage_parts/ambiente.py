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

from src.engine.core import settings
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

    def _configurar_vfx_opcionales(self) -> None:
        """Enciende la niebla de guerra y el efecto de agua si el mapa los pide.

        Los dos estaban escritos, documentados (`docs/46_`, `docs/47_`) y con
        pruebas que los ejercitaban en aislamiento, y **ninguna escena los
        instanciaba**: un jugador no podía llegar a ellos por ningún camino. Es
        el mismo patrón que el nado y que el ultimate.

        Se activan por propiedad de mapa y no por defecto porque los dos pintan
        una superficie del tamaño de la pantalla en cada fotograma. Encenderlos
        siempre le cobraría ese coste a los catorce escenarios que no los
        quieren.
        """
        from src.framework.vfx.fog_of_war import FogOfWar
        from src.framework.vfx.water_effect import WaterEffect

        datos = self._stage_data
        self._niebla = None
        self._agua_vfx = None

        radio = getattr(datos, "fog_of_war", 0.0)
        if radio and radio > 0:
            self._niebla = FogOfWar(radius=int(radio))
        if getattr(datos, "water_effect", False):
            self._agua_vfx = WaterEffect()
            # AUD-240 — el agua se configura desde el mapa.
            #
            # `docs/47` documenta cinco mandos y decía «all adjustable via
            # `set_params()`». Nadie la llamaba: aquí se construía un
            # `WaterEffect()` a secas, así que el charco de una cueva y el mar
            # de un acantilado ondulaban exactamente igual. Los `getattr` con
            # defecto son por las entregas de estudiante que traen su propio
            # `StageData` sin estos campos.
            self._agua_vfx.set_params(
                speed=float(getattr(datos, "water_speed", 1.5)),
                amplitude=int(getattr(datos, "water_amplitude", 4)),
                frequency=float(getattr(datos, "water_frequency", 0.04)),
                alpha=int(getattr(datos, "water_alpha", 100)),
                tint=tuple(getattr(datos, "water_tint", (40, 80, 160))),
            )

    def _publicar_los_rayos_de_luz(self) -> None:
        """Enciende los rayos volumétricos y decide de qué luz salen.

        AUD-226 — el sombreador necesita un foco, y la tubería no tiene forma
        de saber cuál: sólo ve una textura de luz ya compuesta, sin separar
        los focos que la formaron. Quien sí lo sabe es la escena.

        Se elige la luz **más fuerte que esté en pantalla**, ponderando
        intensidad y radio: es la que domina la iluminación del fotograma y,
        por tanto, la que el ojo lee como fuente. Elegir la más cercana al
        jugador daría rayos que saltan de una farola a otra al caminar.

        Si el escenario pide rayos y no hay ninguna luz visible, se apagan en
        vez de dejarlos en el centro de la pantalla: un abanico saliendo de la
        nada es peor que ninguno.
        """
        fuerza = getattr(self._stage_data, "god_rays", 0.0)
        if not fuerza or fuerza <= 0:
            return

        from src.engine.core import gpu_effects

        w, h = settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT
        off = self._camera.offset
        mejor = None
        mejor_peso = 0.0
        for luz in self._lighting.lights:
            sx = luz.position.x - off.x
            sy = luz.position.y - off.y
            radio = luz.get_current_radius()
            # Fuera de pantalla con todo su radio: no aporta nada al fotograma.
            if sx + radio < 0 or sx - radio > w or sy + radio < 0 or sy - radio > h:
                continue
            peso = luz.get_current_intensity() * radio
            if peso > mejor_peso:
                mejor_peso = peso
                mejor = (sx, sy)

        if mejor is None:
            return
        # A UV, y con la Y volteada: la tubería sube la escena invertida
        # (`pygame.image.tostring(..., True)`) y el sombreador muestrea en ese
        # sistema. Es el mismo desfase que documenta `region_to_gl_uv`.
        gpu_effects.publish_god_rays(
            (mejor[0] / w, 1.0 - mejor[1] / h), float(fuerza),
        )

    def _capture_enemy_trails(self, dt: float) -> None:
        """Estela para los enemigos que se mueven rápido, jefes incluidos.

        Se usa un `TrailSystem` aparte del jugador a propósito: los dos
        comparten un único temporizador de intervalo, así que meterlos en el
        mismo sistema haría que el jugador y el jefe se robaran capturas y
        ninguno de los dos dejara una estela continua.

        La velocidad se deduce del desplazamiento entre fotogramas porque los
        enemigos **no tienen atributo `velocity`**: a diferencia del jugador,
        mueven `position` directamente. El primer intento comprobaba
        `entity.velocity` y por tanto nunca capturaba nada, lo que habría
        pasado por una característica que "no se nota".
        """
        if self._stage_data is None or dt <= 0:
            return
        mas_rapido = None
        mejor_velocidad = self.ENEMY_TRAIL_SPEED
        for entity in self._stage_data.entity_list:
            if entity.rect is None or not getattr(entity, "visible", True):
                continue
            anterior = self._enemy_prev_x.get(id(entity))
            self._enemy_prev_x[id(entity)] = entity.position.x
            if anterior is None:
                continue
            velocidad = abs(entity.position.x - anterior) / dt
            if velocidad > mejor_velocidad:
                mejor_velocidad = velocidad
                mas_rapido = entity

        if mas_rapido is None:
            return
        # Rojo tenue: se distingue del azul del jugador de un vistazo, que es
        # lo que hace falta cuando las dos estelas se cruzan.
        self._enemy_trail_system.capture_at(
            mas_rapido.position.x, mas_rapido.position.y,
            (mas_rapido.rect.width, mas_rapido.rect.height),
            (255, 90, 70, 110),
        )
