"""
Module: test_audio_wiring
System: tests
Academic Unit: N/A

Los sonidos declarados tienen que sonar (AUD-064).

Por qué existe
--------------
Tercera aparición del mismo patrón que produjo AUD-060 y AUD-062: algo escrito
por completo, cableado a medias, y nadie comprobando el último tramo.

Cada efecto de sonido del juego atraviesa cuatro pasos:

1. se declara como evento en `Events`;
2. se asocia a un archivo en el mapa de `StageScene`;
3. se le da un subtítulo en `subtitle_overlay.py` — accesibilidad;
4. **alguien lo emite** cuando ocurre la acción.

Veinte de los treinta y ocho sonidos tenían los tres primeros pasos y **no el
cuarto**. El jefe embestía, pisaba y lanzaba lianas en silencio absoluto;
golpear a cualquier enemigo era mudo; parar —la acción más difícil del juego—
no hacía ruido; la pantalla de game over aparecía sin sonido.

Y no era sólo audio: como el subtítulo se dispara con el mismo evento, quien
juegue con subtítulos activados tampoco recibía nada. El sistema de
accesibilidad estaba tan mudo como los altavoces.

Nada de esto rompía ninguna prueba, porque los tres primeros pasos son tablas
de datos y las tablas estaban perfectas.
"""
from __future__ import annotations

import inspect
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _fichero_del_mapa_de_sonidos() -> pathlib.Path:
    """Dónde vive la tabla `Events.SFX_… → nombre de muestra`.

    Se pregunta al módulo en vez de escribir la ruta a mano. AUD-152 movió la
    tabla de `stage_scene.py` a `stage_parts/senales.py`, y AUD-290 de ahí a
    `stage_parts/sonido.py`. Una constante fija habría hecho que estas pruebas
    fallaran con «ya no está cableado», que es una acusación falsa: el cableado
    estaba intacto y lo que se movió fue el archivo. Un `getsourcefile` sigue al
    módulo se mueva donde se mueva — lo que hay que actualizar es **qué módulo**
    se mira, y eso es una línea.
    """
    from src.framework.scenes.stage_parts import sonido

    ruta = inspect.getsourcefile(sonido)
    assert ruta is not None
    return pathlib.Path(ruta)


SFX_MAP_FILE = _fichero_del_mapa_de_sonidos()
SUBTITLE_FILE = ROOT / "src" / "engine" / "ui" / "subtitle_overlay.py"

#: Sonidos que todavía no puede disparar nadie porque su jefe **no existe**.
#: Los tres jefes de zona 2, 3 y 4 son trabajo de los estudiantes; sus efectos
#: ya están grabados y esperando. Esta lista sólo puede encoger: cuando alguien
#: construya el jefe, quitará su línea de aquí.
#:
#: Es la misma disciplina que `AWAITING_MIGRATION` en `test_ui_consistency`:
#: una excepción con nombre y motivo se puede revisar; un silencio no.
AWAITING_THEIR_BOSS = {
    "SFX_BOSSES_GAVILAN_DIVE",
    "SFX_BOSSES_GAVILAN_MASK_BEAM",
    # `SFX_BOSSES_PABURU_EYE_BEAM` estaba aquí y ya no: la entrega de Paburu lo
    # emite (`boss_paburu.py`). La lista encogió, que es lo que se dijo que
    # pasaría. `SFX_BOSSES_PABURU_WAVE` sigue esperando a su fase.
    "SFX_BOSSES_PABURU_WAVE",
    # `SFX_BOSSES_REY_SPIT`/`REY_SPLIT` salieron: `boss_rey.py` los emite
    # desde su nueva fase (ya en `HEAD`).
    # La reliquia aparece al derrotar a un jefe de zona; hoy sólo existe el
    # Venado y su recompensa se resuelve por la escena de créditos.
    "SFX_BOSSES_RELIC_APPEAR",
}

#: Sonidos cuya acción todavía no está implementada en el jugador o el entorno.
#: Distinto motivo que el anterior, así que lista distinta: aquí el que falta
#: es el *hecho*, no el jefe.
#
# AUD-255 la vació: los cuatro que quedaban —agacharse, curarse, posarse en una
# repisa atravesable y el proyectil contra la pared— tenían fichero, tabla y
# subtítulo, y les faltaba **sólo el `emit`**. Ninguno esperaba una
# funcionalidad: esperaban una línea. La lista se deja declarada porque el
# hueco que vigila es real y volverá a haber sonidos por delante de su acción.
# AUD-722 — veneno: el daño por segundo existe pero aún no emite su tic sonoro.
AWAITING_THEIR_FEATURE: set[str] = {"SFX_POISON_TICK"}


