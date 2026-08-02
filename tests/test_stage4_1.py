"""
Nivel 4-1 — La Entrada al Cementerio.

Un nivel sin enemigos es un nivel donde **todo lo que hay es atmósfera**, y la
atmósfera es justo lo que se rompe sin que nadie se entere: un clima que no
cambia, un brasero que se apaga al retroceder o una visión espectral que no
revela nada se ven igual de bien en una captura de pantalla.

Así que estas pruebas no comprueban que las clases existan: mueven al jugador
por el mapa y **miran el resultado**.

Lo que defienden
-----------------
1. **La regla de oro.** Cero enemigos, contados sobre el mapa cargado.
2. **Que el fondo avance.** Cinco actos, cada uno con su clima, sus partículas
   y su luz — y que la progresión sea monótona, no un vaivén.
3. **Que los braseros sean la barra de progreso.** Se encienden al pasar y
   **no se apagan** al volver.
4. **Que la visión espectral revele.** Una huella que no se ve sin la visión y
   sí con ella, comprobada píxel a píxel.
5. **Que quepa en el presupuesto de fotograma.** Un efecto de pantalla completa
   a 60 fps es exactamente donde un nivel bonito se vuelve injugable.
"""
from __future__ import annotations

from itertools import pairwise

import pygame
import pytest

from src.engine.core import settings


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


@pytest.fixture
def escena(_video):
    from src.engine.audio.audio_manager import AudioManager
    from src.engine.core.event_bus import EventBus
    from src.engine.core.game_context import GameContext
    from src.engine.core.save_manager import SaveManager
    from src.engine.input.input_manager import InputManager
    from src.engine.scene.scene_manager import SceneManager
    from src.framework.entities import entity_factory
    from src.stages.stage4_1.stage4_1 import Stage4_1

    entity_factory.ensure_registered()
    ctx = GameContext(
        input_manager=InputManager(), audio_manager=AudioManager(),
        scene_manager=None, event_bus=EventBus(), clock=None,
        save_manager=SaveManager(),
    )
    ctx.scene_manager = SceneManager(ctx)
    sc = Stage4_1(ctx)
    ctx.scene_manager.push(sc)
    yield sc
    sc.on_exit()


def _llevar_a(escena, baldosa: int) -> None:
    """Coloca al jugador en esa columna y deja correr unos fotogramas."""
    x = baldosa * settings.TILE_SIZE
    escena._player.rect.x = x
    escena._player.position.x = float(x)
    for _ in range(4):
        escena.update(1 / 60)


class TestLaReglaDeOro:
    """«Si el nivel aburre, se arregla con más marcas ocultas, no con
    serpientes.» — la ficha del nivel."""

    def test_no_hay_un_solo_enemigo(self, escena) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        enemigos = [e for e in escena._stage_data.entity_list
                    if isinstance(e, EnemyBase)]
        assert enemigos == [], (
            f"el 4-1 tiene {len(enemigos)} enemigos y su regla de oro es cero"
        )

    def test_ni_siquiera_una_entidad(self, escena) -> None:
        """Se cuenta la lista entera, no sólo lo que hereda de `EnemyBase`.

        Un enemigo colocado por un tipo raro también contaría, y leer el XML
        no lo detectaría.
        """
        assert list(escena._stage_data.entity_list) == []

    def test_las_siluetas_no_son_entidades(self, escena) -> None:
        """El canon: «no atacan. Testifican.»"""
        from src.stages.stage4_1 import siluetas

        for _nombre, forma in siluetas.ESPIRITUS:
            assert callable(forma), "una silueta debe ser una forma, no un objeto"
        assert not hasattr(siluetas, "Enemigo")
        assert not hasattr(siluetas, "Cegua")


