"""AUD-519 — 4.1b, la variante acuática del slot de la Fase 4 (AUD-518).
Misma travesía horizontal que el 4-1, sumergida, con un pez abismal que
aparece y persigue sin poder tocar ni ser tocado.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from pathlib import Path

import pygame
import pytest

from src.stages.stage4_1b import trazado


@pytest.fixture(scope="module")
def _video() -> None:
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


def _construir_escena():
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1b.stage4_1b import Stage4_1B

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1B(ctx)
    ctx.scene_manager.push(sc)
    return sc


@pytest.fixture
def escena(_video):
    sc = _construir_escena()
    try:
        yield sc
    finally:
        sc.on_exit()


class TestElTrazadoTieneElMismoLargoQueElCementerio:
    def test_mismas_dimensiones_que_stage4_1(self) -> None:
        from src.stages.stage4_1 import trazado as trazado_4_1

        assert trazado.MW == trazado_4_1.MW
        assert trazado.MH == trazado_4_1.MH
        assert trazado.TS == trazado_4_1.TS

    def test_seis_secciones(self) -> None:
        assert trazado.MW == trazado.ANCHO_SECCION * 6

    def test_hay_siete_checkpoints_por_evento(self) -> None:
        """AUD-576 — 4.1b pasó de «uno por fase» (AUD-516) a «uno por
        evento» (blueprint 10/10 §15-16): el respawn acompaña a cada
        dominio mecánico nuevo y a cada set piece, no a cada tramo de
        distancia. Siete puntos, uno por hito — el CP7 del tramo final,
        que el propio blueprint deja «opcional si el encuentro final
        produce muertes frecuentes» (aquí se incluye: el pez del clímax
        es el único momento con riesgo real de bucle largo)."""
        puntos = trazado.checkpoints()
        assert len(puntos) == 7
        columnas = [c for c, _f in puntos]
        assert columnas == sorted(columnas), (
            "los checkpoints por evento no avanzan de forma monótona"
        )


class TestElMapaSigueAtadoASuGenerador:
    def test_el_tmx_coincide_con_generar(self) -> None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1b import DESTINO, generar

        assert DESTINO.exists(), "corre tools/generate_stage4_1b.py primero"
        actual = DESTINO.read_text(encoding="utf-8")
        assert actual == generar(), (
            "assets/maps/stage4_1b/stage4_1b.tmx está desactualizado respecto "
            "de tools/generate_stage4_1b.py — corre el generador de nuevo"
        )


class TestElNivelSePuedeJugar:
    def test_tiene_spawn_checkpoints_y_salida(self, escena) -> None:
        assert escena._stage_data.spawn_point is not None
        assert escena._stage_data.next_trigger is not None
        assert len(escena._stage_data.checkpoints) == 7

    def test_los_checkpoints_brillan(self, escena) -> None:
        """AUD-517 — pedido explícito para 4.1b/4.1c: un área que brilla,
        no el sprite/rectángulo de siempre."""
        for cp in escena._stage_data.checkpoints:
            assert cp._light is not None

    def test_el_agua_se_ve_no_solo_se_siente(self, escena) -> None:
        """AUD-525: `ZonaDeAgua` es la física (nado, oxígeno, corriente) y
        `WaterEffect` es lo que se ve — van por separado a propósito
        (`water_effect.py`), y el TMX nunca encendió el segundo. El nivel se
        jugaba sumergido de verdad y se veía completamente seco: sin tinte,
        sin ondas, nada distinguía la fosa de caminar al aire libre.
        """
        datos = escena._stage_data
        assert datos.water_effect is True, (
            "stage4_1b está sumergido de principio a fin y no enciende "
            "WaterEffect — el agua no tiene ningún rastro visual"
        )

    def test_el_tinte_del_agua_se_ve_de_verdad(self, escena) -> None:
        """AUD-574 — reporte jugando: «no se sabe cuál es el límite del
        agua». El tinte viejo (`#0a3038`, alpha 130) era azul casi negro
        sobre un fondo casi negro: las ondas existían y no se veían. El
        tinte de fosa `#1a5c6e` con alpha 150 suma la luz suficiente para
        que las líneas de `WaterEffect` se lean en toda la columna."""
        tint = tuple(escena._stage_data.water_tint)
        assert len(tint) == 3, f"water_tint no es un color RGB: {tint}"
        assert sum(tint) >= 90, (
            f"el tinte del agua ({tint}) es casi negro: las ondas del "
            "WaterEffect no se ven y el límite del agua no se lee"
        )
        assert escena._stage_data.water_alpha >= 140, (
            "el alpha del agua es tan bajo que el tinte no se nota"
        )

    def test_hay_faroles_declarados(self, escena) -> None:
        """AUD-531 — pedido: "lámparas que iluminen hacia el agua... un
        límite visual inalcanzable"."""
        assert len(escena._stage_data.lights) >= 6, (
            "4.1b no declara faroles — el techo de la fosa no tiene "
            "ningún límite visual"
        )

    def test_el_fondo_no_es_negro_puro(self, escena) -> None:
        """AUD-531 — `LightSystem.render` compone con `BLEND_RGB_MULT`:
        multiplicar por un multiplicador de luz sobre negro puro sigue
        dando negro puro (0 × n = 0). Sin un fondo pintado, los faroles
        estaban calculados correctamente y eran invisibles igual —
        comprobado jugando, no una hipótesis."""
        assert escena._fondo_mina.get_at((0, 0))[:3] != (0, 0, 0)

    def test_el_farol_se_nota_en_el_fotograma_compuesto(self, escena) -> None:
        """No basta con que el sistema de luces calcule el foco — tiene
        que sobrevivir hasta el píxel final, con fondo pintado debajo.
        (AUD-576: las luces viven en columnas de mapa y la primera está
        en `(45, 4)` — x=720 — así que la cámara se posa de modo que esa
        luz caiga dentro del lienzo y se muestrea en coordenadas de
        lienzo, sin fijar una columna a mano.)"""
        import pygame

        primer_farol = escena._stage_data.lights[0]
        fx, fy = int(primer_farol.position[0]), int(primer_farol.position[1])
        cam_x = max(0.0, float(fx - 200))
        escena._camera.offset.x = cam_x
        escena._camera.offset.y = 0.0
        for _ in range(30):
            escena.update(1 / 60)
            escena._camera.offset.x = cam_x
            escena._camera.offset.y = 0.0

        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)

        px = fx - int(cam_x)  # coordenadas del lienzo
        cerca = lienzo.get_at((px, fy))
        lejos = lienzo.get_at((min(px + 400, 799), fy))
        assert sum(cerca[:3]) > sum(lejos[:3]), (
            f"el píxel junto al farol ({tuple(cerca)}) no es más claro que "
            f"uno lejos de cualquier luz ({tuple(lejos)})"
        )

    def test_la_zona_de_agua_cubre_la_columna_por_encima_del_lecho(self, escena) -> None:
        from src.framework.ecs import ZonaDeAgua

        zonas = [z for _eid, z in escena._mundo.cada(ZonaDeAgua)]
        assert len(zonas) >= 1
        zona = zonas[0]
        assert zona.rect.width >= trazado.MW * trazado.TS - trazado.MURO_ANCHO * trazado.TS * 2
        assert zona.rect.bottom <= trazado.FILA_SUELO * trazado.TS

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        from src.stages.stage4_1b.stage4_1b import Stage4_1B

        assert Stage4_1B.ZONE == 4
        assert escena._stage_data.zone == Stage4_1B.ZONE