def _wired_sounds() -> set[str]:
    """Eventos SFX asociados a un archivo de sonido."""
    text = SFX_MAP_FILE.read_text(encoding="utf-8")
    return set(re.findall(r'Events\.(SFX_\w+):\s*"[\w_]+"', text))


def _emitted_sounds() -> set[str]:
    """Eventos SFX que alguien dispara en algún punto del código.

    Se considera «disparable» toda aparición que no sea una tabla de datos: ni
    el mapa evento→archivo, ni el de subtítulos, ni la definición del enum, ni
    una suscripción.

    Buscar literalmente `emit(Events.X)` no vale: hay sitios que eligen el
    evento con un ternario —`SFX_ENEMY_DIE_LARGE if grande else
    SFX_ENEMY_DIE_SMALL`— y una versión anterior de esta comprobación los dio
    por huérfanos. Un detector con falsos positivos habría hecho que alguien
    «arreglara» sonidos que ya funcionaban.
    """
    emitted: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        if path.name == "events.py":
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            for name in re.findall(r"Events\.(SFX_\w+)", stripped):
                is_table = re.match(rf'Events\.{name}:\s*"', stripped)
                is_subscription = (
                    "subscribe(" in stripped or "_vfx_handlers[" in stripped
                )
                if not (is_table or is_subscription):
                    emitted.add(name)
    return emitted


class TestEverySoundCanActuallyPlay:
    def test_no_sound_is_wired_but_never_triggered(self) -> None:
        """Un sonido con archivo, handler y subtítulo que nadie emite es mudo.

        El fallo es invisible: las tablas están bien, las pruebas de las tablas
        pasan, y el juego simplemente no suena.
        """
        orphans = _wired_sounds() - _emitted_sounds()
        unexplained = orphans - AWAITING_THEIR_BOSS - AWAITING_THEIR_FEATURE
        assert not unexplained, (
            f"sonidos cableados que nadie dispara: {sorted(unexplained)}. "
            f"O se emiten donde ocurre la acción, o se añaden a una lista de "
            f"espera con su motivo."
        )

    def test_the_waiting_lists_only_contain_real_sounds(self) -> None:
        """Una lista de espera con nombres inventados deja de ser revisable."""
        wired = _wired_sounds()
        stale = (AWAITING_THEIR_BOSS | AWAITING_THEIR_FEATURE) - wired
        assert not stale, f"la lista de espera nombra sonidos inexistentes: {stale}"

    def test_the_waiting_lists_do_not_hide_a_sound_that_already_plays(self) -> None:
        """Si alguien lo conectó, hay que sacarlo de la lista o mentirá."""
        both = (AWAITING_THEIR_BOSS | AWAITING_THEIR_FEATURE) & _emitted_sounds()
        assert not both, (
            f"estos sonidos ya se emiten y siguen en la lista de espera: "
            f"{sorted(both)}"
        )

    def test_every_wired_sound_has_a_file_on_disk(self) -> None:
        """Un evento apuntando a un archivo inexistente falla en silencio."""
        text = SFX_MAP_FILE.read_text(encoding="utf-8")
        pairs = re.findall(r'Events\.(SFX_\w+):\s*"([\w_]+)"', text)
        available = {p.stem for p in (ROOT / "assets" / "sfx").rglob("*.wav")}
        missing = [(event, key) for event, key in pairs if key not in available]
        assert not missing, f"eventos sin archivo .wav: {missing}"

    def test_informational_sounds_have_a_subtitle(self) -> None:
        """Accesibilidad, con el criterio del propio módulo de subtítulos.

        La primera versión de esta prueba exigía subtítulo para **todos** los
        sonidos audibles, y fallaba señalando pasos, saltos y el hover del
        menú. Estaba equivocada: `subtitle_overlay` explica en su docstring que
        excluye a propósito esos sonidos porque subtitularlos «produce un muro
        de texto que hace ilegibles los subtítulos que sí importan, lo cual es
        peor para la accesibilidad que no mostrar nada». Tiene razón, y una
        prueba no debe imponer un criterio de diseño distinto del que el módulo
        argumentó.

        Lo que sí se puede exigir es que cumpla **su propia** promesa: los
        eventos que comunican información que no está en pantalla.
        """
        subtitles = set(re.findall(
            r"Events\.(\w+):", SUBTITLE_FILE.read_text(encoding="utf-8"),
        ))
        # Los que el módulo se compromete a cubrir en su docstring: cambio de
        # fase del jefe, parada, checkpoint y zona de daño.
        informational = {
            "SFX_BOSS_PHASE_CHANGE",
            "SFX_PLAYER_PARRY",
            "CHECKPOINT_REACHED",
            "SFX_HAZARD_ZONE",
        }
        missing = sorted(informational - subtitles)
        assert not missing, (
            f"el módulo promete subtitular estos eventos y no lo hace: {missing}"
        )

    def test_texture_sounds_are_not_subtitled(self) -> None:
        """El otro lado del criterio, que también hay que proteger.

        Subtitular cada paso y cada salto llena la pantalla y entierra los
        avisos que sí salvan una vida. Esta prueba impide «mejorar» la
        accesibilidad empeorándola.
        """
        subtitles = set(re.findall(
            r"Events\.(\w+):", SUBTITLE_FILE.read_text(encoding="utf-8"),
        ))
        texture = {
            "SFX_PLAYER_FOOTSTEP", "SFX_PLAYER_JUMP", "SFX_PLAYER_LAND",
            "SFX_MENU_HOVER",
        }
        noisy = sorted(texture & subtitles)
        assert not noisy, f"sonidos de textura subtitulados: {noisy}"


