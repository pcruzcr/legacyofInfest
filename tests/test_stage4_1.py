"""
Nivel 4-1 — El Cementerio Sagrado, reconstruido desde cero (AUD-467…470).

Segunda reconstrucción: la primera (AUD-462…466) heredaba el pozo vertical
del diseño anterior con una gradación de color encima, y el dueño del
proyecto la rechazó jugada — *«el nuevo nivel es horizontal completamente»*,
porque una repisa que ocupa casi todo el ancho de pantalla se lee como una
plataforma genérica, no como un pozo. Esta versión es un pasillo horizontal
de verdad, con terreno propio por sección, cutscene, diálogo y un easter egg
personal.

Estas pruebas no comprueban que las clases existan: mueven al jugador por
el mapa y miran el resultado — la misma disciplina que ya defendió la
versión anterior, aplicada a la geometría nueva.
"""
from __future__ import annotations

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
    # La cutscene de introducción bloquea el juego hasta que el jugador
    # confirma — como estas pruebas no simulan pulsaciones reales de tecla,
    # se salta a mano, igual que ya hace `_video`/`escena` con la carga del
    # escenario en el resto de las pruebas del proyecto. La cutscene en sí
    # (que el guion parsea sin errores) la cubre `TestLaCutsceneDeIntroduccion`.
    if getattr(sc, "_cutscenes", None) is not None:
        sc._cutscenes._activos.clear()
    yield sc
    sc.on_exit()


def _posicionar_sin_fisica(escena, columna: float, fila: float | None = None) -> None:
    """Pone al jugador en esa columna **sin simular física** y actualiza
    sólo la fase y la gradación — para las pruebas que necesitan un
    `avance` exacto dentro de la sección, sin depender de que la física
    real (gravedad, colisión) termine en la posición esperada."""
    from src.stages.stage4_1 import trazado

    if fila is None:
        fila = trazado.altura_de_colision(int(columna))
    x = columna * settings.TILE_SIZE
    y = fila * settings.TILE_SIZE
    escena._player.rect.center = (int(x), int(y))
    escena._player.position.update(float(x), float(y))
    escena._actualizar_fase()
    escena._actualizar_gradacion()


def _llevar_a(escena, columna: int, asentar: int = 200) -> None:
    """Coloca al jugador **de pie** en esa columna y deja que la física
    (gravedad) lo asiente sobre el suelo sólido real."""
    from src.stages.stage4_1 import trazado

    x = columna * settings.TILE_SIZE
    y = (trazado.altura_de_colision(columna) - 3) * trazado.TS
    escena._player.rect.topleft = (x, y)
    escena._player.position.update(float(x), float(y))
    escena._player.velocity.update(0.0, 0.0)
    for _ in range(asentar):
        escena.update(1 / 60)


def _dentro_de_la_fase(numero: int) -> int:
    from src.stages.stage4_1.fases import FASES

    return FASES[numero - 1].desde_columna + 6


class TestLaReglaDeOro:
    def test_no_hay_un_solo_enemigo(self, escena) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        enemigos = [e for e in escena._stage_data.entity_list
                    if isinstance(e, EnemyBase)]
        assert enemigos == []

    def test_ni_siquiera_una_entidad(self, escena) -> None:
        assert list(escena._stage_data.entity_list) == []

    def test_no_queda_ni_un_foso_ni_una_zona_de_dano(self, escena) -> None:
        assert escena._stage_data.death_pits == []
        assert list(escena._stage_data.hazard_zones) == []


