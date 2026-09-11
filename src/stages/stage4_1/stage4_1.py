"""AUD-814 — Stage 4.1 «La Entrada al Cementerio Sagrado» (reconstrucción).

Jhon y Jin atraviesan seis espacios reales (960x40, seis secciones de 160
columnas): cementerio a color, bosque del Venado en B&N, osamentas de la
Serpiente en grises con tormenta, bosque talado del Halcón en vintage
ámbar, planicie nocturna de luna y camino verde hacia Paburu.

Cero enemigos: las presencias de `espiritus.py` son contornos sin colisión
ni IA. La puerta final es causal: el WarpZone a `boss_paburu` exige la
llave `paburu_despertado`, que sólo se otorga con los tres espíritus
liberados (llaves + `context.banderas`, persistidas en el save).
"""
from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Any

import pygame

from src.engine.core import settings
from src.engine.core.events import Events
from src.framework.audio.dynamic_music import resolver_pista_de_musica
from src.framework.scenes.stage_scene import StageScene
from src.framework.stage.interactable_system import EVENTO_DISPARADOR
from src.stages.stage4_1 import espiritus, trazado
from src.stages.stage4_1.fases import FASES, Fase, Gradacion, fase_en

if TYPE_CHECKING:
    from src.engine.core.game_context import GameContext

#: Identidad 3x3: «color pleno» para interpolar hacia/desde ella.
IDENTIDAD: tuple[int, ...] = (255, 0, 0, 0, 255, 0, 0, 0, 255)

_ALTARES = {
    # altar: (índice, llave, bandera, id_diálogo, nombre visible)
    "altar_venado": (0, trazado.LLAVE_VENADO, trazado.BANDERA_VENADO,
                     "venado", "El Venado"),
    "altar_serpiente": (1, trazado.LLAVE_SERPIENTE, trazado.BANDERA_SERPIENTE,
                        "serpiente", "La Serpiente"),
    "altar_halcon": (2, trazado.LLAVE_HALCON, trazado.BANDERA_HALCON,
                     "halcon", "El Halcón"),
}