class TestTheFightMakesNoise:
    """Lo mismo, medido en una partida en vez de leyendo el código."""

    def test_hitting_an_enemy_makes_a_sound(self, _pygame_init) -> None:
        import pygame

        from src.engine.core.events import Events
        from src.framework.entities.enemy_base import EnemyBase

        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        from src.engine.core.app import App
        from src.stages.stage0.stage0 import Stage0

        app = App()
        scene = Stage0(app.context)
        app.scene_manager.push(scene)

        heard: list[str] = []

        def on_hit(**payload: object) -> None:
            heard.append("hit")

        app.event_bus.subscribe(Events.SFX_ENEMY_HIT, on_hit)

        enemy = next(e for e in scene._stage_data.entity_list
                     if isinstance(e, EnemyBase))
        enemy.apply_hit(0.5, (enemy.rect.centerx + 30, enemy.rect.centery))
        app.event_bus.dispatch()

        assert heard, "golpear a un enemigo no emite ningún sonido"

    def test_the_boss_fight_is_not_silent(self, _pygame_init) -> None:
        """Quince segundos de combate real deben producir varios sonidos.

        Se exige variedad, no un sonido cualquiera: un combate que sólo emite
        el impacto sigue faltándole el aviso de fase y los ataques, que es
        justo la información que el jugador necesita oír.
        """
        import pygame

        from src.engine.core.events import Events
        from src.framework.entities.boss_base import BossBase

        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        from src.engine.core.app import App
        from src.stages.boss_venado.boss_venado_scene import BossVenadoScene

        app = App()
        scene = BossVenadoScene(app.context)
        app.scene_manager.push(scene)
        surface = pygame.Surface((800, 600))

        heard: set[str] = set()
        # El bus guarda referencias débiles, así que los manejadores tienen que
        # sobrevivir al bucle: si se dejan como temporales, se recolectan y no
        # llega nada. (El bus lo avisa por el log; me pasó y tardé en leerlo.)
        handlers = []

        def make_handler(sound_name: str):
            def handler(**payload: object) -> None:
                heard.add(sound_name)
            return handler

        for name in (
            "SFX_BOSS_HIT", "SFX_BOSS_PHASE_CHANGE",
            "SFX_BOSSES_VENADO_STOMP", "SFX_BOSSES_VENADO_CHARGE",
            "SFX_BOSSES_VENADO_VINE",
        ):
            handler = make_handler(name)
            handlers.append(handler)
            app.event_bus.subscribe(getattr(Events, name), handler)

        boss = next(e for e in scene._stage_data.entity_list
                    if isinstance(e, BossBase))

        # Se corta en cuanto hay variedad suficiente, en vez de simular los
        # quince segundos enteros.
        #
        # Al arreglar esta prueba (AUD-107) el combate empezó a ocurrir de
        # verdad —antes el jugador no entraba en la arena y el jefe no atacaba—
        # y con ello el coste pasó de un segundo a **23**, con proyectiles,
        # partículas y colisiones reales en cada fotograma. Una prueba correcta
        # que tarda 23 s en un CI que se ejecuta por tandas es una prueba que
        # alguien acaba desactivando.
        #
        # La condición ya se conoce a mitad de camino, así que se sale al
        # cumplirla. Si nunca se cumple, se agotan los 900 fotogramas y la
        # prueba falla como debe.

        # Hay que **entrar en la arena**, no mirarla desde fuera.
        #
        # Esta prueba se quedó en dos sonidos al sustituir el jefe de
        # referencia por la entrega del estudiante, y no era un fallo suyo: su
        # Venado sólo pelea en su terreno sagrado —se activa cuando el jugador
        # cruza la boca de la arena— y está escrito así a propósito en su
        # código. El jugador aparecía al principio del mapa y no se movía, así
        # que el jefe recibía golpes de lejos y no contestaba nunca.
        #
        # Un combate en el que el jugador no se acerca no es un combate. La
        # prueba decía «quince segundos de combate real» y estaba midiendo
        # quince segundos de acoso a distancia.
        if getattr(scene, "_player", None) is not None:
            scene._player.rect.centerx = boss.rect.centerx + 60
            scene._player.position.x = float(scene._player.rect.x)

        for frame in range(900):
            if frame % 60 == 0:
                boss.apply_hit(0.5, (boss.rect.centerx + 40, boss.rect.centery))
            app.scene_manager.update(1 / 60)
            app.scene_manager.current.draw(surface)
            app.event_bus.dispatch()
            if len(heard) >= 3:
                break

        assert len(heard) >= 3, (
            f"el combate de jefe sólo produjo {sorted(heard)}; debería sonar "
            f"al golpear, al cambiar de fase y al atacar"
        )


