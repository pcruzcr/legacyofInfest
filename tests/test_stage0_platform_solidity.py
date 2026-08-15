"""
Solidez de las plataformas de Stage 0, medida sobre el mapa que haya.

AUD-112 — por qué se reescribió
================================
Esta suite fijaba **columnas concretas** del trazado::

    P1_C1, P1_C2 = 6, 11        # plataforma de la zona A
    PIT_C1, PIT_C2 = 54, 56     # tapa del foso
    HP_C1, HP_C2 = 58, 62       # plataforma alta

Al regenerar Stage 0 las tres cambiaron de sitio y las pruebas se pusieron rojas
sin que el motor hubiera cambiado una línea. Estaban midiendo **dónde** está una
plataforma en vez de **qué hace**, y con eso rediseñar el escenario de
referencia obligaba a reescribir las pruebas — que es la forma más rápida de
enseñar a editar pruebas hasta que pasen.

Es la misma lección que `assert len(PlayerState) == 24`, que además se llamaba
`test_player_state_enum_has_19_values` porque a alguien ya le había tocado
editarla y sólo cambió el número.

Ahora las coordenadas **salen del mapa cargado**: se busca el sólido más a la
izquierda contra el que se pueda chocar y la plataforma atravesable más baja, y
se prueba sobre ellas. El contrato es el mismo y el trazado puede moverse.
"""
from __future__ import annotations

import os

import pygame
import pytest

from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player
from src.framework.stage.stage_loader import StageLoader

STAGE0_TMX = "assets/maps/stage0/stage0.tmx"
DT = 1.0 / 60.0
TILE = 16

#: Los obstáculos sólidos interiores, `(columna, alto en baldosas)`. Es la
#: misma tabla que `tools/generate_stage0_tmx.OBSTACULOS`; se repite aquí a
#: propósito para que la prueba falle si el generador cambia sin querer, en vez
#: de adaptarse en silencio a lo que el generador diga hoy.
OBSTACULOS_ESPERADOS: tuple[tuple[int, int], ...] = ((10, 2), (50, 3))


def _hold(*actions: Action) -> InputManager:
    im = InputManager()
    for action in actions:
        for key in im._bindings.get(action, []):
            im._held.add(key)
    return im


@pytest.fixture(scope="module")
def stage():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    from src.framework.entities import entity_factory
    entity_factory.ensure_registered()
    return StageLoader.load(STAGE0_TMX)


def _muro_vertical(stage) -> pygame.Rect | None:
    """Una caja sólida contra la que se pueda chocar andando.

    Se descartan las más anchas que altas —el suelo— y las de casi toda la
    altura del mapa, que son los muros de cierre y quedan fuera del área
    jugable.
    """
    alto_mapa = stage.map_pixel_size[1]
    candidatas = [
        r for r in stage.collision_rects
        if r.height > r.width and r.height < alto_mapa * 0.6 and r.left >= 0
    ]
    return min(candidatas, key=lambda r: r.left) if candidatas else None


def _plataforma_atravesable(stage) -> pygame.Rect | None:
    """La plataforma de un solo sentido más baja: la más fácil de alcanzar."""
    if not stage.one_way_rects:
        return None
    return max(stage.one_way_rects, key=lambda r: r.top)


class TestElSueloSostiene:
    def test_el_jugador_no_atraviesa_el_suelo(self, stage) -> None:
        """La prueba más básica, y la que ninguna coordenada necesita."""
        p = Player(pygame.Vector2(stage.spawn_point))
        for _ in range(180):
            p.update(DT, stage.collision_rects, None,
                     one_way_rects=stage.one_way_rects)
        assert p.is_grounded, "el jugador cayó a través del suelo del prólogo"
        assert p.rect.bottom <= stage.map_pixel_size[1]


