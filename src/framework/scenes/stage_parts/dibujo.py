"""La mitad dibujada de `StageScene` — AUD-343.

`StageScene.draw` se partió en dos mitades en el mismo turno en que el
presupuesto de `stage_scene.py` se agotaba: `dibujar_mundo` (mapa, entidades,
niebla, agua y **luz**) y `dibujar_ui` (todo lo que va después de la luz:
trayectoria, HUD, minimapa, subtítulos, notificaciones).

La razón de la partición no es estética: la ruta de GPU dibuja el mundo y la
interfaz en superficies distintas porque el mundo entra en la cadena de
pasadas de la tarjeta y la interfaz se compone al final, encima de todo —
igual que el camino software la dibuja después de la luz (AUD-090, AUD-194).
`draw` sigue siendo el dibujo entero en orden; las dos mitades existen para
que `App` pueda intercalar la tarjeta entre ellas, y la tarjeta que sube es
`light_surface`, que sólo existe en esta ruta (AUD-343).

Espera de la escena: `_stage_data`, `_player`, `_camera`, `_drawing`, `_hud`,
`_msg_box`, `_banner`, `_paused`, `_debug`, `_pausa_tab`,
`_pausa_menu_seleccion`, `_pestana_de_consulta_activa` (de
`PausaDeEscenario`), `_particle_system`, `_damage_numbers`, `_ambient_particles`,
`_weather`, `_trail_system`, `_enemy_trail_system`, `_interactables`,
`_tutorial`, `_learning`, `_dialogue`, `_niebla`, `_agua_vfx`, `_bloques`,
`_cutscenes`, `_minimap`, `_subtitles`, `_achievements`, `_lighting`,
`_post_processing`, `dibujar_fondo` y el contexto (`usar_gl`).
"""
from __future__ import annotations

import pygame

from src.framework.scenes.stage_parts import dibujo_mecanicas