class TestElNivelSePuedeJugar:
    def test_tiene_salida(self, escena) -> None:
        """La ficha la llama «Portal»; el motor sólo acepta `NextTrigger`."""
        assert escena._stage_data.next_trigger is not None

    def test_tiene_punto_de_aparicion_y_checkpoints(self, escena) -> None:
        assert escena._stage_data.spawn_point is not None
        assert len(escena._stage_data.checkpoints) >= 1

    def test_el_mapa_tiene_el_tamano_minimo(self, escena) -> None:
        ancho, alto = escena._stage_data.map_pixel_size
        assert ancho >= 1600 and alto >= 608, (
            f"la ficha pide 1600x608 y el mapa mide {ancho}x{alto}"
        )

    def test_el_reloj_va_de_las_19_a_las_23(self, escena) -> None:
        datos = escena._stage_data
        assert getattr(datos, "start_hour", None) == 19
        assert getattr(datos, "day_length", 0) == 900


class TestElFondoAvanzaConElJugador:
    """Los cinco actos. Sin esto el nivel es un pasillo con decoración."""

    def test_los_cinco_actos_se_alcanzan_en_orden(self, escena) -> None:
        vistos = []
        for baldosa in (5, 25, 45, 65, 90):
            _llevar_a(escena, baldosa)
            vistos.append(escena.acto.numero)
        assert vistos == [1, 2, 3, 4, 5], f"la progresión salió {vistos}"

    def test_el_clima_cambia_con_el_acto(self, escena) -> None:
        climas = {}
        for baldosa in (5, 45, 65, 90):
            _llevar_a(escena, baldosa)
            climas[escena.acto.numero] = escena._weather._climate
        assert climas[1] == "fog"
        assert climas[4] == "storm", "el acto de la tormenta no llueve"
        assert climas[5] == "clear", "el umbral no se queda en silencio"

    def test_las_particulas_verdes_estan_encendidas(self, escena) -> None:
        """`spores` es el único efecto verde del motor, y el lore le pone al
        cementerio «luz espectral verde»."""
        _llevar_a(escena, 25)
        assert escena._ambient_particles._particle_type == "spores"
        assert escena._ambient_particles.rate > 0.0

    def test_las_particulas_suben_hacia_la_tormenta(self, escena) -> None:
        _llevar_a(escena, 25)
        pocas = escena._ambient_particles.rate
        _llevar_a(escena, 65)
        muchas = escena._ambient_particles.rate
        assert muchas > pocas

    def test_la_luna_baja_y_crece(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        for anterior, siguiente in pairwise(ACTOS):
            assert siguiente.luna_y > anterior.luna_y, (
                f"la luna sube entre el acto {anterior.numero} y el "
                f"{siguiente.numero}: el reloj del nivel iría al revés"
            )
            assert siguiente.luna_radio > anterior.luna_radio

    def test_los_espiritus_se_acercan_y_no_se_van(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        for anterior, siguiente in pairwise(ACTOS):
            assert siguiente.espiritus >= anterior.espiritus
            assert siguiente.cegua >= anterior.cegua

    def test_el_umbral_es_el_acto_mas_claro(self) -> None:
        """En el acto V arden los doce braseros: tiene que verse."""
        from src.stages.stage4_1.actos import ACTOS

        assert ACTOS[-1].ambiente == max(a.ambiente for a in ACTOS)

    def test_solo_truena_en_la_tormenta(self) -> None:
        from src.stages.stage4_1.actos import ACTOS

        con_rayos = [a.numero for a in ACTOS if a.rayos_por_minuto > 0]
        assert con_rayos == [3, 4], (
            f"los rayos deben anunciarse en el III y caer en el IV; están en "
            f"{con_rayos}"
        )


class TestLosBraserosSonLaBarraDeProgreso:
    def test_arrancan_los_doce_apagados(self, escena) -> None:
        assert len(escena._luces) == 12
        assert escena.braseros_encendidos == 0
        assert all(luz.intensity == 0.0 for luz in escena._luces)

    def test_se_encienden_al_pasar(self, escena) -> None:
        for luz in list(escena._luces):
            escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
            escena._player.position.update(luz.position)
            escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 12

    def test_la_llama_sube_en_vez_de_aparecer(self, escena) -> None:
        luz = escena._luces[0]
        escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
        escena._player.position.update(luz.position)
        escena._actualizar_braseros(1 / 60)
        recien = luz.intensity
        for _ in range(60):
            escena._actualizar_braseros(1 / 60)
        assert 0.0 < recien < luz.intensity

    def test_no_se_apagan_al_volver(self, escena) -> None:
        """«El sendero queda marcado de luz detrás del jugador.»"""
        luz = escena._luces[0]
        escena._player.rect.center = (int(luz.position.x), int(luz.position.y))
        escena._player.position.update(luz.position)
        escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 1

        escena._player.rect.center = (5000, 200)
        escena._player.position.update(pygame.Vector2(5000, 200))
        for _ in range(30):
            escena._actualizar_braseros(1 / 60)
        assert escena.braseros_encendidos == 1, (
            "alejarse apagó el brasero: la barra de progreso retrocedería"
        )

    def test_el_ultimo_es_el_grande(self, escena) -> None:
        """El del umbral. Es la imagen final del nivel."""
        assert escena._luces[-1].radius > escena._luces[0].radius


class TestLaVisionEspectral:
    """La mecánica protagonista (Unidad VIII)."""

    def test_apagada_al_empezar(self, escena) -> None:
        assert escena.vision_activa is False

    def test_se_agota_sola(self, escena) -> None:
        escena._vision = 0.1
        for _ in range(12):
            escena._actualizar_vision(1 / 60)
        assert escena.vision_activa is False

    def test_no_se_puede_encadenar_sin_recarga(self, escena) -> None:
        escena._vision = 0.0
        escena._recarga = escena.RECARGA_DE_LA_VISION
        escena._actualizar_vision(1 / 60)
        assert escena.vision_activa is False

    def test_la_huella_solo_existe_con_la_vision(self, escena) -> None:
        """El corazón de la mecánica, comprobado píxel a píxel."""
        from src.stages.stage4_1.siluetas import VERDE_ESPECTRAL

        _llevar_a(escena, 43)
        marca = escena._marcas[0]

        def color_en_la_huella() -> tuple[int, int, int]:
            lienzo = pygame.Surface((800, 600))
            escena.draw(lienzo)
            off = escena._camera.offset
            return lienzo.get_at((int(marca.centerx - off.x),
                                  int(marca.centery - off.y)))[:3]

        assert color_en_la_huella() != VERDE_ESPECTRAL
        escena._vision = escena.DURACION_DE_LA_VISION
        assert color_en_la_huella() == VERDE_ESPECTRAL, (
            "la visión no reveló la huella: sin enemigos, ésta es la única "
            "mecánica del nivel"
        )

    def test_hay_huellas_en_los_dos_tramos_de_saltos(self, escena) -> None:
        ts = settings.TILE_SIZE
        columnas = [m.x // ts for m in escena._marcas]
        assert any(40 <= c < 60 for c in columnas), "faltan huellas en el acto III"
        assert any(60 <= c < 80 for c in columnas), "faltan huellas en el acto IV"

    def test_la_vision_ilumina_y_no_oscurece(self, escena) -> None:
        """Lo primero que probé multiplicaba sobre la pantalla y el verde medio
        bajaba de 26 a 11. Una «visión» que quita luz no es una visión."""
        import numpy as np

        _llevar_a(escena, 44)
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)
        sin = np.asarray(pygame.surfarray.array3d(lienzo), dtype=int)[:, :, 1].mean()
        escena._vision = escena.DURACION_DE_LA_VISION
        escena.draw(lienzo)
        con = np.asarray(pygame.surfarray.array3d(lienzo), dtype=int)[:, :, 1].mean()
        assert con >= sin


class TestElRelampagoEnsenaAntesDeCastigar:
    """«Ningún peligro aparece sin que un relámpago anterior lo haya
    mostrado.» — §5 del diseño."""

    def test_el_destello_sube_la_luz(self, escena) -> None:
        _llevar_a(escena, 65)
        base = escena._lighting.ambient_brightness
        escena._rayo = escena.DURACION_DEL_RAYO
        escena._actualizar_rayos(1 / 60)
        assert escena._lighting.ambient_brightness > base

    def test_el_destello_se_apaga(self, escena) -> None:
        _llevar_a(escena, 65)
        escena._rayo = escena.DURACION_DEL_RAYO
        for _ in range(40):
            escena._actualizar_rayos(1 / 60)
        assert escena._rayo == 0.0

    def test_no_hay_rayos_en_el_umbral(self, escena) -> None:
        """El silencio es el jefe."""
        _llevar_a(escena, 90)
        escena._rayo = 0.0
        for _ in range(600):
            escena._actualizar_rayos(1 / 60)
        assert escena._rayo == 0.0


class TestCabeEnElPresupuestoDeFotograma:
    #: 60 fps son 16,6 ms para todo. Un efecto de pantalla completa es donde un
    #: nivel bonito se vuelve injugable, así que se mide.
    PRESUPUESTO_MS = 12.0

    def _medir(self, escena, veces: int = 15) -> float:
        import time

        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)          # calentar cachés
        t0 = time.perf_counter()
        for _ in range(veces):
            escena.draw(lienzo)
        return (time.perf_counter() - t0) / veces * 1000.0

    def test_el_dibujo_normal_cabe(self, escena) -> None:
        _llevar_a(escena, 44)
        assert self._medir(escena) < self.PRESUPUESTO_MS

    def test_con_la_vision_puesta_tambien(self, escena) -> None:
        _llevar_a(escena, 44)
        escena._vision = 999.0
        coste = self._medir(escena)
        assert coste < self.PRESUPUESTO_MS, (
            f"la visión cuesta {coste:.1f} ms por fotograma. Se umbraliza a 1/4 "
            f"de resolución justo por esto: a 1/2 medía 4,6 ms de más"
        )


class TestElMapaSigueAtadoASuGenerador:
    def test_el_tmx_es_el_que_produce_el_script(self) -> None:
        import sys
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(raiz / "tools"))
        from generate_stage4_1 import DESTINO, generar

        assert DESTINO.read_text(encoding="utf-8") == generar(), (
            "stage4_1.tmx no coincide con su generador: ejecuta "
            "`python tools/generate_stage4_1.py`"
        )


