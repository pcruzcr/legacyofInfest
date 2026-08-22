"""
Module: stage4_1b
System: src.stages.stage4_1b
Academic Unit: N/A

NIVEL 4-1b — LA MINA INUNDADA

Una de las tres variantes que puede tocarle al jugador en el slot de la
Fase 4 (AUD-518, `src/stages/stage4_1/selector.py`): la misma travesía
horizontal del 4-1, dentro de una mina abandonada que se inundó (AUD-575).
El agua llega a la fila 11 de 38 — no al techo: once filas de aire con
estalactitas sobre veintiuna de agua, para "estar encerrados bajo una gran
cantidad de agua" como en el SMB 2-2. El jugador nada entre vigas y
pilares oxidados, emerge en los andenes secos a respirar, y esquiva el
ecosistema de la mina — maleza que agarra, cangrejos que patrullan,
medusas que derivan — mientras el pez abismal (`EnemyPezAbismal`)
aparece de la nada, persigue y desaparece.

Regla del nivel: **nada daña**. Cero enemigos de combate: la fauna (pez,
cangrejos, medusas) es presencia — obstruye, estresa, pero nunca quita
vida ni empuja (`damage_on_contact=0.0`, `contact_knockback=0.0`). El
único reloj que castiga es el del aire: 30 s bajo el agua, y al emerger
se respira (AUD-575, GAP-071 resuelto: el HUD avisa).

`Stage4_1B` añade a `StageScene`: el ciclo de aparición del pez, la fauna
fija del trazado (cangrejos y medusas), el fondo pintado de la mina y el
castigo de oxígeno activado.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import azar, settings
from src.engine.core.events import Events
from src.framework.entities.enemy_cangrejo import EnemyCangrejo
from src.framework.entities.enemy_medusa import EnemyMedusa
from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal
from src.framework.scenes.stage_scene import StageScene
from src.stages.stage4_1b.trazado import (
    COL_CLIMAX,
    COL_PERSECUCIONES,
    COL_PRIMER_EVENTO,
    COL_SEGUNDO_EVENTO,
    FAUNA,
    fase_de_la_columna,
)

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage4_1B(StageScene):
    """4-1b — La Mina Inundada."""

    STAGE_ID: str = "stage4_1b"
    STAGE_NAME: str = "4-1b  LA MINA INUNDADA"
    ZONE: int = 4
    BGM_TRACK: str = "4_1_b"
    TMX_PATH = "assets/maps/stage4_1b/stage4_1b.tmx"

    # ── El ciclo del pez abismal ──────────────────────────────
    #
    # AUD-576 — el pez es el "monstruo psicológico" (blueprint 10/10
    # §17-19): NO persigue hasta que el jugador ya está aterrorizado.
    # Las fases las marca la columna del jugador (`trazado.COL_*`):
    # antes del primer evento no hay pez en absoluto; el primer evento es
    # una sombra que cruza el fondo con su gemido (sin persecución); las
    # persecuciones reales llegan después del CP5 (col 581); y el clímax
    # (col 778) cruza el espacio con una duración larga — la revelación.
    ESPERA_ENTRE_APARICIONES: tuple[float, float] = (12.0, 22.0)
    #: Cuánto dura cada persecución antes de que el pez se retire.
    DURACION_DE_LA_PERSECUCION: tuple[float, float] = (5.0, 9.0)
    #: En el clímax (a partir de la col 778) el pez atraviesa el espacio:
    #: la persecución dura más — el jugador lo ve de verdad, no un susto.
    DURACION_DE_LA_PERSECUCION_CLIMAX: tuple[float, float] = (10.0, 14.0)
    #: En el pozo del drenaje (sección 5) la persecución se espacia menos:
    #: es la sección más cerrada y el pez ya no sorprende — se hace
    #: presencia constante en el peor sitio posible (AUD-575).
    ESPERA_ENTRE_APARICIONES_POZO: tuple[float, float] = (6.0, 10.0)
    #: A qué distancia, en píxeles más allá del borde visible de la
    #: cámara, aparece el pez — lo bastante lejos para que "sale de la
    #: nada" sea literal, no un pop-in a medio cuadro.
    MARGEN_DE_APARICION_PX: float = 60.0
    #: Cuántos segundos tarda la sombra del pez en cruzar el fondo de
    #: punta a punta en cada evento (AUD-576).
    DURACION_DE_LA_SOMBRA: float = 3.0

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        # AUD-575 — el oxígeno vuelve a castigar. La versión "sumergido de
        # principio a fin" (AUD-519) apagó `dano_por_segundo` porque no
        # había superficie a la que emerger (AUD-572: el ahogamiento era
        # inevitable). Con la superficie real en la fila 11 hay aire al que
        # salir a respirar (el `ControlDeNado` recupera el aire a 8×/s
        # fuera del agua), así que el reloj de 30 s vuelve a ser el
        # contrapeso del buceo — y el aviso de oxígeno bajo ya lo muestra
        # el HUD (GAP-071 resuelto, docs/45_SWIMMING_SPEC.md §4).
        self._nado.dano_por_segundo = 1.0
        # `azar.generador()` — el generador aislado del proceso (AUD-374),
        # no el global: mismo criterio que `src/stages/stage4_1/selector.py`.
        self._azar = azar.generador()
        # AUD-576 — el respiro inicial ya no es temporal: mientras el
        # jugador no cruce `COL_PRIMER_EVENTO` no hay pez ni sombra, y el
        # contador de aparición se (re)siembra por fase (ver
        # `_actualizar_pez_abismal`). Este valor inicial es irrelevante
        # hasta que se cruza la columna de persecuciones.
        self._proxima_aparicion_pez: float = 8.0
        self._pez: EnemyPezAbismal | None = None
        self._tiempo_restante_del_pez: float = 0.0
        # AUD-576 — los eventos de sombra del pez (una sola vez cada uno).
        self._sombra_primera: bool = False
        self._sombra_segunda: bool = False
        self._sombra_x: float | None = None
        self._sombra_restante: float = 0.0
        # AUD-576 — el fondo ya no es uno: la mina se deshace. Tres
        # variantes (mina → caverna → abismo) elegidas por la columna del
        # jugador en `dibujar_fondo`.
        self._fondo_mina = self._construir_fondo_mina()
        self._fondo_caverna = self._construir_fondo_caverna()
        self._fondo_abismo = self._construir_fondo_abismo()
        self._sombra_pez = self._construir_sombra_del_pez()

    def on_enter(self) -> None:
        # AUD-575 — la fauna se siembra AQUÍ y no en `__init__`:
        # `super().on_enter()` es quien carga `_stage_data` y crea al
        # jugador, y las criaturas necesitan ambas cosas (rect de
        # referencia, capas de colisión) para existir.
        super().on_enter()
        self._sembrar_fauna()

    def _sembrar_fauna(self) -> None:
        """AUD-575 — los habitantes fijos de la mina: cangrejos en el
        lecho y en el andén del patio de carga, medusas en la columna de
        la esclusa y el pozo. Los instancia la escena (no el TMX), como
        al pez: son fauna del nivel, no un arquetipo que el resto del
        motor deba conocer. Presencia, nunca combate (regla del nivel).

        La configuración repite la de `StageScene.on_enter` porque llegan
        a `entity_list` DESPUÉS de que su bucle las procese — si algún
        día el bucle cambia, esta lista es el recordatorio de qué
        necesita un enemigo de la escena para vivir.
        """
        assert self._stage_data is not None and self._player is not None
        from src.framework.physics.capas import Capa

        for col, fila, tipo in FAUNA:
            pos = pygame.Vector2(col * 16, (fila - 1) * 16)
            if tipo == "cangrejo":
                criatura: EnemyCangrejo | EnemyMedusa = EnemyCangrejo(pos)
            else:
                criatura = EnemyMedusa(pos)
            criatura.set_event_bus(self.context.event_bus)
            criatura.set_player_ref(self._player.rect)
            criatura.set_collision_rects(
                self._stage_data.capas.solidos_para(Capa.SOLIDO),
                one_way=self._stage_data.capas.solidos_para(Capa.PLATAFORMA),
            )
            criatura.set_pendientes(self._stage_data.pendientes)
            self._stage_data.entity_list.append(criatura)

    def _construir_fondo_mina(self) -> pygame.Surface:
        """AUD-531 — «el negro debe representar únicamente la ausencia de
        luz». Sin un fondo pintado, los faroles (`Light`, AUD-531 más
        abajo) no tienen nada que iluminar: `LightSystem.render` compone
        con `BLEND_RGB_MULT` — multiplicar por un multiplicador de luz
        sobre negro puro sigue dando negro puro (0 × n = 0), así que la
        luz era invisible aunque estuviera calculada bien.

        AUD-575 — la mina inundada: ya no un degradado liso, sino roca de
        mina con la boca de la cueva perfilada — estalactitas colgando del
        techo (se ven desde el fondo, siluetas contra la luz de los
        faroles), vigas horizontales oxidadas y los rieles del desagüe.
        Todo en el color café de la paleta (AUD-531); el negro queda
        reservado a la ausencia de luz de verdad.

        AUD-576 — la primera de las tres variantes del fondo (mina →
        caverna → abismo, blueprint §45). Esta es la que se ve en las
        secciones 1-3: la mina reconocible.

        Constante en X salvo las siluetas (estáticas por definición), así
        que se calcula una sola vez (no en cada fotograma) y se estira al
        ancho real de pantalla.
        """
        alto = settings.INTERNAL_HEIGHT
        tira = pygame.Surface((1, alto))
        oscuro = (20, 15, 10)
        techo = (78, 58, 38)
        for y in range(alto):
            t = y / max(1, alto - 1)
            col = tuple(int(techo[i] + (oscuro[i] - techo[i]) * t) for i in range(3))
            tira.set_at((0, y), col)

        silueta = pygame.Surface((8, alto), pygame.SRCALPHA)
        roca_silueta = (30, 22, 13)
        oxido_silueta = (52, 34, 22)
        estalactitas = [(1, 0, 5, 26), (5, 3, 8, 18), (3, 14, 6, 22),
                        (7, 26, 8, 12), (0, 34, 4, 20), (4, 44, 7, 14)]
        for x0, y0, ancho, largo in estalactitas:
            cx = x0 + ancho / 2
            pygame.draw.polygon(
                silueta, roca_silueta,
                [(x0, y0), (x0 + ancho, y0), (cx, y0 + largo)])
        vigas = [(y, x0, ancho) for y, x0, ancho in
                 ((9, 0, 8), (40, 2, 6), (58, 0, 8), (76, 3, 5))]
        for y, x0, ancho in vigas:
            pygame.draw.rect(silueta, oxido_silueta, (x0, y, ancho, 2))
        # AUD-575 — el return devolvía `tira_ancha` (el escalado de la
        # silueta, una superficie transparente) y el degradado pintado
        # arriba quedaba descartado: el fondo «café de mina» era un lienzo
        # de alfa 0 y la prueba del farol (y los faroles mismos, que se
        # multiplican sobre el fondo) veían negro puro.
        tira_ancha = pygame.transform.scale(tira, (settings.INTERNAL_WIDTH, alto))
        tira_ancha.blit(
            pygame.transform.scale(silueta, (settings.INTERNAL_WIDTH, alto)), (0, 0))
        return tira_ancha

    def _construir_fondo_caverna(self) -> pygame.Surface:
        """AUD-576 — la segunda variante (secciones 4-5): la mina se
        deshace. La roca se oscurece, las estalactitas se vuelven
        formaciones altas y las vigas desaparecen — la arquitectura
        humana terminó, la escala aumenta (blueprint §24/27)."""
        alto = settings.INTERNAL_HEIGHT
        tira = pygame.Surface((1, alto))
        oscuro = (14, 11, 8)
        techo = (52, 38, 26)
        for y in range(alto):
            t = y / max(1, alto - 1)
            col = tuple(int(techo[i] + (oscuro[i] - techo[i]) * t) for i in range(3))
            tira.set_at((0, y), col)

        silueta = pygame.Surface((8, alto), pygame.SRCALPHA)
        roca_silueta = (26, 19, 12)
        # Formaciones altas y puntiagudas — "el vacío comunica escala".
        columnas = [(0, 0, 3, 40), (3, 6, 4, 70), (5, 2, 2, 30), (7, 20, 3, 55)]
        for x0, y0, ancho, largo in columnas:
            cx = x0 + ancho / 2
            pygame.draw.polygon(
                silueta, roca_silueta,
                [(x0, y0), (x0 + ancho, y0), (cx, y0 + largo)])
        tira_ancha = pygame.transform.scale(tira, (settings.INTERNAL_WIDTH, alto))
        tira_ancha.blit(
            pygame.transform.scale(silueta, (settings.INTERNAL_WIDTH, alto)), (0, 0))
        return tira_ancha

    def _construir_fondo_abismo(self) -> pygame.Surface:
        """AUD-576 — la tercera variante (sección 6): "el agua debe
        parecer infinita" (blueprint §32). El fondo se vuelve casi negro
        con un tinte teal muy tenue y siluetas gigantes — no se ve el
        fondo, y el jugador no sabe cuánto hay debajo."""
        alto = settings.INTERNAL_HEIGHT
        tira = pygame.Surface((1, alto))
        oscuro = (8, 10, 10)
        techo = (22, 26, 24)   # teal casi negro: lo desconocido del agua
        for y in range(alto):
            t = y / max(1, alto - 1)
            col = tuple(int(techo[i] + (oscuro[i] - techo[i]) * t) for i in range(3))
            tira.set_at((0, y), col)

        silueta = pygame.Surface((8, alto), pygame.SRCALPHA)
        roca_silueta = (12, 14, 14)
        # Siluetas enormes y distantes — "lo que el jugador imagina es
        # más aterrador que lo que el juego muestra" (blueprint §54).
        masas = [(0, 4, 3, 60), (4, 0, 4, 90), (6, 30, 2, 45)]
        for x0, y0, ancho, largo in masas:
            cx = x0 + ancho / 2
            pygame.draw.polygon(
                silueta, roca_silueta,
                [(x0, y0), (x0 + ancho, y0), (cx, y0 + largo)])
        tira_ancha = pygame.transform.scale(tira, (settings.INTERNAL_WIDTH, alto))
        tira_ancha.blit(
            pygame.transform.scale(silueta, (settings.INTERNAL_WIDTH, alto)), (0, 0))
        return tira_ancha

    def _construir_sombra_del_pez(self) -> pygame.Surface:
        """AUD-576 — la sombra del pez (blueprint §22): una silueta
        gigante semi-transparente que cruza el fondo en el primer evento,
        sin perseguir ni tocar — el jugador no sabe qué era, y eso es
        exactamente lo que el diseño quiere."""
        alto = settings.INTERNAL_HEIGHT
        ancho = int(alto * 1.6)  # desproporcionada: "es mucho más grande"
        sombra = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        cuerpo = (6, 8, 8)
        cx = ancho / 2
        cy = alto / 2
        # Cuerpo alargado con aleta: el contorno que se ve contra la luz.
        pygame.draw.ellipse(sombra, (*cuerpo, 110), (cx - ancho * 0.28,
                                                     cy - alto * 0.12,
                                                     ancho * 0.56,
                                                     alto * 0.24))
        pygame.draw.polygon(sombra, (*cuerpo, 110),
                            [(cx - ancho * 0.18, cy - alto * 0.10),
                             (cx - ancho * 0.18, cy + alto * 0.10),
                             (cx + ancho * 0.20, cy)])
        pygame.draw.polygon(sombra, (*cuerpo, 90),
                            [(cx + ancho * 0.12, cy - alto * 0.10),
                             (cx + ancho * 0.10, cy + alto * 0.12),
                             (cx + ancho * 0.34, cy)])
        return sombra

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        """AUD-576 — el fondo ya no es uno: la mina se deshace a medida
        que se avanza (mina → caverna → abismo). La columna del jugador
        elige la variante, con la sombra del pez por encima cuando un
        evento está en curso."""
        if self._player is None:
            fondo = self._fondo_mina
        else:
            col = int(self._player.rect.centerx // 16)
            if col >= 650:
                fondo = self._fondo_abismo
            elif col >= 450:
                fondo = self._fondo_caverna
            else:
                fondo = self._fondo_mina
        if surface.get_size() == fondo.get_size():
            surface.blit(fondo, (0, 0))
        else:
            surface.blit(pygame.transform.scale(fondo, surface.get_size()), (0, 0))
        # La sombra cruza el fondo de punta a punta (evento único).
        if self._sombra_x is not None:
            surface.blit(self._sombra_pez, (int(self._sombra_x), 0))

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        self._actualizar_pez_abismal(dt)

    def _actualizar_pez_abismal(self, dt: float) -> None:
        """AUD-576 — el pez por fases (blueprint §17-19): sombras primero,
        persecuciones sólo en el abismo, clímax al final. La columna del
        jugador manda: quedarse en la mina es no ver nunca al pez."""
        col = int(self._player.rect.centerx // 16)

        # La sombra en curso se desliza por el fondo.
        if self._sombra_x is not None:
            self._sombra_restante -= dt
            self._sombra_x += 120.0 * dt  # cruza de izquierda a derecha
            if self._sombra_restante <= 0.0:
                self._sombra_x = None
            return

        # Eventos de sombra, una sola vez cada uno (sin pez que persiga).
        if not self._sombra_primera and col >= COL_PRIMER_EVENTO \
                and col < COL_PERSECUCIONES:
            self._sombra_primera = True
            self._disparar_sombra()
            return
        if not self._sombra_segunda and col >= COL_SEGUNDO_EVENTO:
            self._sombra_segunda = True
            self._disparar_sombra()
            return

        # Persecuciones de verdad: sólo después del primer evento (col 581).
        if col < COL_PERSECUCIONES:
            return
        if self._pez is not None:
            self._tiempo_restante_del_pez -= dt
            if self._tiempo_restante_del_pez <= 0.0 or not self._pez.is_alive:
                self._retirar_pez()
            return
        self._proxima_aparicion_pez -= dt
        if self._proxima_aparicion_pez <= 0.0:
            self._invocar_pez(col)

    def _disparar_sombra(self) -> None:
        """AUD-576 — el evento de sombra: el gemido del pez desde fuera
        de cámara y la silueta cruzando el fondo. Nada persigue."""
        self.context.event_bus.emit(Events.SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE)
        self._sombra_x = -self._sombra_pez.get_width()
        self._sombra_restante = self.DURACION_DE_LA_SOMBRA

    def _invocar_pez(self, col: int) -> None:
        """Lo aparece justo más allá del borde de la cámara, en la
        dirección en la que avanza el jugador — nunca dentro del cuadro,
        que se leería como un enemigo que se materializa encima."""
        assert self._player is not None and self._stage_data is not None
        mirando_a_la_derecha = self._player.facing_direction >= 0
        borde_x = (self._camera.offset.x
                   + (settings.INTERNAL_WIDTH if mirando_a_la_derecha else 0.0))
        x = borde_x + (self.MARGEN_DE_APARICION_PX if mirando_a_la_derecha
                       else -self.MARGEN_DE_APARICION_PX)
        # En profundidad, cerca de donde ya está el jugador —no en la
        # superficie ni pegado al lecho— para que la primera silueta que
        # se vea sea la del pez acercándose, no un punto lejano en el
        # extremo de la columna de agua.
        y = self._player.rect.centery + self._azar.uniform(-48.0, 48.0)

        pez = EnemyPezAbismal(pygame.Vector2(x, y), event_bus=self.context.event_bus)
        pez.set_player_ref(self._player.rect)
        self._stage_data.entity_list.append(pez)
        self._pez = pez
        # AUD-529 — «que el jugador lo sienta y lo escuche antes de poder
        # verlo». El pez nace fuera de cámara a propósito (arriba); este
        # sonido es el aviso de un segundo o dos antes de que la silueta
        # entre nadando en cuadro.
        self.context.event_bus.emit(Events.SFX_ENEMIES_PEZ_ABISMAL_ACERCARSE)
        # AUD-576 — el clímax (col ≥ COL_CLIMAX) dura más: es la
        # revelación, no un susto.
        if col >= COL_CLIMAX:
            duracion = self.DURACION_DE_LA_PERSECUCION_CLIMAX
        else:
            duracion = self.DURACION_DE_LA_PERSECUCION
        self._tiempo_restante_del_pez = self._azar.uniform(*duracion)

    def _retirar_pez(self) -> None:
        if self._pez is not None and self._stage_data is not None:
            try:
                self._stage_data.entity_list.remove(self._pez)
            except ValueError:
                pass  # ya no estaba -- no hay nada que retirar dos veces
        self._pez = None
        if self._player is not None and fase_de_la_columna(
                int(self._player.rect.centerx // 16)) == 5:
            espera = self.ESPERA_ENTRE_APARICIONES_POZO
        else:
            espera = self.ESPERA_ENTRE_APARICIONES
        self._proxima_aparicion_pez = self._azar.uniform(*espera)