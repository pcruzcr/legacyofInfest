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

        Asigna por la **propiedad**, no por el atributo de respaldo: el
        `setter` es quien avisa a la simulación. La primera versión escribía
        `_estacion_nombre` directamente y las pruebas de estaciones se
        quedaron en rojo — cambiar la estación después de montar el escenario
        no llegaba al dibujo, que es exactamente el defecto que este cambio
        viene a cerrar. Que el camino corto no funcione es la propiedad
        buena: sólo hay una manera de cambiar la estación.
        """
        self._estacion = str(getattr(self._stage_data, "season", "") or "")

    # AUD-362 — `_estacion` pasa a ser una **vista** de la estación que lleva
    # la simulación, no un objeto aparte. Antes eran dos: la escena guardaba
    # su `Estacion` y componía la luz con ella, y ahora quien compone es
    # `WorldSimulation`. Dejar las dos habría sido el defecto de siempre —dos
    # sistemas con su copia del mismo hecho— y la primera vez que alguien
    # cambiara una, la otra seguiría mandando en el dibujo.
    #
    # Se conserva como atributo (lectura y escritura) porque lo usan
    # `_setup_ambient_particles`, `_clima_efectivo`, las pruebas y
    # posiblemente alguna entrega: asignarle una estación sigue funcionando y
    # ahora, además, llega hasta la luz.

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

        F2.1: sin `day_length` el reloj queda congelado en su hora inicial y el
        escenario se comporta exactamente como antes de esta fase. Es
        deliberado: un prólogo de tres minutos no gana nada con un ciclo, y
        obligar a todos los mapas a tener uno sería imponer una decisión de
        diseño desde el motor.
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
    #: jugable.
    #:
    #: F2.1: el ciclo **multiplica** el ambiente del escenario, así que los dos
    #: factores se componen. Medido en Stage 0, que declara `ambient_light`
    #: 0,70: a medianoche el factor 0,35 daba un ambiente aplicado de 0,245 y
    #: un brillo de pantalla de 12,7 sobre 255. El jugador no ve los enemigos.
    #: Una noche realista que impide jugar es un defecto, no una decisión
    #: artística: la hora se comunica con el color, que sí cambia por completo.
    MIN_AMBIENTE = 0.45

    #: Cuánto sube el suelo de luz con la luna llena (AUD-362). 0,10 sobre
    #: 0,45 es una noche clara frente a una cerrada: se nota al jugar sin
    #: convertir la noche en día, que es lo que haría 0,30.
    LUNA_LLENA_SUMA = 0.10

    def _aplicar_hora(self) -> None:
        """Aplica el ambiente del fotograma: luz, bloom, tinte y agarre.

        AUD-362 — antes esto **componía** la cuenta (hora × estación) además de
        aplicarla, y hacía lo mismo que `WorldSimulation` hace ahora. Componer
        y aplicar en el mismo sitio es lo que impedía que nadie más pudiera
        preguntar por el ambiente: para saber si llovía había que ir a un
        privado de la escena.

        Ahora la escena **consume** un `EnvironmentState`. Los números son
        exactamente los de antes —lo fija
        `test_la_luz_compuesta_es_la_misma_que_calcula_la_escena_hoy` sobre 7
        horas × 4 estaciones—, así que los dieciséis escenarios existentes se
        ven igual.

        Se conserva el nombre porque lo llaman `actualizaciones.py`, las
        pruebas y posiblemente alguna entrega.
        """
        estado = self._simulacion.estado()
        # AUD-362 — el suelo de luz de la noche sube con la luna. Es la
        # primera consecuencia jugable de la astronomía: una noche de luna
        # llena se ve y una de luna nueva da miedo, sin que el escenario
        # tenga que saber qué día es ni tocar una propiedad del mapa.
        # `luz_lunar` ya vale 0 de día, así que esto no toca el mediodía.
        suelo = self.MIN_AMBIENTE
        if estado.es_de_noche:
            suelo += self.LUNA_LLENA_SUMA * estado.luz_lunar
        #: El ambiente de este fotograma, público. Ésta es la API que faltaba:
        #: un enemigo que quiera comportarse distinto de noche, o un efecto
        #: que quiera saber si llueve, leen esto y no un privado ajeno.
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
        # `AmbientLightZone` bajo los pies del jugador (GAP-072.4); sin
        # zonas es el base estático del mapa y nada cambia.
        #
        # Cuando una zona manda, su `valor` es la PALABRA FINAL del autor
        # para ese tramo: se aplica tal cual —sólo lo modula el pulso del
        # reloj musical— y NO se multiplica por la hora. Multiplicarlo era
        # oscurecer dos veces: en el 4-1b, mina congelada a las 2 AM
        # (factor 0.59), el 0.25 del abismo componía a 0.147 — negro sobre
        # negro. El suelo nocturno tampoco rige aquí: esa oscuridad es
        # diseño, no ciclo horario.
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

    def _aplicar_audio_ambiental(self, estado: EnvironmentState) -> None:
        """El ambiente se oye — AUD-402 (GAP-051).

        `sonido.py` es despacho de efectos por eventos, y nada leía el clima:
        el canal de ambiente y su bus existían desde AUD-149 y sonaban igual en
        calma que en tormenta.

        Se **modula** el volumen del bus en vez de fijarlo. Llamar a
        `set_ambient_volume` con un número propio pisaría la preferencia del
        jugador, que es lo que ese bus existe para respetar: aquí sólo se
        multiplica lo que él eligió por lo que hace el tiempo.
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

        La pasada existía en `gl_pipeline.py` con una matriz **fija en el
        config** que no tocaba nadie: un efecto compilado y alimentado con la
        identidad, o sea apagado de hecho. Aquí es donde se entera de la hora,
        de la estación y de la niebla.

        Se publica por `gpu_effects` y no tocando el renderer porque una escena
        **no puede alcanzarlo**: el contexto expone `usar_gl` y no el objeto,
        deliberadamente, para que el framework no arrastre ModernGL. Es el mismo
        canal que usa el bloom. Sin tarjeta, `App` no lee la publicación y no
        pasa nada — que es exactamente lo que pasaba antes de este lote.
        """
        from src.engine.core import gpu_effects

        gpu_effects.publish_color_matrix(estado.matriz_de_color)

    def _cambiar_clima(self, nombre: str) -> None:
        """Cambia el clima del mundo. **Ésta** es la puerta — AUD-374.

        Un escenario que quiera tormenta en su tercer acto la pide aquí, no al
        sistema que dibuja la lluvia. La diferencia no es de estilo: el clima
        decide humedad, viento, visibilidad y nubes, y de la humedad cuelga el
        suelo mojado y el control del jugador (AUD-362). Pedírselo al VFX deja
        todo eso en el clima del TMX para siempre.

        Medido antes de existir esta puerta, con la secuencia real de
        `stage4_1` —mapa `fog`, acto `storm` vía `WeatherSystem.set_climate`—:
        humedad 0,50 y `suelo_mojado` en falso. Sus actos de tormenta **nunca
        resbalaron**, con el hilo entero construido y consumido. El dato
        llegaba caducado, que se ve peor que si no llegara.

        El sistema de clima se entera solo: `_aplicar_hora` le pasa el clima y
        el viento del estado en el mismo sitio donde reparte la luz.
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

        AUD-500 — esto vivía dentro de `StageScene.on_enter`, así que se
        cableaba una sola vez al cargar el escenario y no volvía a mirarse.
        El clima sí cambia en mitad de la partida —`_cambiar_clima` es su
        puerta, y el 4-1 la usa seis veces—, de modo que el ambiente se
        quedaba con el del mapa para siempre. Reportado jugando: *«el sonido
        de la lluvia queda pegado»*.

        Y no basta con arrancar: `WeatherSystem.AMBIENTES["clear"]` es
        `None`, así que despejar el cielo tiene que **parar** lo que hubiera.
        Antes no entraba en ninguna rama y la lluvia seguía sonando sobre un
        cielo limpio.

        Vive aquí y no en `stage_scene` para que esté junto a `_cambiar_clima`,
        que es quien lo llama. El `getattr` sobre `self._weather` es el mismo
        patrón que usa `_clima_efectivo` unas líneas más abajo: una escena
        mínima —las de las pruebas, las entregas parciales— compone esta
        parte sin tener sistema de clima, y no debe reventar por eso.
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

        Antes iba al revés y por dos caminos que no se hablaban: el clima
        llegaba al `WeatherSystem` como cadena desde `_clima_efectivo()`, y el
        `EnvironmentState` calculaba el suyo en paralelo. El viento era el caso
        extremo de esa separación —se calculaba cada fotograma y **nadie lo
        leía**, mientras el sistema de clima sorteaba uno propio con su
        segunda tabla de valores.

        La comparación se hace **aquí** y no se delega en la guarda interna de
        `set_climate`. Las dos evitan que se vacíe el emisor, pero
        `test_el_acto_se_aplica_una_vez_y_no_en_cada_fotograma` vigila que la
        llamada no ocurra, no que sea inocua — y con razón: esa prueba salió de
        una comprobación de mutación, donde reaplicar el clima sin parar dejaba
        todo en verde. Apoyarse en la guarda ajena convierte un invariante
        comprobado en una propiedad de la que depende otro módulo sin decirlo.

        El sistema puede no existir todavía —el ambiente se monta antes que
        los efectos— y una entrega puede no tenerlo: en los dos casos no hay
        nada que pintar y no es un error, igual que en `_aplicar_agarre` con
        el jugador.
        """
        clima = getattr(self, "_weather", None)
        if clima is None:
            return
        if clima.climate != estado.clima:
            clima.set_climate(estado.clima)
        clima.aplicar_viento(estado.viento)

    #: El ambiente antes de que exista simulación: mediodía despejado, que
    #: es la identidad. Una escena preguntada antes de `on_enter` responde
    #: un estado válido en vez de reventar, y ningún consumidor necesita
    #: una rama `if ambiente is None` — la rama que nunca se prueba.
    ambiente = EnvironmentState.neutro()

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
        # La guarda es explícita, y no sólo `frenado_del_suelo` (que ya
        # devuelve 0 en seco), para que quien lea esto vea la condición que
        # importa: el suelo mojado es lo que cambia la regla.
        perfil.friccion = (
            estado.frenado_del_suelo if estado.suelo_mojado else 0.0)

