"""
Module: test_orphan_systems
System: tests
Academic Unit: N/A

Los sistemas que nadie probaba.

F2.5 — la auditoría de julio contó **doce módulos sin una sola prueba propia**.
Se ejercitaban de refilón por el arnés de escenas, que sólo pregunta si algo se
cae. Es exactamente el hueco por el que se colaron los defectos más caros de
este proyecto:

* la iluminación, que nunca iluminó un píxel porque un `uint8` desbordaba;
* las partículas de ambiente, cuyo emisor nadie encendía;
* el bloom, que aclaraba las sombras más que las luces.

Los tres pasaban el arnés. Ninguno hacía lo que prometía.

Estas pruebas preguntan lo que el arnés no pregunta: **¿el efecto cambia los
píxeles?**, **¿el contador cuenta?**, **¿el estado avanza?**. No buscan
cobertura de líneas; buscan la promesa de cada módulo.
"""
from __future__ import annotations

import numpy as np
import pygame
import pytest


@pytest.fixture(scope="module")
def display():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield pygame.display.get_surface()


def _lienzo(color=(120, 120, 120)) -> pygame.Surface:
    s = pygame.Surface((320, 180))
    s.fill(color)
    return s


def _pixeles(s: pygame.Surface) -> np.ndarray:
    return pygame.surfarray.array3d(s).astype(float)


class TestLaNieblaDeGuerraOcultaYRevela:
    """Un velo que no oscurece, o que no se abre, no es niebla de guerra."""

    def test_sin_revelar_nada_la_pantalla_queda_a_oscuras(self, display):
        from src.framework.vfx.fog_of_war import FogOfWar

        niebla = FogOfWar(320, 180, radius=40)
        lienzo = _lienzo()
        antes = _pixeles(lienzo).mean()
        niebla.draw(lienzo, pygame.Vector2(0, 0))
        assert _pixeles(lienzo).mean() < antes * 0.4, (
            "la niebla no oscurece nada"
        )

    def test_revelar_abre_un_hueco(self, display):
        from src.framework.vfx.fog_of_war import FogOfWar

        niebla = FogOfWar(320, 180, radius=40)
        niebla.reveal(160, 90)
        lienzo = _lienzo()
        niebla.draw(lienzo, pygame.Vector2(0, 0))
        pix = _pixeles(lienzo)
        assert pix[160, 90].mean() > pix[10, 10].mean() * 1.5, (
            f"el punto revelado ({pix[160, 90].mean():.0f}) no está más claro "
            f"que el resto ({pix[10, 10].mean():.0f})"
        )

    def test_el_hueco_sigue_a_la_camara(self, display):
        from src.framework.vfx.fog_of_war import FogOfWar

        niebla = FogOfWar(320, 180, radius=40)
        niebla.reveal(200, 90)
        a = _lienzo()
        niebla.draw(a, pygame.Vector2(0, 0))
        b = _lienzo()
        niebla.draw(b, pygame.Vector2(100, 0))
        assert _pixeles(b)[100, 90].mean() > _pixeles(b)[200, 90].mean(), (
            "el hueco no se desplaza con el desplazamiento de cámara"
        )

    def test_clear_vuelve_a_taparlo_todo(self, display):
        from src.framework.vfx.fog_of_war import FogOfWar

        niebla = FogOfWar(320, 180, radius=40)
        niebla.reveal_all([(50, 50), (160, 90), (280, 120)])
        niebla.clear()
        lienzo = _lienzo()
        niebla.draw(lienzo, pygame.Vector2(0, 0))
        pix = _pixeles(lienzo)
        assert pix.std() < 2.0, "quedan huecos tras limpiar la niebla"


