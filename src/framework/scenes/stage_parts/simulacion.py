"""La mitad de `WorldSimulation` que vive en la escena — AUD-362.

Por qué es una parte propia
===========================
`ambiente.py` reunía dos trabajos distintos que se parecían: **resolver la
precedencia** de las propiedades del TMX (mapa > zona > motor) y **componer y
aplicar** el ciclo día/noche con la estación. El segundo dejó de ser trabajo
de la escena cuando `WorldSimulation` (AUD-358) pasó a componerlo: aquí sólo
queda montar la simulación desde el mapa y consumir su estado.

Separarlos no es cosmético. `_aplicar_hora` componía la cuenta *además* de
aplicarla, y eso es lo que impedía que nadie más pudiera preguntar por el
ambiente: para saber si llovía había que ir a `_weather._climate`, un privado
de otra parte. Ahora la escena publica `self.ambiente` —un `EnvironmentState`
inmutable— y cualquiera lo lee.

Lo que este módulo aporta al escenario
--------------------------------------
* `_setup_season` / `_setup_day_night` — el mapa **configura**: hora, estación
  y clima. La simulación calcula el resto.
* `_aplicar_hora` — consume el estado: luz ambiente, bloom, tinte y agarre.
* `_aplicar_agarre` — el hilo que convierte el ambiente en jugabilidad:
  lluvia → humedad → suelo mojado → frenado → control.
* `_estacion` — una **vista** de la estación que lleva la simulación, no una
  segunda copia del mismo hecho.
"""
from __future__ import annotations

import logging

from src.framework.vfx import pulso
from src.framework.world import EnvironmentState