class Stage4_1(StageScene):
    """4-1 — La Entrada al Cementerio Sagrado."""

    STAGE_ID: str = "stage4_1"
    STAGE_NAME: str = "4-1  LA ENTRADA AL CEMENTERIO SAGRADO"
    ZONE: int = 4
    BGM_TRACK: str = "mus_stage41_f1"
    TMX_PATH = settings.ASSETS_DIR / "maps/stage4_1/stage4_1.tmx"

    # ── Tormenta (F3) ────────────────────────────────────────────
    #: Trueno 0.2–1.5 s tras el flash: la luz llega antes que el sonido.
    ESPERA_DEL_TRUENO = (0.2, 1.5)
    # ── Silencio (F4) ────────────────────────────────────────────
    AVANCE_DEL_SILENCIO = 0.5
    DURACION_DEL_SHAKE = 0.45
    AMPLITUD_DEL_SHAKE = 14.0
    DURACION_DEL_SILENCIO = 6.0
    ESPERA_ENTRE_GRITOS = (4.0, 10.0)
    DISTANCIA_DEL_GRITO = (150.0, 420.0)
    ESPERA_ENTRE_SOMBRAS = (6.0, 14.0)
    DURACION_DEL_CRUCE = 3.5
    # ── Luna (F5) ────────────────────────────────────────────────
    PERIODO_DE_LA_LUNA = 8.0
    # El suelo de luz del motor (MIN_AMBIENTE = 0.45) impide la oscuridad
    # total: por debajo el nivel deja de ser jugable y es regla global, no
    # de este escenario. La luna oscila entre penumbra jugable (0.45) y
    # noche clara (0.75): se percibe sin romper el suelo.
    LUZ_MINIMA_LUNA = 0.45
    LUZ_MAXIMA_LUNA = 0.75
    # ── Grietas (F6) ─────────────────────────────────────────────
    PASO_QUE_ENCIENDE = 90.0
    # ── Sonidos aislados ─────────────────────────────────────────
    ESPERA_ENTRE_SONIDOS = (8.0, 15.0)
    DISTANCIA_SONIDO_AISLADO = (250.0, 500.0)
    FUNDIDO_MUSICA_MS = 2500

    def __init__(self, context: GameContext) -> None:
        super().__init__(context)
        self._azar = random.Random(812)
        self._fase_actual: Fase = FASES[0]
        self._gradacion_previa: Gradacion = None
        self._tinte_previo: tuple[tuple[int, int, int], float] | None = None
        self._musica_sonando: str | None = None
        self._liberados: list[bool] = [False, False, False]
        self._dialogo_visto: set[str] = set()
        self._ascensiones: list[dict[str, Any]] = []
        self._mensajes_vistos: set[int] = set()
        self._silencio_activo = False
        self._reloj_silencio = 0.0
        self._silencio_hecho = False
        self._proximo_rayo = 5.0
        self._trueno_pendiente: float | None = None
        self._trueno_x = 0.0
        self._proximo_grito = 8.0
        self._sombra: dict[str, Any] | None = None
        self._proxima_sombra = 9.0
        self._proximo_aislado = 10.0
        self._serpiente_visible = False
        self._reloj_serpiente = 4.0
        self._distancia_f6 = 0.0
        self._ultima_x = 0.0
        self._luces_encendidas = 0
        self._tiempo = 0.0
        self._fondos: dict[int, list[pygame.Surface]] = {}
        self._despertar_hecho = False
        self._arrancado = False
        # AUD-815 — estado de la experiencia dirigida.
        self._aviso_cima_hecho = False
        self._reloj_susurro_f1 = 9.0
        self._silueta_f1: dict | None = None
        self._reloj_silueta_f1 = 20.0
        self._reloj_ojos_f2 = 14.0
        self._ojos_f2: dict | None = None
        self._reloj_animal_f2 = 22.0
        self._animal_f2: dict | None = None
        self._revelacion_serpiente = 0.0
        self._clima_adelantado = 0
        self._piras_encendidas: list[bool] = [False, False, False]
        self._incendio_activo = False
        self._caza_x: float | None = None
        self._reloj_caza = 0.0
        self._vel_caza = 0.0
        self._nube = 0.0
        self._reloj_nube = 0.0
        self._antorcha_encendidas = 0
        self._aparicion_f6: dict | None = None
        self._templo_iniciado = False
        self._reloj_templo = 0.0
        self._paso_templo = 0
        # AUD-816 — lluvia por capas y niebla estratificada.
        self._gotas: list[dict] = []
        self._salpicaduras: list[dict] = []
        self._niebla_tex: list[pygame.Surface] | None = None

    # ── Arranque ─────────────────────────────────────────────────
    def on_stage_start(self) -> None:
        super().on_stage_start()
        self._cargar_fondos()
        # AUD-814: aquí sólo estado. El motor monta iluminación, postfx,
        # día/noche, diálogos del TMX y suscriptores DESPUÉS de
        # on_stage_start (stage_scene.on_enter), así que la primera fase se
        # aplica en el primer update (ver _arranque diferido abajo).

    def _arranque_diferido(self) -> None:
        self.context.event_bus.subscribe(EVENTO_DISPARADOR, self._al_disparar)
        self._restaurar_progreso()
        self._fase_actual = self._fase_del_jugador()
        self._aplicar_fase(self._fase_actual, primera=True)

    def _restaurar_progreso(self) -> None:
        """Las llaves del llavero mueren con la escena; las banderas no.

        Al reentrar (muerte, backtracking, carga) se re-otorgan las llaves
        desde context.banderas para no pedir dos veces lo ya liberado.
        """
        banderas = getattr(self.context, "banderas", {}) or {}
        llavero = self._interactables.llavero
        for i, (_altar, llave, bandera, _col, _nombre) in enumerate(
                _ALTARES.values()):
            if banderas.get(bandera):
                self._liberados[i] = True
                if not llavero.tiene(llave):
                    llavero.coger(llave)
        if all(self._liberados):
            if not llavero.tiene(trazado.LLAVE_PABURU):
                llavero.coger(trazado.LLAVE_PABURU)
            self._despertar_hecho = True

    def _cargar_fondos(self) -> None:
        base = settings.ASSETS_DIR / "backgrounds" / "stage41"
        for fase in range(1, 7):
            planos = []
            for plano in ("far", "mid", "near"):
                ruta = base / f"f{fase}_{plano}.png"
                if ruta.is_file():
                    # AUD-814: convert_alpha, no convert — los planos mid/near
                    # traen transparencia y convert() la vuelve negro opaco,
                    # tapando el cielo del plano far.
                    planos.append(pygame.image.load(str(ruta)).convert_alpha())
            if planos:
                self._fondos[fase] = planos

    # ── Bucle ────────────────────────────────────────────────────
    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        if not self._arrancado:
            self._arrancado = True
            self._arranque_diferido()
        if self._cutscenes is not None and self._cutscenes.bloquea:
            return
        if self._dialogue.active:
            return
        self._tiempo += dt
        fase = self._fase_del_jugador()
        if fase.numero != self._fase_actual.numero:
            self._gradacion_previa = self._fase_actual.gradacion
            self._tinte_previo = self._fase_actual.tinte
            self._fase_actual = fase
            self._aplicar_fase(fase)
            self._anunciar_fase(fase)
        self._actualizar_gradacion()
        self._actualizar_mensajes()
        self._actualizar_aviso_cima()
        self._actualizar_eventos_f1(dt)
        self._actualizar_eventos_f2(dt)
        self._actualizar_transiciones()
        self._actualizar_rayos(dt)
        self._actualizar_silencio(dt)
        self._actualizar_gritos(dt)
        self._actualizar_sombras(dt)
        self._actualizar_aislados(dt)
        self._actualizar_serpiente_de_fondo(dt)
        self._actualizar_luna(dt)
        self._actualizar_grietas(dt)
        self._actualizar_ascensiones(dt)
        self._actualizar_incendio(dt)
        self._actualizar_caza(dt)
        self._actualizar_nubes(dt)
        self._actualizar_antorchas()
        self._actualizar_templo(dt)
        self._pasos_templo(dt)
        self._actualizar_lluvia(dt)
        if self._revelacion_serpiente > 0:
            self._revelacion_serpiente -= dt

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        if self._player is None:
            return
        desfase = self._camera.offset

        def mundo(x: float, y: float) -> tuple[float, float]:
            return (x - desfase.x, y - desfase.y)

        fase = self._fase_actual.numero
        t = self._tiempo
        # AUD-816 FASE A: sombra de contacto. La física apoya los pies en el
        # borde del tile; sin ancla visual el ojo lee "flota".
        if getattr(self._player, "is_grounded", True):
            px, py = mundo(self._player.rect.centerx,
                           self._player.rect.bottom + 1)
            capa = pygame.Surface((38, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(capa, (8, 8, 10, 140), (0, 0, 38, 10))
            pygame.draw.ellipse(capa, (8, 8, 10, 70), (4, 1, 30, 8))
            surface.blit(capa, (px - 19, py - 5))
        if fase == 1 and self._silueta_f1 is not None:
            alfa = int(120 * min(1.0, self._silueta_f1["t"])
                       * min(1.0, max(0.0, 3.0 - self._silueta_f1["t"])))
            x, y = mundo(self._silueta_f1["x"], 500)
            capa = pygame.Surface((30, 70), pygame.SRCALPHA)
            pygame.draw.ellipse(capa, (20, 22, 30, alfa), (5, 5, 20, 60))
            pygame.draw.circle(capa, (20, 22, 30, alfa), (15, 10), 8)
            surface.blit(capa, (x - 15, y - 70))
        if fase == 2:
            if self._ojos_f2 is not None:
                a = int(220 * min(1.0, self._ojos_f2["t"] * 2)
                        * min(1.0, max(0.0, 2.0 - self._ojos_f2["t"])))
                x, y = mundo(self._ojos_f2["x"], 420)
                capa = pygame.Surface((30, 12), pygame.SRCALPHA)
                pygame.draw.circle(capa, (255, 220, 120, a), (9, 6), 3)
                pygame.draw.circle(capa, (255, 220, 120, a), (21, 6), 3)
                surface.blit(capa, (x - 15, y - 6))
            if self._animal_f2 is not None:
                x, y = mundo(self._animal_f2["x"], 498)
                capa = pygame.Surface((36, 14), pygame.SRCALPHA)
                pygame.draw.ellipse(capa, (30, 30, 34, 200), (2, 2, 32, 10))
                surface.blit(capa, (x - 18, y - 14))
        if fase == 2 and not self._liberados[0]:
            px = self._player.rect.centerx
            # Apariciones previas: el Venado asoma y se va antes del diálogo.
            if px < trazado.COLUMNA_DIALOGO_VENADO * trazado.TS:
                ciclo = (t % 9.0)
                if 4.0 < ciclo < 7.0:
                    alfa = int(150 * min(1.0, (ciclo - 4.0)) * min(1.0, (7.0 - ciclo)))
                    x, y = mundo(198 * trazado.TS, 500)
                    espiritus.dibujar_venado(surface, x, y, 1.0,
                                             espiritus.BLANCO_HUESO, alfa, t)
            else:
                x, y = mundo(222 * trazado.TS, 500)
                espiritus.dibujar_venado(surface, x, y, 1.1,
                                         espiritus.BLANCO_HUESO, 200, t)
        if fase == 3:
            if self._serpiente_visible:
                x, y = mundo(self._player.rect.centerx - 200, 470)
                espiritus.dibujar_serpiente_de_fondo(
                    surface, x, y, 400, espiritus.BLANCO_HUESO, 160, t)
            if not self._liberados[1]:
                x, y = mundo(450 * trazado.TS, 470)
                espiritus.dibujar_serpiente(surface, x, y, 1.0,
                                            espiritus.BLANCO_HUESO, 190, t)
            if self._revelacion_serpiente > 0:
                x, _y = mundo(self._player.rect.centerx + 100, 200)
                espiritus.dibujar_revelacion_serpiente(surface, x, 200, 1.0,
                                                       200)
        if fase == 4:
            x, y = mundo(600, 78)
            espiritus.dibujar_luna(surface, int(x), int(y), 22, 130)
            if self._sombra is not None:
                sx, _sy = mundo(self._sombra["x"], 120)
                espiritus.dibujar_sombra_de_ave(surface, sx, 120, 1.0, 150)
            if not self._liberados[2]:
                x, y = mundo(606 * trazado.TS, 300)
                espiritus.dibujar_halcon(surface, x, y, 1.2,
                                         espiritus.AMBAR_VIEJO, 200, t)
            for i, encendida in enumerate(self._piras_encendidas):
                if not encendida:
                    continue
                bx, by = mundo(trazado.PIRAS_FASE4[i] * trazado.TS, 500)
                espiritus.dibujar_llama_simple(surface, bx, by, 70, t,
                                               desfase=float(i * 2))
                espiritus.dibujar_humo(surface, bx, by - 60, 200, t,
                                       desfase=float(i))
            if self._caza_x is not None:
                sx, sy = mundo(self._caza_x, 470)
                capa = pygame.Surface((220, 60), pygame.SRCALPHA)
                pygame.draw.ellipse(capa, (15, 12, 12, 170), (10, 5, 200, 50))
                pygame.draw.polygon(capa, (15, 12, 12, 170),
                                    [(110, 10), (30, 0), (60, 22), (110, 26)])
                pygame.draw.polygon(capa, (15, 12, 12, 170),
                                    [(110, 10), (190, 0), (160, 22), (110, 26)])
                surface.blit(capa, (sx - 110, sy - 30))
        if fase == 5:
            if self._nube > 0.03:
                # La nube tapa la luna: banda oscura a la deriva en el cielo.
                nx = ((t * 30.0) % 1600.0) - 160.0
                capa = pygame.Surface((420, 130), pygame.SRCALPHA)
                a = int(200 * min(1.0, self._nube * 1.5))
                pygame.draw.ellipse(capa, (10, 12, 26, a), (0, 10, 420, 110))
                pygame.draw.ellipse(capa, (16, 19, 36, a), (60, 0, 300, 90))
                surface.blit(capa, (nx, 40))
            luz = self._luz_de_luna()
            if luz > 0.58:
                alfa = int(60 + 140 * (luz - 0.58) / 0.17)
                for cx in (700, 730, 762):
                    x, y = mundo(cx * trazado.TS, 500)
                    capa = pygame.Surface((44, 84), pygame.SRCALPHA)
                    pygame.draw.ellipse(
                        capa, (200, 208, 230, min(255, alfa)), (7, 5, 30, 74))
                    pygame.draw.circle(
                        capa, (215, 222, 240, min(255, alfa)), (22, 12), 9)
                    surface.blit(capa, (x - 22, y - 84))
        if fase == 6 and self._despertar_hecho:
            x, y = mundo(936 * trazado.TS, 512)
            espiritus.dibujar_paburu(surface, x, y, 1.0, 70, t)
        for i, col in enumerate(trazado.ANTORCHAS_FASE6):
            if i >= self._antorcha_encendidas:
                continue
            bx, by = mundo(col * trazado.TS, 500)
            espiritus.dibujar_llama_simple(surface, bx, by, 44, t,
                                           desfase=float(i * 3))
        if self._aparicion_f6 is not None:
            self._aparicion_f6["t"] += 1 / 60
            ap = self._aparicion_f6
            if ap["t"] < 5.0:
                alfa = int(180 * min(1.0, ap["t"]) * (1.0 - ap["t"] / 5.0))
                x, y = mundo(ap["x"], 500)
                if ap["cual"] == "venado":
                    espiritus.dibujar_venado(surface, x, y, 0.9,
                                             espiritus.VERDE_ESPECTRAL, alfa,
                                             t)
                elif ap["cual"] == "serpiente":
                    espiritus.dibujar_serpiente(surface, x, y, 0.9,
                                                espiritus.VERDE_ESPECTRAL,
                                                alfa, t)
                else:
                    espiritus.dibujar_halcon(surface, x, y, 1.0,
                                             espiritus.VERDE_ESPECTRAL, alfa,
                                             t)
            else:
                self._aparicion_f6 = None
        for asc in self._ascensiones:
            x, y = mundo(asc["x"], 500)
            espiritus.dibujar_ascension(surface, x, y, 260,
                                        espiritus.VERDE_ESPECTRAL,
                                        int(200 * asc["alfa"]), t)
        # AUD-816: hitos que rompen la línea de baldosas.
        if fase == 1:
            x, y = mundo(90 * trazado.TS, 512)
            espiritus.dibujar_mausoleo(surface, x, y, (190, 184, 168),
                                       (120, 114, 100))
        elif fase == 3:
            x, y = mundo(400 * trazado.TS, 512)
            espiritus.dibujar_costillar(surface, x, y, (215, 208, 190))
        elif fase == 4:
            x, y = mundo(540 * trazado.TS, 512)
            espiritus.dibujar_gran_quemado(surface, x, y, (70, 46, 28))
        elif fase == 5:
            x, y = mundo(720 * trazado.TS, 512)
            espiritus.dibujar_gran_cruz(surface, x, y, (110, 118, 140))
        elif fase == 6:
            x, y = mundo(948 * trazado.TS, 512)
            # Piedra apagada: el bloom y la niebla ya dan luz; piedra
            # clara se quemaba a blanco y parecía pegada.
            espiritus.dibujar_arco_templo(surface, x, y, (104, 116, 98),
                                          (140, 255, 180), t)
        self._dibujar_lluvia(surface)
        if fase == 6:
            self._dibujar_niebla(surface)

    # ── Detección y aplicación de fase ───────────────────────────
    def _fase_del_jugador(self) -> Fase:
        col = self._player.rect.centerx / trazado.TS
        return fase_en(col)

    def _avance_en_fase(self, fase: Fase) -> float:
        col = self._player.rect.centerx / trazado.TS
        recorrido = col - fase.desde_columna
        return max(0.0, min(1.0, recorrido / trazado.ANCHO_SECCION))

    def _aplicar_fase(self, fase: Fase, primera: bool = False) -> None:
        self._cambiar_clima(fase.clima)
        self._ambient_particles.set_effect(*fase.particulas)
        self._ambiente_base = fase.ambiente
        self._post_processing.set_vignette(0.55 if fase.numero in (3, 5) else 0.40)
        self._musica_de_fase(fase)
        self._fondo_de_fase(fase)
        audio = self.audio
        if audio is not None and fase.sonido_ambiente and not self._silencio_activo:
            ruta = settings.ASSETS_DIR / fase.sonido_ambiente
            if ruta.is_file():
                if getattr(audio, "_ambient_active", False):
                    audio.crossfade_ambient(ruta, duration=1.5, volume=0.35)
                else:
                    audio.play_ambient(ruta, volume=0.35)

    def _anunciar_fase(self, fase: Fase) -> None:
        self.context.event_bus.emit(
            Events.SHOW_MESSAGE,
            text=f"Fase {fase.numero} — {fase.nombre}", duration=4.0)

    def _musica_de_fase(self, fase: Fase) -> None:
        if fase.musica == self._musica_sonando:
            return
        self._musica_sonando = fase.musica
        audio = self.audio
        if audio is None or fase.musica is None:
            return
        pista = resolver_pista_de_musica(fase.musica)
        if pista is None:
            return
        audio.play_music(pista, fundido_ms=self.FUNDIDO_MUSICA_MS)

    def _fondo_de_fase(self, fase: Fase) -> None:
        planos = self._fondos.get(fase.numero)
        if not planos:
            return
        self._stage_data.background_layers = list(planos)
        factores = (0.15, 0.35, 0.6)
        self._stage_data.background_factors = list(factores[:len(planos)])

    # ── Aviso P0 + eventos F1/F2 + transiciones ────────────────
    def _actualizar_aviso_cima(self) -> None:
        """El bot de P0 demostró que todo se camina salvo los vértices.
        El primero avisa una vez: nadie debe leerlo como bug."""
        if self._aviso_cima_hecho:
            return
        col = self._player.rect.centerx / trazado.TS
        if trazado.COLUMNA_AVISO_CIMA <= col < trazado.REPISO_VENADO[0]:
            self._aviso_cima_hecho = True
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text="La cima se corona saltando (ESPACIO).", duration=4.0)

    def _actualizar_eventos_f1(self, dt: float) -> None:
        """Percepción sin combate: susurro sin fuente y silueta lejana."""
        if self._fase_actual.numero != 1:
            return
        px = self._player.rect.centerx
        self._reloj_susurro_f1 -= dt
        if self._reloj_susurro_f1 <= 0:
            self._reloj_susurro_f1 = self._azar.uniform(10.0, 18.0)
            d = self._azar.uniform(*self.DISTANCIA_SONIDO_AISLADO)
            self._play_sfx_spatial("sfx_environment_crujido_seco",
                                   self._punto_lateral(d), 0.6)
        if self._silueta_f1 is None:
            self._reloj_silueta_f1 -= dt
            if self._reloj_silueta_f1 <= 0:
                self._silueta_f1 = {"x": px + self._azar.choice((-1.0, 1.0))
                                    * self._azar.uniform(300.0, 500.0),
                                    "t": 0.0}
        else:
            self._silueta_f1["t"] += dt
            if self._silueta_f1["t"] > 3.0:
                self._silueta_f1 = None
                self._reloj_silueta_f1 = self._azar.uniform(18.0, 30.0)

    def _actualizar_eventos_f2(self, dt: float) -> None:
        """Ojos entre los árboles y un animal que cruza: nadie ataca."""
        if self._fase_actual.numero != 2:
            self._ojos_f2 = None
            self._animal_f2 = None
            return
        px = self._player.rect.centerx
        if self._ojos_f2 is None:
            self._reloj_ojos_f2 -= dt
            if self._reloj_ojos_f2 <= 0:
                self._ojos_f2 = {"x": px + self._azar.choice((-1.0, 1.0))
                                 * self._azar.uniform(250.0, 450.0), "t": 0.0}
        else:
            self._ojos_f2["t"] += dt
            if self._ojos_f2["t"] > 2.0:
                self._ojos_f2 = None
                self._reloj_ojos_f2 = self._azar.uniform(16.0, 26.0)
        if self._animal_f2 is None:
            self._reloj_animal_f2 -= dt
            if self._reloj_animal_f2 <= 0:
                lado = self._azar.choice((-1.0, 1.0))
                self._animal_f2 = {"x": px + lado * 600.0, "vx": -lado * 500.0,
                                   "t": 0.0}
        else:
            self._animal_f2["t"] += dt
            self._animal_f2["x"] += self._animal_f2["vx"] * dt
            if self._animal_f2["t"] > 3.0:
                self._animal_f2 = None
                self._reloj_animal_f2 = self._azar.uniform(18.0, 30.0)

    def _actualizar_transiciones(self) -> None:
        """El clima del vecino empieza 16 columnas antes del borde: se
        entra a la lluvia, no se aparece en ella."""
        col = self._player.rect.centerx / trazado.TS
        fase = self._fase_actual.numero
        if fase >= 6:
            return
        borde = fase * trazado.ANCHO_SECCION
        if borde - 16 <= col < borde and self._clima_adelantado != fase:
            self._clima_adelantado = fase
            siguiente = FASES[fase]
            self._cambiar_clima(siguiente.clima)
            self._ambient_particles.set_effect(*siguiente.particulas)
        elif col < borde - 16 or col >= borde:
            if self._clima_adelantado == fase and col < borde - 16:
                self._clima_adelantado = 0

    # ── Mensajes y diálogos del TMX ──────────────────────────────
    def _actualizar_mensajes(self) -> None:
        """Los MessageTrigger del mapa no se muestran solos: el escenario
        los sondea (mismo patrón que stage0/stage1_1). Texto → MessageBox;
        `dialogue` → árbol de data/dialogues/stage4_1.json. Una sola vez
        cada uno: son hitos narrativos, no carteles de repaso."""
        if self._dialogue.active:
            return
        for i, mt in enumerate(self._stage_data.message_triggers):
            if i in self._mensajes_vistos:
                continue
            if not self._player.rect.colliderect(mt.rect):
                continue
            arbol_id = getattr(mt, "dialogue_tree_id", "") or ""
            if arbol_id:
                arbol = self._arboles_de_dialogo.get(arbol_id)
                if arbol is None:
                    continue
                self._mensajes_vistos.add(i)
                self._dialogo_visto.add(arbol_id)
                self._dialogue.start_dialogue(arbol)
                return
            texto = getattr(mt, "text", "") or ""
            if texto:
                self._mensajes_vistos.add(i)
                self.context.event_bus.emit(
                    Events.SHOW_MESSAGE, text=texto, duration=6.0)

    # ── Gradación ────────────────────────────────────────────────
    @staticmethod
    def _interpolar(a: Gradacion, b: Gradacion, t: float) -> tuple[int, ...]:
        ga = a if a is not None else IDENTIDAD
        gb = b if b is not None else IDENTIDAD
        return tuple(round(ga[i] + (gb[i] - ga[i]) * t) for i in range(9))

    def _actualizar_gradacion(self) -> None:
        """La transición F1→F2 (y todas) es gradual: interpola de la
        gradación anterior a la actual por avance dentro del tramo.

        El tinte funde más rápido (primer tercio): es un velo sobre la
        imagen y arrastrarlo por toda la fase teñiría la fase siguiente
        (el ámbar vintage se metía en la planicie nocturna).
        """
        fase = self._fase_actual
        t = self._avance_en_fase(fase)
        # La fase establece su imagen en el primer cuarto del tramo: cruzar
        # el borde debe transformar, no prometer. Sin esta curva, a mitad de
        # fase todo seguía a medio camino y ninguna fase se veía pura.
        tg = min(1.0, t * 4.0)
        if self._gradacion_previa is None and fase.gradacion is None:
            self._post_processing.clear_color_grading()
        else:
            self._post_processing.set_color_grading(
                *self._interpolar(self._gradacion_previa, fase.gradacion, tg))
        previa = self._tinte_previo
        alfa_previo = previa[1] if previa is not None else 0.0
        te = min(1.0, t * 3.0)
        if fase.tinte is not None:
            color, objetivo = fase.tinte
            alfa = alfa_previo + (objetivo - alfa_previo) * te
        else:
            color = previa[0] if previa is not None else (0, 0, 0)
            alfa = alfa_previo * (1.0 - te)
        if alfa <= 0.001:
            self._post_processing.clear_tint()
        else:
            self._post_processing.set_tint(color, alfa)

    # ── Tormenta (F3) ────────────────────────────────────────────
    def _actualizar_rayos(self, dt: float) -> None:
        if self._fase_actual.numero != 3:
            self._proximo_rayo = 3.0
            return
        if self._trueno_pendiente is not None:
            self._trueno_pendiente -= dt
            if self._trueno_pendiente <= 0:
                self._trueno_pendiente = None
                self._play_sfx_spatial("s41_trueno", self._trueno_x, 0.8)
            return
        self._proximo_rayo -= dt
        if self._proximo_rayo > 0:
            return
        espera = 60.0 / max(1.0, self._fase_actual.rayos_por_minuto)
        self._proximo_rayo = espera * self._azar.uniform(0.6, 1.4)
        self._post_processing.flash((235, 240, 255), alpha=180, duration=0.12)
        self._trueno_x = self._player.rect.centerx + self._azar.uniform(-500, 500)
        self._trueno_pendiente = self._azar.uniform(*self.ESPERA_DEL_TRUENO)
        # El flash revela un instante lo que la tormenta oculta.
        self._revelacion_serpiente = 0.6

    # ── Silencio (F4) ────────────────────────────────────────────
    def _actualizar_silencio(self, dt: float) -> None:
        if self._fase_actual.numero != 4:
            return
        if self._silencio_hecho:
            if self._silencio_activo:
                self._reloj_silencio -= dt
                if self._reloj_silencio <= 0:
                    self._silencio_activo = False
                    self._aplicar_fase(self._fase_actual)
            return
        col = self._player.rect.centerx / trazado.TS
        umbral = (trazado.INICIO_DE_FASE[3]
                  + self.AVANCE_DEL_SILENCIO * trazado.ANCHO_SECCION)
        if col < umbral:
            return
        self._silencio_hecho = True
        self._silencio_activo = True
        self._reloj_silencio = self.DURACION_DEL_SILENCIO
        audio = self.audio
        if audio is not None:
            audio.stop_ambient()
            audio.stop_music()
            self._musica_sonando = "___silencio___"
        self._play_sfx_spatial("s41_golpe_silencio",
                               self._player.rect.centerx, 1.0)
        self._camera.apply_shake(amplitude=self.AMPLITUD_DEL_SHAKE,
                                 duration=self.DURACION_DEL_SHAKE)
        self.context.event_bus.emit(
            Events.SHOW_MESSAGE, text="Silencio.", duration=3.0)

    # ── Gritos, sombras, aislados, serpiente (F3-F4) ─────────────
    def _punto_lateral(self, distancia: float) -> float:
        return self._player.rect.centerx + self._azar.choice((-1.0, 1.0)) * distancia

    def _actualizar_gritos(self, dt: float) -> None:
        if self._fase_actual.numero != 4 or self._silencio_activo:
            return
        if not self._silencio_hecho:
            return
        self._proximo_grito -= dt
        if self._proximo_grito > 0:
            return
        self._proximo_grito = self._azar.uniform(*self.ESPERA_ENTRE_GRITOS)
        d = self._azar.uniform(*self.DISTANCIA_DEL_GRITO)
        self._play_sfx_spatial("s41_grito_halcon", self._punto_lateral(d), 0.8)

    def _actualizar_sombras(self, dt: float) -> None:
        if self._fase_actual.numero != 4 or self._silencio_activo:
            return
        if not self._silencio_hecho:
            return
        if self._sombra is None:
            self._proxima_sombra -= dt
            if self._proxima_sombra <= 0:
                px = self._player.rect.centerx
                lado = self._azar.choice((-1.0, 1.0))
                self._sombra = {"x": px + lado * 700.0, "vx": -lado * 400.0,
                                "t": 0.0}
            return
        self._sombra["t"] += dt
        self._sombra["x"] += self._sombra["vx"] * dt
        if self._sombra["t"] >= self.DURACION_DEL_CRUCE:
            self._sombra = None
            self._proxima_sombra = self._azar.uniform(*self.ESPERA_ENTRE_SOMBRAS)

    def _actualizar_aislados(self, dt: float) -> None:
        fase = self._fase_actual
        if not fase.sonidos_aislados or self._silencio_activo:
            return
        self._proximo_aislado -= dt
        if self._proximo_aislado > 0:
            return
        self._proximo_aislado = self._azar.uniform(*self.ESPERA_ENTRE_SONIDOS)
        nombre = self._azar.choice(fase.sonidos_aislados)
        d = self._azar.uniform(*self.DISTANCIA_SONIDO_AISLADO)
        self._play_sfx_spatial(nombre, self._punto_lateral(d), 0.7)

    def _actualizar_serpiente_de_fondo(self, dt: float) -> None:
        if self._fase_actual.numero != 3:
            self._serpiente_visible = False
            return
        self._reloj_serpiente -= dt
        if self._reloj_serpiente <= 0:
            self._serpiente_visible = not self._serpiente_visible
            self._reloj_serpiente = (self._azar.uniform(2.0, 5.0)
                                     if self._serpiente_visible
                                     else self._azar.uniform(4.0, 9.0))

    # ── Luna (F5): la luz real manda ─────────────────────────────
    def _luz_de_luna(self) -> float:
        fase = 0.5 + 0.5 * math.sin(2 * math.pi * self._tiempo
                                    / self.PERIODO_DE_LA_LUNA)
        return self.LUZ_MINIMA_LUNA + (self.LUZ_MAXIMA_LUNA
                                       - self.LUZ_MINIMA_LUNA) * fase

    def _actualizar_luna(self, dt: float) -> None:
        if self._fase_actual.numero != 5:
            return
        self._ambiente_base = self._luz_de_luna()

    # ── Grietas (F6): el paso enciende ───────────────────────────
    def _luces_f6(self) -> list:
        """Las 13 luces verdes del TMX, de oeste a este (radio 70: las
        antorchas de 150 van aparte en `_luces_antorcha`)."""
        inicio = trazado.COLUMNAS_DE_LUZ[0] * trazado.TS
        fin = trazado.COLUMNAS_DE_LUZ[-1] * trazado.TS
        candidatas = [luz for luz in getattr(self, "_stage_lights", [])
                      if inicio - 8 <= luz.position.x <= fin + 8
                      and luz.radius < 100.0]
        return sorted(candidatas, key=lambda luz: luz.position.x)

    def _actualizar_grietas(self, dt: float) -> None:
        if self._fase_actual.numero != 6:
            self._ultima_x = self._player.rect.centerx
            return
        dx = abs(self._player.rect.centerx - self._ultima_x)
        self._ultima_x = self._player.rect.centerx
        en_suelo = getattr(self._player, "is_grounded",
                         getattr(self._player, "en_suelo", True))
        if not en_suelo:
            return
        self._distancia_f6 += dx
        if self._distancia_f6 < self.PASO_QUE_ENCIENDE:
            return
        self._distancia_f6 = 0.0
        px = self._player.rect.centerx
        mejor = None
        mejor_d = float("inf")
        for luz in self._luces_f6():
            if luz.intensity > 0.05:
                continue
            d = abs(luz.position.x - px)
            if d < mejor_d:
                mejor, mejor_d = luz, d
        if mejor is None or mejor_d > 400.0:
            return
        mejor.intensity = 0.9
        self._luces_encendidas += 1
        self._play_sfx_spatial("s41_paso_luz", mejor.position.x, 0.8)

    # ── Antorchas (F6): el camino se enciende al avanzar ────────
    def _luces_antorcha(self) -> list:
        inicio = trazado.ANTORCHAS_FASE6[0] * trazado.TS - 8
        fin = trazado.ANTORCHAS_FASE6[-1] * trazado.TS + 8
        return sorted(
            (luz for luz in getattr(self, "_stage_lights", [])
             if inicio <= luz.position.x <= fin and luz.radius >= 100.0),
            key=lambda luz: luz.position.x)

    def _actualizar_antorchas(self) -> None:
        if self._fase_actual.numero != 6:
            return
        if self._antorcha_encendidas == 0 and not self._luces_antorcha():
            try:
                from src.framework.vfx.lighting import LightSource
            except Exception:
                return
            for col in trazado.ANTORCHAS_FASE6:
                self._stage_lights.append(LightSource(
                    position=pygame.Vector2(col * trazado.TS, 440.0),
                    radius=150.0, color=(255, 180, 90), intensity=0.0,
                    flicker=True, flicker_speed=5.0, flicker_amount=0.2))
        px = self._player.rect.centerx
        antorchas = self._luces_antorcha()
        espiritus_orden = ("venado", "serpiente", "halcon")
        for i, luz in enumerate(antorchas):
            if luz.intensity > 0.05:
                continue
            if i > 0 and antorchas[i - 1].intensity <= 0.05:
                continue
            col = trazado.ANTORCHAS_FASE6[i]
            if px < col * trazado.TS:
                continue
            luz.intensity = 1.0
            self._antorcha_encendidas = max(self._antorcha_encendidas, i + 1)
            self._play_sfx_spatial("s41_paso_luz", luz.position.x, 0.9)
            self._post_processing.flash((140, 255, 180), alpha=90,
                                        duration=0.3)
            for grieta in self._luces_f6():
                if abs(grieta.position.x - luz.position.x) < 120.0:
                    grieta.intensity = 0.9
            if i < 3:
                self._aparicion_f6 = {"cual": espiritus_orden[i], "t": 0.0,
                                      "x": luz.position.x + 60.0}
                self.context.event_bus.emit(
                    Events.SHOW_MESSAGE,
                    text=f"La antorcha {i + 1} arde. Algo liberado vela "
                    "el camino.", duration=4.0)
            else:
                self.context.event_bus.emit(
                    Events.SHOW_MESSAGE,
                    text="Las cuatro antorchas arden. El templo aguarda.",
                    duration=5.0)

    # ── Templo (F6): la entrada en diez pasos ─────────────────────
    def _actualizar_templo(self, dt: float) -> None:
        if self._fase_actual.numero != 6 or self._templo_iniciado:
            # Anticipación: cerca del portal dormido, la tierra vibra.
            if (self._fase_actual.numero == 6 and not self._despertar_hecho
                    and not getattr(self, "_aviso_portal", False)):
                col = self._player.rect.centerx / trazado.TS
                if col >= 935:
                    self._aviso_portal = True
                    self._camera.apply_shake(amplitude=3.0, duration=0.6)
                    self.context.event_bus.emit(
                        Events.SHOW_MESSAGE,
                        text="El portal duerme. Tres espíritus faltan... "
                             "o ya cantan.", duration=5.0)
            return
        if self._player.rect.centerx < 940 * trazado.TS:
            return
        self._templo_iniciado = True
        self._reloj_templo = 0.0
        self._paso_templo = 0

    def _pasos_templo(self, dt: float) -> None:
        if not self._templo_iniciado or self._paso_templo >= 10:
            return
        self._reloj_templo += dt
        pasos = [
            (0.5, "El camino termina."),
            (2.0, "Las antorchas arden al máximo."),
            (3.5, "La niebla se arremolina."),
            (5.0, "La energía verde crece."),
            (6.5, None),
            (7.5, "La tierra tiembla."),
            (9.0, "Se escucha el despertar."),
            (10.5, "El portal se abre."),
            (12.0, "Paburu despierta. Entra."),
            (13.5, None),
        ]
        umbral, texto = pasos[self._paso_templo]
        if self._reloj_templo < umbral:
            return
        self._paso_templo += 1
        if texto:
            self.context.event_bus.emit(Events.SHOW_MESSAGE, text=texto,
                                        duration=3.0)
        if self._paso_templo == 2:
            for luz in self._luces_antorcha():
                luz.intensity = 1.0
        elif self._paso_templo == 4:
            self._ambient_particles.set_effect("spores", 40.0)
        elif self._paso_templo == 5:
            self._post_processing.flash((140, 255, 180), alpha=140,
                                        duration=0.6)
        elif self._paso_templo == 7:
            self._camera.apply_shake(amplitude=8.0, duration=0.8)
            self._play_sfx_spatial("s41_despertar",
                                   self._player.rect.centerx, 1.0)
            try:
                self.audio.play_voz("sfx_voz_paburu_risa")
            except Exception:
                pass
        elif self._paso_templo == 9:
            self._post_processing.flash((200, 255, 210), alpha=180,
                                        duration=1.0)

    # ── Lluvia por capas (F2/F3): la del motor es demasiado fina ──
    def _actualizar_lluvia(self, dt: float) -> None:
        """Tres planos de gotas con tamaño, velocidad y alfa propios, más
        salpicadura en el suelo. La intensidad la manda el clima real:
        F2 lluvia, F3 tormenta; con el incendio cesa de verdad."""
        clima = self._weather.climate if self._weather is not None else "clear"
        objetivo = {"rain": 110.0, "storm": 200.0}.get(clima, 0.0)
        while len(self._gotas) < int(objetivo):
            capa = self._azar.choices((0, 1, 2), weights=(0.45, 0.35, 0.20))[0]
            self._gotas.append({
                "x": self._azar.uniform(-40.0, 1320.0),
                "y": self._azar.uniform(-40.0, 720.0),
                "capa": capa,
            })
        if len(self._gotas) > int(objetivo):
            del self._gotas[int(objetivo):]
        # far: corta, lenta, tenue; mid: media; near: larga, rápida, marcada.
        vel = (420.0, 640.0, 900.0)
        viento = -140.0 if clima == "storm" else -40.0
        for g in self._gotas:
            c = g["capa"]
            g["y"] += vel[c] * dt
            g["x"] += viento * (0.4 + 0.3 * c) * dt
            if g["y"] > 730.0:
                g["y"] = -20.0
                g["x"] = self._azar.uniform(-40.0, 1320.0)
                if c == 2 and len(self._salpicaduras) < 40:
                    self._salpicaduras.append({"x": g["x"], "t": 0.0})
            if g["x"] < -60.0:
                g["x"] = 1300.0
        vivos = []
        for s in self._salpicaduras:
            s["t"] += dt
            if s["t"] < 0.25:
                vivos.append(s)
        self._salpicaduras = vivos

    def _dibujar_lluvia(self, surface: pygame.Surface) -> None:
        if not self._gotas and not self._salpicaduras:
            return
        conf = ((6, 1, 90), (12, 2, 130), (22, 3, 175))
        for g in self._gotas:
            largo, grosor, alfa = conf[g["capa"]]
            x, y = g["x"], g["y"]
            incl = -4.0 if self._fase_actual.numero == 3 else -1.5
            pygame.draw.line(surface, (170, 190, 220, alfa), (x, y),
                             (x + incl * (g["capa"] + 1), y - largo), grosor)
        sy = 512 - self._camera.offset.y
        for s in self._salpicaduras:
            r = 2 + s["t"] * 14
            pygame.draw.ellipse(surface, (190, 205, 230, 120),
                                (s["x"] - r, sy - 2, r * 2, 4), 1)

    # ── Niebla estratificada (F6): ocupa el espacio ──────────────
    def _texturas_niebla(self) -> list[pygame.Surface]:
        if self._niebla_tex is None:
            self._niebla_tex = []
            # AUD-816: la niebla abraza el suelo, no el cielo. Muchas
            # manchas pequeñas y tenues; las grandes se leen como objetos.
            for base in (26, 20, 14):
                tex = pygame.Surface((640, 120), pygame.SRCALPHA)
                rng = random.Random(99 + base)
                for _ in range(220):
                    x = rng.randrange(640)
                    w = rng.randrange(15, 45)
                    a = rng.randrange(3, base)
                    pygame.draw.ellipse(tex, (200, 215, 205, a),
                                        (x, rng.randrange(110), w, 10))
                self._niebla_tex.append(tex)
        return self._niebla_tex

    def _dibujar_niebla(self, surface: pygame.Surface) -> None:
        """Tres bandas pegadas al suelo y al midground, a distinta
        profundidad: la lejana tapa el fondo, la cercana apenas roza.
        Derivan con la cámara a distinto factor más el tiempo."""
        tex = self._texturas_niebla()
        camx = self._camera.offset.x
        for i, (y, factor, vel) in enumerate(((300, 0.08, 12.0),
                                              (420, 0.20, 26.0),
                                              (520, 0.45, 48.0))):
            desf = -((camx * factor + self._tiempo * vel) % 640.0)
            x = desf
            while x < 1280.0:
                surface.blit(tex[i], (x, y))
                x += 640.0

    # ── Liberaciones ─────────────────────────────────────────────
    def _al_disparar(self, evento: str = "", nombre: str = "",
                     **_resto: Any) -> None:
        altar = nombre or evento
        if altar not in _ALTARES:
            return
        indice, llave, bandera, dialogo_id, nombre_esp = _ALTARES[altar]
        if self._liberados[indice]:
            return
        # Causalidad narrativa: el altar sólo libera a quien ya habló con
        # el espíritu (su MessageTrigger abrió el árbol). Sin diálogo, el
        # altar responde pero no entrega nada.
        if dialogo_id not in self._dialogo_visto:
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text=f"{nombre_esp} aún no te ha hablado. Escúchalo "
                "primero.", duration=4.0)
            return
        self._liberados[indice] = True
        llavero = self._interactables.llavero
        if not llavero.tiene(llave):
            llavero.coger(llave)
        self.context.event_bus.emit(Events.FLAG_SET, flag=bandera)
        self._play_sfx_spatial("s41_liberacion",
                               self._player.rect.centerx, 1.0)
        self._post_processing.flash((140, 255, 180), alpha=120, duration=0.4)
        self._ascensiones.append({"x": self._player.rect.centerx,
                                  "t": 0.0, "alfa": 1.0})
        self.context.event_bus.emit(
            Events.SHOW_MESSAGE,
            text=f"{nombre_esp} asciende. ({sum(self._liberados)}/3)",
            duration=5.0)
        if all(self._liberados) and not self._despertar_hecho:
            self._despertar_hecho = True
            if not llavero.tiene(trazado.LLAVE_PABURU):
                llavero.coger(trazado.LLAVE_PABURU)
            self.context.event_bus.emit(Events.FLAG_SET,
                                        flag=trazado.BANDERA_PABURU)
            self._play_sfx_spatial("s41_despertar",
                                   self._player.rect.centerx, 1.0)
            self._camera.apply_shake(amplitude=8.0, duration=0.6)
            self._post_processing.flash((140, 255, 180), alpha=160,
                                        duration=0.8)
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text="Los tres espíritus ascendieron. Paburu despierta: "
                     "el portal del este está abierto.", duration=7.0)

    def _actualizar_ascensiones(self, dt: float) -> None:
        vivas = []
        for asc in self._ascensiones:
            asc["t"] += dt
            asc["alfa"] = max(0.0, 1.0 - asc["t"] / 4.0)
            if asc["alfa"] > 0:
                vivas.append(asc)
        self._ascensiones = vivas

    # ── Incendio (F4): los rayos prenden, la lluvia cesa ──────────
    def _actualizar_incendio(self, dt: float) -> None:
        if self._fase_actual.numero != 4 or self._incendio_activo:
            return
        col = self._player.rect.centerx / trazado.TS
        for i, pira in enumerate(trazado.PIRAS_FASE4):
            if not self._piras_encendidas[i] and col >= pira - 20:
                self._piras_encendidas[i] = True
                self._post_processing.flash((255, 220, 150), alpha=200,
                                            duration=0.25)
                self._trueno_x = self._player.rect.centerx
                self._trueno_pendiente = self._azar.uniform(0.3, 0.8)
                self.context.event_bus.emit(
                    Events.SHOW_MESSAGE,
                    text="Un rayo prende el bosque...", duration=3.0)
        if all(self._piras_encendidas):
            self._incendio_activo = True
            # La lluvia se detiene: el cambio debe ser evidente.
            self._cambiar_clima("clear")
            self._ambient_particles.set_effect("embers", 22.0)
            audio = self.audio
            if audio is not None:
                ruta = (settings.ASSETS_DIR / "sfx" / "environment"
                        / "amb_stage41_fuego.wav")
                if ruta.is_file():
                    audio.crossfade_ambient(ruta, duration=2.0, volume=0.35)
            self._encender_luces_incendio()
            self.context.event_bus.emit(
                Events.SHOW_MESSAGE,
                text="La lluvia cesa. El bosque arde.", duration=4.0)

    def _encender_luces_incendio(self) -> None:
        """Tres focos anaranjados con parpadeo sobre las piras (objetos de
        luz del motor, creados en runtime y atados a las piras)."""
        try:
            from src.framework.vfx.lighting import LightSource
        except Exception:
            return
        for i, pira in enumerate(trazado.PIRAS_FASE4):
            self._stage_lights.append(LightSource(
                position=pygame.Vector2(pira * trazado.TS, 430.0),
                radius=190.0, color=(255, 150, 60), intensity=0.85,
                flicker=True, flicker_speed=6.0 + i, flicker_amount=0.25))

    # ── Caza (F4): la sombra sigue al jugador ─────────────────────
    def _actualizar_caza(self, dt: float) -> None:
        if (self._fase_actual.numero != 4 or not self._incendio_activo
                or self._silencio_hecho):
            self._caza_x = None
            return
        px = self._player.rect.centerx
        if self._caza_x is None:
            self._caza_x = px - 500.0
        # Acelera, se detiene, vuelve: nunca a ritmo constante.
        self._reloj_caza -= dt
        if self._reloj_caza <= 0:
            self._reloj_caza = self._azar.uniform(1.5, 4.0)
            self._vel_caza = self._azar.uniform(-60.0, 260.0)
        objetivo = px - 80.0
        self._caza_x += max(-320.0, min(320.0,
                                       (objetivo - self._caza_x) * 1.5)) * dt
        self._caza_x += self._vel_caza * dt * 0.3
        if abs(self._caza_x - px) < 50.0:
            self._camera.apply_shake(amplitude=6.0, duration=0.25)
            self._play_sfx_spatial("sfx_environment_screen_shake", px, 0.7)
            self._caza_x = px - 400.0

    # ── Nubes (F5): tapan la luna por rachas ──────────────────────
    def _actualizar_nubes(self, dt: float) -> None:
        if self._fase_actual.numero != 5:
            self._nube = 0.0
            return
        self._reloj_nube += dt
        ciclo = (self._reloj_nube % 16.0) / 16.0
        # Cubierto entre el 40% y el 75% del ciclo, con bordes suaves.
        if ciclo < 0.4:
            objetivo = 0.0
        elif ciclo < 0.5:
            objetivo = (ciclo - 0.4) / 0.1
        elif ciclo < 0.65:
            objetivo = 1.0
        elif ciclo < 0.75:
            objetivo = 1.0 - (ciclo - 0.65) / 0.1
        else:
            objetivo = 0.0
        self._nube += (objetivo - self._nube) * min(1.0, dt * 2.0)

    def _luz_de_luna(self) -> float:
        fase = 0.5 + 0.5 * math.sin(2 * math.pi * self._tiempo
                                    / self.PERIODO_DE_LA_LUNA)
        base = self.LUZ_MINIMA_LUNA + (self.LUZ_MAXIMA_LUNA
                                       - self.LUZ_MINIMA_LUNA) * fase
        return base * (1.0 - 0.65 * self._nube)