class TestElPezAbismal:
    def test_no_hay_pez_ni_sombra_antes_del_primer_evento(self, escena) -> None:
        """AUD-576 — el pez es el «monstruo psicológico» (blueprint
        §17-19): NO persigue hasta que el jugador ya está aterrorizado.
        Antes de `COL_PRIMER_EVENTO` (col 553) no hay pez ni siquiera
        sombra — la mina entera se juega sin persecución (la fauna
        basta), y el respiro del principio es real."""
        from src.stages.stage4_1b.trazado import COL_PRIMER_EVENTO

        # A mitad de la esclusa (col 450), en agua abierta y sin corriente.
        escena._player.position.x = 450.0 * 16
        escena._player.position.y = 320.0
        assert int(escena._player.position.x // 16) < COL_PRIMER_EVENTO
        for _ in range(600):  # 10 s buceando delante del primer evento
            escena.update(1 / 60)
        assert escena._pez is None
        assert escena._sombra_x is None

    def test_el_pez_aparece_persigue_y_se_va_sin_dejar_fuga(self, escena) -> None:
        """AUD-576 — la persecución de verdad existe sólo en el abismo
        (col ≥ COL_PERSECUCIONES): el pez aparece desde fuera de cámara,
        persigue un rato y se retira, sin dejar peces fantasma en la
        lista ni morir por su cuenta."""
        from src.stages.stage4_1b.trazado import COL_PERSECUCIONES

        # En el abismo (col 750), tras la zona del pozo y fuera de las
        # corrientes: aquí sí caza.
        escena._player.position.x = 750.0 * 16
        escena._player.position.y = 320.0
        assert int(escena._player.position.x // 16) >= COL_PERSECUCIONES
        apariciones = 0
        estaba_activo = False
        for _ in range(3600):  # 60 s de juego
            escena.update(1 / 60)
            activo = escena._pez is not None
            if activo and not estaba_activo:
                apariciones += 1
            estaba_activo = activo
        assert apariciones >= 1, (
            "en el abismo el pez debería haber cazado al menos una vez"
        )
        assert escena._pez is None or escena._pez.is_alive
        # Nada de peces fantasma acumulados en la lista de entidades.
        from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal

        peces_en_la_lista = [
            e for e in escena._stage_data.entity_list
            if isinstance(e, EnemyPezAbismal)
        ]
        assert len(peces_en_la_lista) <= 1

    def test_el_pez_no_hace_dano_al_jugador(self, escena) -> None:
        """Pedido explícito: que no lo mate ni lo toque."""
        from src.framework.entities.enemy_pez_abismal import EnemyPezAbismal

        pez = EnemyPezAbismal(pygame.Vector2(escena._player.rect.center))
        assert pez.damage_on_contact == 0.0


class TestElJugadorNadaNoCaminaPorElLecho:
    """AUD-573 — reporte jugando: «el personaje no nada». Reproducido
    en simulación con el input real del nivel: manteniendo derecha y
    salto desde el spawn, el jugador saltaba con física de tierra y
    acababa WALKING sobre el lecho dentro del agua. Ahora debe quedarse
    nadando: subir con el impulso de nado y volver a tocar el lecho sin
    perder nunca el estado de nado.

    AUD-575 — el salto sostenido ya no se usa en la simulación: con la
    superficie real, subir nadando con salto sostenido EMERGE (la
    expulsión de `_salir`, AUD-572) y el estado oscila a propósito entre
    nado y aire. Lo que custodia la prueba es el refuerzo: dentro del
    agua, la máquina de tierra nunca gana."""

    def test_mantener_derecha_nada_y_no_camina_por_el_lecho(self, escena) -> None:
        from src.engine.input.action_map import DEFAULT_KEY_BINDINGS, Action

        im = escena.context.input_manager
        eventos = [
            pygame.event.Event(pygame.KEYDOWN,
                               key=DEFAULT_KEY_BINDINGS[Action.MOVE_RIGHT][0]),
        ]
        # Aguas abiertas de la esclusa (sin paredes ni corrientes que
        # desvíen la simulación).
        escena._player.position.x = 600.0
        escena._player.position.y = 320.0
        dt = 1 / 60
        for _ in range(120):  # 2 s con derecha mantenida
            im.pump(eventos)
            escena.update(dt)
        from src.framework.entities.states import SwimmingState

        jugador = escena._player
        assert isinstance(jugador._state_instance, SwimmingState), (
            "manteniendo derecha, el jugador quedó en "
            f"{jugador._state_instance.state_enum.value} — la máquina de "
            "WALKING le ganó dentro del agua"
        )
        assert jugador.position.y < 448.0, (
            "nadie puede nadar: el jugador sigue pegado al lecho "
            f"(y={jugador.position.y:.0f}) pese a mantener derecha"
        )


class TestElOxigenoVigilaAlBuceador:
    """AUD-575 — la mina inundada ya tiene superficie de verdad
    (`trazado.FILA_SUPERFICIE_AGUA = 11`: aire encima, agua debajo), así
    que el límite de aire de `ControlDeNado` vuelve a ser la tensión que
    era en el diseño: bucear sin emerger acaba en daño, y emerger
    respira. Es el cierre del GAP-071: `avisando` ya tiene consumidor
    (barra de oxígeno en el HUD + pulso sonoro)."""

    def test_el_dano_por_ahogamiento_esta_activo(self, escena) -> None:
        assert escena._nado.dano_por_segundo > 0.0, (
            "la mina inundada tiene superficie a la que emerger: el "
            "ahogamiento apagado era la solución de un nivel sin aire"
        )

    def test_quedarse_sumergido_agota_el_aire_y_quita_vida(self, escena) -> None:
        """30 s de aire y después daño a 1/s. Se simulan 36 s sumergido:
        el aire se agota de sobra y el daño entra — sin llegar a morir
        (morir haría respawn con aire lleno, que es justo lo que el
        diseño quiere: el castigo es el bucle, no la muerte única)."""
        escena._player.position.x = 600.0  # aguas abiertas de la esclusa
        escena._player.position.y = 320.0  # dentro del agua, lejos de la superficie
        vida_inicial = escena._player.current_health
        for _ in range(36 * 60):
            escena.update(1 / 60)
        assert escena._nado.sin_aire
        assert escena._player.current_health < vida_inicial

    def test_emerger_respira_y_el_aire_se_recupera(self, escena) -> None:
        """El trato del diseño: fuera del agua, `ControlDeNado` restaura
        el aire (8 puntos por segundo) — bucear deja de ser una condena."""
        escena._player.position.x = 600.0
        escena._player.position.y = 320.0
        for _ in range(10 * 60):
            escena.update(1 / 60)
        aire_sumergido = escena._nado.aire
        assert aire_sumergido < escena._nado.aire_maximo
        # AUD-575 — "emerger" de verdad es salir a una zona sin agua: el
        # andén seco del patio (S3, techo en la fila 8). Poner el jugador
        # "a flote" no sirve: la gravedad lo devuelve al agua.
        escena._player.position.x = 350.0 * trazado.TS
        escena._player.position.y = 60.0  # cae al andén (fila 8), fuera del agua
        for _ in range(3 * 60):
            escena.update(1 / 60)
        assert not escena._nado.en_agua, (
            "el jugador siguió en el agua sobre el andén del patio"
        )
        assert escena._nado.aire >= escena._nado.aire_maximo

    def test_el_jugador_nace_fuera_del_agua(self, escena) -> None:
        """El spawn está sobre el andén seco de la sección 1, no sumergido:
        el jugador respira mientras aprende a bucear."""
        assert not escena._nado.en_agua
        assert escena._player.position.y < trazado.FILA_SUPERFICIE_AGUA * trazado.TS


class TestLasCorrientesDeAgua:
    """AUD-543 — «corrientes de agua», pedido tras jugarlo.
    `ZonaDeAgua.corriente` existía en el motor y ningún nivel lo declaraba.
    Los números de `trazado.ZONAS_DE_CORRIENTE` están verificados por
    simulación (ver el comentario junto a la constante), no a ojo: esta
    clase fija esa evidencia en una prueba, para que quien cambie la
    magnitud tenga que volver a medir, no volver a adivinar.
    """

    def test_hay_al_menos_una_zona_a_favor_y_una_en_contra(self) -> None:
        signos = {1 if fx > 0 else -1 for _, _, fx in trazado.ZONAS_DE_CORRIENTE}
        assert signos == {1, -1}, (
            "las corrientes son todas del mismo signo: no hay variedad de "
            "ritmo (empuje/resistencia) a lo largo del nivel"
        )

    def test_las_zonas_caen_dentro_del_mapa(self) -> None:
        for col_ini, col_fin, _fx in trazado.ZONAS_DE_CORRIENTE:
            assert 0 <= col_ini < col_fin <= trazado.MW

    def test_el_tmx_declara_las_mismas_zonas_que_trazado(self, escena) -> None:
        from src.framework.ecs import ZonaDeAgua

        zonas = [z for _eid, z in escena._mundo.cada(ZonaDeAgua)
                 if z.corriente.length_squared() > 0.0]
        assert len(zonas) == len(trazado.ZONAS_DE_CORRIENTE), (
            "el TMX generado no trae la misma cantidad de zonas con "
            "corriente que declara trazado.ZONAS_DE_CORRIENTE — "
            "¿hace falta correr tools/generate_stage4_1b.py de nuevo?"
        )

    def test_nadar_en_contra_de_la_corriente_frena_de_verdad(self, escena) -> None:
        """La cifra medida (no una promesa): 90 px/s en régimen, contra
        120 px/s sin corriente — un 25% más lento, verificado aquí con el
        mismo mecanismo que usa el nivel real (`sistema_corriente_de_agua`
        + `SwimmingState`), no con la fórmula de FUERZAS/dt a mano."""
        from src.engine.input.action_map import Action
        from src.framework.ecs import Velocidad, ZonaDeAgua
        from src.framework.ecs import systems as ecs_systems
        from src.framework.ecs.world import World
        from src.framework.entities.player import Player
        from src.framework.entities.states.swim import SwimmingState

        class _EntradaFalsa:
            def __init__(self, sostenidas: set) -> None:
                self._sostenidas = sostenidas

            def is_action_held(self, accion: object) -> bool:
                return accion in self._sostenidas

            def is_action_pressed(self, accion: object) -> bool:
                return False

            def pulsada_en_buffer(self, accion: object) -> bool:
                return False

        jugador = Player(pygame.Vector2(100.0, 100.0))
        jugador._change_state_instance(SwimmingState())
        mundo = World()
        jugador.adoptar_en(mundo)
        mundo.poner(jugador.entidad, Velocidad(jugador.velocity))
        mundo.crear(ZonaDeAgua(
            rect=pygame.Rect(0, 0, 4000, 4000),
            corriente=pygame.Vector2(-30.0, 0.0)))

        entrada = _EntradaFalsa({Action.MOVE_RIGHT})
        dt = 1 / 60
        for _ in range(int(3.0 / dt)):
            jugador.update(dt, [], entrada)
            ecs_systems.sistema_corriente_de_agua(mundo, dt)

        assert jugador.velocity.x == pytest.approx(90.0, abs=1.0), (
            f"la velocidad en régimen contra la corriente es "
            f"{jugador.velocity.x:.1f} px/s, no ~90: si esto cambió, la "
            f"nota de `ZONAS_DE_CORRIENTE` también hay que actualizarla"
        )


class TestLaMinaInundada:
    """AUD-575 — el rediseño del 4-1b: una mina abandonada e inundada
    (estética café/óxido, agua azul con superficie real, estalactitas,
    luces de seguridad rojas y blancas, fauna que estorba sin dañar y
    música propia)."""

    def test_hay_estalactitas_en_la_decoracion_del_fondo(self, escena) -> None:
        import csv
        from io import StringIO

        ruta = Path(__file__).resolve().parents[1] / "assets/maps/stage4_1b/stage4_1b.tmx"
        texto = ruta.read_text(encoding="utf-8")
        en_bg_near = False
        for fila in texto.splitlines():
            if 'name="BG_Near"' in fila:
                en_bg_near = True
                continue
            if en_bg_near:
                if "</data>" in fila:
                    break
                if "<" in fila or ">" in fila:
                    continue
                celdas = next(csv.reader(StringIO(fila)))
                gids = {int(c) for c in celdas if c}
                if gids & {65, 66}:
                    return
        assert False, "BG_Near no contiene estalactitas (gid 65/66)"

    def test_el_agua_no_llega_al_techo(self, escena) -> None:
        """La superficie está en la fila 11: la columna de arriba es aire
        respirable, no agua negra hasta el borde del mapa."""
        assert trazado.FILA_SUPERFICIE_AGUA < trazado.FILA_SUELO
        assert escena._player.position.y < trazado.FILA_SUPERFICIE_AGUA * trazado.TS
        from src.framework.ecs import ZonaDeAgua

        zonas = [z for _eid, z in escena._mundo.cada(ZonaDeAgua)]
        assert zonas[0].rect.top == trazado.FILA_SUPERFICIE_AGUA * trazado.TS

    def test_hay_luces_rojas_y_blancas_ademas_de_calidas(self, escena) -> None:
        from src.framework.stage.stage_objetos import ObjetosDeTiled

        colores = {tuple(luz.color) for luz in escena._stage_data.lights}
        paleta = {nombre: tuple(c) for nombre, c in ObjetosDeTiled.LIGHT_COLORS.items()}
        assert paleta["blood"] in colores, (
            "no hay luces rojas de peligro — la mina no avisa de la zona "
            "de riesgo"
        )
        assert paleta["white"] in colores, (
            "no hay luces blancas de trabajo — los focos del patio no están"
        )
        assert paleta["warm"] in colores, (
            "no hay luces cálidas de refugio en el 4-1b"
        )

    def test_los_bloques_de_mineral_son_destructibles(self, escena) -> None:
        from src.framework.stage.bloques import BloqueDestructible

        bloques = [b for b in escena._stage_data.destructibles
                   if isinstance(b, BloqueDestructible)]
        assert len(bloques) == len(trazado.BLOQUES_DE_MINERAL), (
            "el TMX no declara todos los bloques de mineral de "
            "trazado.BLOQUES_DE_MINERAL — ¿hay que regenerarlo?"
        )
        for b in bloques:
            assert b.golpes >= 1

    def test_la_fauna_del_nivel_estorba_sin_danar(self, escena) -> None:
        """Cangrejos y medusas son presencia: bloquean el paso y se
        apartan, pero con `damage_on_contact=0` y `contact_knockback=0`
        (el knockback de un daño 0 aún metía `HurtState`). El pez
        abismal ya tenía su regla aparte."""
        from src.framework.entities.enemy_cangrejo import EnemyCangrejo
        from src.framework.entities.enemy_medusa import EnemyMedusa

        fauna = [e for e in escena._stage_data.entity_list
                 if isinstance(e, (EnemyCangrejo, EnemyMedusa))]
        assert len(fauna) == len(trazado.FAUNA), (
            "la escena no siembra toda la fauna de trazado.FAUNA"
        )
        for e in fauna:
            assert e.damage_on_contact == 0.0
            assert e.contact_knockback == 0.0

    def test_la_musica_del_nivel_es_la_de_la_mina(self, escena) -> None:
        from src.stages.stage4_1b.stage4_1b import Stage4_1B

        assert Stage4_1B.BGM_TRACK == "4_1_b", (
            "BGM_TRACK documental desincronizado del TMX"
        )
        assert escena._stage_data.bgm_track == "4_1_b"

    def test_los_bloques_de_mineral_caen_dentro_del_mapa(self, escena) -> None:
        """Toda la geometría nueva del trazado queda dentro del mapa y
        por encima del lecho — y el patio tiene su bloque al aire (fila
        por encima de la superficie), para la alternancia agua/aire."""
        for (col, fila) in trazado.BLOQUES_DE_MINERAL:
            assert 0 <= col < trazado.MW
            # La fila 32 es la primera del lecho: los bloques de mineral
            # descansan SOBRE él, no dentro.
            assert 0 <= fila <= trazado.FILA_SUELO
        assert any(fila < trazado.FILA_SUPERFICIE_AGUA
                   for _, fila in trazado.BLOQUES_DE_MINERAL), (
            "ningún bloque de mineral está al aire: la alternancia "
            "agua/área seca del diseño no existe"
        )
