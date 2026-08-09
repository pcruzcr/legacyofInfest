"""La partición de `DrawingSystem` — AUD-352.

`drawing_system.py` era el pintor del mundo, el de la interfaz y el de los
gizmos de depuración (AUD-285). La familia de F1 —cajas, flechas de velocidad
y conos de visión— salió a un mixin propio, `GizmosDeDepuracion` en
`stage/gizmos.py`, y la disciplina es la misma que la de `StageScene`
(AUD-152): el texto se movió verbatim y el juego no puede notarlo.

Lo que estas pruebas defienden
------------------------------
1. **Que los métodos sigan llegando.** No que existan: que el MRO de
   `DrawingSystem` los resuelva en el mixin, no en una copia suelta.
2. **Que lo que se quedó siga estando en la clase.** El corte fue sólo la
   familia de F1; el pintor (`draw`, `draw_ui`, `_draw_entities`, pausa…)
   sigue definido en `DrawingSystem` y no se movió de más.
3. **Que sigan corriendo de verdad.** `draw_ui` con `ctx.debug` activo pinta
   las cajas, la flecha y el cono atravesando los métodos movidos.
4. **Que los ficheros no vuelvan a crecer.** Un presupuesto de líneas es la
   única forma de que la partición dure más que este turno.
5. **Que nadie confunda el mixin con un componente.** No se instancia solo;
   el docstring lo dice.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: El mixin y lo que se llevó.
PARTES = {
    "gizmos": (
        "GizmosDeDepuracion",
        ("_draw_debug", "_dibujar_velocidades", "_dibujar_conos",
         "_GIZMO_SEGUNDOS"),
    ),
}

TODOS_LOS_MIEMBROS = [
    (modulo, clase, miembro)
    for modulo, (clase, miembros) in PARTES.items()
    for miembro in miembros
]


class TestLosMetodosSiguenLlegando:
    """El fallo característico del proyecto, aplicado a una refactorización.

    Que un método exista en algún sitio no significa que el motor lo alcance.
    Aquí se pregunta por el camino real: qué resuelve el MRO de
    `DrawingSystem`.
    """

    @pytest.mark.parametrize("modulo,clase,miembro", TODOS_LOS_MIEMBROS)
    def test_el_mro_resuelve_al_mixin(self, modulo, clase, miembro) -> None:
        import importlib

        from src.framework.stage.drawing_system import DrawingSystem

        mod = importlib.import_module(f"src.framework.stage.{modulo}")
        esperada = getattr(mod, clase)
        resuelto = getattr(DrawingSystem, miembro)
        assert resuelto is getattr(esperada, miembro), (
            f"`{miembro}` ya no se resuelve en {clase}: el texto se movió y el "
            f"motor acabó en otra implementación"
        )

    def test_el_pintor_no_se_fue_con_los_gizmos(self) -> None:
        """El corte fue la familia de F1; lo demás quedó en la clase.

        `__qualname__` dice dónde está definido el método: si algo del pintor
        se escapa al mixin por accidente, esta prueba lo caza.
        """
        from src.framework.stage.drawing_system import DrawingSystem

        for nombre in ("draw", "draw_ui", "_draw_entities",
                       "_draw_inundaciones", "_draw_pause_menu",
                       "_escala_de_profundidad"):
            assert getattr(DrawingSystem, nombre).__qualname__.split(".")[0] == (
                "DrawingSystem"
            ), f"`{nombre}` ya no está definido en DrawingSystem"


class TestSiguenCorriendoDeVerdad:
    """Que el MRO apunte bien no basta: hay que pasar por la ruta real.

    `draw_ui` con `ctx.debug` encendido es el único camino de producción que
    llega a los gizmos; si el cableado se rompiera, aquí no pinta nada.
    """

    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))

    def test_el_camino_de_debug_usa_los_metodos_movidos(self) -> None:
        from src.framework.ecs.components import ConoDeVision, Transform
        from src.framework.ecs.world import World
        from src.framework.stage.drawing_system import DrawContext, DrawingSystem

        class Cuerpo:
            def __init__(self, x, y, vx=0.0, vy=0.0) -> None:
                self.rect = pygame.Rect(x, y, 16, 16)
                self.position = pygame.Vector2(x, y)
                self.velocity = pygame.Vector2(vx, vy)
                self.hurtbox = pygame.Rect(x + 2, y + 2, 12, 12)
                self.hitbox = pygame.Rect(x - 1, y - 1, 18, 18)

        class CamaraFalsa:
            offset = pygame.Vector2(0, 0)

        class StageFalso:
            def __init__(self, entidades) -> None:
                self.entity_list = list(entidades)

        mundo = World()
        cono = ConoDeVision(mira=pygame.Vector2(1.0, 0.0), alcance=120.0,
                            semiangulo=30.0)
        mundo.crear(Transform(rect=pygame.Rect(300, 300, 16, 16)), cono)

        lienzo = pygame.Surface((800, 600))
        lienzo.fill((0, 0, 0))
        ctx = DrawContext(
            surface=lienzo,
            stage=StageFalso([Cuerpo(100, 100, vx=200.0)]),
            camera=CamaraFalsa(),
            debug=True,
            mundo=mundo,
        )
        DrawingSystem().draw_ui(ctx)
        pixeles = set(pygame.surfarray.array2d(lienzo).ravel().tolist()) - {0}
        assert pixeles, "con F1 y la escena parada, el debug no pintó nada"


class TestElArchivoNoVuelveACrecer:
    #: 850 y no 737 —lo que mide hoy— porque un presupuesto pegado al valor
    #: actual convierte cualquier arreglo de dos líneas en una discusión sobre
    #: el límite. El margen es para arreglos; para una fase nueva, se parte
    #: otra vez.
    PRESUPUESTO = 850

    def test_drawing_system_cabe_en_el_presupuesto(self) -> None:
        ruta = RAIZ / "src" / "framework" / "stage" / "drawing_system.py"
        lineas = len(ruta.read_text(encoding="utf-8").splitlines())
        assert lineas <= self.PRESUPUESTO, (
            f"drawing_system.py tiene {lineas} líneas y el presupuesto es "
            f"{self.PRESUPUESTO}: toca extraer otro grupo cohesivo, no subir "
            f"el número"
        )

    @pytest.mark.parametrize("modulo", sorted(PARTES))
    def test_cada_parte_es_legible_de_una_sentada(self, modulo) -> None:
        ruta = RAIZ / "src" / "framework" / "stage" / f"{modulo}.py"
        assert len(ruta.read_text(encoding="utf-8").splitlines()) <= 400


class TestSeDiceLoQueSonYLoQueNo:
    """Un mixin que parece un componente reutilizable acaba reutilizado.

    Este no lo es: dibuja sobre el lienzo del pintor y lee `_debug_font` del
    sistema. Que el docstring lo diga es lo que evita que alguien lo saque de
    aquí.
    """

    def test_el_mixin_declara_lo_que_espera_del_sistema(self) -> None:
        import importlib

        mod = importlib.import_module("src.framework.stage.gizmos")
        doc = inspect.getdoc(mod.GizmosDeDepuracion) or ""
        assert "Espera del sistema" in doc, (
            "GizmosDeDepuracion no dice de qué depende: alguien lo usará suelto"
        )