class TestElAguaSeMueve:
    def test_el_reflejo_cambia_con_el_tiempo(self, display):
        from src.framework.vfx.water_effect import WaterEffect

        agua = WaterEffect(320, 180)
        a = _lienzo((20, 20, 30))
        agua.draw(a, pygame.Vector2(0, 0))
        primero = _pixeles(a)
        for _ in range(30):
            agua.update(1 / 60)
        b = _lienzo((20, 20, 30))
        agua.draw(b, pygame.Vector2(0, 0))
        assert not np.array_equal(primero, _pixeles(b)), (
            "el agua se dibuja igual medio segundo después: no está animada"
        )

    def test_el_agua_aclara_la_escena(self, display):
        """Se suma con BLEND_RGB_ADD: tiene que aportar luz, no quitarla."""
        from src.framework.vfx.water_effect import WaterEffect

        agua = WaterEffect(320, 180)
        lienzo = _lienzo((20, 20, 30))
        antes = _pixeles(lienzo).mean()
        agua.draw(lienzo, pygame.Vector2(0, 0))
        assert _pixeles(lienzo).mean() > antes

    def test_la_amplitud_controla_cuanto_ondula(self, display):
        from src.framework.vfx.water_effect import WaterEffect

        def recorrido(amplitud: int) -> int:
            agua = WaterEffect(320, 180)
            agua.set_params(amplitude=amplitud)
            for _ in range(60):
                agua.update(1 / 60)
            return max(agua._wave_offsets) - min(agua._wave_offsets)

        assert recorrido(12) > recorrido(2), (
            "subir la amplitud no ensancha la onda"
        )


class TestElCronometroDeSpeedrunCuenta:
    def test_avanza_mientras_corre_y_se_para_al_parar(self):
        from src.framework.stage.speedrun_mode import SpeedrunTimer

        crono = SpeedrunTimer()
        crono.start()
        for _ in range(60):
            crono.update(1 / 60)
        corriendo = crono._global_time
        assert corriendo == pytest.approx(1.0, abs=0.05)

        crono.stop()
        for _ in range(60):
            crono.update(1 / 60)
        parado = crono._global_time
        assert parado == pytest.approx(corriendo, abs=1e-6), (
            "el cronómetro sigue contando después de pararlo"
        )

    def test_reset_lo_devuelve_a_cero(self):
        from src.framework.stage.speedrun_mode import SpeedrunTimer

        crono = SpeedrunTimer()
        crono.start()
        for _ in range(120):
            crono.update(1 / 60)
        crono.reset()
        assert (crono._global_time) == 0.0

    def test_los_parciales_se_acumulan_en_orden(self):
        from src.framework.stage.speedrun_mode import SpeedrunTimer

        crono = SpeedrunTimer()
        crono.start()
        for etapa in ("stage0", "stage1", "stage2"):
            crono.start_stage(etapa)
            for _ in range(30):
                crono.update(1 / 60)
            crono.split(etapa)
        parciales = crono.get_splits()
        assert len(parciales) == 3
        tiempos = [p.get("time", p.get("total", 0)) for p in parciales]
        assert tiempos == sorted(tiempos), (
            f"los parciales no crecen de forma monótona: {tiempos}"
        )

    def test_el_formato_es_legible(self):
        from src.framework.stage.speedrun_mode import SpeedrunTimer

        crono = SpeedrunTimer()
        texto = crono.get_formatted_time(125.5)
        assert ":" in texto, f"el tiempo no sale como reloj: {texto!r}"
        assert "2" in texto, f"125,5 s son más de dos minutos: {texto!r}"

    def test_guardar_y_cargar_conserva_los_parciales(self, tmp_path):
        from src.framework.stage.speedrun_mode import SpeedrunTimer

        crono = SpeedrunTimer()
        crono.start()
        crono.start_stage("stage0")
        for _ in range(60):
            crono.update(1 / 60)
        crono.split("stage0")
        destino = tmp_path / "records.json"
        crono.save(destino)

        otro = SpeedrunTimer()
        otro.load(destino)
        assert otro.get_splits(), "cargar no recuperó ningún parcial"


