"""
El arco del jugador: apuntar, disparar y dibujar la parábola.

Extraído de `stage_scene.py` en AUD-299 sin cambiar una línea de lógica.

Por qué es un grupo cohesivo
============================
Los cuatro métodos son una sola pregunta vista desde cuatro sitios: **hacia
dónde va la flecha**. Uno decide si manda el ratón o el mando, otro convierte
esa intención en un vector, el tercero lleva el estado del disparo y el cuarto
pinta la previsualización de lo que va a pasar.

Fuera de ellos, `StageScene` no sabe nada de balística. Y la previsualización
tiene que usar exactamente la misma integración que el proyectil, o dibujaría
una parábola distinta de la que vuela — de ahí que salgan juntos.
"""
from __future__ import annotations

import pygame

from src.engine.core.events import Events
from src.engine.input.action_map import Action

#: Segundos que el apuntado sigue siendo del ratón tras el último
#: movimiento. Corto, pero no tanto como para que soltar el ratón un
#: instante devuelva el tiro al frente en mitad de una pelea.
MEMORIA_DEL_RATON: float = 1.5


#: Color de los puntos que previsualizan el tiro del arco.
#:
#: AUD-194. Un blanco roto, el mismo tono del contorno del jugador
#: (AUD-190): los fondos de este juego son oscuros y saturados, y
#: cualquier color con tinte se confunde con el decorado de alguna zona.
TINTA_DE_LA_TRAYECTORIA: tuple[int, int, int] = (236, 232, 220)


#: Congelación al clavar una flecha, en segundos de tiempo real.
#:
#: AUD-196. Menos que los 0,05 s del cuerpo a cuerpo
#: (`collision_system.HITSTOP_DURATION`): el impacto ocurre lejos del
#: jugador y darle el mismo peso que a un golpe en la cara miente sobre
#: lo que acaba de pasar. Con cero no se notaría que la flecha acertó.
HITSTOP_DEL_FLECHAZO: float = 0.035