class TestLasPlataformasAtravesablesSonDeUnSentido:
    def test_stage0_declara_alguna(self, stage) -> None:
        """Sin ninguna, el resto de esta clase no probaría nada.

        Una prueba que se salta en silencio cuando el dato no está es una
        prueba que pasa por no haber mirado.
        """
        assert stage.one_way_rects, (
            "el prólogo no declara ninguna plataforma atravesable: es donde el "
            "estudiante va a mirar cómo se hacen"
        )

    def test_se_aterriza_encima_cayendo(self, stage) -> None:
        plat = _plataforma_atravesable(stage)
        assert plat is not None
        p = Player(pygame.Vector2(plat.centerx - 10, plat.top - 80))
        p.is_grounded = False
        for _ in range(120):
            p.update(DT, stage.collision_rects, None,
                     one_way_rects=stage.one_way_rects)
            if p.is_grounded and abs(p.rect.bottom - plat.top) <= 2:
                break
        else:
            pytest.fail(
                f"cayendo sobre la plataforma {tuple(plat)} el jugador acabó en "
                f"{tuple(p.rect)} sin apoyarse en ella",
            )

    def test_subiendo_no_frena_al_jugador(self, stage) -> None:
        """Es lo que la hace de un solo sentido y no un techo.

        Se llama a `_resolve_one_way_collision` directamente y no a `update`:
        la máquina de estados gobierna la velocidad vertical, así que
        empujar al jugador hacia arriba a mano y llamar a `update` mide lo que
        decide el estado, no lo que decide la plataforma. La primera versión de
        esta prueba caía en eso y acusaba a la plataforma de bloquear.
        """
        plat = _plataforma_atravesable(stage)
        assert plat is not None
        p = Player(pygame.Vector2(plat.centerx - 10, plat.bottom - 4))
        p.velocity.y = -400.0          # subiendo
        p.is_grounded = False
        antes = p.position.y
        p._resolve_one_way_collision(DT, stage.one_way_rects)
        assert p.position.y == pytest.approx(antes), (
            f"la plataforma {tuple(plat)} recolocó al jugador mientras subía: "
            f"es un techo, no una plataforma de un solo sentido"
        )
        assert p.velocity.y < 0.0, "le frenó el impulso hacia arriba"

    def test_no_se_apoya_si_venia_de_abajo(self, stage) -> None:
        """El otro lado del contrato: sólo aterriza quien venía por encima."""
        plat = _plataforma_atravesable(stage)
        assert plat is not None
        p = Player(pygame.Vector2(plat.centerx - 10, plat.bottom + 2))
        p.velocity.y = 60.0            # cayendo, pero ya por debajo
        p._prev_foot_y = plat.bottom + 34
        p.is_grounded = False
        p._resolve_one_way_collision(DT, stage.one_way_rects)
        assert not p.is_grounded, (
            "se apoyó en una plataforma que tenía por encima"
        )


class TestLosSolidosBloquean:
    def test_andar_contra_un_solido_detiene_al_jugador(self, stage) -> None:
        muro = _muro_vertical(stage)
        # Antes era un `pytest.skip`, y se saltaba en todas las ejecuciones
        # desde que se escribió, porque stage 0 no tenía ni una caja sólida
        # interior. Verde en el informe sin haber probado nada. Ahora los
        # obstáculos existen y su ausencia es un fallo, no una excusa.
        assert muro is not None, (
            "el prólogo no tiene ningún sólido interior contra el que chocar: "
            "sin eso no se enseña la colisión horizontal"
        )
        p = Player(pygame.Vector2(muro.left - 60, muro.top + 8))
        im = _hold(Action.MOVE_RIGHT)
        for _ in range(120):
            p.update(DT, stage.collision_rects, im,
                     one_way_rects=stage.one_way_rects)
        assert p.rect.right <= muro.left + 1, (
            f"el jugador atravesó el sólido {tuple(muro)}: acabó en {tuple(p.rect)}"
        )


class TestLosObstaculosSePuedenSaltar:
    """Un obstáculo que bloquea de verdad puede bloquear del todo.

    Poner cajas sólidas en el camino sin comprobar que se superan es la forma
    de dejar un escenario de referencia con un callejón sin salida. La altura
    del salto (72 px medidos) es un dato del jugador, no del mapa: si alguien
    la baja, esta prueba se pone roja aquí en vez de en la partida de un
    estudiante.
    """

    @pytest.mark.parametrize("columna,alto", OBSTACULOS_ESPERADOS)
    def test_el_jugador_supera_cada_obstaculo(self, stage, columna, alto) -> None:
        obstaculo = pygame.Rect(columna * TILE, (30 - alto) * TILE,
                                TILE, alto * TILE)
        assert obstaculo in stage.collision_rects, (
            f"el obstáculo esperado en la columna {columna} no está en el mapa"
        )

        p = Player(pygame.Vector2((columna - 8) * TILE, obstaculo.bottom - 48))
        for _ in range(30):
            p.update(DT, stage.collision_rects, None,
                     one_way_rects=stage.one_way_rects)

        saltando = False
        for _ in range(600):
            im = InputManager()
            for key in im._bindings.get(Action.MOVE_RIGHT, []):
                im._held.add(key)
            if p.is_grounded:
                saltando = p.rect.right > obstaculo.left - 24
                if saltando:
                    for key in im._bindings.get(Action.JUMP, []):
                        im._pressed_this_frame.add(key)
                        im._held.add(key)
            elif saltando:
                for key in im._bindings.get(Action.JUMP, []):
                    im._held.add(key)
            p.update(DT, stage.collision_rects, im,
                     one_way_rects=stage.one_way_rects)
            if p.rect.left > obstaculo.right:
                return
        pytest.fail(
            f"el jugador no logró superar el obstáculo de {alto} baldosas en la "
            f"columna {columna} en diez segundos: se quedó en {tuple(p.rect)}"
        )