class TestElModoJefesAvanza:
    @staticmethod
    def _modo():
        from src.framework.stage.boss_rush_mode import BossRushMode, BossRushStage

        return BossRushMode([
            BossRushStage("boss_venado", "Venado", lambda: None),
            BossRushStage("boss_gavilan", "Gavilán", lambda: None),
        ])

    def test_empieza_inactivo_y_start_lo_activa(self):
        modo = self._modo()
        assert not modo.active
        modo.start()
        assert modo.active
        assert modo.get_current_stage().boss_id == "boss_venado"

    def test_avanzar_recorre_los_jefes_en_orden(self):
        modo = self._modo()
        modo.start()
        assert modo.advance_to_next().boss_id == "boss_gavilan"
        assert modo.advance_to_next() is None, (
            "hay un tercer jefe donde sólo se declararon dos"
        )

    def test_el_modo_se_puede_terminar(self):
        """F2.5 — `is_complete()` no podía devolver True nunca.

        Exigía `_active and _current_index >= len(_stages)`, y el código
        anterior nunca pasaba el índice del último jefe y además apagaba
        `_active` al llegar al final. Las dos condiciones eran incompatibles:
        un modo de juego sin final.
        """
        modo = self._modo()
        modo.start()
        assert not modo.is_complete()
        modo.advance_to_next()
        assert not modo.is_complete(), "se da por terminado con un jefe vivo"
        modo.advance_to_next()
        assert modo.is_complete(), (
            "tras superar a los dos jefes el modo sigue sin darse por terminado"
        )

    def test_terminar_no_depende_de_que_el_modo_siga_activo(self):
        """El invariante que hacía imposible completar el modo.

        La versión anterior fallaba por la combinación de dos cosas: el índice
        nunca pasaba del último jefe **y** `advance_to_next` apagaba `_active`
        al llegar al final, mientras que `is_complete()` exigía las dos. Basta
        arreglar el índice para que funcione, así que un mutante que reponga la
        condición `_active` no se nota hoy.

        Esta prueba fija el invariante directamente: haber terminado es un
        hecho sobre el progreso, no sobre si el modo sigue corriendo.
        """
        modo = self._modo()
        modo.start()
        modo.advance_to_next()
        modo.advance_to_next()
        assert modo.is_complete()
        modo._active = False           # el jugador sale al menú
        assert modo.is_complete(), (
            "salir del modo borra el hecho de haberlo terminado"
        )

    def test_el_ultimo_jefe_tambien_cuenta(self):
        """F2.5 — sólo se acreditaba al jefe si quedaba otro después.

        Derrotar al jefe final no daba puntos y lo dejaba marcado como vivo.
        Medido con dos jefes antes de la corrección: `[True, False]`.
        """
        modo = self._modo()
        modo.start()
        modo.advance_to_next()
        puntos_intermedios = modo.score
        modo.advance_to_next()
        assert all(s.defeated for s in modo._stages), (
            f"jefes marcados como derrotados: "
            f"{[s.defeated for s in modo._stages]}"
        )
        assert modo.score > puntos_intermedios, (
            "derrotar al jefe final no suma nada"
        )

    def test_los_golpes_recibidos_bajan_la_puntuacion(self):
        limpio = self._modo()
        limpio.start()
        golpeado = self._modo()
        golpeado.start()
        for _ in range(10):
            golpeado.record_hit()
        assert golpeado.score <= limpio.score, (
            "recibir diez golpes no penaliza la puntuación"
        )

    def test_sin_jefes_declarados_no_revienta(self):
        from src.framework.stage.boss_rush_mode import BossRushMode

        modo = BossRushMode([])
        modo.start()
        assert modo.get_current_stage() is None
        assert modo.advance_to_next() is None


class TestElBancoDeSonidosNoRevientaSinArchivos:
    """Un banco de sonidos que lanza deja al juego mudo y muerto, no sólo mudo."""

    def test_pedir_un_sonido_inexistente_no_lanza(self, display):
        from src.engine.audio.sound_bank import SoundBank

        banco = SoundBank()
        banco.play("no_existe_este_sonido")      # no debe lanzar

    def test_cargar_una_ruta_inexistente_no_lanza(self, display, tmp_path):
        from src.engine.audio.sound_bank import SoundBank

        banco = SoundBank()
        banco.load("fantasma", tmp_path / "no_existe.wav")
        banco.play("fantasma")

    def test_load_all_sin_mezclador_avisa_y_sigue(self, display):
        from src.engine.audio.sound_bank import SoundBank

        estaba = pygame.mixer.get_init() is not None
        if estaba:
            pygame.mixer.quit()
        try:
            SoundBank().load_all()               # no debe lanzar
        finally:
            if estaba:
                try:
                    pygame.mixer.init()
                except pygame.error:
                    pass