class TestLaGeometriaEsHorizontal:
    """AUD-467 — lo que el veredicto del dueño exigía: un pasillo, no un
    pozo. Más ancho que alto, seis secciones de izquierda a derecha."""

    def test_es_mas_ancho_que_alto(self) -> None:
        from src.stages.stage4_1 import trazado

        assert trazado.MW > trazado.MH * 4, (
            "el 4-1 tiene que leerse como un pasillo horizontal, no como un pozo"
        )

    def test_seis_secciones_de_verdad(self) -> None:
        from src.stages.stage4_1 import trazado

        assert trazado.MW == trazado.ANCHO_SECCION * 6

    def test_el_suelo_es_firme_en_toda_la_longitud(self) -> None:
        """Cero `DeathPit` por construcción: el perfil de colisión nunca
        baja del nivel del suelo llano."""
        from src.stages.stage4_1 import trazado

        for col in range(trazado.MURO_ANCHO, trazado.MW - trazado.MURO_ANCHO):
            assert trazado.altura_de_colision(col) <= trazado.FILA_SUELO

    def test_las_seis_fases_se_alcanzan_en_orden(self, escena) -> None:
        vistos = []
        for numero in (1, 2, 3, 4, 5, 6):
            _llevar_a(escena, _dentro_de_la_fase(numero))
            vistos.append(escena.fase.numero)
        assert vistos == [1, 2, 3, 4, 5, 6], f"la progresión salió {vistos}"