class TestElMapaYSuGeneradorVanJuntos:
    """AUD-112 — el defecto que ya había ocurrido aquí.

    El generador anterior declaraba **240 × 14** baldosas; el fichero del
    repositorio mide **100 × 38**. Llevaban desincronizados lo bastante como
    para que nadie supiera cuál era el bueno, y ejecutar `tools/` habría
    borrado el escenario que el juego carga de verdad.

    `stage_mecanicas` previno esto con una prueba. Stage 0 no la tenía, y es
    exactamente donde hacía falta.
    """

    def test_el_tmx_del_repositorio_es_el_que_produce_el_generador(self) -> None:
        import importlib.util
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        ruta = raiz / "tools" / "generate_stage0_tmx.py"
        spec = importlib.util.spec_from_file_location("gen_stage0", ruta)
        assert spec and spec.loader
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        en_disco = (raiz / STAGE0_TMX).read_text(encoding="utf-8")
        assert modulo.generar() == en_disco, (
            "stage0.tmx y su generador se han separado; si el bueno es el "
            "fichero, actualiza el generador — si es el generador, ejecuta "
            "`python tools/generate_stage0_tmx.py`"
        )

    def test_el_generador_declara_el_tamano_real_del_mapa(self, stage) -> None:
        """La comprobación que habría cazado los 240 × 14 sin leer una línea."""
        import importlib.util
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        ruta = raiz / "tools" / "generate_stage0_tmx.py"
        spec = importlib.util.spec_from_file_location("gen_stage0_dims", ruta)
        assert spec and spec.loader
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        ancho_px, alto_px = stage.map_pixel_size
        assert (modulo.MW * modulo.TS, modulo.MH * modulo.TS) == (ancho_px, alto_px), (
            f"el generador cree que el prólogo mide {modulo.MW}×{modulo.MH} "
            f"baldosas; el mapa cargado mide {ancho_px // modulo.TS}×"
            f"{alto_px // modulo.TS}"
        )


class TestLaEspecificacionDiceLaVerdad:
    """AUD-114 — `07_STAGE0_DESIGN.md` describía un escenario inexistente.

    La versión 1.0.0 especificaba 240 × 14 baldosas, 27 mensajes, 12 enemigos
    y 5 checkpoints, con coordenadas al píxel. El mapa real mide 100 × 38 y no
    coincidía en **ninguna** cifra. De ahí salió el 240 × 14 del generador.

    Un documento de diseño que nadie comprueba se vuelve ficción, y éste es el
    primero que lee un estudiante. Las cifras que el documento afirma se
    contrastan aquí contra el `.tmx`.
    """

    @staticmethod
    def _spec() -> str:
        import pathlib
        raiz = pathlib.Path(__file__).resolve().parent.parent
        return (raiz / "docs" / "07_STAGE0_DESIGN.md").read_text(encoding="utf-8")

    def test_el_tamano_que_declara_es_el_real(self, stage) -> None:
        ancho_px, alto_px = stage.map_pixel_size
        texto = f"{ancho_px // TILE} × {alto_px // TILE} baldosas"
        assert texto in self._spec(), (
            f"el documento no menciona el tamaño real del mapa ({texto})"
        )

    def test_el_inventario_cuadra_con_el_mapa(self, stage) -> None:
        """Las cifras de la tabla «Inventario del mapa», una por una."""
        import re

        spec = self._spec()

        def declarado(etiqueta: str) -> int:
            fila = re.search(rf"^\| {re.escape(etiqueta)} \| (\d+)", spec, re.M)
            assert fila, f"la tabla de inventario no tiene la fila «{etiqueta}»"
            return int(fila.group(1))

        from src.framework.entities.enemy_base import EnemyBase
        enemigos = [e for e in stage.entity_list if isinstance(e, EnemyBase)]

        reales = {
            "Enemigos": len(enemigos),
            "Checkpoints": len(stage.checkpoints),
            "Obstáculos sólidos interiores": len(OBSTACULOS_ESPERADOS),
            "Plataformas de un sentido": len(stage.one_way_rects),
        }
        for etiqueta, real in reales.items():
            assert declarado(etiqueta) == real, (
                f"el documento dice {declarado(etiqueta)} en «{etiqueta}» y el "
                f"mapa tiene {real}"
            )


class TestElRecorridoEsCoherente:
    """Lo que de verdad hay que preservar al rediseñar el escenario."""

    def test_hay_spawn_y_salida(self, stage) -> None:
        assert stage.spawn_point is not None
        assert stage.next_trigger is not None, "el prólogo no tiene salida"

    def test_la_salida_esta_a_la_derecha_del_spawn(self, stage) -> None:
        """El prólogo avanza hacia la derecha; invertirlo sería otro nivel."""
        assert stage.next_trigger.left > stage.spawn_point.x

    def test_hay_checkpoints_repartidos(self, stage) -> None:
        assert len(stage.checkpoints) >= 3, (
            f"sólo {len(stage.checkpoints)} checkpoints en el escenario que "
            f"enseña a poner checkpoints"
        )

    def test_el_spawn_no_esta_dentro_de_la_geometria(self, stage) -> None:
        """Aparecer dentro de un muro expulsa al jugador de forma impredecible."""
        cuerpo = pygame.Rect(int(stage.spawn_point.x), int(stage.spawn_point.y), 20, 32)
        dentro = [r for r in stage.collision_rects if r.colliderect(cuerpo)]
        assert not dentro, f"el spawn cae dentro de {[tuple(r) for r in dentro]}"
