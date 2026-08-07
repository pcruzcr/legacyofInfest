"""
Auditoría de ingeniería — AUD-157 a AUD-160.

Cuatro defectos de familias distintas, todos reproducidos antes de tocar nada.

1. **El estado del jugador se escribía dentro del árbol de instalación.**
   `user_data_dir()` existe desde AUD-032 y su propio docstring dice por qué no
   se debe hacer eso. La corrección se aplicó a las preferencias y a los logros
   y no a las partidas, al bestiario, al speedrun ni al progreso académico. En
   el ejecutable de PyInstaller instalado en Program Files, guardar falla.

2. **Los números de daño se desvanecían en bloque.** La superficie del texto
   está cacheada y compartida, y se le escribía el alfa encima. El último en
   dibujarse imponía su transparencia a todos.

3. **Siete ficheros `.ogg` eran WAV.** SDL se fía de la extensión, así que no
   se podían reproducir. Cuatro no tenían gemelo `.wav`, de modo que esos
   escenarios se jugaban **en silencio** con sólo un aviso en el registro.

4. **La escala de texto no llegaba a la pantalla de opciones**, que es donde se
   elige. Y al forzarla, la maqueta —toda en píxeles literales— se salía de la
   pantalla.
"""
from __future__ import annotations

import pygame
import pytest


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestElEstadoDelJugadorNoViveEnLaInstalacion:
    """AUD-157 — lo que se escribe al jugar va al directorio del usuario."""

    def _rutas(self) -> dict[str, object]:
        from src.engine.core.save_manager import SaveManager
        from src.framework.academic.sesion import DIRECTORIO_PROGRESO
        from src.framework.entities.bestiary import _DEFAULT_BESTIARY_PATH
        from src.framework.stage.speedrun_mode import _DEFAULT_SAVE_PATH

        return {
            "partidas": SaveManager.SAVES_DIR,
            "bestiario": _DEFAULT_BESTIARY_PATH,
            "speedrun": _DEFAULT_SAVE_PATH,
            "académico": DIRECTORIO_PROGRESO,
        }

    @pytest.mark.parametrize("cual", ["partidas", "bestiario", "speedrun",
                                      "académico"])
    def test_no_escribe_dentro_del_proyecto(self, cual) -> None:
        from src.engine.core import settings
        from src.engine.core.user_settings import user_data_dir

        ruta = self._rutas()[cual]
        assert user_data_dir() in ruta.parents or ruta == user_data_dir(), (
            f"«{cual}» se guarda en {ruta}, fuera del directorio del usuario"
        )
        assert settings.PROJECT_ROOT not in ruta.parents, (
            f"«{cual}» escribe dentro del árbol de instalación ({ruta}): en "
            f"una instalación de sólo lectura eso falla"
        )

    def test_las_partidas_viejas_se_migran(self, tmp_path) -> None:
        """Nadie puede perder una partida por mover el directorio."""
        import orjson

        from src.engine.core import save_manager as sm_mod
        from src.engine.core.save_manager import SaveManager

        viejo = tmp_path / "instalacion" / "saves"
        viejo.mkdir(parents=True)
        (viejo / "slot_1.json").write_bytes(orjson.dumps(
            {"slot_id": 1, "stage_id": "stage0", "stage_index": 0}))

        nuevo = tmp_path / "usuario" / "saves"
        heredado_original = sm_mod._SAVES_HEREDADO
        dir_original = SaveManager.SAVES_DIR
        try:
            sm_mod._SAVES_HEREDADO = viejo
            SaveManager.SAVES_DIR = nuevo
            SaveManager()
            assert (nuevo / "slot_1.json").exists(), (
                "la partida del sitio viejo no se copió al nuevo"
            )
            assert (viejo / "slot_1.json").exists(), (
                "se borró el original: volver a una versión anterior dejaría "
                "al jugador sin partida"
            )
        finally:
            sm_mod._SAVES_HEREDADO = heredado_original
            SaveManager.SAVES_DIR = dir_original