class TestElTerrenoPropioPorSeccion:
    """Lo que el prototipo anterior no tenía: el suelo cambia de verdad
    entre secciones, no sólo el color encima de él (AUD-469)."""

    def test_seis_familias_de_baldosa_distintas(self) -> None:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import BALDOSAS_POR_FASE

        assert len(BALDOSAS_POR_FASE) == 6
        superficies = [gids[0] for gids in BALDOSAS_POR_FASE.values()]
        assert len(set(superficies)) == 6, "dos secciones comparten baldosa de suelo"

    def test_los_gid_apuntan_a_la_baldosa_que_dicen(self) -> None:
        """El contrato entre el mapa y la hoja (AUD-115, AUD-469)."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_all_assets import STAGE4_1_ORDEN
        from generate_stage4_1 import (
            BOSQUE,
            CALAVERA,
            CRIPTA,
            CRUZ,
            HUESOS,
            LAPIDA_ALTA,
            LAPIDA_BAJA,
            MURO,
            QUEMADO,
            SAGRADA,
            TUMBAS,
            VACIO,
        )

        # `vacio` no entra: su GID es 0 y no ocupa ninguna casilla real de
        # la hoja — es el «sin baldosa» de Tiled, y `ORDEN[0 - 1]` sería el
        # último elemento de la lista por indexado negativo de Python, no
        # una comprobación real.
        esperado = {
            "muro": MURO, "cripta": CRIPTA, "bosque": BOSQUE,
            "huesos": HUESOS, "quemado": QUEMADO, "tumbas": TUMBAS,
            "sagrada": SAGRADA, "lapida_alta": LAPIDA_ALTA,
            "lapida_baja": LAPIDA_BAJA, "cruz": CRUZ, "calavera": CALAVERA,
        }
        assert VACIO == 0
        for nombre, gid in esperado.items():
            assert STAGE4_1_ORDEN[gid - 1] == nombre

    def test_la_hoja_tiene_el_tamano_que_declara_el_mapa(self) -> None:
        import sys
        from pathlib import Path

        from PIL import Image

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import TS_IMAGEN_PX_X, TS_IMAGEN_PX_Y

        hoja = Image.open("assets/tilesets/tileset_stage4_1.png")
        assert hoja.size == (TS_IMAGEN_PX_X, TS_IMAGEN_PX_Y)


class TestLasSuperficiesDeLaFase2:
    """Musgo y lodo, juntos en el mismo tramo — el guion los pide así."""

    def _zonas(self, escena):
        from src.framework.ecs import ZonaDeFriccion

        return [z for _, z in escena._mundo.cada(ZonaDeFriccion)]

    def test_hay_musgo_y_lodo(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        musgo = sum(1 for _i, _a, m in trazado.SEGMENTOS_FASE2 if m == "musgo")
        lodo = sum(1 for _i, _a, m in trazado.SEGMENTOS_FASE2 if m == "lodo")
        arrastres = [z for z in self._zonas(escena) if z.arrastre]
        frenos = [z for z in self._zonas(escena) if z.multiplicador != 1.0]
        assert len(arrastres) == musgo
        assert len(frenos) == lodo
        assert all(0.0 < z.multiplicador < 1.0 for z in frenos)

    def test_los_segmentos_caen_en_la_fase_2(self) -> None:
        from src.stages.stage4_1 import trazado

        for inicio, ancho, _material in trazado.SEGMENTOS_FASE2:
            assert trazado.fase_de_la_columna(inicio) == 2
            assert trazado.fase_de_la_columna(inicio + ancho - 1) == 2


class TestLaLomaDeLaFase3:
    """AUD-297/470 — un `Slope` de verdad, y la colisión bajo la rampa se
    queda plana para que el `Slope` sea quien suba al jugador."""

    def test_hay_exactamente_dos_slopes(self, escena) -> None:
        assert len(escena._stage_data.pendientes) == 2

    def test_las_dos_estan_en_la_fase_3(self) -> None:
        from src.stages.stage4_1 import trazado

        for col, _fila, _ancho, _alto, _sube in trazado.loma():
            assert trazado.fase_de_la_columna(col) == 3

    def test_la_colision_bajo_la_rampa_es_plana(self) -> None:
        """El bug real que encontró jugarlo (AUD-470): un escalón sólido
        por columna bloqueaba el paso antes de que el `Slope` interviniera."""
        from src.stages.stage4_1 import trazado

        alturas = {
            trazado.altura_de_colision(c)
            for c in range(trazado.LOMA_INICIO_SUBIDA, trazado.LOMA_FIN_SUBIDA)
        }
        assert alturas == {trazado.FILA_SUELO}, (
            f"la colisión bajo la rampa ascendente no es plana: {alturas}"
        )

    def test_se_sube_de_verdad_caminando(self, escena) -> None:
        """Recorrido real con física: entra por la izquierda de la rampa y
        camina hacia la derecha; a mitad de rampa tiene que haber subido."""
        from src.stages.stage4_1 import trazado

        col_entrada = trazado.LOMA_INICIO_SUBIDA - 5
        _llevar_a(escena, col_entrada)
        fila_inicial = escena._player.rect.centery

        im = escena.context.input_manager
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        for _ in range(150):  # 2.5 s caminando a la derecha
            escena.update(1 / 60)
        im.pump([pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT)])

        subio = fila_inicial - escena._player.rect.centery
        assert subio > 40, (
            f"subió {subio} px en 2.5 s de caminata sobre la rampa — "
            f"debería subir bastante más que eso"
        )


class TestElVientoDeLaFase3:
    def test_hay_una_zona_de_viento_en_la_fase_3(self, escena) -> None:
        from src.framework.ecs import ZonaDeViento
        from src.stages.stage4_1 import trazado

        vientos = [z for _, z in escena._mundo.cada(ZonaDeViento)]
        assert len(vientos) == 1
        centro_col = vientos[0].rect.centerx // settings.TILE_SIZE
        assert trazado.fase_de_la_columna(centro_col) == 3


class TestLaGradacionYElSonidoPorFase:
    def test_la_gradacion_se_aproxima_al_objetivo_al_final_del_tramo(
        self, escena,
    ) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import IDENTIDAD

        for fase in FASES:
            _posicionar_sin_fisica(
                escena, fase.desde_columna + trazado.ANCHO_SECCION - 1)
            objetivo = fase.gradacion if fase.gradacion is not None else IDENTIDAD
            actual = escena._post_processing._color_grading
            actual = actual if actual is not None else IDENTIDAD
            diferencia = max(abs(a - b) for a, b in zip(actual, objetivo, strict=True))
            assert diferencia <= 8, (
                f"Fase {fase.numero}: gradación {actual} lejos de {objetivo}"
            )

    def test_la_gradacion_no_salta_de_golpe_al_entrar(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import IDENTIDAD

        fase1, fase2 = FASES[0], FASES[1]
        _posicionar_sin_fisica(escena, fase1.desde_columna + 10)
        _posicionar_sin_fisica(escena, fase2.desde_columna)
        actual = escena._post_processing._color_grading
        actual = actual if actual is not None else IDENTIDAD
        diferencia = max(abs(a - b) for a, b in zip(actual, IDENTIDAD, strict=True))
        assert diferencia < 40

    def test_cada_fase_pide_su_sonido(self) -> None:
        from src.stages.stage4_1.fases import FASES

        esperado_none = {1}
        for fase in FASES:
            if fase.numero in esperado_none:
                assert fase.sonido_ambiente is None
            else:
                assert fase.sonido_ambiente is not None

    def test_la_fase_3_suena_a_tormenta(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase3 = FASES[2]
        _llevar_a(escena, fase3.desde_columna + 2)
        ruta = str(settings.ASSETS_DIR / fase3.sonido_ambiente)
        assert ruta in escena.audio._ambient_sounds
        assert "storm_ambient" in ruta


class TestElSilencioYElShakeDeLaFase4:
    def test_dispara_una_vez_pasada_la_mitad(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        objetivo = fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION)
        _llevar_a(escena, objetivo)
        assert escena._shake_disparado is True
        assert escena._weather.climate == "clear"
        assert escena.audio._ambient_active is False

    def test_no_dispara_antes_de_mitad_de_tramo(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        _llevar_a(escena, fase4.desde_columna + 5)
        assert escena._shake_disparado is False


class TestLaSombraDelGavilan:
    def test_solo_existe_en_la_fase_4(self) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            assert fase.sombra_de_ave == (fase.numero == 4)

    def test_cruza_tras_el_silencio(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        objetivo = fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION)
        _llevar_a(escena, objetivo)
        escena._proxima_sombra = 0.0
        for _ in range(30):
            escena.update(1 / 60)
        assert escena._sombra_progreso >= 0.0


class TestLaSerpienteDeFondo:
    def test_solo_en_la_fase_3(self) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            assert fase.serpiente_de_fondo == (fase.numero == 3)

    def test_no_revienta_dibujandola(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        _llevar_a(escena, FASES[2].desde_columna + 20)
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        escena.dibujar_fondo(lienzo, pygame.Vector2(0, 0))


class TestElEasterEggPersonal:
    """§7 del diseño (AUD-467): dos lápidas, un fantasma sobrio. Sin datos
    inventados — sólo los dos nombres que dio el dueño del proyecto."""

    def test_los_dos_nombres_son_los_que_dio_el_dueno(self) -> None:
        from src.stages.stage4_1 import trazado

        assert trazado.NOMBRE_LAPIDA_TERESA == "Teresa Murillo"
        assert trazado.NOMBRE_LAPIDA_HUGO == "Hugo Salazar Castillo"

    def test_las_dos_lapidas_estan_en_la_fase_1(self) -> None:
        from src.stages.stage4_1 import trazado

        assert trazado.fase_de_la_columna(trazado.COLUMNA_LAPIDA_TERESA) == 1
        assert trazado.fase_de_la_columna(trazado.COLUMNA_LAPIDA_HUGO) == 1

    def test_el_tmx_declara_los_dos_nombres(self) -> None:
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        assert "Teresa Murillo" in xml
        assert "Hugo Salazar Castillo" in xml

    def test_el_fantasma_es_distinto_de_los_tres_espiritus(self) -> None:
        from src.stages.stage4_1 import siluetas

        assert siluetas.BLANCO_RECUERDO not in (
            siluetas.VERDE_ESPECTRAL, siluetas.BLANCO_CEGUA,
        )
        assert callable(siluetas._fantasma)

    def test_no_revienta_dibujando_el_fantasma(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _llevar_a(escena, trazado.COLUMNA_LAPIDA_TERESA)
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        escena.dibujar_fondo(lienzo, pygame.Vector2(0, 0))


class TestLaCutsceneDeIntroduccion:
    """AUD-136/467 — dispara sola al empezar, sin código nuevo."""

    def test_hay_una_cutscene_declarada(self) -> None:
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        assert 'type="Cutscene"' in xml

    def test_el_guion_no_tiene_errores_de_sintaxis(self) -> None:
        """Se reescribió una vez (AUD-470) porque la primera versión usaba
        `dialogo texto;...` y `camara . .`, que no es la sintaxis real de
        `cutscene_guion.py`. Esto lo comprueba contra el analizador de
        verdad, no a ojo."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import _objetos

        from src.framework.stage.cutscene_guion import ContextoDeGuion, analizar_guion

        objetos_xml = "\n".join(_objetos())
        inicio = objetos_xml.index('type="Cutscene"')
        bloque = objetos_xml[inicio:objetos_xml.index("</object>", inicio)]
        # El guion vive en una <property name="guion" value="...">.
        marca = 'name="guion" value="'
        i0 = bloque.index(marca) + len(marca)
        i1 = bloque.index('"', i0)
        guion = (bloque[i0:i1].replace("&#10;", "\n").replace("&quot;", '"')
                 .replace("&lt;", "<").replace("&amp;", "&"))
        _script, errores = analizar_guion(guion, ContextoDeGuion())
        assert errores == [], f"el guion de la cutscene tiene errores: {errores}"

    def test_cutscene_activa_al_empezar(self) -> None:
        """Sin pasar por el fixture `escena`, que la salta a propósito para
        el resto de las pruebas: aquí se comprueba que de verdad se dispara
        sola."""
        import pygame as pg

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage4_1.stage4_1 import Stage4_1

        pg.init()
        pg.font.init()
        if pg.display.get_surface() is None:
            pg.display.set_mode((800, 600))
        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        sc = Stage4_1(ctx)
        ctx.scene_manager.push(sc)
        try:
            assert len(sc._cutscenes._activos) == 1
        finally:
            sc.on_exit()


