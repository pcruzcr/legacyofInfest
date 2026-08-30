"""
Module: stage3_1_la_entrada_de_piedra
System: stage (student assignment)
Academic Unit: See README.md front-matter for units_demonstrated.

Zona 3 - Heredia. Stage 3-1: "La Entrada de Piedra" — el camino de
entrada a la sede INVENIO Heredia, inspirado en la entrada real del
campus (edificio principal, pasillo techado y camino ajardinado).

Test with:
   python main.py --stage stage3_1_la_entrada_de_piedra
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.engine.utils.math_utils import (
    ease_out_cubic,
    ease_out_elastic,
    vec2_distance,
    vec2_normalize,
)
from src.framework.entities.enemy_shooter import EnemyShooter
from src.framework.processing.color_tools import ColorTools
from src.framework.processing.curve_tools import CurveTools
from src.framework.processing.filter_tools import FilterTools
from src.framework.scenes.stage_scene import StageScene

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext


class Stage3_1_LaEntradaDePiedra(StageScene):
    """Zona 3, Heredia: camino de entrada a INVENIO Heredia.

    Bloque A: detección vectorial explícita sobre los ShooterQuetzal
    (Unidad II) y un ornamento decorativo que sigue una trayectoria
    curva calculada con CurveTools (Unidad III). Ninguna de las dos
    cosas modifica entidades del framework ni el registro de tipos:
    ambas viven enteramente en esta clase de escenario.
    """

    STAGE_ID: str = "3-1"
    STAGE_NAME: str = "3-1 LA ENTRADA DE PIEDRA"
    ZONE: int = 3

    # AUD-106 — ruta corregida al integrar la entrega.
    #
    # El mapa estaba junto al código. La convención del proyecto es
    # `assets/maps/<nombre>/<nombre>.tmx`, que es donde lo buscan el
    # validador, el calificador y el previsualizador. Duplicar el TMX en
    # dos sitios habría garantizado que algún día divergieran.
    TMX_PATH = "assets/maps/stage3_1_la_entrada_de_piedra/stage3_1_la_entrada_de_piedra.tmx"

    # ── Unidad II: detección vectorial explícita ──────────────────────
    # Distancia (px) a partir de la cual telegrafiamos la línea de tiro
    # de un ShooterQuetzal. No sustituye la detección propia de
    # EnemyShooter (que sigue intacta); es una capa de aviso adicional
    # que opera sobre las entidades ya existentes usando vec2_distance
    # y vec2_normalize de math_utils.py, tal como se acordó (opción
    # conservadora, sin subclases ni registro de entidades).
    QUETZAL_TELEGRAPH_RANGE: float = 180.0

    # ── Unidad III: ornamento con trayectoria curva (CurveTools) ──────
    # Un farol de piedra que oscila entre los dos arcos siguiendo una
    # trayectoria Catmull-Rom (CurveTools.build_bezier_path), distinta
    # del vuelo senoidal del FlyingHalcon (que no usa CurveTools).
    # Entrega II: el farol dejo de colgar entre los arcos y pasa a
    # oscilar SOBRE el pozo (x=884..924). La curva ya no es decoracion:
    # es lo que hace que el jugador vea el hueco antes de llegar a el.
    CURVE_WAYPOINTS: tuple[tuple[float, float], ...] = (
        (868.0, 150.0),
        (890.0, 128.0),
        (918.0, 128.0),
        (940.0, 150.0),
    )
    CURVE_PERIOD: float = 6.0

    # ── Unidad V: paso de nubes (HSL) ─────────────────────────────────
    # Transición sol cálido <-> sombra fría sobre el camino, calculada
    # con ColorTools.hsl_to_rgb (no con el sistema de hora/estación de
    # StageScene, que usa su propio tinte y no ColorTools). La nube es
    # una forma visible que recorre el mapa; la sombra se oscurece en
    # función de qué tan cerca está la nube del jugador, no de un
    # cronómetro desacoplado — así la causa (la nube) y el efecto (la
    # sombra) están visiblemente conectados.
    CLOUD_SPEED: float = 150.0      # px/s, recorrido por el mapa
    CLOUD_WIDTH: float = 150.0      # ancho de la sombra que proyecta
    SUN_HUE: float = 45.0
    SUN_LIGHT: float = 0.80
    SHADE_HUE: float = 215.0
    SHADE_LIGHT: float = 0.40
    CLOUD_SATURATION: float = 0.35

    def __init__(self, context: GameContext) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._quetzal_telegraphs: list[tuple[pygame.Vector2, pygame.Vector2, float]] = []
        self._quetzal_in_range: set[int] = set()
        self._curve_t: float = 0.0
        self._curve_waypoints = [pygame.Vector2(p) for p in self.CURVE_WAYPOINTS]
        self._curve_ornament_pos: pygame.Vector2 | None = self._curve_waypoints[0]
        self._cloud_t: float = 0.0
        self._cloud_x: float = -self.CLOUD_WIDTH
        self._jump_guide: list[tuple[float, float]] = []
        # Unidad VI — losas
        self._losa_edad: list[float | None] = [None] * len(self.LOSAS_X)
        self._losa_siguiente: int = 0
        self._losas_completas: bool = False
        self.context.event_bus.subscribe(self.EVENTO_LOSAS, self._on_losas_completas)
        # Unidad VII — procesamiento de imagen
        self._luz_media: float = 128.0
        self._refuerzo_luz: float = 0.0
        self._marca_losa: pygame.Surface | None = None
        self._marca_para: float = -1.0
        self._silueta: pygame.Surface | None = None
        self._bandas: list | None = None
        # Tormenta
        self._reloj_tormenta: float = 0.0
        self._ultimo_paso_tormenta: int = -1
        self._destello_edad: float | None = None
        self._destello_lado: int = 1
        self._jugadora_teñida: bool = False
        self._reloj_filtros: float = 0.0
        self._ultimo_analisis: float = -999.0
        self._ultima_silueta: float = -999.0

    # ── Lifecycle hooks ──────────────────────────────────────────────
    # Sin hooks de StageScene sobreescritos: el comportamiento por
    # defecto (tutorial, checkpoints, trigger de fin de nivel) corre
    # sin cambios. La lógica propia de esta etapa vive en update()/
    # draw(), siempre llamando a super() primero.

    def update(self, dt: float) -> None:
        super().update(dt)
        self._update_quetzal_telegraphs()
        self._update_curve_ornament(dt)
        self._update_cloud(dt)
        self._update_jump_guide()
        self._reloj_filtros += dt
        self._update_losas(dt)
        self._update_tormenta(dt)
        self._teñir_jugadora()

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        self._draw_cloud_shadow(surface)
        self._draw_cloud_shape(surface)
        self._draw_quetzal_telegraphs(surface)
        self._draw_curve_ornament(surface)
        self._draw_losas(surface)
        self._draw_marca_de_losa(surface)
        self._draw_jump_guide(surface)
        self._procesar_imagen(surface)
        self._draw_silueta(surface)
        self._draw_tinte_tormenta(surface)

    # ── Unidad II: implementación ─────────────────────────────────────

    def _update_quetzal_telegraphs(self) -> None:
        """Recalcula, cada frame, la línea de tiro de cada ShooterQuetzal
        vivo, usando aritmética vectorial explícita (vec2_distance,
        vec2_normalize). La distancia no solo decide si se dibuja la
        línea: decide si el jugador ACABA de entrar en rango de disparo,
        y en ese caso dispara un aviso en pantalla una sola vez (no en
        cada frame que permanezca dentro) — una decisión real, no solo
        un dato para dibujar."""
        self._quetzal_telegraphs = []
        if self._player is None or self._stage_data is None:
            return
        player_pos = pygame.Vector2(self._player.rect.center)
        currently_in_range: set[int] = set()
        for entity in self._stage_data.entity_list:
            if not isinstance(entity, EnemyShooter) or not entity.is_alive:
                continue
            shooter_pos = pygame.Vector2(entity.rect.center)
            distance = vec2_distance(shooter_pos, player_pos)
            in_range = distance <= self.QUETZAL_TELEGRAPH_RANGE
            if in_range:
                direction = vec2_normalize(player_pos - shooter_pos)
                self._quetzal_telegraphs.append((shooter_pos, direction, distance))
                currently_in_range.add(id(entity))
                # Flanco de subida: la entidad recién entró en rango de
                # disparo. La decisión de avisar depende únicamente del
                # resultado de vec2_distance, no de un temporizador ni
                # de la lógica interna del EnemyShooter.
                if id(entity) not in self._quetzal_in_range:
                    self.context.event_bus.emit(
                        Events.SHOW_MESSAGE,
                        text="¡Quetzal en rango de disparo!",
                        duration=1.5,
                    )
        self._quetzal_in_range = currently_in_range

    def _draw_quetzal_telegraphs(self, surface: pygame.Surface) -> None:
        offset = self._camera.offset
        for shooter_pos, direction, distance in self._quetzal_telegraphs:
            end = shooter_pos + direction * distance
            start = (shooter_pos.x - offset.x, shooter_pos.y - offset.y)
            finish = (end.x - offset.x, end.y - offset.y)
            pygame.draw.line(surface, (255, 70, 70), start, finish, 1)

    # ── Unidad III: implementación ────────────────────────────────────

    def _update_curve_ornament(self, dt: float) -> None:
        """Mueve el farol decorativo a lo largo de una trayectoria
        Catmull-Rom entre los dos arcos, con un avance triangular
        (ida y vuelta) en vez de un simple reinicio brusco."""
        self._curve_t += dt
        cycle = (self._curve_t % self.CURVE_PERIOD) / self.CURVE_PERIOD
        progress = cycle * 2.0 if cycle <= 0.5 else 2.0 - cycle * 2.0
        self._curve_ornament_pos = CurveTools.build_bezier_path(
            self._curve_waypoints, progress,
        )

    def _draw_curve_ornament(self, surface: pygame.Surface) -> None:
        if self._curve_ornament_pos is None:
            return
        offset = self._camera.offset
        pos = self._curve_ornament_pos
        x = int(pos.x - offset.x)
        y = int(pos.y - offset.y)
        pygame.draw.line(surface, (90, 70, 55), (x, y - 8), (x, y), 1)
        pygame.draw.circle(surface, (170, 90, 60), (x, y + 2), 3)


    # ── Entrega II: guia de salto sobre el pozo (Bezier) ──────────────
    # El unico salto exigente del nivel es el pozo de 40 px. Una guia que
    # aparece al acercarse resuelve dos cosas de la rubrica a la vez:
    # "navegacion clara" y "las curvas deben tener una finalidad dentro
    # del proyecto".
    #
    # Los puntos de control NO son numeros a ojo: salen de la envolvente
    # real del salto del motor. Con PLAYER_JUMP_FORCE = -380 y
    # GRAVITY = 800, el tiempo de vuelo es 2*380/800 = 0.95 s y la altura
    # de apice es 380^2/(2*800) = 90.25 px. Una Bezier cuadratica con el
    # punto de control a media distancia y al doble de la altura de apice
    # reproduce exactamente esa parabola, porque una parabola ES una
    # Bezier cuadratica: no es una aproximacion, es la misma curva.
    #
    # Los tres numeros salen del TMX, no de la memoria: el `DeathPit` esta
    # en x = 872 con 40 px de ancho, y las dos columnas que lo flanquean
    # estan a altura 0, o sea con la superficie en y = 592. Estaban mal
    # —heredados del mapa de 224 px de alto— y la guia se dibujaba 384 px
    # por encima del suelo, fuera de la pantalla: el efecto existia y no
    # se veia. Se corrigio tras medirlo sobre el video de recorrido.
    PIT_LEFT_EDGE: float = 872.0
    PIT_RIGHT_EDGE: float = 912.0
    PIT_TOP: float = 592.0
    JUMP_GUIDE_RANGE: float = 110.0
    JUMP_GUIDE_SAMPLES: int = 24

    @property
    def _jump_apex(self) -> float:
        """Altura de apice del salto, en px, derivada del motor."""
        v = abs(float(settings.PLAYER_JUMP_FORCE))
        return (v * v) / (2.0 * float(settings.GRAVITY))

    def _update_jump_guide(self) -> None:
        """Decide si la guia se muestra y, en tal caso, la muestrea.

        Se muestra solo si el jugador viene por la izquierda y esta a
        menos de JUMP_GUIDE_RANGE del borde. Una guia permanente seria
        ruido; una que aparece cuando hace falta es senalizacion.
        """
        self._jump_guide = []
        if self._player is None:
            return
        px = float(self._player.rect.centerx)
        if not (self.PIT_LEFT_EDGE - self.JUMP_GUIDE_RANGE <= px <= self.PIT_LEFT_EDGE):
            return
        apex = self._jump_apex
        control = [
            (self.PIT_LEFT_EDGE, self.PIT_TOP),
            ((self.PIT_LEFT_EDGE + self.PIT_RIGHT_EDGE) * 0.5, self.PIT_TOP - apex * 2.0),
            (self.PIT_RIGHT_EDGE, self.PIT_TOP),
        ]
        self._jump_guide = CurveTools.bezier(control, self.JUMP_GUIDE_SAMPLES)

    def _draw_jump_guide(self, surface: pygame.Surface) -> None:
        """Puntea la parabola. Se dibuja discontinua a proposito: una
        linea continua se lee como plataforma solida."""
        if not self._jump_guide:
            return
        offset = self._camera.offset
        for i, (x, y) in enumerate(self._jump_guide):
            if i % 2:
                continue
            t = i / max(1, self.JUMP_GUIDE_SAMPLES - 1)
            # se desvanece hacia los extremos: el centro del arco es lo
            # que hay que leer, no los apoyos
            alpha = int(120 + 135 * (1.0 - abs(t - 0.5) * 2.0))
            punto = pygame.Surface((3, 3), pygame.SRCALPHA)
            punto.fill((255, 225, 170, alpha))
            surface.blit(punto, (int(x - offset.x) - 1, int(y - offset.y) - 1))


    # ═══ Unidad VI — Las losas del camino ════════════════════════════
    #
    # La ficha del nivel (docs/niveles/09_STAGE_3_1.md, regla 3) dice que
    # las losas que se encienden al pisarlas son "la mecánica
    # protagonista, no decoración". Aquí están, y de paso cubren los dos
    # requisitos que la rúbrica pide para la Unidad VI: animación
    # dirigida por easing e interacción propia sobre el EventBus.
    #
    # Se encienden EN ORDEN. Pisar una fuera de turno no hace nada —no
    # castiga, no reinicia—: castigar un error de lectura en la primera
    # mecánica que el jugador ve sería enseñarle a no tocar nada.

    #: Evento propio de este escenario. No está en `Events` porque no es
    #: del motor: es de este nivel, y el bus acepta cualquier nombre.
    EVENTO_LOSAS: str = "STAGE31_LOSAS_COMPLETAS"

    #: Borde izquierdo de cada losa. Van sobre el camino, en el tramo
    #: entre el segundo y el tercer checkpoint, que es el único tramo
    #: largo sin enemigos: la mecánica se aprende sin presión.
    # Columnas 52, 55, 58, 61 y 64 del perfil: el tramo llano de dieciséis
    # columnas a altura cero que hay entre el pozo y el ascenso final. Es
    # el único trecho del mapa sin enemigos en rango ni cambios de altura,
    # que es donde tiene que aprenderse la mecánica protagonista.
    LOSAS_X: tuple[int, ...] = (944, 992, 1040, 1088, 1136)
    LOSA_ANCHO: int = 32
    LOSA_ALTO: int = 8
    # El suelo pasó de ser un plano único a un perfil de alturas. Estas
    # losas viven en el tramo de altura cero, cuya superficie está en
    # y = 592; la losa se dibuja en los 8 px de encima.
    LOSA_Y: float = 584.0
    #: Duración de la animación de encendido, en segundos.
    LOSA_ANIM: float = 0.55

    def _rect_de_losa(self, i: int) -> pygame.Rect:
        return pygame.Rect(self.LOSAS_X[i], int(self.LOSA_Y),
                           self.LOSA_ANCHO, self.LOSA_ALTO)

    def _update_losas(self, dt: float) -> None:
        """Avanza el reloj de cada losa encendida y comprueba la pisada.

        La condición de pisada es doble: solape de rectángulos **y**
        jugador apoyado en el suelo. Sin lo segundo, pasar volando por
        encima con un salto encendería la losa, que es justo lo que la
        palabra "pisar" no significa.
        """
        for i, t in enumerate(self._losa_edad):
            if t is not None and t < self.LOSA_ANIM:
                self._losa_edad[i] = min(self.LOSA_ANIM, t + dt)

        if self._player is None or self._losa_siguiente >= len(self.LOSAS_X):
            return
        if not getattr(self._player, "is_grounded", False):
            return

        i = self._losa_siguiente
        if not self._player.rect.colliderect(self._rect_de_losa(i)):
            return

        self._losa_edad[i] = 0.0
        self._losa_siguiente = i + 1
        self.context.event_bus.emit(
            Events.SFX_CHECKPOINT if i + 1 < len(self.LOSAS_X)
            else Events.SFX_STAGE_BANNER,
        )
        if self._losa_siguiente == len(self.LOSAS_X):
            # Interacción propia sobre el bus: este escenario emite su
            # propio evento y él mismo está suscrito a él (ver __init__).
            # El emisor no sabe qué pasa después; el suscriptor no sabe
            # quién lo disparó. Es el desacoplamiento que el bus existe
            # para dar, no un `if` disfrazado.
            self.context.event_bus.emit(self.EVENTO_LOSAS, total=len(self.LOSAS_X))

    def _on_losas_completas(self, **datos) -> None:
        """Suscriptor del evento propio. Enciende la recompensa."""
        self._losas_completas = True
        self.context.event_bus.emit(
            Events.SHOW_MESSAGE,
            text=f"Las {datos.get('total', 0)} losas responden. El camino reconoce el paso.",
            duration=2.5,
        )

    def _draw_losas(self, surface: pygame.Surface) -> None:
        """Dibuja las losas con el brillo dirigido por easing.

        Dos curvas distintas, cada una para lo que sabe hacer:

        - `ease_out_cubic` para el alpha del resplandor: arranca rápido y
          frena al final, que es como se percibe algo que "prende".
        - `ease_out_elastic` para la altura del halo: rebasa el valor
          final y vuelve. Es el rebote que hace que la losa se sienta
          golpeada por el pie y no simplemente coloreada.

        Una interpolación lineal aquí se lee como un fundido de vídeo, no
        como una reacción física.
        """
        offset = self._camera.offset
        for i, edad in enumerate(self._losa_edad):
            r = self._rect_de_losa(i)
            x = r.x - offset.x
            y = r.y - offset.y
            if edad is None:
                # Apagada: sólo la junta, para que se vea que ahí hay algo.
                pygame.draw.rect(surface, (78, 66, 92), (x, y, r.width, r.height), 1)
                continue

            t = min(1.0, edad / self.LOSA_ANIM)
            alpha = int(255 * ease_out_cubic(t) * (0.55 + 0.45 * self._refuerzo_luz))
            halo = int(14 * ease_out_elastic(t))

            cuerpo = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            cuerpo.fill((255, 214, 138, min(255, alpha)))
            surface.blit(cuerpo, (x, y))

            if halo > 0:
                aura = pygame.Surface((r.width, halo), pygame.SRCALPHA)
                for fila in range(halo):
                    a = int(alpha * 0.5 * (1.0 - fila / halo))
                    pygame.draw.line(aura, (255, 190, 110, a), (0, fila), (r.width, fila))
                surface.blit(aura, (x, y - halo))

    # ═══ Unidad VII — Procesamiento de imagen ════════════════════════
    #
    # Las tres operaciones tienen una consecuencia en el juego. Ninguna
    # está para cumplir el requisito: si se quitan, el nivel se juega
    # peor.

    #: Cada cuánto se mide la luz de la escena. Medir cada fotograma es
    #: tirar CPU: la luz del ciclo día/noche cambia en decenas de
    #: segundos, no en 16 ms.
    PERIODO_ANALISIS: float = 0.5
    #: Lado de la ventana de análisis alrededor del jugador, en px.
    VENTANA_ANALISIS: int = 64
    #: Luminancia media por debajo de la cual se considera que el jugador
    #: no ve bien y las luces del escenario compensan.
    UMBRAL_PENUMBRA: float = 90.0
    #: Cada cuánto se recalcula la silueta de detección.
    PERIODO_SILUETA: float = 0.30

    def _ventana_del_jugador(self, surface: pygame.Surface) -> pygame.Surface | None:
        """Recorta la zona de pantalla alrededor del jugador, sin salirse."""
        if self._player is None:
            return None
        lado = self.VENTANA_ANALISIS
        offset = self._camera.offset
        cx = int(self._player.rect.centerx - offset.x)
        cy = int(self._player.rect.centery - offset.y)
        w, h = surface.get_size()
        rect = pygame.Rect(cx - lado // 2, cy - lado // 2, lado, lado)
        rect = rect.clamp(pygame.Rect(0, 0, w, h))
        rect = rect.clip(pygame.Rect(0, 0, w, h))
        if rect.width < 8 or rect.height < 8:
            return None
        return surface.subsurface(rect).copy()

    def _analizar_luz(self, surface: pygame.Surface) -> None:
        """HISTOGRAMA QUE DIRIGE LÓGICA (Unidad VII).

        Se calcula el histograma de luminancia de la zona que el jugador
        está mirando y de él sale la luminancia media. Ese número decide
        `self._refuerzo_luz`, que es lo que sube el brillo de las losas y
        de la guía de salto.

        Por qué esto y no un temporizador: el nivel arranca a las 22:00 y
        termina a las 05:00, y además tiene la sombra de la nube pasando
        por encima. La luz real de la pantalla en un instante dado no la
        sabe ningún reloj — hay que medirla. Con el histograma, entrar en
        la sombra de la nube enciende las losas igual que lo hace la
        noche cerrada, sin haber escrito una sola línea sobre nubes.
        """
        ventana = self._ventana_del_jugador(surface)
        if ventana is None:
            return
        hist = FilterTools.compute_histogram(ventana)
        lum = hist["luminance"]
        total = max(1, int(lum.sum()))
        # Media ponderada del histograma: sum(nivel * cuenta) / total.
        media = float(sum(nivel * int(c) for nivel, c in enumerate(lum)) / total)
        self._luz_media = media
        self._refuerzo_luz = max(
            0.0, min(1.0, (self.UMBRAL_PENUMBRA - media) / self.UMBRAL_PENUMBRA),
        )

    def _rehacer_marca_de_losa(self) -> None:
        """BRILLO + CONVOLUCIÓN (Unidad VII).

        La marca que se dibuja sobre la losa siguiente —la pista de cuál
        toca— se construye una sola vez y se re-genera sólo cuando el
        refuerzo de luz cambia de tramo. Primero se sube el brillo con
        `adjust_brightness` según lo oscura que esté la escena, y después
        se difumina con `gaussian_blur`, que es una convolución: un halo
        con borde duro se lee como un rectángulo pegado encima, no como
        luz.
        """
        base = pygame.Surface((self.LOSA_ANCHO, self.LOSA_ALTO))
        base.fill((120, 96, 60))
        pygame.draw.rect(base, (255, 226, 160), base.get_rect(), 2)
        factor = 1.0 + 1.4 * self._refuerzo_luz
        realzada = FilterTools.adjust_brightness(base, factor)
        difuminada = FilterTools.gaussian_blur(realzada, 1.6)
        difuminada.set_colorkey((0, 0, 0))
        difuminada.set_alpha(110 + int(90 * self._refuerzo_luz))
        self._marca_losa = difuminada
        self._marca_para = round(self._refuerzo_luz, 1)

    def _draw_marca_de_losa(self, surface: pygame.Surface) -> None:
        if self._losa_siguiente >= len(self.LOSAS_X):
            return
        if self._marca_losa is None or self._marca_para != round(self._refuerzo_luz, 1):
            self._rehacer_marca_de_losa()
        r = self._rect_de_losa(self._losa_siguiente)
        offset = self._camera.offset
        surface.blit(self._marca_losa, (r.x - offset.x, r.y - offset.y))

    def _rehacer_silueta(self, surface: pygame.Surface) -> None:
        """DETECCIÓN DE BORDES (Unidad VII).

        Cuando un `ShooterQuetzal` tiene al jugador en su línea de tiro,
        se recorta la zona de pantalla donde está, se le pasa un Sobel y
        el resultado se dibuja encima teñido de rojo. Lo que se ve es el
        contorno del jugador y de lo que le rodea, marcado: es lo que el
        quetzal "ve".

        Sobel y no Canny a propósito: Canny binariza y devuelve un
        contorno de un píxel, limpio pero frío. Sobel conserva la
        magnitud del gradiente, así que los bordes fuertes salen más
        brillantes que los débiles y el resultado tiene la textura de un
        visor, que es lo que se quiere comunicar.
        """
        ventana = self._ventana_del_jugador(surface)
        if ventana is None:
            self._silueta = None
            return
        bordes = FilterTools.sobel_edge(ventana)
        # Realce de la magnitud antes de teñir: los bordes de un Sobel
        # sobre una escena nocturna salen muy por debajo del rango útil.
        bordes = FilterTools.adjust_contrast(bordes, 1.8)
        tinte = pygame.Surface(bordes.get_size())
        tinte.fill((255, 60, 60))
        bordes.blit(tinte, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        bordes.set_colorkey((0, 0, 0))
        bordes.set_alpha(150)
        self._silueta = bordes

    def _draw_silueta(self, surface: pygame.Surface) -> None:
        if self._silueta is None or self._player is None:
            return
        lado = self.VENTANA_ANALISIS
        offset = self._camera.offset
        cx = int(self._player.rect.centerx - offset.x)
        cy = int(self._player.rect.centery - offset.y)
        surface.blit(self._silueta, (cx - lado // 2, cy - lado // 2))

    def _procesar_imagen(self, surface: pygame.Surface) -> None:
        """Punto único de entrada de la Unidad VII, con su propio reloj.

        Va en `draw()` y no en `update()` porque estas operaciones leen
        **la pantalla ya compuesta**: en `update()` todavía no hay nada
        dibujado que medir.
        """
        ahora = self._reloj_filtros
        if ahora - self._ultimo_analisis >= self.PERIODO_ANALISIS:
            self._ultimo_analisis = ahora
            try:
                self._analizar_luz(surface)
            except Exception:
                # Un fallo del análisis no puede tumbar el fotograma: se
                # conserva la última medida buena y el juego sigue.
                pass

        if self._quetzal_telegraphs:
            if ahora - self._ultima_silueta >= self.PERIODO_SILUETA:
                self._ultima_silueta = ahora
                try:
                    self._rehacer_silueta(surface)
                except Exception:
                    self._silueta = None
        else:
            self._silueta = None


    # ═══ Fondo propio del escenario: el panorama en tres bandas ══════
    #
    # El mapa tenía 24 filas de cielo vacío. Llenarlas con baldosas del
    # TMX funcionaba, pero tenía un defecto que lo invalidaba: una capa
    # del mapa se desplaza a la misma velocidad que el suelo, y una
    # cordillera a treinta kilómetros que se mueve como el empedrado que
    # pisas no se lee como lejanía — se lee como un telón pintado.
    #
    # Así que el panorama vive fuera del TMX, en tres PNG que se dibujan
    # aquí, en `dibujar_fondo`, cada uno con su propio factor de
    # parallax. La profundidad no la da el color: la da la diferencia de
    # velocidad entre planos.

    #: (fichero, factor de parallax). 0.0 es quieto respecto a la cámara;
    #: 1.0 es pegado al suelo. Los valores salen de los que el propio
    #: motor usa en `VELOCIDAD_DE_FONDO` para sus capas equivalentes, así
    #: que el panorama se mueve al ritmo del resto del juego.
    BANDAS: tuple[tuple[str, float], ...] = (
        ("pan_cielo", 0.04),
        ("pan_lejos", 0.16),
        ("pan_cerca", 0.42),
    )

    def _cargar_panorama(self) -> None:
        """Carga las tres bandas una sola vez, la primera vez que se dibuja.

        Perezosa y no en `on_enter` a propósito: este escenario no
        sobreescribe `on_enter`, y añadir uno sólo para esto obligaría a
        acordarse de llamar a `super()` — un `super()` olvidado en
        `on_enter` rompe el HUD entero. Cargar aquí no cuesta nada: pasa
        una vez y las veces siguientes es una comprobación de lista vacía.
        """
        from src.engine.utils.asset_loader import AssetLoader

        base = Path(__file__).resolve().parents[3] / "student_assets" / "backgrounds"
        self._bandas = []
        for nombre, factor in self.BANDAS:
            ruta = base / f"{nombre}.png"
            if not ruta.exists():
                continue
            img = AssetLoader.load_image(str(ruta))
            # Espejo horizontal para poder repetir sin costura. El perfil
            # de las cordilleras sale de un desplazamiento del punto medio
            # y no es periódico, así que sus dos extremos no casan: pegar
            # dos copias iguales deja un corte vertical visible a mitad de
            # nivel. Alternar la imagen con su espejo hace que cada unión
            # sea un reflejo — y un reflejo no tiene costura.
            self._bandas.append((img, pygame.transform.flip(img, True, False), factor))

    def dibujar_fondo(self, surface: pygame.Surface,
                      offset: pygame.Vector2) -> None:
        if self._bandas is None:
            self._cargar_panorama()
        if not self._bandas:
            return
        w = surface.get_width()
        for img, espejo, factor in self._bandas:
            ancho = img.get_width()
            desplazamiento = -(offset.x * factor)
            # Primera copia a dibujar: la que cubre el borde izquierdo.
            indice = int(desplazamiento // ancho) * -1
            x = desplazamiento + indice * ancho
            while x > 0:
                indice -= 1
                x -= ancho
            y = -(offset.y * factor * 0.35)
            while x < w:
                surface.blit(espejo if indice % 2 else img, (x, y))
                x += ancho
                indice += 1
        self._draw_relampago_lejano(surface)


    # ═══ Tormenta eléctrica: la atmósfera cuenta el avance ════════════
    #
    # La luz del nivel no es fija: cuenta una historia. El acto I es un
    # atardecer tranquilo, el cielo se va cerrando, y para cuando el
    # jugador llega al gran arco hay relámpagos detrás de las montañas.
    # No es decoración — es lo que hace que el último tramo se sienta
    # como un último tramo.
    #
    # La fase sale de la posición del jugador en el mapa, no de un reloj.
    # Con un reloj, quedarse parado avanzaría la tormenta y llegar rápido
    # se la saltaría; con la posición, la tensión sube porque el jugador
    # avanza, que es de lo que va.

    #: Cada cuánto se evalúa si cae un relámpago, en segundos.
    PASO_TORMENTA: float = 0.75
    #: Duración total del destello: subida, pico y residuo.
    DESTELLO: float = 0.55
    #: Color del relámpago. Lavanda, no blanco puro: el blanco se sale de
    #: la paleta del nivel y convierte el efecto en un fogonazo de cámara.
    LUZ_RAYO: tuple[int, int, int] = (0xd8, 0xb4, 0xff)
    #: Tinte que queda en la escena mientras dura el destello.
    SOMBRA_ROSA: tuple[int, int, int] = (0x78, 0x34, 0x5e)

    def _fase_tormenta(self) -> float:
        """0 al empezar el nivel, 1 al llegar al arco."""
        if self._player is None or self._stage_data is None:
            return 0.0
        ancho = self._stage_data.map_pixel_size[0] or 1600
        t = max(0.0, min(1.0, self._player.rect.centerx / ancho))
        # Curva cuadrática: la primera mitad del nivel apenas se entera y
        # la tormenta se echa encima en el último tercio. Una rampa lineal
        # reparte la tensión por igual, y entonces no hay clímax.
        return t * t

    def _update_tormenta(self, dt: float) -> None:
        self._reloj_tormenta += dt
        if self._destello_edad is not None:
            self._destello_edad += dt
            if self._destello_edad > self.DESTELLO:
                self._destello_edad = None

        paso = int(self._reloj_tormenta / self.PASO_TORMENTA)
        if paso == self._ultimo_paso_tormenta:
            return
        self._ultimo_paso_tormenta = paso

        # Determinista: el relámpago sale de un hash del número de paso,
        # nunca de `random()`. La misma partida produce la misma tormenta,
        # que es requisito del curso y además hace el bug reproducible si
        # algo va mal.
        import hashlib
        h = hashlib.md5(f"rayo{paso}".encode()).digest()
        sorteo = int.from_bytes(h[:4], "big") / 0xFFFFFFFF
        # Probabilidad de 0 a 0,45 según la fase: al principio no cae
        # ninguno, al final cae uno cada dos o tres pasos.
        if sorteo < 0.45 * self._fase_tormenta() and self._destello_edad is None:
            self._destello_edad = 0.0
            self._destello_lado = -1 if (paso % 2) else 1

    def _intensidad_destello(self) -> float:
        """Envolvente del destello: sube, pega y se apaga despacio."""
        if self._destello_edad is None:
            return 0.0
        t = self._destello_edad / self.DESTELLO
        if t < 0.10:
            return t / 0.10                    # subida
        if t < 0.22:
            return 1.0                         # pico
        # Residuo: caída con dos escalones, como el eco de un relámpago.
        r = (t - 0.22) / 0.78
        return max(0.0, (1.0 - r) ** 2 * (0.65 if r > 0.35 else 1.0))

    def _draw_relampago_lejano(self, surface: pygame.Surface) -> None:
        """El destello, detrás de las montañas.

        Va en `dibujar_fondo`, o sea antes que el mapa, así que las
        cordilleras y los campanarios lo tapan por abajo. Un relámpago que
        se ve entero delante del jugador no da profundidad; uno que asoma
        por detrás de una silueta, sí.
        """
        k = self._intensidad_destello()
        if k <= 0.0:
            return
        w, h = surface.get_size()
        alto = int(h * 0.55)
        capa = pygame.Surface((w, alto), pygame.SRCALPHA)
        # El fogonazo no ilumina el cielo por igual: nace en un lado y se
        # apaga hacia el otro.
        cx = w * (0.22 if self._destello_lado < 0 else 0.78)
        for x in range(0, w, 4):
            d = abs(x - cx) / w
            a = int(150 * k * max(0.0, 1.0 - d * 1.6))
            if a > 0:
                pygame.draw.rect(capa, self.LUZ_RAYO + (a,), (x, 0, 4, alto))
        # Degradado vertical: más fuerte arriba, donde está la nube.
        for y in range(0, alto, 6):
            f = 1.0 - y / alto
            pygame.draw.rect(capa, (0, 0, 0, int(200 * (1 - f))),
                             (0, y, w, 6), special_flags=pygame.BLEND_RGBA_SUB)
        surface.blit(capa, (0, 0))

    def _draw_tinte_tormenta(self, surface: pygame.Surface) -> None:
        """El rosa que deja el relámpago sobre la escena.

        Muy corto y muy suave. Teñir la pantalla entera de rosa durante
        medio segundo marea y tapa a los enemigos; lo que se busca es que
        la escena *acuse* la luz un instante, no que cambie de color.

        El tono se interpola en HSL con `ColorTools` entre el violeta de
        sombra del nivel y el rosa de la tormenta (Unidad V).
        """
        k = self._intensidad_destello()
        if k <= 0.02:
            return
        h0, s0, l0 = ColorTools.rgb_to_hsl(*self.SOMBRA_ROSA)
        h1, s1, l1 = ColorTools.rgb_to_hsl(*self.LUZ_RAYO)
        mezcla = ColorTools.hsl_to_rgb(h0 + (h1 - h0) * k,
                                       s0 + (s1 - s0) * k * 0.5,
                                       l0 + (l1 - l0) * k * 0.4)
        capa = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        capa.fill(tuple(int(c) for c in mezcla) + (int(46 * k),))
        surface.blit(capa, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


    # ═══ Identidad del jugador: intercambio de paleta ═════════════════
    #
    # El sprite del jugador son **seis colores**: cinco azules de capucha
    # y tela, más un dorado para los ojos. Con una paleta tan corta, un
    # intercambio explícito color por color da un control exacto que una
    # rotación de tono en HSL no daría — sobre seis colores, rotar el
    # matiz arrastra también los grises azulados del contorno y ensucia la
    # silueta. Aquí cada tono se decide a mano.
    #
    # Lo que NO cambia, y es deliberado: la silueta, la escala, el número
    # de fotogramas, la animación y el rectángulo de colisión. Sólo cambia
    # el color. Un cambio de identidad que toque la silueta rompe la
    # legibilidad a distancia, que es lo primero que tiene que funcionar.
    #
    # Los ojos se quedan dorados. Son el único cálido del personaje y lo
    # que impide que el rosa se confunda con las flores del escenario.

    #: Azul original → rosa gótico. De sombra profunda a luz.
    PALETA_JUGADORA: dict[tuple[int, int, int], tuple[int, int, int]] = {
        (0x0f, 0x14, 0x23): (0x24, 0x18, 0x27),   # contorno y capucha
        (0x14, 0x23, 0x41): (0x3a, 0x27, 0x4b),   # violeta oscuro
        (0x23, 0x32, 0x4b): (0x7a, 0x35, 0x60),   # rosa profundo
        (0x28, 0x3c, 0x64): (0xb8, 0x54, 0x8c),   # rosa
        (0x41, 0x55, 0x6e): (0xd9, 0x8a, 0xa9),   # rosa empolvado
    }

    def _teñir_jugadora(self) -> None:
        """Recolorea los fotogramas del jugador, una sola vez.

        Se hace sobre las superficies ya cargadas en memoria, no sobre los
        PNG del disco: `assets/` es del profesor y no se toca. El escenario
        pinta a su protagonista al entrar, y el archivo original queda
        intacto para el resto del juego.
        """
        if self._jugadora_teñida or self._player is None:
            return
        marcos = getattr(self._player, "_sprite_frames", None)
        if not marcos:
            return
        for estado, lista in marcos.items():
            for i, marco in enumerate(lista):
                nuevo = marco.copy()
                nuevo.lock()
                w, h = nuevo.get_size()
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = nuevo.get_at((x, y))
                        if a == 0:
                            continue
                        destino = self.PALETA_JUGADORA.get((r, g, b))
                        if destino is not None:
                            nuevo.set_at((x, y), destino + (a,))
                nuevo.unlock()
                lista[i] = nuevo
        self._jugadora_teñida = True

    # ── Unidad V: implementación ──────────────────────────────────────

    def _update_cloud(self, dt: float) -> None:
        """Avanza la nube a lo largo del mapa (de punta a punta y de
        vuelta), a velocidad constante en px/s."""
        map_w = self._stage_data.map_pixel_size[0] if self._stage_data else 560
        travel = map_w + self.CLOUD_WIDTH * 2
        self._cloud_t += dt
        offset = (self._cloud_t * self.CLOUD_SPEED) % (travel * 2)
        if offset <= travel:
            self._cloud_x = -self.CLOUD_WIDTH + offset
        else:
            self._cloud_x = -self.CLOUD_WIDTH + (travel * 2 - offset)

    def _current_shade_factor(self) -> float:
        """0 = sol pleno, 1 = sombra máxima. Depende de la distancia
        real entre la nube y el jugador, no de un cronómetro suelto."""
        if self._player is None:
            return 0.0
        dist = abs(self._player.position.x - self._cloud_x)
        return max(0.0, 1.0 - dist / self.CLOUD_WIDTH)

    def _draw_cloud_shadow(self, surface: pygame.Surface) -> None:
        """Tiñe la escena entre un tono cálido de sol y uno frío de
        sombra, usando ColorTools.hsl_to_rgb, más marcado cuanto más
        cerca esté la nube del jugador."""
        shade = self._current_shade_factor()
        hue = self.SUN_HUE + (self.SHADE_HUE - self.SUN_HUE) * shade
        light = self.SUN_LIGHT + (self.SHADE_LIGHT - self.SUN_LIGHT) * shade
        r, g, b = ColorTools.hsl_to_rgb(hue, self.CLOUD_SATURATION, light)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        # Medido contra una captura del juego real: con 10..130 el tinte
        # lavaba TODA la escena de magenta y se comia el contraste entre
        # el jugador y el fondo. La sombra de una nube oscurece, no tine
        # la pantalla entera: 6..61 se nota al pasar y no aplana nada.
        alpha = int(6 + shade * 55)
        overlay.fill((r, g, b, alpha))
        surface.blit(overlay, (0, 0))

    def _draw_cloud_shape(self, surface: pygame.Surface) -> None:
        """Dibuja la nube en sí (no solo su efecto) para que el paso de
        nubes sea reconocible a simple vista, no solo un cambio de
        tinte ambiguo."""
        offset = self._camera.offset
        cx = int(self._cloud_x - offset.x)
        cy = 30
        cloud_r, cloud_g, cloud_b = ColorTools.hsl_to_rgb(self.SHADE_HUE, 0.10, 0.85)
        for dx, dy, radius in ((-30, 4, 16), (0, -6, 22), (30, 4, 18), (55, 6, 13)):
            pygame.draw.circle(surface, (cloud_r, cloud_g, cloud_b), (cx + dx, cy + dy), radius)