class TestLosNumerosDeDanoNoSePisanElAlfa:
    """AUD-158 — el desvanecimiento en bloque."""

    def test_la_superficie_cacheada_no_cambia_de_alfa(self, _video) -> None:
        from src.framework.vfx.damage_numbers import DamageNumber

        vivo = DamageNumber(100, 100, "5")
        muriendo = DamageNumber(200, 200, "5")
        assert vivo._surf is muriendo._surf, (
            "ya no se comparte la superficie; esta prueba dejó de tener sentido"
        )
        muriendo.life = 0.1

        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        vivo.draw(lienzo, pygame.Vector2())
        antes = vivo._surf.get_alpha()
        muriendo.draw(lienzo, pygame.Vector2())
        assert vivo._surf.get_alpha() == antes, (
            "dibujar un número casi apagado cambió el alfa de la superficie "
            "compartida: todos los números iguales se apagan a la vez"
        )

    def test_cada_numero_se_dibuja_con_su_transparencia(self, _video) -> None:
        from src.framework.vfx.damage_numbers import DamageNumber

        def opacidad(vida: float) -> int:
            n = DamageNumber(100, 100, "7")
            n.life = vida
            lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
            n.draw(lienzo, pygame.Vector2())
            return int(pygame.surfarray.pixels_alpha(lienzo).max())

        assert opacidad(1.0) > opacidad(0.1)

    def test_un_critico_tambien_se_dibuja(self, _video) -> None:
        """El camino del crítico escala la superficie; se comprueba aparte."""
        from src.framework.vfx.damage_numbers import DamageNumber

        n = DamageNumber(50, 50, "9", is_critical=True)
        n.life = 0.5
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        n.draw(lienzo, pygame.Vector2())
        assert pygame.surfarray.pixels_alpha(lienzo).max() > 0

    def test_el_cache_de_texto_tiene_tope(self, _video) -> None:
        """Es un atributo de clase: vive lo que el proceso."""
        from src.framework.vfx.damage_numbers import DamageNumber

        DamageNumber.clear_caches()
        for i in range(DamageNumber._MAX_CACHE * 2):
            DamageNumber(0, 0, f"{i}.{i}")
        assert len(DamageNumber._render_cache) <= DamageNumber._MAX_CACHE
        DamageNumber.clear_caches()


class TestLaMusicaSuena:
    """AUD-159 — siete `.ogg` que eran WAV."""

    def _musica(self):
        from src.engine.core import settings

        return sorted((settings.ASSETS_DIR / "music").iterdir())

    def test_ninguna_pista_miente_sobre_su_formato_en_los_caminos_vivos(self) -> None:
        """Los ficheros que el juego puede llegar a pedir tienen que cargar.

        Quedan tres `.ogg` mal etiquetados a propósito: tienen al lado un
        `.wav` que el motor prefiere, así que son inalcanzables. El validador
        de assets los señala para que el profesor decida si son los buenos —
        duran 60 s contra los 8-12 s del marcador de posición— pero cambiarlos
        es una decisión de contenido, no de ingeniería.
        """
        import wave

        vivos = [p for p in self._musica()
                 if p.suffix == ".wav" or not p.with_suffix(".wav").exists()]
        malos = []
        for p in vivos:
            esperada = b"RIFF" if p.suffix == ".wav" else b"OggS"
            if p.read_bytes()[:4] != esperada:
                malos.append(p.name)
        assert malos == [], (
            f"estas pistas se pueden pedir y no se pueden reproducir: {malos}"
        )
        # y que al menos una sea legible de verdad
        with wave.open(str(vivos[0])) as w:
            assert w.getnframes() > 0

    def test_toda_pista_que_pide_un_escenario_existe(self) -> None:
        import re

        from src.engine.core import settings

        pedidas = set()
        for tmx in (settings.ASSETS_DIR / "maps").rglob("*.tmx"):
            texto = tmx.read_text(encoding="utf-8", errors="replace")
            pedidas |= set(re.findall(r'bgm_track" value="([^"]+)"', texto))

        faltan = [t for t in sorted(pedidas)
                  if not (settings.ASSETS_DIR / "music" / f"{t}.wav").exists()
                  and not (settings.ASSETS_DIR / "music" / f"{t}.ogg").exists()]
        assert faltan == [], f"escenarios que pedirían música inexistente: {faltan}"

    def test_el_validador_detecta_una_extension_mentirosa(self, tmp_path) -> None:
        """La prueba de la prueba: que el chequeo pueda fallar."""
        import sys

        from src.engine.core import settings

        sys.path.insert(0, str(settings.PROJECT_ROOT / "scripts"))
        import validate_assets

        falso = tmp_path / "mentira.ogg"
        falso.write_bytes(b"RIFF" + b"\0" * 100)
        antes = len(validate_assets.WARNINGS)
        validate_assets.check_audio_format(falso)
        assert len(validate_assets.WARNINGS) == antes + 1
        del validate_assets.WARNINGS[antes:]