class TestLosNumerosDeDanoAparecenYSeVan:
    def test_un_numero_nuevo_se_dibuja(self, display):
        from src.framework.vfx.damage_numbers import DamageNumberManager

        numeros = DamageNumberManager()
        numeros.add(160, 90, "42")
        lienzo = _lienzo((0, 0, 0))
        numeros.draw(lienzo, pygame.Vector2(0, 0))
        assert (_pixeles(lienzo).max(axis=2) > 0).sum() > 0, (
            "el número de daño no pinta ni un píxel"
        )

    def test_acaba_desapareciendo(self, display):
        from src.framework.vfx.damage_numbers import DamageNumberManager

        numeros = DamageNumberManager()
        numeros.add(160, 90, "42")
        for _ in range(300):                      # cinco segundos
            numeros.update(1 / 60)
        lienzo = _lienzo((0, 0, 0))
        numeros.draw(lienzo, pygame.Vector2(0, 0))
        assert (_pixeles(lienzo).max(axis=2) > 0).sum() == 0, (
            "los números de daño se quedan en pantalla para siempre"
        )

    def test_clear_los_borra_de_golpe(self, display):
        from src.framework.vfx.damage_numbers import DamageNumberManager

        numeros = DamageNumberManager()
        for i in range(5):
            numeros.add(50 + i * 40, 90, str(i))
        numeros.clear()
        lienzo = _lienzo((0, 0, 0))
        numeros.draw(lienzo, pygame.Vector2(0, 0))
        assert (_pixeles(lienzo).max(axis=2) > 0).sum() == 0


class TestLaMusicaDinamicaEligeSegunLaSituacion:
    """La intensidad tiene que salir del estado del juego, no de un contador."""

    @staticmethod
    def _sistema():
        from src.framework.audio.dynamic_music import DynamicMusicSystem

        class _AudioFalso:
            def __init__(self):
                self.reproducido = []

            def play_music(self, ruta, loops=-1):
                self.reproducido.append(str(ruta))

        audio = _AudioFalso()
        return DynamicMusicSystem(audio), audio

    def test_un_jefe_manda_sobre_todo_lo_demas(self):
        sistema, _audio = self._sistema()
        assert sistema.detect_intensity_from_state(
            has_boss=True, has_alive_enemies=False) == sistema.INTENSITY_BOSS
        assert sistema.detect_intensity_from_state(
            has_boss=True, has_alive_enemies=True) == sistema.INTENSITY_BOSS

    def test_enemigos_vivos_dan_combate_y_ninguno_da_calma(self):
        sistema, _audio = self._sistema()
        assert sistema.detect_intensity_from_state(
            False, True) == sistema.INTENSITY_COMBAT
        assert sistema.detect_intensity_from_state(
            False, False) == sistema.INTENSITY_CALM

    def test_repetir_la_misma_intensidad_no_reinicia_la_musica(self):
        """Volver a poner la pista desde el principio cada fotograma se oye."""
        sistema, audio = self._sistema()
        sistema.set_zone(1, "bgm_zone1")
        sistema.set_intensity(sistema.INTENSITY_COMBAT)
        reproducciones = len(audio.reproducido)
        for _ in range(10):
            sistema.set_intensity(sistema.INTENSITY_COMBAT)
        assert len(audio.reproducido) == reproducciones, (
            "la misma intensidad relanza la pista una y otra vez"
        )

    def test_sin_pista_base_no_intenta_reproducir_nada(self):
        sistema, audio = self._sistema()
        sistema.set_intensity(sistema.INTENSITY_BOSS)
        assert audio.reproducido == [], (
            "intenta reproducir música sin saber qué pista corresponde"
        )

    def test_una_pista_inexistente_no_lanza(self):
        sistema, audio = self._sistema()
        sistema.set_zone(9, "bgm_que_no_existe")
        sistema.set_intensity(sistema.INTENSITY_BOSS)   # no debe lanzar
        assert audio.reproducido == [], (
            "reproduce una pista que no existe en disco"
        )


