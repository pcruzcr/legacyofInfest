"""
La partición de `StageScene` — AUD-152.

`stage_scene.py` llegó a 1.884 líneas. Partirlo es fácil; partirlo **sin
cambiar el juego** es lo que hay que demostrar, y el proyecto ya tiene catorce
casos registrados de código correcto que dejó de alcanzarse. Mover doscientas
líneas a otro archivo es exactamente la maniobra que produce el número quince.

Lo que estas pruebas defienden
-------------------------------
1. **Que los métodos sigan llegando.** No que existan: que el MRO los resuelva
   en el mixin y no en `BaseScene`.
2. **Que sigan corriendo de verdad.** Una escena real se monta y se le mira la
   luz, el bloom y las partículas, que es lo que producían los métodos movidos.
3. **Que el archivo no vuelva a crecer.** Un presupuesto de líneas es la única
   forma de que la partición dure más que este turno.
4. **Que nadie confunda el mixin con una arquitectura.** No se instancian
   solos; dependen de los atributos de la escena y el docstring lo dice.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: Los tres mixins y lo que cada uno se llevó.
PARTES = {
    "ambiente": (
        "MezclaDeAmbiente",
        ("_setup_lighting", "_setup_post_processing", "_setup_ambient_particles",
         "_clima_efectivo", "_configurar_vfx_opcionales",
         "_publicar_los_rayos_de_luz", "_capture_enemy_trails"),
    ),
    # AUD-362 — el ciclo día/noche y la estación salen de `ambiente`. Aquel
    # módulo resolvía la precedencia del TMX (mapa > zona > motor) y además
    # componía y aplicaba la luz de la hora; lo segundo dejó de ser trabajo
    # suyo cuando `WorldSimulation` pasó a componerlo, y el fichero había
    # llegado a su presupuesto.
    "simulacion": (
        "SimulacionDeEscenario",
        ("_setup_season", "_setup_day_night", "_aplicar_hora",
         "_aplicar_agarre"),
    ),
    "senales": (
        "SenalesDeEscenario",
        ("_subscribe_event_handlers", "_unsubscribe_all_handlers"),
    ),
    # AUD-595 — la economía (el botín que deja cada enemigo) sale de
    # `senales`: vivía ahí por historia, no por concepto, y el fichero había
    # vuelto a rozar su presupuesto.
    "economia": (
        "EconomiaDeEscenario",
        ("_soltar_botin",),
    ),
    # AUD-290 — la mitad sonora sale de `senales`. El docstring de aquel módulo
    # ya decía que eran «dos familias»; compartían fichero hasta que el fichero
    # llegó a su presupuesto.
    "sonido": (
        "SonidoDeEscenario",
        ("_subscribe_sfx_handlers", "_make_sfx_handler",
         "_play_sfx_named", "_play_sfx_spatial"),
    ),
    "diagnostico": (
        "DiagnosticoDeEscenario",
        ("medidas_de_depuracion", "_retirar_entidad_rota"),
    ),
    "cinematicas": (
        "CinematicasDeEscenario",
        ("_actualizar_escenas", "_montar_director_de_escenas",
         "_cargar_los_arboles_de_dialogo"),
    ),
    # AUD-299 — las dos que bajaron el fichero a su presupuesto.
    "arco": (
        "ArcoDelJugador",
        ("_raton_esta_apuntando", "_direccion_de_tiro", "_actualizar_arco",
         "_dibujar_trayectoria_del_arco"),
    ),
    "mundo_ecs": (
        "MundoDelEscenario",
        ("_construir_planificador", "_poblar_mundo_ecs", "_actualizar_agarres"),
    ),
    "fantasma": (
        "FantasmaDeCarrera",
        ("_ruta_del_fantasma", "_preparar_fantasma",
         "_guardar_fantasma_si_es_mejor", "_dibujar_fantasma"),
    ),
    # AUD-343 — el orden de pintado partido en dos (mundo/UI) para que la
    # ruta de GPU pueda intercalar la tarjeta entre ambos. Empezó en el
    # presupuesto agotado de `stage_scene.py` y el split ya no cabía allí.
    "dibujo": (
        "DibujoDeEscenario",
        ("draw", "dibujar_mundo", "dibujar_ui", "_contexto_de_dibujo",
         "light_surface"),
    ),
    # AUD-351 — la familia `_update_*` de periféricos (audio, HUD, efectos,
    # luz, logros, temporizadores, minimapa y estelas) salió al agotarse el
    # presupuesto. La simulación (`_update_gameplay`) se quedó en la escena.
    "actualizaciones": (
        "ActualizacionesDeEscenario",
        ("_update_audio", "_update_hud_ui", "_update_vfx",
         "_update_lighting", "_update_tracking", "_update_timers",
         "_update_minimap", "_update_trail"),
    ),
}

TODOS_LOS_METODOS = [
    (modulo, clase, metodo)
    for modulo, (clase, metodos) in PARTES.items()
    for metodo in metodos
]


class TestLosMetodosSiguenLlegando:
    """El fallo característico del proyecto, aplicado a una refactorización.

    Que un método exista en algún sitio no significa que el motor lo alcance.
    Aquí se pregunta por el camino real: qué resuelve el MRO de `StageScene`.
    """

    @pytest.mark.parametrize("modulo,clase,metodo", TODOS_LOS_METODOS)
    def test_el_mro_resuelve_al_mixin(self, modulo, clase, metodo) -> None:
        import importlib

        from src.framework.scenes.stage_scene import StageScene

        mod = importlib.import_module(f"src.framework.scenes.stage_parts.{modulo}")
        esperada = getattr(mod, clase)
        resuelto = getattr(StageScene, metodo)
        assert resuelto is getattr(esperada, metodo), (
            f"`{metodo}` ya no se resuelve en {clase}: el texto se movió y el "
            f"motor acabó en otra implementación"
        )

    def test_los_mixins_van_antes_que_la_escena_base(self) -> None:
        """Si `BaseScene` fuera primero, cualquier nombre compartido lo ganaría
        ella y el mixin quedaría escrito y muerto — que es justo lo que no
        pasaba cuando el método estaba en la propia clase."""
        from src.engine.scene.base_scene import BaseScene
        from src.framework.scenes.stage_scene import StageScene

        orden = StageScene.__mro__
        assert orden.index(BaseScene) > max(
            orden.index(getattr(
                __import__(f"src.framework.scenes.stage_parts.{m}",
                           fromlist=[c]), c))
            for m, (c, _) in PARTES.items()
        )

    def test_una_subclase_puede_seguir_sobreescribiendo(self) -> None:
        """Las entregas de los estudiantes sobreescriben `_setup_lighting`.

        Con un colaborador en vez de un mixin, esas subclases habrían dejado de
        tener efecto en silencio.
        """
        from src.framework.scenes.stage_scene import StageScene

        marca = []

        class Hija(StageScene):
            def _setup_lighting(self) -> None:
                marca.append("mia")

        Hija._setup_lighting(object.__new__(Hija))
        assert marca == ["mia"]


class TestSiguenCorriendoDeVerdad:
    """Que el MRO apunte bien no basta: hay que montar una escena y mirar."""

    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    @pytest.fixture
    def escena(self):
        """Stage 0 montado con el mismo contexto que usa el arnés de humo.

        Se monta la escena de verdad y no un doble: lo que hay que comprobar es
        que `on_enter` sigue llamando a los métodos movidos, y un doble sólo
        comprobaría que los llamo yo.
        """
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)

        escena = Stage0(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        yield escena
        escena.on_exit()

    def test_la_luz_del_escenario_quedo_puesta(self, escena) -> None:
        assert 0.0 < escena._lighting.ambient_brightness <= 1.0

    def test_el_bloom_del_escenario_quedo_puesto(self, escena) -> None:
        assert escena._post_processing._bloom_base > 0.0, (
            "`_setup_post_processing` no llegó a correr: el escenario se vería "
            "plano y nadie lo notaría hasta jugarlo"
        )

    def test_las_particulas_de_ambiente_tienen_ritmo(self, escena) -> None:
        assert escena._ambient_particles.rate > 0.0

    def test_hay_manejadores_de_sonido_suscritos(self, escena) -> None:
        assert len(escena._sfx_handlers) > 30, (
            f"sólo {len(escena._sfx_handlers)} sonidos suscritos: el nivel se "
            f"jugaría en silencio"
        )

    def test_darse_de_baja_los_quita_todos(self, escena) -> None:
        escena._unsubscribe_all_handlers()
        assert not escena._sfx_handlers and not escena._vfx_handlers


class TestElArchivoNoVuelveACrecer:
    #: 1.500 y no 1.405 —lo que mide hoy— porque un presupuesto pegado al valor
    #: actual convierte cualquier arreglo de dos líneas en una discusión sobre
    #: el límite. El margen es para arreglos; para una fase nueva, se parte otra
    #: vez.
    PRESUPUESTO = 1500

    def test_stage_scene_cabe_en_el_presupuesto(self) -> None:
        ruta = RAIZ / "src" / "framework" / "scenes" / "stage_scene.py"
        lineas = len(ruta.read_text(encoding="utf-8").splitlines())
        assert lineas <= self.PRESUPUESTO, (
            f"stage_scene.py tiene {lineas} líneas y el presupuesto es "
            f"{self.PRESUPUESTO}: toca extraer otro grupo cohesivo a "
            f"`stage_parts/`, no subir el número"
        )

    @pytest.mark.parametrize("modulo", sorted(PARTES))
    def test_cada_parte_es_legible_de_una_sentada(self, modulo) -> None:
        ruta = (RAIZ / "src" / "framework" / "scenes" / "stage_parts"
                / f"{modulo}.py")
        assert len(ruta.read_text(encoding="utf-8").splitlines()) <= 400


class TestSeDiceLoQueSonYLoQueNo:
    """Un mixin que parece un componente reutilizable acaba reutilizado.

    Estos no lo son: leen `self._stage_data`, `self._camera`, `self.context`.
    Que el docstring lo diga es lo que evita que alguien los saque de aquí.
    """

    @pytest.mark.parametrize("modulo,clase", [(m, c) for m, (c, _) in PARTES.items()])
    def test_cada_mixin_declara_lo_que_espera_de_la_escena(self, modulo, clase) -> None:
        import importlib

        mod = importlib.import_module(f"src.framework.scenes.stage_parts.{modulo}")
        doc = inspect.getdoc(getattr(mod, clase)) or ""
        assert "Espera de la escena" in doc, (
            f"{clase} no dice de qué atributos depende: alguien lo usará suelto"
        )

    def test_el_paquete_explica_por_que_son_mixins(self) -> None:
        from src.framework.scenes import stage_parts

        doc = stage_parts.__doc__ or ""
        assert "mixin" in doc.lower()
        assert "lectura" in doc.lower(), (
            "sin decir que la separación es por legibilidad y no por "
            "dependencia, esto se lee como una arquitectura que no es"
        )