class TestLaEscalaDeTextoLlegaAOpciones:
    """AUD-160 — la opción no se aplicaba en la pantalla donde se elige."""

    @pytest.fixture
    def contexto(self, _video):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager

        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        return ctx

    @pytest.fixture(autouse=True)
    def _restaurar(self):
        from src.engine.core import user_settings
        from src.engine.ui.theme import clear_font_cache

        yield
        user_settings.get().text_scale = 1.0
        clear_font_cache()

    def _pantalla(self, contexto, escala):
        from src.engine.core import user_settings
        from src.engine.scenes.options_scene import OptionsScene
        from src.engine.ui.theme import clear_font_cache

        user_settings.get().text_scale = escala
        clear_font_cache()
        escena = OptionsScene(contexto)
        contexto.scene_manager.push(escena)
        return escena

    def test_el_texto_crece_con_la_escala(self, contexto) -> None:
        pequeno = self._pantalla(contexto, 1.0)._btn_back.font.size("BACK")[1]
        grande = self._pantalla(contexto, 2.0)._btn_back.font.size("BACK")[1]
        assert grande > pequeno, (
            f"la escala no llega a pygame_gui: {pequeno} px → {grande} px"
        )

    @pytest.mark.parametrize("escala", [1.0, 1.25, 1.5, 2.0])
    def test_nada_se_sale_de_la_pantalla(self, contexto, escala) -> None:
        from src.engine.core import settings

        escena = self._pantalla(contexto, escala)
        # `_btn_contorno` entró en la lista con AUD-304, que es justo lo que
        # esta prueba cazó: la opción nueva empujaba el menú 20 px fuera de la
        # pantalla. Vigilarlo evita que la próxima haga lo mismo sin avisar.
        for nombre in ("_btn_back", "_btn_keybindings", "_btn_mantener",
                       "_btn_contorno", "_dropdown_texto", "_slider_music"):
            r = getattr(escena, nombre).get_abs_rect()
            assert r.bottom <= settings.INTERNAL_HEIGHT, (
                f"a {escala}× «{nombre}» acaba en y={r.bottom}, fuera de la "
                f"pantalla ({settings.INTERNAL_HEIGHT})"
            )
            assert r.right <= settings.INTERNAL_WIDTH, (
                f"a {escala}× «{nombre}» acaba en x={r.right}, fuera de la "
                f"pantalla ({settings.INTERNAL_WIDTH})"
            )

    @pytest.mark.parametrize("escala", [1.0, 2.0])
    def test_pygame_gui_no_avisa_de_texto_recortado(self, contexto, escala) -> None:
        """`UILabel` avisa cuando el texto no cabe en su rectángulo. Con la
        maqueta en píxeles literales avisaba once veces a 2×."""
        import warnings

        with warnings.catch_warnings(record=True) as capturados:
            warnings.simplefilter("always")
            self._pantalla(contexto, escala)
        recortes = [str(w.message) for w in capturados
                    if "too small for text" in str(w.message)]
        assert recortes == [], f"a {escala}× se recorta: {recortes}"

    def test_los_botones_siguen_respondiendo_con_el_texto_grande(
            self, contexto) -> None:
        """Cambiar la maqueta no puede desconectar lo que AUD-154 arregló."""
        import pygame_gui

        escena = self._pantalla(contexto, 2.0)
        escena.process_events([pygame.event.Event(
            pygame_gui.UI_BUTTON_PRESSED, {"ui_element": escena._btn_back})])
        assert type(contexto.scene_manager.current).__name__ == "TitleScene"