class ArcoDelJugador:
    """Apuntado, disparo y previsualización.

    Espera de la escena: `_player`, `_camera`, `_arco`, `_stage_data` y la
    entrada.
    """

    def _raton_esta_apuntando(self) -> bool:
        """¿El jugador está usando el ratón, o sólo está ahí quieto?

        AUD-193 — sin esto, el ratón secuestra el apuntado. La primera versión
        preguntaba únicamente por `mouse.get_focused()`, y entonces un jugador
        de teclado disparaba hacia donde el cursor se hubiera quedado olvidado:
        medido en stage0, hacia arriba y a la izquierda, en diagonal, sin haber
        tocado el ratón.

        Se considera que apunta con el ratón si lo ha movido hace poco. Es lo
        que hacen los juegos que admiten los dos controles a la vez, y evita
        tener que elegir uno en un menú.
        """
        if not pygame.mouse.get_focused():
            self._raton_ultimo_movimiento = 0.0
            return False

        posicion = pygame.mouse.get_pos()
        if not hasattr(self, "_raton_posicion_previa"):
            # Primera lectura: se toma como referencia, no como movimiento. Sin
            # esto, comparar contra `None` cuenta siempre como que el ratón se
            # ha movido y el apuntado arranca secuestrado antes de que el
            # jugador toque nada.
            self._raton_posicion_previa = posicion
            return False
        if posicion != self._raton_posicion_previa:
            self._raton_posicion_previa = posicion
            self._raton_ultimo_movimiento = MEMORIA_DEL_RATON
        return getattr(self, "_raton_ultimo_movimiento", 0.0) > 0.0

    def _direccion_de_tiro(self, player: object, im: object) -> object:
        """Hacia dónde sale la flecha: apuntado libre si lo hay, si no de frente.

        AUD-193. Devuelve un `Vector2` cuando el jugador está apuntando de
        verdad —stick derecho fuera de su zona muerta, o ratón— y el entero de
        siempre cuando no. Esa caída al comportamiento anterior no es pereza:
        es lo que permite que los 17 mapas calibrados y las entregas de
        estudiantes se sigan jugando igual con sólo el teclado.

        El ratón se lee en coordenadas de pantalla y hay que restarle el
        desplazamiento de la cámara, porque el jugador vive en coordenadas de
        mundo. Sin eso, apuntar funcionaría sólo con la cámara en el origen —el
        defecto clásico de mezclar los dos espacios.
        """
        eje = getattr(im, "aim_axis", None)
        if callable(eje):
            # Se comprueba el tipo y no sólo que exista: `getattr` sobre un
            # doble de prueba con `__getattr__` genérico devuelve un invocable
            # para cualquier nombre, y llamar a `length_squared()` sobre lo que
            # sea que conteste revienta la escena entera en mitad del combate.
            vector = eje()
            if isinstance(vector, pygame.Vector2) and vector.length_squared() > 0.0:
                return vector

        if self._raton_esta_apuntando():
            raton = pygame.Vector2(pygame.mouse.get_pos())
            camara = getattr(self, "_camera", None)
            desplazamiento = (camara.offset if camara is not None
                              else pygame.Vector2(0, 0))
            objetivo = raton + desplazamiento
            apuntado = objetivo - pygame.Vector2(
                player.rect.centerx, player.rect.centery,
            )
            # Un cursor pegado al jugador da una dirección sin sentido: por
            # debajo de media baldosa se dispara de frente.
            if apuntado.length_squared() > 64.0:
                return apuntado

        return player.facing

    def _actualizar_arco(self, dt: float, player: object, im: object, stage: object) -> None:
        """F4.2 — disparo a distancia.

        El arma no conoce la escena ni la escena decide su munición: el arco
        informa de qué flecha tocó a quién y aquí se aplica el daño, porque
        quién puede dañar a quién es una regla del escenario y no del arma.
        """
        arco = getattr(player, "arco", None)
        if arco is None:
            return

        arco.update(dt)
        self._raton_ultimo_movimiento = max(
            0.0, getattr(self, "_raton_ultimo_movimiento", 0.0) - dt)

        # AUD-195 — tensar y soltar.
        #
        # Se dispara al **soltar**, no al pulsar: es lo que permite que
        # mantener signifique algo. Un toque rápido sigue disparando —la
        # potencia mínima es utilizable— así que quien no quiera cargar no
        # tiene que aprender nada nuevo.
        # AUD-196: sólo se salta el **disparo**, no el resto del método. Mi
        # primera versión de esto retornaba aquí, y sin gestor de entrada las
        # flechas ya lanzadas dejaban de volar, de chocar con las paredes y de
        # impactar en los enemigos. Una escena sin entrada —un guion, una
        # demostración automática— se quedaba con las flechas colgadas en el
        # aire.
        if im is not None and im.is_action_pressed(Action.RANGED_ATTACK):
            arco.tensar(dt)
        elif arco.tensando:
            origen = pygame.Vector2(player.rect.centerx, player.rect.centery)
            direccion = self._direccion_de_tiro(player, im)
            if arco.disparar(origen, direccion) is not None:
                self.context.event_bus.emit(Events.SFX_PLAYER_SHORT_ATTACK)
            else:
                # Sin munición o en enfriamiento: se suelta la tensión igual,
                # o el arco se quedaría cargado para siempre y el siguiente
                # disparo saldría con una potencia que nadie pidió.
                arco.soltar_tension()

        # Una flecha que da en la pared se para; si no, atraviesa el nivel.
        arco.choca_con_muros(stage.collision_rects)

        enemigos = [e for e in stage.entity_list if hasattr(e, "apply_hit")]
        for flecha, objetivo in arco.impactos_contra(enemigos):
            objetivo.apply_hit(flecha.damage, (flecha.rect.centerx, flecha.rect.centery))
            # AUD-196 — un flechazo tiene que pesar igual que un espadazo.
            #
            # El cuerpo a cuerpo ya congelaba el mundo al conectar (AUD-001) y
            # la cámara ya se sacude en seis eventos del juego, pero el arco
            # —añadido en AUD-193— entró sin nada de eso: acertar a veinte
            # baldosas bajaba un número y no se notaba. La congelación es más
            # corta que la del cuerpo a cuerpo y la sacudida menor: el impacto
            # ocurre lejos del jugador, y darle el mismo peso que a un golpe
            # en la cara miente sobre lo que acaba de pasar.
            self._collision.trigger_hitstop(HITSTOP_DEL_FLECHAZO)
            if self._camera is not None:
                self._camera.apply_shake(amplitude=1.5, duration=0.08)
            self._damage_numbers.add(
                flecha.rect.centerx, flecha.rect.top, str(round(flecha.damage, 1)),
            )

    def _dibujar_trayectoria_del_arco(self, surface: pygame.Surface) -> None:
        """La parábola punteada, mientras se apunta.

        AUD-194. Sólo aparece cuando el jugador está apuntando de verdad —stick
        o ratón— y le quedan flechas. Con el disparo horizontal de teclado no
        se dibuja nada: ahí la curva no aporta información y sería ruido
        permanente en pantalla.

        Se dibuja **después** del mundo y antes de la niebla y el HUD: tiene
        que verse sobre el decorado, pero no sobre el marcador ni tapar un
        diálogo.
        """
        jugador, arco = self._player, getattr(self._player, "arco", None)
        if jugador is None or arco is None or arco.vacio:
            return
        entrada = self.input
        if entrada is None:
            return

        direccion = self._direccion_de_tiro(jugador, entrada)
        if not isinstance(direccion, pygame.Vector2):
            return

        from src.framework.entities.ranged_weapon import trayectoria

        desplazamiento = (self._camera.offset if self._camera is not None
                          else pygame.Vector2(0, 0))
        origen = pygame.Vector2(jugador.rect.centerx, jugador.rect.centery)
        # AUD-195: la curva se dibuja con la potencia acumulada, así que
        # tensar se **ve**: la parábola se estira mientras se mantiene pulsado.
        # Esa es la mitad del valor del tensado — sin previsualización, cargar
        # sería una espera a ciegas.
        puntos = trayectoria(origen, direccion, potencia=arco.potencia)

        # Punteada y desvaneciéndose: una línea continua se lee como una
        # cuerda tendida y sugiere que la flecha llega hasta el final, cuando
        # en realidad choca con lo primero que encuentre. El punteado dice
        # «por aquí pasará», no «aquí terminará».
        total = len(puntos)
        marco = surface.get_rect()
        for indice, punto in enumerate(puntos):
            # Uno de cada dos: el muestreo del cálculo es más fino que lo que
            # hace falta ver, y dibujarlos todos da una línea continua.
            if indice % 2:
                continue
            # La cola se corta en vez de desvanecerse a nada: el final de la
            # curva es el menos fiable —cualquier pared la interrumpe antes— y
            # dibujarlo entero prometería un alcance que no existe.
            if indice / max(total - 1, 1) > 0.75:
                break
            pantalla = punto - desplazamiento
            if not marco.collidepoint(pantalla.x, pantalla.y):
                continue
            radio = 2 if indice < total // 3 else 1
            pygame.draw.circle(
                surface,
                TINTA_DE_LA_TRAYECTORIA,
                (int(pantalla.x), int(pantalla.y)),
                radio,
            )