class TestElGanchoDeFondoLlegaAlEscenario:
    """AUD-162 — sin él, la luna y las siluetas se dibujarían encima del
    jugador y dejarían de ser fondo."""

    def test_stage_scene_ofrece_el_gancho(self) -> None:
        from src.framework.scenes.stage_scene import StageScene

        assert hasattr(StageScene, "dibujar_fondo")

    def test_el_4_1_lo_sobreescribe(self) -> None:
        from src.framework.scenes.stage_scene import StageScene
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.dibujar_fondo is not StageScene.dibujar_fondo

    def test_el_sistema_de_dibujo_lo_llama_antes_del_mapa(self) -> None:
        import inspect

        from src.framework.stage.drawing_system import DrawingSystem

        fuente = inspect.getsource(DrawingSystem.draw)
        i_fondo = fuente.index("fondo_del_escenario")
        i_mapa = fuente.index("_draw_stage_layers")
        assert i_fondo < i_mapa, (
            "el fondo del escenario se pinta después del mapa: taparía el nivel"
        )

    def test_un_fondo_que_falla_no_tumba_el_fotograma(self, escena) -> None:
        """Es decoración. El nivel tiene que seguir jugándose."""
        escena.dibujar_fondo = lambda *_a: 1 / 0
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)          # no debe lanzar