class SimulacionDeEscenario:
    """El escenario monta un mundo y consume su ambiente.

    Espera de la escena: `_stage_data`, `_lighting`, `_post_processing`,
    `_player` (puede no existir aún) y `_clima_efectivo` (de `MezclaDeAmbiente`).
    """

    def _setup_season(self) -> None:
        """Resuelve la estación del escenario. Ver `framework.stage.seasons`.

        Asigna por la **propiedad** —el setter avisa a la simulación—;
        escribir `_estacion_nombre` a pelo no llegaba al dibujo.
        """
        self._estacion = str(getattr(self._stage_data, "season", "") or "")

    # AUD-362 — `_estacion` es una **vista** de la estación de la simulación,
    # no una copia. Se conserva como atributo (lectura/escritura) porque lo
    # usan `_setup_ambient_particles`, `_clima_efectivo`, pruebas y entregas.

    @property
    def _estacion(self):  # type: ignore[no-untyped-def]
        from src.framework.stage.seasons import estacion

        return estacion(getattr(self, "_estacion_nombre", ""))

    @_estacion.setter
    def _estacion(self, valor) -> None:  # type: ignore[no-untyped-def]
        from src.framework.stage.seasons import ESTACIONES, POR_DEFECTO, es_valida

        if isinstance(valor, str):
            # Un nombre mal escrito en Tiled produce un aviso y un escenario
            # jugable, no un error de carga: la misma decisión que toma
            # `seasons.estacion()` y por el mismo motivo — el estudiante que
            # escribe `invierno` necesita ver su nivel para darse cuenta.
            nombre = valor.strip().lower()
            self._estacion_nombre = nombre if es_valida(nombre) else POR_DEFECTO
        else:
            # Un `Estacion` no sabe cómo se llama, así que se busca. Son
            # cuatro entradas y la asignación ocurre al montar la escena o en
            # una prueba, nunca por fotograma.
            self._estacion_nombre = next(
                (n for n, e in ESTACIONES.items() if e == valor), POR_DEFECTO)
        simulacion = getattr(self, "_simulacion", None)
        if simulacion is not None:
            simulacion.set_estacion(self._estacion_nombre)

    def _setup_day_night(self) -> None:
        """Arranca el reloj del escenario a partir del TMX.

        F2.1: sin `day_length` el reloj queda congelado en su hora inicial —
        un prólogo de tres minutos no gana nada con un ciclo, y obligar a
        todos los mapas a tenerlo sería imponer diseño desde el motor.
        """
        from src.framework.world import WorldSimulation

        hora = getattr(self._stage_data, "start_hour", None)
        if hora is None:
            hora = self.HORA_POR_DEFECTO
        # AUD-362 — el escenario ya no habla con tres sistemas ambientales por
        # separado: monta **una** simulación y luego consume su estado. El
        # mapa configura (hora, estación, clima) y ella calcula el resto.
        self._simulacion = WorldSimulation(
            hora_inicial=hora,
            duracion_dia=getattr(self._stage_data, "day_length", 0.0) or 0.0,
            estacion=getattr(self, "_estacion_nombre", "") or "summer",
            clima=self._clima_efectivo(),
        )
        # `_reloj` se conserva como alias del reloj de la simulación: lo leen
        # las pruebas, `actualizaciones.py` y cualquier entrega que consultara
        # la hora. Es el mismo objeto, así que no hay dos relojes que
        # desincronizar — que es justamente lo que este cambio viene a evitar.
        self._reloj = self._simulacion.reloj
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
    #: jugable: a medianoche, 0,35 × 0,70 daba un brillo de pantalla de
    #: 12,7 sobre 255 y el jugador no veía los enemigos (F2.1). La hora se
    #: comunica con el color, que sí cambia por completo.
    MIN_AMBIENTE = 0.45

    #: Cuánto sube el suelo de luz con la luna llena (AUD-362). 0,10 sobre
    #: 0,45 es una noche clara frente a una cerrada: se nota al jugar sin
    #: convertir la noche en día, que es lo que haría 0,30.
    LUNA_LLENA_SUMA = 0.10

    def _aplicar_hora(self) -> None:
        """Aplica el ambiente del fotograma: luz, bloom, tinte y agarre.
        Con indoor/outdoor real: bajo techo la luz es cálida constante y no
        llueve — ver _es_indoor().

        AUD-362 — la escena **consume** un `EnvironmentState` que compone
        la simulación; los números son los de antes (lo fija
        `test_la_luz_compuesta_es_la_misma_que_calcula_la_escena_hoy`).
        Se conserva el nombre porque lo llaman `actualizaciones.py`, las
        pruebas y posiblemente alguna entrega.
        """
        estado = self._simulacion.estado()
        # Indoor/outdoor: bajo techo la lluvia y el ciclo se atenúan
        es_indoor = self._es_indoor()  # type: ignore[attr-defined]
        if es_indoor:
            # Indoor: luz cálida constante 0.85, sin variación día/noche, sin bloom extra nocturno
            # Se construye un estado indoor derivado: factor 0.85, tinte cálido, sin lluvia
            from src.framework.world.environment import EnvironmentState

            estado = EnvironmentState(
                hora=estado.hora,
                factor_ambiente=0.85,
                color_ambiente=(255, 230, 180),
                bloom_extra=0.02,
                clima="clear",
                humedad=0.0,
                viento=0.0,
                visibilidad=1.0,
                altura_solar=estado.altura_solar,
                azimut_solar=estado.azimut_solar,
                fase_lunar=estado.fase_lunar,
            )
        # AUD-362 — el suelo de luz de la noche sube con la luna.
        suelo = self.MIN_AMBIENTE
        if not es_indoor and estado.es_de_noche:
            suelo += self.LUNA_LLENA_SUMA * estado.luz_lunar
        self.ambiente = estado

        # AUD-425 — el pulso visual, la última pieza del reloj musical.
        #
        # `music_clock.py` sabía desde AUD-137 en qué punto del compás va la
        # música y **ningún consumidor visual lo miraba**: la información
        # estaba, faltaba enchufarla. Sin `bpm` en el mapa no hay reloj, así
        # que `factor_de_luz` devuelve 1,0 y los diecisiete escenarios se ven
        # exactamente igual que antes.
        #
        # Se aplica sobre el brillo ya compuesto y no sobre `_ambiente_base`
        # para que el latido no se acumule con el ciclo de día y noche: de
        # madrugada late poco porque hay poca luz que modular, que es lo que se
        # espera.
        # `getattr` y no `self._reloj_musical` a secas: esto es un **mixin**, y
        # lo usan escenas de prueba y escenarios que no montan el reloj. La
        # primera versión accedía al atributo directamente y tiraba cinco
        # pruebas con `AttributeError` — un adorno que tumba el fotograma que
        # decora, que es justo lo que AUD-413 vino a corregir en otro sitio.
        # AUD-598 — la base del fotograma puede venir de una
        # `AmbientLightZone` (GAP-072.4); su `valor` es la palabra final del
        # autor para ese tramo y NO se multiplica por la hora (doble oscurecido).
        base_fotograma = self._ambiente_base_del_fotograma()
        if base_fotograma != self._ambiente_base:
            self._lighting.ambient_brightness = min(1.0,
                base_fotograma
                * pulso.factor_de_luz(getattr(self, "_reloj_musical", None)))
        else:
            self._lighting.ambient_brightness = min(1.0, max(
                suelo, base_fotograma * estado.factor_ambiente,
            ) * pulso.factor_de_luz(getattr(self, "_reloj_musical", None)))
        self._post_processing.set_base_bloom(
            self._bloom_base_escenario + estado.bloom_extra)
        # El tinte de la hora ya viene compuesto con el de la estación: los dos
        # son multiplicadores y la simulación los compone sin que ninguno
        # tenga que conocer al otro. A mediodía en verano sale casi blanco; de
        # madrugada en invierno, azul doble.
        self._lighting.ambient_color = estado.color_ambiente
        self._aplicar_agarre(estado)
        self._aplicar_clima(estado)
        self._aplicar_grading(estado)
        self._aplicar_audio_ambiental(estado)
        # AUD-403 — el sol orienta las sombras (GAP-051). Hasta aquí el sistema
        # de luz sólo proyectaba desde focos, porque el dato para orientar una
        # sombra solar no existía hasta AUD-399.
        if self._lighting is not None:
            self._lighting.set_sombra_solar(estado.direccion_de_sombra)

    def _ambiente_base_del_fotograma(self) -> float:
        """Brillo base del fotograma con zonas de luz (GAP-072.4, AUD-604).

        Vive aquí —y no en `MezclaDeAmbiente`— porque `_aplicar_hora` es
        su único llamante y así las escenas mínimas que componen sólo
        `SimulacionDeEscenario` también lo tienen. Sin jugador o sin
        zonas: el base estático del mapa y nada cambia. Con ellas manda
        la **última declarada** que afecte al punto del jugador: dentro
        del rect su `valor`; en la banda de `fundido` interpola hacia el
        base; más lejos no existe.
        """
        import math

        base = getattr(self, "_ambiente_base", 1.0)
        rect_jugador = getattr(getattr(self, "_player", None), "rect", None)
        zonas = list(getattr(self, "_zonas_luz_ambiente", []) or [])
        if rect_jugador is None or not zonas:
            return base
        punto = rect_jugador.center
        elegido = base
        for zona in zonas:
            r = getattr(zona, "rect", None)
            if r is None:
                continue
            if r.collidepoint(punto):
                elegido = float(getattr(zona, "valor", 1.0))
                continue
            fundido = int(getattr(zona, "fundido", 0) or 0)
            if fundido <= 0:
                continue
            dx = max(r.left - punto[0], punto[0] - r.right, 0)
            dy = max(r.top - punto[1], punto[1] - r.bottom, 0)
            distancia = math.hypot(dx, dy)
            if distancia < fundido:
                # 0 en el borde (= valor) → 1 en el límite del fundido (= base).
                t = distancia / float(fundido)
                elegido = base + (
                    float(getattr(zona, "valor", 1.0)) - base) * (1.0 - t)
        return elegido

    def _aplicar_audio_ambiental(self, estado: EnvironmentState) -> None:
        """El ambiente se oye — AUD-402 (GAP-051).

        Se **modula** el volumen del bus en vez de fijarlo: fijarlo pisaría
        la preferencia del jugador que ese bus existe para respetar.
        """
        # `getattr` sobre el propio `self` y no `self.context` a secas: este
        # mixin lo usan escenas mínimas de prueba que no montan contexto, y una
        # línea de audio no puede tumbarlas.
        contexto = getattr(self, "context", None)
        audio = getattr(contexto, "audio", None) if contexto is not None else None
        if audio is None or not hasattr(audio, "set_ambient_volume"):
            return
        base = 1.0
        mezcla = getattr(audio, "mezcla", None)
        if mezcla is not None and hasattr(mezcla, "volumen_de"):
            from src.engine.audio.mixer_buses import BUS_AMBIENTE

            base = mezcla.volumen_de(BUS_AMBIENTE)
        audio.set_ambient_volume(base * estado.intensidad_sonora)

    def _aplicar_grading(self, estado: EnvironmentState) -> None:
        """La corrección de color, desde el ambiente — AUD-401 (GAP-051).

        La matriz fija de `gl_pipeline` no tocaba nadie: efecto compilado y
        alimentado con la identidad. Se publica por `gpu_effects` y no
        tocando el renderer porque la escena **no puede alcanzarlo** — el
        contexto expone `usar_gl`, deliberadamente, para no arrastrar
        ModernGL al framework.
        """
        from src.engine.core import gpu_effects

        gpu_effects.publish_color_matrix(estado.matriz_de_color)

    def _cambiar_clima(self, nombre: str) -> None:
        """Cambia el clima del mundo. **Ésta** es la puerta — AUD-374.

        Un escenario que quiera tormenta en su tercer acto la pide aquí, no
        al VFX: el clima decide humedad, viento y visibilidad, y de la
        humedad cuelga el control del jugador (AUD-362). Medido antes de
        que existiera: los actos de tormenta del 4-1 **nunca resbalaron**,
        con el hilo entero construido — el dato llegaba caducado.
        """
        self._simulacion.set_clima(nombre)
        self._aplicar_hora()
        # AUD-500 — y el ambiente sonoro sigue al clima.
        #
        # Esta es «la puerta» del clima, pero no tocaba el audio: el ambiente
        # se cableaba una sola vez en `on_enter` y no volvía a mirarse. El
        # clima sí cambia en mitad de la partida —el 4-1 lo hace seis veces—,
        # así que la lluvia del mapa seguía sonando aunque el cielo se
        # despejara. Va después de `_aplicar_hora`, que es quien deja al
        # sistema de clima al día para que `get_ambient_audio_key` acierte.
        self._aplicar_ambiente_del_clima()

    def _aplicar_ambiente_del_clima(self) -> None:
        """Pone, funde o **quita** el ambiente sonoro que pide el clima.

        AUD-500 — vivía en `on_enter`, así que se cableaba una vez y el
        clima de mitad de partida (el 4-1 cambia seis veces) dejaba la
        lluvia sonando sobre cielo limpio — *«el sonido de la lluvia queda
        pegado»*. Y `AMBIENTES["clear"]` es `None`: despejar tiene que
        **parar** lo que hubiera. El `getattr` tolera escenas mínimas sin
        sistema de clima, como `_clima_efectivo`.
        """
        from src.engine.core import settings

        clima = getattr(self, "_weather", None)
        audio = getattr(getattr(self, "context", None), "audio", None)
        if clima is None or audio is None:
            return
        ruta_relativa = clima.get_ambient_audio_key()
        if not ruta_relativa:
            if getattr(audio, "_ambient_active", False):
                audio.stop_ambient()
            return
        ruta = settings.ASSETS_DIR / ruta_relativa
        if not ruta.exists():
            logging.getLogger(__name__).warning(
                "el clima pide %s y no está en el disco", ruta,
            )
            return
        # AUD-149 — se FUNDE si ya había ambiente sonando. Cortar en seco y
        # arrancar otro se oye como un fallo.
        if getattr(audio, "_ambient_active", False):
            audio.crossfade_ambient(ruta, duration=1.5, volume=0.3)
        else:
            audio.play_ambient(ruta, volume=0.3)

    def _aplicar_clima(self, estado: EnvironmentState) -> None:
        """El mundo dice qué tiempo hace; el VFX lo pinta — AUD-374.
        Indoor/outdoor real: bajo techo la lluvia/p polvo se atenúa y el viento no entra.
        """
        clima = getattr(self, "_weather", None)
        if clima is None:
            return
        if clima.climate != estado.clima:
            clima.set_climate(estado.clima)
        clima.aplicar_viento(estado.viento)
        # Indoor/outdoor: si está bajo techo, atenuar lluvia y viento, intensificar polvo
        try:
            indoor = 1.0 if self._es_indoor() else 0.0
            prev = getattr(clima, "_indoor_factor", 0.0)
            cur = prev * 0.9 + indoor * 0.1
            clima.set_indoor_factor(cur)
            # Polvo ambiental: indoor más denso (rayo de luz), outdoor tenue
            amb = getattr(self, "_ambient_particles", None)
            if amb is not None and hasattr(amb, "set_indoor_factor"):
                amb.set_indoor_factor(cur)
        except Exception:
            pass

    #: El ambiente antes de que exista simulación: mediodía despejado, que
    #: es la identidad. Una escena preguntada antes de `on_enter` responde
    #: un estado válido en vez de reventar, y ningún consumidor necesita
    #: una rama `if ambiente is None` — la rama que nunca se prueba.
    ambiente = EnvironmentState.neutro()

    def _es_indoor(self) -> bool:
        """¿El jugador está bajo techo? Vista-agnóstico: rect collide, funciona en lateral/cenital/isométrica."""
        try:
            player = getattr(self, "_player", None)
            if player is None or not hasattr(player, "rect"):
                return False
            # Si el mapa no declara cielo (cielo=False) es indoor global
            if not getattr(self._stage_data, "cielo", True):
                # Cielo apagado = interior puro (ej. caverna, hub interior)
                # Pero si no hay IndoorZone, se respeta; si hay, se usa el rect
                zones = getattr(self._stage_data, "indoor_zones", []) or []
                if not zones:
                    return True
            zones = getattr(self._stage_data, "indoor_zones", []) or []
            if not zones:
                return False
            pr = player.rect
            for z in zones:
                if z.colliderect(pr):
                    return True
            return False
        except Exception:
            return False

    def _aplicar_agarre(self, estado: EnvironmentState) -> None:
        """El suelo mojado hace derrapar al jugador — AUD-362.

        Es el hilo que convierte el ambiente en jugabilidad y no en decoración:
        `lluvia → humedad → suelo mojado → frenado → control`. Con el suelo
        seco el frenado es 0, que en `PhysicsProfile` significa instantáneo, o
        sea exactamente lo que hacen hoy los dieciséis escenarios.

        El jugador puede no existir todavía (el ambiente se monta antes que
        las entidades) y una entrega puede tener un jugador sin perfil: en los
        dos casos no hay nada que ajustar y no es un error.
        """
        jugador = getattr(self, "_player", None)
        perfil = getattr(jugador, "perfil", None)
        if perfil is None:
            return
        # Indoor: el suelo no se moja bajo techo, aunque llueva fuera
        if self._es_indoor():
            perfil.friccion = 0.0
            return
        perfil.friccion = (
            estado.frenado_del_suelo if estado.suelo_mojado else 0.0)