class TestElDialogoDeLosTresEspiritus:
    """AUD-244/470 — los árboles se cargan de `data/dialogues/stage4_1.json`."""

    def test_los_tres_arboles_se_cargan(self, escena) -> None:
        assert set(escena._arboles_de_dialogo.keys()) == {
            "venado", "rey_terciopelo", "gavilan",
        }

    def test_cada_fase_con_espiritu_tiene_su_dialogo(self) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            if fase.espiritu is not None:
                assert fase.dialogo_id is not None
            else:
                assert fase.numero != 5 or fase.dialogo_id is None

    def test_el_fichero_es_json_valido_con_tres_arboles(self) -> None:
        import json
        from pathlib import Path

        datos = json.loads(
            Path("data/dialogues/stage4_1.json").read_text(encoding="utf-8"))
        assert isinstance(datos, list)
        assert len(datos) == 3
        for arbol in datos:
            assert arbol["id"] in ("venado", "rey_terciopelo", "gavilan")
            assert arbol["start"] in arbol["nodes"]


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


class TestElNivelSePuedeJugar:
    def test_tiene_salida_spawn_y_checkpoints(self, escena) -> None:
        assert escena._stage_data.next_trigger is not None
        assert escena._stage_data.spawn_point is not None
        assert len(escena._stage_data.checkpoints) >= 1

    def test_los_checkpoints_no_dejan_tramos_largos(self, escena) -> None:
        from itertools import pairwise

        from src.stages.stage4_1 import trazado

        puntos = sorted(trazado.checkpoints(), key=lambda p: p[0])
        ts = settings.TILE_SIZE
        for (c1, _f1), (c2, _f2) in pairwise(puntos):
            assert (c2 - c1) * ts <= 500

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.ZONE == 4
        assert escena._stage_data.zone == Stage4_1.ZONE


