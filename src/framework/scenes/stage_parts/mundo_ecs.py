"""
El mundo ECS del escenario: montarlo, poblarlo y consultarlo.

Extraído de `stage_scene.py` en AUD-299 sin cambiar una línea de lógica.

Por qué es un grupo cohesivo
============================
Los tres métodos son el ciclo de vida del `World` visto desde la escena:
declarar en qué orden corren los once sistemas, volcar dentro lo que el TMX
declaró, y preguntarle por lo que el jugador está agarrando.

El orden del planificador es lo que más se agradece tener junto y aparte: es una
lista de fases con un porqué por línea —las plataformas se mueven antes de que
el jugador resuelva colisiones, la fricción va sobre la posición ya resuelta— y
leerla intercalada entre el HUD y el minimapa la hacía invisible.
"""
from __future__ import annotations

from src.engine.input.action_map import Action
from src.framework.ecs import systems as ecs_systems
from src.framework.ecs.components import EsJugador, Salud, Velocidad
from src.framework.ecs.scheduler import Fase, Planificador
from src.framework.ecs.world import World
from src.framework.entities.base_entity import BaseEntity


class MundoDelEscenario:
    """El ECS de la escena: planificador, población y agarres.

    Espera de la escena: `_mundo`, `_stage_data`, `_player` y la entrada.
    """

    @staticmethod
    def _construir_planificador() -> Planificador:
        """El orden de un fotograma de mecánicas, declarado una sola vez.

        F5.11 — esto **sustituye** a `_mundo_ecs_paso`, que llamaba a los once
        sistemas a mano. Aquella función existía por un motivo concreto: los
        sistemas de sigilo recibían el rectángulo del jugador por parámetro, y
        con una firma distinta a `Sistema` no cabían en el planificador. Ahora
        lo buscan por su marca `EsJugador` y todos tienen la misma firma.

        La diferencia no es estética. Con la llamada a mano, el orden vivía en
        el cuerpo de un método de la escena y sólo se podía leer entero
        leyéndolo entero; una mecánica nueva se insertaba «donde pareciera». Con
        el planificador, cada sistema declara **en qué fase** corre, el orden
        sale de ahí, y `framework/ecs/scheduler.py` explica cada fase con los
        fallos concretos que produce equivocarse.

        Además el planificador mide cada sistema por separado, así que cuando el
        fotograma se pase de presupuesto se sabrá cuál fue sin tener que
        adivinarlo.
        """
        p = Planificador()
        p.registrar(Fase.IA, "conos_de_vision", ecs_systems.sistema_conos_de_vision)
        p.registrar(Fase.IA + 1, "alerta", ecs_systems.sistema_alerta)
        p.registrar(Fase.IA + 2, "acosador", ecs_systems.sistema_acosador)
        # AUD-131 — el resorte va **antes** del viento y de la integración:
        # impone la velocidad de rebote y deja que el resto del fotograma la
        # use. Después, la colisión del suelo la habría puesto a cero.
        p.registrar(Fase.FUERZAS, "resortes", ecs_systems.sistema_resortes)
        p.registrar(Fase.FUERZAS, "viento", ecs_systems.sistema_viento)
        p.registrar(
            Fase.FUERZAS + 1, "corriente", ecs_systems.sistema_corriente_de_agua,
        )
        p.registrar(
            Fase.ESCENARIO, "plataformas_moviles",
            ecs_systems.sistema_plataformas_moviles,
        )
        p.registrar(
            Fase.ESCENARIO + 1, "bloques_ritmicos",
            ecs_systems.sistema_bloques_ritmicos,
        )
        p.registrar(
            Fase.ESCENARIO + 2, "plataformas_hundibles",
            ecs_systems.sistema_plataformas_hundibles,
        )
        p.registrar(
            Fase.ESCENARIO + 3, "lianas_moviles",
            ecs_systems.sistema_lianas_moviles,
        )
        p.registrar(
            Fase.ARRASTRE, "arrastre", ecs_systems.sistema_arrastre_de_plataformas,
        )
        # La fricción va en ZONAS y no en FUERZAS porque arrastra posición, no
        # velocidad: tiene que correr sobre la posición ya resuelta.
        p.registrar(Fase.ZONAS, "friccion", ecs_systems.sistema_friccion)
        p.registrar(Fase.ZONAS + 1, "zonas_letales", ecs_systems.sistema_zonas_letales)
        # AUD-388 — los efectos temporales, junto al resto de lo que reacciona
        # a la posición ya resuelta. Van **después** de las zonas letales para
        # que una charca que acaba de envenenar cobre su primer tick en el
        # fotograma siguiente y no en el mismo, que se leería como daño doble.
        p.registrar(Fase.ZONAS + 5, "efectos", ecs_systems.sistema_efectos)
        return p

    def _poblar_mundo_ecs(self) -> None:
        """Vuelca al mundo los componentes del TMX, el jugador y los enemigos.

        Mundo nuevo por escenario y no reutilizado: arrastrar el anterior
        llevaría al nivel siguiente las plataformas del anterior y su estado a
        medio ciclo. Es el mismo motivo por el que `InteractableSystem` se
        reconstruye justo arriba.

        F5.11 — el jugador y los enemigos entran al mundo
        -------------------------------------------------
        Hasta ahora sólo entraban las mecánicas del TMX, y el jugador se pasaba
        por parámetro a los dos sistemas que lo necesitaban. Eso dejaba una
        rareza que se notaba jugando: **el viento y las corrientes no empujaban
        a los enemigos**, porque los enemigos no estaban en el mundo. Un nivel
        con viento tenía viento para el jugador y calma para todo lo demás.

        Ahora entran los tres. `adoptar_en` traslada los componentes que ya
        tienen —el mismo `Transform`, por referencia— del mundo privado que cada
        entidad crea al nacer, al mundo de la escena.
        """
        self._mundo = World()
        # AUD-381 — la geometría del nivel, para que los conos de visión no
        # atraviesen las paredes. Se publica **una vez** al montar y no por
        # fotograma: `RejillaEspacial` indexa la lista al construirse, y
        # rehacerla cada fotograma costaría más que la consulta que ahorra
        # (AUD-379 midió lo que vale ese índice: 0,011 ms sobre 51
        # rectángulos).
        #
        # Se publican los sólidos del mapa y no los de la escena compuesta
        # —plataformas móviles, bloques rítmicos, puertas— a propósito: ésos
        # cambian cada fotograma y reindexarlos por cada cambio devolvería el
        # coste que AUD-379 descartó. Una plataforma móvil no tapa la vista de
        # un vigilante; un muro sí, y los muros no se mueven.
        from src.framework.stage.rejilla import RejillaEspacial

        self._mundo.poner_recurso(
            "geometria", RejillaEspacial(list(self._stage_data.collision_rects)))
        # AUD-389 — la malla de navegación, para que el acosador rodee en vez
        # de empotrarse. Se construye una vez por escenario, como la rejilla y
        # por el mismo motivo: indexar por fotograma costaría más que las
        # consultas que ahorra.
        #
        # Los mismos sólidos del mapa, y no los de la escena compuesta: una
        # plataforma móvil no es un muro que haya que rodear —se pisa— y
        # reindexar por cada cambio devolvería el coste que AUD-379 descartó.
        from src.framework.ai.navegacion import MallaDeNavegacion

        ancho, alto = getattr(self._stage_data, "map_pixel_size", (0, 0)) or (0, 0)
        if ancho and alto:
            self._mundo.poner_recurso("malla_navegacion", MallaDeNavegacion.desde_rects(
                list(self._stage_data.collision_rects), int(ancho), int(alto)))
        for grupo in self._stage_data.componentes:
            self._mundo.crear(*grupo)

        if self._player is not None:
            self._player.adoptar_en(self._mundo)
            self._mundo.poner(self._player.entidad, EsJugador())
            self._mundo.poner(self._player.entidad, Velocidad(self._player.velocity))

        for entidad in self._stage_data.entity_list:
            if isinstance(entidad, BaseEntity):
                entidad.adoptar_en(self._mundo)
                # Sin `Velocidad` un enemigo tiene posición pero nada que
                # empujar, así que el viento y las corrientes lo ignorarían.
                self._mundo.poner(entidad.entidad, Velocidad(entidad.velocity))
                # F5.12 — `Salud` como **vista** sobre `current_health`, no como
                # copia sincronizada. Las zonas letales escriben aquí y la vida
                # del enemigo baja de verdad, sin un paso de sincronización que
                # alguien pueda olvidar.
                if hasattr(entidad, "current_health"):
                    self._mundo.poner(entidad.entidad, Salud(duenio=entidad))

    def _actualizar_agarres(self, player, im) -> None:
        """Agarrarse a una liana o engancharse a una tirolesa.

        Se hace aquí y no en un sistema ECS por la misma razón que el nado:
        quien decide en qué estado está el jugador es su máquina de estados, y
        empujarle un cambio desde un sistema sería el desorden que la fase 5
        quiso evitar. El sistema **informa**; la escena **pregunta**.

        Con el botón de agarrar y no automáticamente: una liana que te atrapa
        al pasar corriendo por delante convierte un adorno en una trampa, y es
        el fallo que más se repite en los juegos que las tienen.
        """
        from src.framework.entities.states import TirolesaState, TrepandoState

        if player is None or im is None:
            return
        actual = getattr(player, "_state_instance", None)
        if isinstance(actual, (TrepandoState, TirolesaState)):
            return
        # Liana: GRAB (G/C) o X (ataque corto) — el mensaje de stage0 decía X y
        # los jugadores lo intentaban con X. Se aceptan ambos y también UP (W).
        if not (
            im.is_action_just_pressed(Action.GRAB)
            or im.is_action_just_pressed(Action.SHORT_ATTACK)
            or im.is_action_just_pressed(Action.MOVE_UP)
            or im.is_action_just_pressed(Action.JUMP)
        ):
            return

        cable = ecs_systems.tirolesa_alcanzable(self._mundo, player.rect)
        if cable is not None:
            player._change_state_instance(TirolesaState(cable))
            return
        liana = ecs_systems.liana_alcanzable(self._mundo, player.rect)
        if liana is not None:
            player._change_state_instance(TrepandoState(liana))