class DibujoDeEscenario:
    """El orden de pintado del escenario y su reparto entre CPU y GPU.

    Espera de la escena: `_stage_data`, `_player`, `_camera`, `_drawing`,
    `_hud`, `_msg_box`, `_banner`, `_paused`, `_debug`, `_pausa_tab`,
    `_pausa_menu_seleccion`, `_pestana_de_consulta_activa` (de
    `PausaDeEscenario`), `_particle_system`, `_damage_numbers`,
    `_ambient_particles`, `_weather`, `_trail_system`, `_enemy_trail_system`,
    `_interactables`, `_tutorial`, `_learning`, `_dialogue`, `_niebla`,
    `_agua_vfx`, `_bloques`, `_cutscenes`, `_minimap`, `_subtitles`,
    `_achievements`, `_lighting`, `_post_processing`, `dibujar_fondo` y el
    contexto (`usar_gl`). No instanciar solo: ver `stage_parts/__init__.py`.
    """

    def draw(self, surface: pygame.Surface) -> None:
        if self._stage_data is None or self._player is None:
            return
        # AUD-601 — GAP-072.3: el zoom cinematográfico. El mundo se dibuja
        # a tamaño alterno y se reescala sobre el lienzo; la UI sigue a
        # tamaño completo — es interfaz, no mundo.
        # Fix reporte Guillermo 3: antes recortaba desde la esquina superior
        # izquierda de la cámara, dejando al jugador fuera del cuadro con zoom
        # >1.2 y suelo cerca del borde inferior. Ahora el recorte se centra en
        # el mismo punto que el viewport original.
        zoom = getattr(self._camera, "zoom", 1.0)
        if abs(zoom - 1.0) < 1e-3:
            self.dibujar_mundo(surface)
        else:
            w, h = surface.get_size()
            base_w, base_h = max(1, int(w / zoom)), max(1, int(h / zoom))
            base = pygame.Surface((base_w, base_h))
            # Centrar el recorte: mismo centro que el viewport original
            # (evita que el jugador desaparezca con zoom 1.25 en borde inferior)
            orig_cx = self._camera.offset.x + w / 2.0
            orig_cy = self._camera.offset.y + h / 2.0
            saved_offset = pygame.Vector2(self._camera.offset)
            self._camera.offset.x = orig_cx - base_w / 2.0
            self._camera.offset.y = orig_cy - base_h / 2.0
            self.dibujar_mundo(base)
            self._camera.offset = saved_offset
            escalado = pygame.transform.smoothscale(base, (w, h))
            surface.blit(escalado, (0, 0))
        self.dibujar_ui(surface)

    def _contexto_de_dibujo(self, surface: pygame.Surface):
        from src.framework.stage.drawing_system import DrawContext
        return DrawContext(
            surface=surface,
            stage=self._stage_data,
            player=self._player,
            checkpoints=self._checkpoints,
            camera=self._camera,
            hud=self._hud,
            msg_box=self._msg_box,
            banner=self._banner,
            paused=self._paused,
            debug=self._debug,
            # AUD-555 — el panel de pausa con pestañas: las tres primeras
            # (Equipo/Habilidades/Mapa) son escenas embebidas que
            # `PausaDeEscenario` construye al pausar; "Menú" no tiene
            # escena propia (`_pestana_de_consulta_activa()` devuelve
            # `None` en su índice) y se dibuja con la lista corta de
            # `OPCIONES_DEL_MENU_DE_PAUSA`.
            pausa_tabs=self.PESTANAS_DE_PAUSA if self._paused else None,
            pausa_tab_index=getattr(self, "_pausa_tab", 0),
            pausa_pestana_activa=(
                self._pestana_de_consulta_activa() if self._paused else None
            ),
            pausa_menu_opciones=self.OPCIONES_DEL_MENU_DE_PAUSA,
            pausa_menu_seleccion=getattr(self, "_pausa_menu_seleccion", 0),
            particle_system=self._particle_system,
            damage_numbers=self._damage_numbers,
            ambient_particles=self._ambient_particles,
            weather_system=self._weather,
            trail_system=self._trail_system,
            enemy_trail_system=self._enemy_trail_system,
            interactables=self._interactables,
            tutorial_overlay=self._tutorial,
            learning_overlay=self._learning,
            dialogue_system=self._dialogue,
            fondo_del_escenario=self.dibujar_fondo,
            # AUD-285 — para los conos de visión de F1. Los conos son
            # componentes del ECS, no entidades, y sin el mundo no hay de
            # dónde sacarlos.
            mundo=self._mundo,
        )

    def dibujar_mundo(self, surface: pygame.Surface) -> None:
        """El mundo: mapa, entidades, niebla, agua y luz, en ese orden.

        AUD-343 — la mitad del antiguo `draw` que **sí** recibe la luz del
        escenario. Se separó de `dibujar_ui` porque la ruta de GPU dibuja la
        interfaz encima de la cadena de pasadas, no dentro: el mundo se sube
        a la tarjeta, la luz se multiplica allí, y la interfaz (que nunca fue
        iluminada en el camino software, AUD-090) se compone después — igual
        que aquí abajo en el camino de CPU.
        """
        if self._stage_data is None or self._player is None:
            return
        self._drawing.draw(self._contexto_de_dibujo(surface))
        # AUD-111 — la niebla y el agua. Van **entre** el mundo y la luz, y
        # ése es el único sitio correcto: después de la luz, la niebla taparía
        # los focos que definen lo que se ve; antes del mundo, no taparía
        # nada. Se activan desde el TMX (`fog_of_war`, `water_effect`), así
        # que un escenario que no las pide no paga nada por ellas.
        if self._niebla is not None:
            self._niebla.reveal(self._player.rect.centerx, self._player.rect.centery)
            self._niebla.draw(surface, self._camera.offset)
        if self._agua_vfx is not None:
            self._publicar_o_dibujar_el_agua(surface)
        self._publicar_los_rayos_de_luz()
        # AUD-343 — la luz se compone siempre, pero se aplica una sola vez y
        # en un solo sitio. Con la ruta de GPU encendida (bandera del
        # contexto, la misma que usa el lote de sprites de AUD-342), el
        # multiplicador se calcula y se deja en `mapa_de_luz()` para que
        # `App` lo suba a la tarjeta: aplicarlo aquí y de nuevo en el
        # sombreador multiplicaría la sombra dos veces. En el camino
        # software, `render` hace las dos cosas como siempre.
        if getattr(self.context, "usar_gl", False):
            self._lighting.render_map(surface.get_size(), self._camera.offset)
        else:
            self._lighting.render(surface, self._camera.offset)
        self._post_processing.apply(surface)

    def dibujar_ui(self, surface: pygame.Surface) -> None:
        """La interfaz: lo que nunca recibe la luz del escenario.

        AUD-343 — la mitad del antiguo `draw` que va **después** de la luz y
        del post-procesado (AUD-090, AUD-194). En el camino software `draw`
        la llama justo después de `dibujar_mundo`; en la ruta de GPU, `App`
        la dibuja en una superficie aparte que el renderer compone **después**
        de la cadena de pasadas: sin luz, sin viñeta y sin bloom, en las dos
        tuberías.
        """
        # AUD-194 — la previsualización del tiro va DESPUÉS de la luz y del
        # post-procesado: puesta antes, la luz la apagaba (medido, cero píxeles
        # en stage0). Es una ayuda de interfaz, no un objeto del mundo.
        if self._stage_data is None or self._player is None:
            return
        self._dibujar_trayectoria_del_arco(surface)
        # AUD-090 — la interfaz va DESPUÉS de la luz y del post-procesado.
        # Antes se pintaba dentro de `_drawing.draw` y el ambiente la
        # multiplicaba: medido, el HUD perdía el 58 % de su brillo y el
        # indicador de combo desaparecía.
        # AUD-136 — las escenas van sobre el mundo y bajo la interfaz: las
        # bandas cinematográficas tapan el juego, no el HUD.
        if self._bloques is not None:
            self._dibujar_bloques(surface)
            # AUD-242 — lo del ECS tampoco lo pintaba nadie. Ver
            # `stage_parts/`.
            dibujo_mecanicas.dibujar_mecanicas_ecs(
                surface, getattr(self, "_mundo", None), self._camera.offset)
        self._dibujar_fantasma(surface)
        if self._cutscenes is not None:
            self._cutscenes.draw(surface)
        self._drawing.draw_ui(self._contexto_de_dibujo(surface))
        self._minimap.draw(surface)
        # Captions after post-processing so the colourblind filter does not
        # wash out text that exists for accessibility (AUD-036).
        self._subtitles.draw(surface)
        self._achievements.draw_notifications(surface)
        from src.engine.core.inventory import get_inventory
        get_inventory().draw_notifications(surface)
        # AUD-296 — lo último, encima de todo. Nadie publica un evento por
        # fotograma con la superficie dentro; un overlay propio obligaría a
        # editar `DrawingSystem`.
        from src.engine.core import plugins
        plugins.get_gestor().disparar(
            "escenario_dibujado", superficie=surface, escena=self)

    @property
    def light_surface(self) -> pygame.Surface | None:
        """El mapa de luz del fotograma, sólo para la ruta de GPU.

        AUD-343 — el mapa que `App` sube a la tarjeta. Devuelve `None` en el
        camino software: ahí la luz ya se aplicó en `dibujar_mundo` y subir el
        mapa de nuevo la multiplicaría dos veces. Que el `None` lo decida la
        escena y no `App` deja el contrato en un sitio: una escena que dibuja
        su luz en CPU no tiene nada que ofrecer a la tarjeta.
        """
        if not getattr(self.context, "usar_gl", False):
            return None
        return self._lighting.mapa_de_luz()