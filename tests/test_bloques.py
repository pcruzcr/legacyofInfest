"""
Bloques que se empujan y bloques que se rompen — AUD-140.

Las dos últimas filas del catálogo de mecánicas. Lo que aportan al diseño:

* **Empujable**: es el único objeto del motor que el jugador puede *colocar*.
  Con eso se hacen puentes sobre pinchos, escalones para llegar a una cornisa
  y parapetos contra proyectiles. Convierte una sala en un problema.
* **Destructible**: convierte una pared en una pregunta. Un muro que cede a
  golpes premia probar cosas, que es lo contrario de un muro normal.

Los tres fallos que estas pruebas vigilan
------------------------------------------
1. **El redondeo.** El `rect` va en enteros y la velocidad en float: a 45 px/s
   y 60 fps son 0,75 px por fotograma, que redondeados a 1 harían al bloque ir
   a 60 px/s. Es el mismo defecto de la inundación (AUD-135), y aquí se nota
   más porque el jugador está calculando a ojo dónde va a quedar el bloque.
2. **Empujar de lado, no desde arriba.** Sin esa condición, quedarse quieto
   encima de un bloque lo iría desplazando: el suelo se movería solo.
3. **Volver a su sitio al morir.** Un bloque empujado a un foso deja el nivel
   sin solución, y el jugador no tiene cómo saber que ya no se puede pasar.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.bloques import (
    BloqueDestructible,
    BloqueEmpujable,
    SistemaDeBloques,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)


def _suelo(y: int = 200, ancho: int = 400) -> list[pygame.Rect]:
    return [pygame.Rect(0, y, ancho, 16)]


class TestEmpujar:
    def _montaje(self, x_bloque: int = 100):
        bloque = BloqueEmpujable(rect=pygame.Rect(x_bloque, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(x_bloque - 20, 170, 20, 30)
        return sistema, bloque, jugador

    def test_el_bloque_se_mueve_al_empujarlo(self) -> None:
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        assert bloque.rect.x > antes

    def test_a_la_velocidad_declarada_y_no_a_la_del_redondeo(self) -> None:
        """45 px/s a 60 fps son 0,75 px por fotograma.

        Redondeando cada fotograma a 1 px, el bloque iría a 60 px/s: un tercio
        más rápido de lo que dice su propiedad, y el diseñador que midió el
        salto sobre el papel se encuentra otra cosa.
        """
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
            # El jugador camina pegado al bloque, que es lo que hace la
            # resolución de colisión cuando se anda contra un sólido.
            jugador.right = bloque.rect.left
        recorrido = bloque.rect.x - antes
        assert recorrido == pytest.approx(45, abs=2), (
            f"recorrió {recorrido} px en un segundo a 45 px/s"
        )

    def test_sin_direccion_no_se_mueve(self) -> None:
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        sistema.empujar(jugador, 0, 1 / 60, _suelo())
        assert bloque.rect.x == antes

    def test_desde_arriba_no_se_empuja(self) -> None:
        """Si pisarlo lo arrastrara, el suelo se movería solo."""
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        encima = pygame.Rect(105, 138, 20, 30)      # justo sobre el bloque
        antes = bloque.rect.x
        for _ in range(30):
            sistema.empujar(encima, 1, 1 / 60, _suelo())
        assert bloque.rect.x == antes

    def test_no_se_empuja_a_traves_de_una_pared(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(80, 170, 20, 30)
        pared = pygame.Rect(140, 100, 16, 120)
        for _ in range(120):
            sistema.empujar(jugador, 1, 1 / 60, [*_suelo(), pared])
        assert bloque.rect.right <= pared.left

    def test_un_bloque_no_empuja_a_otro_a_traves(self) -> None:
        uno = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        dos = BloqueEmpujable(rect=pygame.Rect(140, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[uno, dos])
        jugador = pygame.Rect(80, 170, 20, 30)
        for _ in range(120):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        assert not uno.rect.colliderect(dos.rect)

    def test_se_empuja_hacia_la_izquierda(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(132, 170, 20, 30)
        for _ in range(60):
            sistema.empujar(jugador, -1, 1 / 60, _suelo())
        assert bloque.rect.x < 100


class TestCaer:
    def test_el_bloque_cae_hasta_el_suelo(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        for _ in range(180):
            sistema.caer(1 / 60, _suelo())
        assert bloque.rect.bottom == 200

    def test_no_atraviesa_el_suelo_con_un_dt_grande(self) -> None:
        """Un `dt` grande —una carga, un tirón— no puede meter el bloque
        dentro del suelo: la caída se resuelve por pasos de un píxel."""
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        sistema.caer(2.0, _suelo())
        assert bloque.rect.bottom <= 200

    def test_sin_gravedad_se_queda_flotando(self) -> None:
        """Para escenarios cenitales, donde «abajo» no significa nada."""
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32),
                                 con_gravedad=False)
        sistema = SistemaDeBloques(empujables=[bloque])
        for _ in range(60):
            sistema.caer(1 / 60, _suelo())
        assert bloque.rect.y == 50


class TestRomper:
    def test_un_golpe_rompe_un_bloque_de_un_golpe(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        assert sistema.golpear(pygame.Rect(96, 96, 24, 24)) == 1
        assert bloque.roto

    def test_uno_de_tres_golpes_aguanta_dos(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16), golpes=3)
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        assert sistema.golpear(caja) == 0
        assert sistema.golpear(caja) == 0
        assert sistema.golpear(caja) == 1

    def test_un_golpe_que_no_toca_no_cuenta(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        assert sistema.golpear(pygame.Rect(300, 300, 24, 24)) == 0
        assert not bloque.roto

    def test_sin_caja_de_golpe_no_pasa_nada(self) -> None:
        """`active_hitbox` es `None` casi todos los fotogramas."""
        sistema = SistemaDeBloques(
            destructibles=[BloqueDestructible(rect=pygame.Rect(0, 0, 16, 16))])
        assert sistema.golpear(None) == 0

    def test_un_bloque_roto_no_se_vuelve_a_romper(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        sistema.golpear(caja)
        assert sistema.golpear(caja) == 0

    def test_al_romperse_emite_su_evento(self) -> None:
        """Cierra el circuito con el resto: abrir una puerta (AUD-132),
        arrancar una inundación (AUD-135), lanzar una escena (AUD-136)."""
        bus = _Bus()
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16),
                                    evento_al_romper="ABRIR_EL_PASO")
        SistemaDeBloques(destructibles=[bloque], bus=bus).golpear(
            pygame.Rect(96, 96, 24, 24))
        assert bus.emitidos == ["ABRIR_EL_PASO"]

    def test_sin_evento_no_emite_nada(self) -> None:
        bus = _Bus()
        SistemaDeBloques(
            destructibles=[BloqueDestructible(rect=pygame.Rect(0, 0, 16, 16))],
            bus=bus,
        ).golpear(pygame.Rect(0, 0, 16, 16))
        assert bus.emitidos == []


class TestLosSolidos:
    def test_los_dos_tipos_estorban_el_paso(self) -> None:
        sistema = SistemaDeBloques(
            empujables=[BloqueEmpujable(rect=pygame.Rect(0, 0, 16, 16))],
            destructibles=[BloqueDestructible(rect=pygame.Rect(32, 0, 16, 16))],
        )
        assert len(sistema.rects_solidos()) == 2

    def test_un_bloque_roto_deja_de_estorbar(self) -> None:
        roto = BloqueDestructible(rect=pygame.Rect(32, 0, 16, 16))
        sistema = SistemaDeBloques(destructibles=[roto])
        roto.golpear()
        assert sistema.rects_solidos() == []


class TestReiniciarAlMorir:
    def test_el_empujable_vuelve_a_su_sitio(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(80, 170, 20, 30)
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        sistema.reiniciar()
        assert bloque.rect.topleft == (100, 168)

    def test_el_destructible_vuelve_entero(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16), golpes=2)
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        sistema.golpear(caja)
        sistema.golpear(caja)
        sistema.reiniciar()
        assert not bloque.roto
        assert sistema.golpear(caja) == 0, "conservó los golpes de la vida anterior"


class TestLoQueLlegaDesdeTiled:
    def _cargar(self, tipo: str, props: dict, ancho: int = 32, alto: int = 32):
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("Obj", (), {"x": 64, "y": 96, "width": ancho, "height": alto})()
        StageLoader._handle_bloque(stage, obj, props,
                                   empujable=(tipo == "PushBlock"))
        return stage

    def test_el_empujable_llega_con_su_velocidad(self) -> None:
        stage = self._cargar("PushBlock", {"velocidad": 80})
        assert stage.empujables and stage.empujables[0].velocidad == 80

    def test_el_destructible_llega_con_sus_golpes_y_su_evento(self) -> None:
        stage = self._cargar("BreakableBlock",
                             {"golpes": 3, "evento_al_romper": "PASO"})
        bloque = stage.destructibles[0]
        assert bloque.golpes == 3
        assert bloque.evento_al_romper == "PASO"

    def test_un_bloque_sin_tamano_se_descarta(self) -> None:
        """0×0 sería un sólido invisible de área nula: no estorba, no se ve, y
        el estudiante creería haberlo puesto."""
        stage = self._cargar("PushBlock", {}, ancho=0, alto=0)
        assert stage.empujables == []

    def test_cero_golpes_se_trata_como_uno(self) -> None:
        """Dato hostil: `golpes = 0` sería un bloque imposible de romper por
        contar mal, no por diseño."""
        stage = self._cargar("BreakableBlock", {"golpes": 0})
        assert stage.destructibles[0].golpes >= 1

    def test_una_velocidad_de_basura_no_rompe_la_carga(self) -> None:
        stage = self._cargar("PushBlock", {"velocidad": "rápido"})
        assert stage.empujables[0].velocidad > 0

    @pytest.mark.parametrize("tipo", ["PushBlock", "BreakableBlock"])
    def test_los_dos_tipos_los_conoce_el_validador(self, tipo) -> None:
        """Si no están en la lista, el validador le dice al estudiante que su
        objeto es de un tipo desconocido — y el objeto funciona."""
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert tipo in known_object_types(())


class TestLleganAlJuegoDeVerdad:
    """La comprobación que este proyecto ha necesitado nueve veces este mes.

    Que el sistema funcione aislado no significa que la escena lo construya,
    lo actualice y lo dibuje. Aquí se arranca el laboratorio de mecánicas
    entero y se mira lo que hay dentro.
    """

    def _escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage_mecanicas.stage_mecanicas import StageMecanicas

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
        escena = StageMecanicas(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        return escena

    def test_el_laboratorio_tiene_los_dos_tipos(self) -> None:
        escena = self._escena()
        try:
            assert escena._stage_data.empujables, (
                "ningún mapa usa PushBlock: la mecánica existe y nadie la verá"
            )
            assert escena._stage_data.destructibles
        finally:
            escena.on_exit()

    def test_la_escena_construye_su_sistema(self) -> None:
        escena = self._escena()
        try:
            assert escena._bloques is not None
            assert escena._bloques.rects_solidos(), (
                "los bloques del mapa no estorban el paso: son decoración"
            )
        finally:
            escena.on_exit()

    def test_correr_y_dibujar_no_lanza(self) -> None:
        escena = self._escena()
        pantalla = pygame.display.get_surface()
        try:
            for _ in range(10):
                escena.update(1 / 60)
                escena.draw(pantalla)
        finally:
            escena.on_exit()