class TestLosPeligrosHacenDano:
    """Zonas de daño, mensajes y pozos: lo que mata al jugador."""

    @pytest.fixture
    def montaje(self, display):
        import pygame as pg

        from src.engine.core.event_bus import EventBus
        from src.framework.stage.hazard_system import HazardSystem
        from src.framework.stage.stage_loader import DeathPit, HazardZone, MessageTrigger

        class _Contexto:
            def __init__(self):
                self.event_bus = EventBus()
                self.scene_manager = None

        class _Jugador:
            def __init__(self):
                self.rect = pg.Rect(100, 100, 20, 30)
                self.danos = []

            def apply_damage(self, cantidad, origen=None):
                self.danos.append(cantidad)

        class _Escenario:
            message_triggers = []
            hazard_zones = []
            death_pits = []

        ctx = _Contexto()
        return HazardSystem(ctx), _Jugador(), _Escenario(), ctx, (
            HazardZone, DeathPit, MessageTrigger)

    def test_una_zona_de_dano_hace_dano_al_tocarla(self, montaje):
        import pygame as pg

        sistema, jugador, escenario, _ctx, (HazardZone, _, _) = montaje
        escenario.hazard_zones = [
            HazardZone(rect=pg.Rect(90, 90, 60, 60), damage=0.5, timer=0.0)]
        sistema.update(1 / 60, jugador, escenario)
        assert jugador.danos == [0.5], (
            f"el jugador dentro de la zona recibió {jugador.danos}"
        )

    def test_la_zona_respeta_su_enfriamiento(self, montaje):
        import pygame as pg

        sistema, jugador, escenario, _ctx, (HazardZone, _, _) = montaje
        escenario.hazard_zones = [
            HazardZone(rect=pg.Rect(90, 90, 60, 60), damage=0.5,
                       cooldown=0.5, timer=0.0)]
        for _ in range(10):                    # menos de medio segundo
            sistema.update(1 / 60, jugador, escenario)
        assert len(jugador.danos) == 1, (
            f"la zona hizo daño {len(jugador.danos)} veces en 0,17 s pese a "
            "tener medio segundo de enfriamiento"
        )

    def test_fuera_de_la_zona_no_hay_dano(self, montaje):
        import pygame as pg

        sistema, jugador, escenario, _ctx, (HazardZone, _, _) = montaje
        escenario.hazard_zones = [
            HazardZone(rect=pg.Rect(500, 500, 40, 40), damage=0.5, timer=0.0)]
        for _ in range(30):
            sistema.update(1 / 60, jugador, escenario)
        assert jugador.danos == []

    def test_un_mensaje_se_dispara_una_sola_vez(self, montaje):
        import pygame as pg

        sistema, jugador, escenario, ctx, (_, _, MessageTrigger) = montaje
        recibidos = []
        ctx.event_bus.subscribe("show_message", lambda **d: recibidos.append(d))
        escenario.message_triggers = [
            MessageTrigger(rect=pg.Rect(90, 90, 60, 60), text="hola")]
        for _ in range(20):
            sistema.update(1 / 60, jugador, escenario)
            ctx.event_bus.dispatch()
        assert len(recibidos) <= 1, (
            f"el mensaje se disparó {len(recibidos)} veces"
        )
        assert escenario.message_triggers[0].triggered is True

    def test_caer_a_un_pozo_programa_la_muerte(self, montaje):
        import pygame as pg

        sistema, jugador, escenario, _ctx, (_, DeathPit, _) = montaje
        escenario.death_pits = [DeathPit(rect=pg.Rect(90, 90, 60, 60))]
        sistema.update(1 / 60, jugador, escenario)
        assert sistema._pending_death is True, (
            "el jugador cayó al pozo y no se programó su muerte"
        )