class TestCabeEnElPresupuestoDeFotograma:
    PRESUPUESTO_MS = 15.0
    RONDAS = 5

    def _medir(self, escena, veces: int = 15) -> float:
        import statistics
        import time

        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)
        muestras = []
        for _ in range(self.RONDAS):
            t0 = time.perf_counter()
            for _ in range(veces):
                escena.draw(lienzo)
            muestras.append((time.perf_counter() - t0) / veces * 1000.0)
        return statistics.median(muestras)

    def test_el_dibujo_cabe(self, escena) -> None:
        _llevar_a(escena, _dentro_de_la_fase(4))  # la fase con más dibujo de fondo
        assert self._medir(escena) < self.PRESUPUESTO_MS


class TestElGanchoDeFondoLlegaAlEscenario:
    def test_stage_scene_ofrece_el_gancho(self) -> None:
        from src.framework.scenes.stage_scene import StageScene

        assert hasattr(StageScene, "dibujar_fondo")

    def test_el_4_1_lo_sobreescribe(self) -> None:
        from src.framework.scenes.stage_scene import StageScene
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.dibujar_fondo is not StageScene.dibujar_fondo

    def test_un_fondo_que_falla_no_tumba_el_fotograma(self, escena) -> None:
        escena.dibujar_fondo = lambda *_a: 1 / 0
        lienzo = pygame.Surface((800, 600))
        escena.draw(lienzo)