@pytest.mark.parametrize("sound", sorted(AWAITING_THEIR_BOSS))
def test_deferred_boss_sounds_have_their_asset_ready(sound: str) -> None:
    """El día que un estudiante construya el jefe, el sonido tiene que estar.

    Se comprueba ahora y no entonces: descubrir que falta el .wav mientras se
    programa un jefe es una interrupción evitable.
    """
    text = SFX_MAP_FILE.read_text(encoding="utf-8")
    match = re.search(rf'Events\.{sound}:\s*"([\w_]+)"', text)
    assert match, f"{sound} ya no está cableado a ningún archivo"
    available = {p.stem for p in (ROOT / "assets" / "sfx").rglob("*.wav")}
    assert match.group(1) in available, (
        f"{sound} apunta a '{match.group(1)}', que no existe en assets/sfx"
    )


class TestElJuegoSobreviveSinTarjetaDeSonido:
    """AUD-089 — un aula sin dispositivo de audio tumbaba el juego.

    `play_music` envolvía sus llamadas en `try/except pygame.error`, pero
    `stop_music`, `pause_music`, `resume_music`, `set_music_volume` y
    `toggle_mute` no. Si `pygame.mixer.init()` falla —máquina sin dispositivo,
    sesión remota, contenedor, laboratorio con el sonido deshabilitado—
    cualquier transición de escena que pare la música lanzaba
    ``pygame.error: mixer not initialized`` y la partida se perdía.

    No es un problema de sonido, es de disponibilidad: el jugador pierde el
    juego entero por no tener altavoces.
    """

    @pytest.fixture
    def sin_mezclador(self):
        import pygame

        estaba = pygame.mixer.get_init() is not None
        if estaba:
            pygame.mixer.quit()
        yield
        if estaba:
            try:
                pygame.mixer.init()
            except pygame.error:
                pass

    def test_las_operaciones_de_musica_no_lanzan(self, sin_mezclador):
        import pygame

        from src.engine.audio.audio_manager import AudioManager

        assert pygame.mixer.get_init() is None, "el escenario no se preparó"
        audio = AudioManager()
        # Ninguna de éstas puede lanzar: todas ocurren en transiciones normales.
        audio.play_music("assets/music/bgm_title.ogg")
        audio.stop_music()
        audio.pause_music()
        audio.resume_music()
        audio.set_music_volume(0.5)
        audio.set_sfx_volume(0.5)
        audio.toggle_mute()
        audio.toggle_mute()
        audio.play_sfx("sfx_ui_confirm")
        audio.stop_ambient()

    def test_una_escena_completa_entra_y_sale_sin_mezclador(self, sin_mezclador):
        """La prueba que importa: el ciclo real de una escena con música."""
        import pygame

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.splash_scene import SplashScene

        pygame.display.set_mode((800, 600))
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = SplashScene(ctx)
        superficie = pygame.Surface((800, 600))
        escena.awake()
        escena.start()
        escena.on_enter()
        for _ in range(5):
            escena.update(1 / 60)
            escena.draw(superficie)
        escena.on_exit()          # aquí reventaba
