"""
Nivel 4-1 — El Cementerio Sagrado (AUD-462/463/464).

Reemplaza al diseño anterior de La Cegua. Un nivel sin enemigos es un nivel
donde **todo lo que hay es atmósfera**, y la atmósfera es justo lo que se
rompe sin que nadie se entere: un clima que no cambia, una gradación de color
que no interpola o un shake que dispara dos veces se ven igual de bien en una
captura de pantalla.

Así que estas pruebas no comprueban que las clases existan: mueven al
jugador por el mapa y **miran el resultado**.

Lo que defienden
-----------------
1. **La regla de oro.** Cero enemigos, contados sobre el mapa cargado.
2. **Cero trampas.** Cero `DeathPit`, cero `HazardZone` fija.
3. **Que el fondo cambie de piel.** Seis fases, cada una con su clima y su
   gradación de color — interpolada, no cortada en seco.
4. **Que los tres espíritus asciendan.** Aparecen, testifican y se
   desvanecen hacia arriba, cada uno en su fase.
5. **Que la loma de la Fase 3 sea un slope de verdad**, no un adorno.
6. **Que el silencio de la Fase 4 dispare el shake una sola vez.**
7. **Que la luna de la Fase 5 oscile de verdad.**
8. **Que las grietas de la Fase 6 se enciendan al paso y se apaguen solas.**
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
    yield sc
    sc.on_exit()


def _llevar_a(escena, fila: int, columna: int = 30, asentar: int = 400) -> None:
    """Coloca al jugador **de pie** en esa fila del pozo y espera a la cámara.

    `fila` es la fila de la repisa: el jugador se coloca con los **pies**
    ahí (no la esquina superior), o si no cae de inmediato y las pruebas que
    miden distancias a una luz o una zona de fricción miden una caída, no una
    posición. La espera no es un número fijo de fotogramas: la cámara
    persigue con interpolación y aquí tiene más de 4.500 px de recorrido
    vertical.
    """
    x = columna * settings.TILE_SIZE
    y = fila * settings.TILE_SIZE - escena._player.rect.height
    escena._player.rect.topleft = (x, y)
    escena._player.position.update(float(x), float(y))
    escena._player.velocity.update(0.0, 0.0)
    for _ in range(asentar):
        escena.update(1 / 60)
        objetivo = escena._player.rect.centery - settings.INTERNAL_HEIGHT / 2
        if abs(escena._camera.offset.y - objetivo) < 2.0:
            break


def _posicionar_sin_fisica(escena, fila: float, columna: int = 30) -> None:
    """Pone al jugador en esa fila **sin simular física**, y actualiza sólo
    la fase y la gradación.

    Las pruebas de gradación necesitan un `avance` exacto dentro del tramo.
    `_llevar_a` deja caer al jugador con gravedad real durante cientos de
    fotogramas, y entre dos repisas eso puede desplazarlo varias filas antes
    de asentarse — bastante para que una prueba que pide «recién entrando en
    la fase» mida en realidad varias filas más abajo. Aquí se fija la
    posición a mano y se llaman directamente los dos métodos que dependen de
    ella, sin física de por medio.
    """
    x = columna * settings.TILE_SIZE
    y = fila * settings.TILE_SIZE
    escena._player.rect.center = (x, int(y))
    escena._player.position.update(float(x), float(y))
    escena._actualizar_fase()
    escena._actualizar_gradacion()


def _dentro_de_la_fase(numero: int) -> int:
    """Una fila que cae dentro de la fase pedida, 1 a 6.

    Se calcula de la tabla y no se escribe a mano — una prueba que sigue en
    verde midiendo el sitio equivocado es peor que una que falla.
    """
    from src.stages.stage4_1.fases import FASES

    return FASES[numero - 1].desde_fila + 6


class TestLaReglaDeOro:
    """«Si el nivel aburre, se arregla con más atmósfera, no con combate.»"""

    def test_no_hay_un_solo_enemigo(self, escena) -> None:
        from src.framework.entities.enemy_base import EnemyBase

        enemigos = [e for e in escena._stage_data.entity_list
                    if isinstance(e, EnemyBase)]
        assert enemigos == [], (
            f"el 4-1 tiene {len(enemigos)} enemigos y su regla de oro es cero"
        )

    def test_ni_siquiera_una_entidad(self, escena) -> None:
        """Se cuenta la lista entera, no sólo lo que hereda de `EnemyBase`."""
        assert list(escena._stage_data.entity_list) == []

    def test_las_siluetas_no_son_entidades(self, escena) -> None:
        """El canon: «no atacan. Testifican.» Las tres son Venado, Rey
        Terciopelo (la serpiente) y Gavilán, en ese orden — el mismo orden
        que usa `Fase.espiritu` como índice."""
        from src.stages.stage4_1 import siluetas

        assert [n for n, _f in siluetas.ESPIRITUS] == ["venado", "serpiente", "gavilan"]
        for _nombre, forma in siluetas.ESPIRITUS:
            assert callable(forma)


class TestNoHayTrampas:
    """El 4-1 hereda la regla del rediseño anterior (AUD-225): un cementerio
    se baja, y caer es el movimiento, no el castigo."""

    def test_no_queda_ni_un_foso(self, escena) -> None:
        assert escena._stage_data.death_pits == []

    def test_no_queda_ni_una_zona_de_dano(self, escena) -> None:
        assert list(escena._stage_data.hazard_zones) == []

    def test_el_mapa_no_declara_esos_tipos(self) -> None:
        from pathlib import Path

        xml = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        for tipo in ('type="DeathPit"', 'type="HazardZone"'):
            assert tipo not in xml, f"el TMX sigue declarando {tipo}"


class TestLasSuperficiesSeVen:
    """La Fase 2 (El Venado) es donde vive el musgo y el lodo — juntos,
    porque el guion los pide en el mismo tramo."""

    def _zonas(self, escena):
        from src.framework.ecs import ZonaDeFriccion

        return [z for _, z in escena._mundo.cada(ZonaDeFriccion)]

    def test_cada_repisa_de_musgo_arrastra(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        arrastres = [z for z in self._zonas(escena) if z.arrastre]
        assert len(arrastres) == len(trazado.INDICES_MUSGO)

    def test_cada_repisa_de_lodo_frena(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        frenos = [z for z in self._zonas(escena) if z.multiplicador != 1.0]
        assert len(frenos) == len(trazado.INDICES_LODO)
        assert all(0.0 < z.multiplicador < 1.0 for z in frenos)

    def test_musgo_y_lodo_estan_en_la_fase_2(self) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase2 = FASES[1]
        lista = trazado.repisas()
        for indice in (*trazado.INDICES_MUSGO, *trazado.INDICES_LODO):
            _x0, _ancho, fila = lista[indice]
            assert trazado.fase_de_la_fila(fila) == fase2.numero, (
                f"la repisa {indice} (fila {fila}) no cae en la Fase 2"
            )

    def test_el_musgo_arrastra_hacia_el_hueco_y_no_contra_el(self) -> None:
        from src.stages.stage4_1 import trazado

        lista = trazado.repisas()
        for i in trazado.INDICES_MUSGO:
            x0, ancho, _fila = lista[i]
            hacia_la_derecha = x0 == trazado.MURO_ANCHO
            hueco_a_la_derecha = x0 + ancho < trazado.MW - trazado.MURO_ANCHO
            assert hacia_la_derecha == hueco_a_la_derecha

    def test_los_gid_apuntan_a_la_baldosa_que_dicen(self) -> None:
        """El contrato entre el mapa y la hoja de baldosas (AUD-237, vigente
        tras el rediseño: el tileset no cambió, sólo el guion)."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_all_assets import CEM_ORDEN
        from generate_stage4_1 import (
            LODO,
            LODO_RELLENO,
            MURO,
            MUSGO,
            MUSGO_RELLENO,
            PIEDRA,
            RELLENO,
        )

        esperado = {
            "losa": PIEDRA, "relleno": RELLENO, "muro": MURO,
            "musgo": MUSGO, "musgo_relleno": MUSGO_RELLENO,
            "lodo": LODO, "lodo_relleno": LODO_RELLENO,
        }
        for nombre, gid in esperado.items():
            assert CEM_ORDEN[gid - 1] == nombre, (
                f"el GID {gid} debería ser «{nombre}» y en la hoja es "
                f"«{CEM_ORDEN[gid - 1]}»"
            )

    def test_la_hoja_del_cementerio_es_la_que_declara_el_mapa(self) -> None:
        import sys
        from pathlib import Path

        from PIL import Image

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import TILESET, TS_COLUMNAS, TS_IMAGEN_PX, TS_TOTAL

        assert TILESET.endswith("tileset_cemetery.png")
        hoja = Image.open("assets/tilesets/tileset_cemetery.png")
        assert hoja.size == (TS_IMAGEN_PX, TS_IMAGEN_PX)
        assert TS_COLUMNAS * TS_COLUMNAS == TS_TOTAL

    def test_la_baldosa_pintada_coincide_con_la_zona(self) -> None:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_stage4_1 import BALDOSAS, _terreno

        from src.stages.stage4_1 import trazado

        g = _terreno()
        for x0, ancho, fila, material in trazado.superficies():
            esperada = BALDOSAS[material][0]
            fila_pintada = {g[fila][x] for x in range(x0, x0 + ancho)}
            assert fila_pintada == {esperada}


class TestSuenaAOrgano:
    """AUD-227. El BGM sigue siendo el mismo tema —el rediseño no tocó el
    audio— así que esta clase se hereda entera del diseño anterior."""

    @staticmethod
    def _muestras():
        import struct
        import wave

        import numpy as np

        with wave.open("assets/music/bgm_final_approach.wav") as w:
            n, rate = w.getnframes(), w.getframerate()
            crudo = struct.unpack(f"<{n}h", w.readframes(n))
        return np.array(crudo, dtype=float) / 32768.0, rate

    def test_los_parciales_son_multiplos_enteros_de_la_nota(self) -> None:
        import numpy as np

        x, rate = self._muestras()
        tramo = x[int(1.0 * rate):int(3.0 * rate)]
        esp = np.abs(np.fft.rfft(tramo * np.hanning(len(tramo))))
        frec = np.fft.rfftfreq(len(tramo), 1.0 / rate)
        orden = np.argsort(esp)[::-1]
        picos: list[float] = []
        for i in orden:
            f = float(frec[i])
            if f < 30.0 or any(abs(f - p) < 4.0 for p in picos):
                continue
            picos.append(f)
            if len(picos) == 10:
                break

        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from generate_all_assets import ORGANO_ACORDES, ORGANO_PEDAL

        fundamentales = (*ORGANO_ACORDES[0], ORGANO_PEDAL[0])
        for pico in picos:
            assert any(
                abs(pico / f - round(pico / f)) < 0.04 and round(pico / f) >= 1
                for f in fundamentales
            ), f"el pico de {pico:.1f} Hz no es múltiplo entero de ninguna nota"

    ATAQUES_POR_SEGUNDO = 1.5

    def test_no_lleva_percusion(self) -> None:
        import numpy as np

        x, rate = self._muestras()
        ventana = int(rate * 0.02)
        energia = np.array([
            float(np.sqrt((x[i:i + ventana] ** 2).mean()))
            for i in range(0, len(x) - ventana, ventana)
        ])
        saltos = np.abs(np.diff(energia))
        golpes = int((saltos > 4.0 * np.median(saltos)).sum())
        por_segundo = golpes / (len(x) / rate)
        assert por_segundo <= self.ATAQUES_POR_SEGUNDO

    def test_el_nivel_apunta_a_esa_pista(self, escena) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.BGM_TRACK == "bgm_final_approach"
        assert escena._stage_data.bgm_track == Stage4_1.BGM_TRACK


class TestElLodoFrenaIgualEnCualquierMaquina:
    """AUD-236. Heredada sin cambios: la física del lodo no la tocó el
    rediseño, sólo en qué fase vive."""

    def _recorrido(self, fps: int, con_entrada: bool) -> float:
        import pygame as pg

        from src.framework.ecs import (
            Transform,
            Velocidad,
            World,
            ZonaDeFriccion,
            systems,
        )
        from src.stages.stage4_1.trazado import FRENO_DEL_LODO

        dt = 1.0 / fps
        mundo = World()
        entidad = mundo.crear(
            Transform(posicion=pg.Vector2(0, 0), rect=pg.Rect(0, 0, 16, 32)),
            Velocidad(pg.Vector2(90, 0)),
        )
        mundo.crear(ZonaDeFriccion(
            rect=pg.Rect(-500, -500, 4000, 4000), multiplicador=FRENO_DEL_LODO,
        ))
        v = mundo.obtener(entidad, Velocidad)
        recorrido = 0.0
        for _ in range(fps):
            if con_entrada:
                v.v.x = 90.0
            systems.sistema_friccion(mundo, dt)
            recorrido += v.v.x * dt
        return recorrido

    def test_andando_recorre_lo_mismo_a_cualquier_tasa(self) -> None:
        medidas = [self._recorrido(fps, True) for fps in (30, 60, 120)]
        assert max(medidas) - min(medidas) < 0.5

    def test_frena_pero_deja_andar(self) -> None:
        andado = self._recorrido(60, True)
        assert 60.0 < andado < 88.0

    def test_deslizarse_sin_empuje_si_depende_de_la_tasa(self) -> None:
        lento = self._recorrido(30, False)
        rapido = self._recorrido(120, False)
        assert lento > rapido * 2


class TestElPozoNoEncierraANadie:
    """Un descenso con un sitio del que no se sale es peor que un foso."""

    def test_repisas_consecutivas_se_solapan(self) -> None:
        from itertools import pairwise

        from src.stages.stage4_1 import trazado

        for (x0, an, fila), (sx, san, sfila) in pairwise(trazado.repisas()):
            solape = min(x0 + an, sx + san) - max(x0, sx)
            assert solape > 0, (
                f"las repisas de las filas {fila} y {sfila} no se solapan"
            )

    def test_se_puede_volver_a_subir(self) -> None:
        from src.framework.stage.level_metrics import JumpEnvelope
        from src.stages.stage4_1 import trazado

        envolvente = JumpEnvelope.from_settings()
        desnivel = trazado.FILAS_POR_REPISA * trazado.TS
        assert desnivel < envolvente.max_height

    def test_el_jugador_cabe_entre_dos_repisas(self) -> None:
        from src.stages.stage4_1 import trazado

        libre = (trazado.FILAS_POR_REPISA - trazado.GROSOR_REPISA) * trazado.TS
        assert libre >= 48


class TestElNivelSePuedeJugar:
    def test_tiene_salida(self, escena) -> None:
        assert escena._stage_data.next_trigger is not None

    def test_tiene_punto_de_aparicion_y_checkpoints(self, escena) -> None:
        assert escena._stage_data.spawn_point is not None
        assert len(escena._stage_data.checkpoints) >= 1

    def test_los_checkpoints_no_dejan_tramos_largos(self, escena) -> None:
        """El calificador recomienda 500 px entre dos checkpoints."""
        from itertools import pairwise

        from src.stages.stage4_1 import trazado

        puntos = sorted(trazado.checkpoints(), key=lambda p: p[1])
        ts = settings.TILE_SIZE
        for (_cx1, f1), (_cx2, f2) in pairwise(puntos):
            tramo = (f2 - f1) * ts
            assert tramo <= 500, f"tramo de {tramo} px entre checkpoints"

    def test_el_mapa_tiene_el_tamano_minimo(self, escena) -> None:
        ancho, alto = escena._stage_data.map_pixel_size
        assert ancho * alto >= 1600 * 608
        assert alto > ancho, "el 4-1 es un descenso: debe ser más alto que ancho"

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.ZONE == 4
        assert escena._stage_data.zone == Stage4_1.ZONE


class TestLasSeisFases:
    """Sin esto el nivel es un pasillo con decoración."""

    def test_las_seis_fases_se_alcanzan_en_orden(self, escena) -> None:
        vistos = []
        for numero in (1, 2, 3, 4, 5, 6):
            _llevar_a(escena, _dentro_de_la_fase(numero))
            vistos.append(escena.fase.numero)
        assert vistos == [1, 2, 3, 4, 5, 6], f"la progresión salió {vistos}"

    def test_cada_fase_ocupa_al_menos_una_pantalla(self) -> None:
        from src.stages.stage4_1.trazado import ALTO_FASE

        pantalla = settings.INTERNAL_HEIGHT // settings.TILE_SIZE
        assert ALTO_FASE >= pantalla

    def test_el_clima_cambia_con_la_fase(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            if fase.numero == 4:
                continue  # a mitad de la Fase 4 el clima cambia a "clear"
            _llevar_a(escena, fase.desde_fila + 2)
            assert escena._weather.climate == fase.clima, (
                f"la Fase {fase.numero} pide clima {fase.clima!r} y está en "
                f"{escena._weather.climate!r}"
            )

    def test_la_gradacion_se_aproxima_al_objetivo_al_final_del_tramo(
        self, escena,
    ) -> None:
        """Cerca del final de cada fase, la interpolación ya casi llegó."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import IDENTIDAD

        for fase in FASES:
            _posicionar_sin_fisica(escena, fase.desde_fila + trazado.ALTO_FASE - 1)
            objetivo = fase.gradacion if fase.gradacion is not None else IDENTIDAD
            actual = escena._post_processing._color_grading
            actual = actual if actual is not None else IDENTIDAD
            diferencia = max(abs(a - b) for a, b in zip(actual, objetivo, strict=True))
            assert diferencia <= 8, (
                f"Fase {fase.numero}: gradación {actual} lejos del objetivo "
                f"{objetivo} (dif {diferencia})"
            )

    def test_la_gradacion_no_salta_de_golpe_al_entrar(self, escena) -> None:
        """Al entrar en la Fase 2, la gradación debe seguir cerca de la de la
        Fase 1 (color pleno) — no saltar directo a blanco y negro."""
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import IDENTIDAD

        fase1, fase2 = FASES[0], FASES[1]
        _posicionar_sin_fisica(escena, fase1.desde_fila + 10)  # asienta la Fase 1
        _posicionar_sin_fisica(escena, fase2.desde_fila)       # el primerísimo paso
        actual = escena._post_processing._color_grading
        actual = actual if actual is not None else IDENTIDAD
        diferencia = max(abs(a - b) for a, b in zip(actual, IDENTIDAD, strict=True))
        assert diferencia < 40, (
            f"la gradación saltó a {actual} nada más entrar en la Fase 2"
        )

    def test_el_tinte_vintage_solo_esta_en_la_fase_4(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        _posicionar_sin_fisica(escena, FASES[0].desde_fila + trazado.ALTO_FASE - 1)
        assert escena._post_processing._tint_alpha == pytest.approx(0.0, abs=0.01)
        _posicionar_sin_fisica(escena, FASES[3].desde_fila + trazado.ALTO_FASE - 1)
        assert escena._post_processing._tint_alpha > 0.05


class TestLosEspiritusAscienden:
    """Venado (Fase 2), Rey Terciopelo (Fase 3) y Gavilán (Fase 4) — «no
    atacan, testifican», y luego ascienden."""

    def test_indice_del_espiritu_por_fase(self) -> None:
        from src.stages.stage4_1.fases import FASES

        esperado = {1: None, 2: 0, 3: 1, 4: 2, 5: None, 6: None}
        for fase in FASES:
            assert fase.espiritu == esperado[fase.numero], (
                f"Fase {fase.numero}: espíritu {fase.espiritu}, se esperaba "
                f"{esperado[fase.numero]}"
            )

    def test_el_fundido_es_cero_al_entrar_y_al_salir(self, escena) -> None:
        assert escena._fundido_del_espiritu(0.0) == 0.0
        assert escena._fundido_del_espiritu(1.0) == 0.0
        assert escena._fundido_del_espiritu(0.5) == 1.0

    def test_no_revienta_en_una_fase_sin_espiritu(self, escena) -> None:
        """La Fase 1, la 5 y la 6 no tienen espíritu (`fase.espiritu is
        None`); `dibujar_fondo` tiene que poder no dibujar nada sin lanzar."""
        from src.stages.stage4_1.fases import FASES

        fase1 = FASES[0]
        assert fase1.espiritu is None
        _llevar_a(escena, fase1.desde_fila + 20)
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        escena.dibujar_fondo(lienzo, pygame.Vector2(0, 0))  # no debe lanzar


class TestLaLomaDeLaFase3:
    """El guion pide «ascender por lomas utilizando slopes» — un `Slope` de
    verdad (AUD-297), no una inversión del eje del pozo."""

    def test_hay_exactamente_una_loma(self, escena) -> None:
        assert len(escena._stage_data.pendientes) == 1

    def test_la_loma_esta_en_la_fase_3(self) -> None:
        from src.stages.stage4_1 import trazado

        _col, fila, _ancho, _alto, _sube = trazado.loma()
        assert trazado.fase_de_la_fila(fila) == 3

    def test_la_loma_no_tapa_el_hueco_entero(self) -> None:
        from src.stages.stage4_1 import trazado

        _inicio, ancho_hueco = trazado.hueco_de(trazado.LOMA_INDICE)
        _col, _fila, ancho_loma, _alto, _sube = trazado.loma()
        assert ancho_loma < ancho_hueco, (
            "la loma tapa el hueco entero: nadie podría seguir cayendo por al "
            "lado"
        )

    def test_sube_es_un_valor_valido(self) -> None:
        from src.stages.stage4_1 import trazado

        *_resto, sube = trazado.loma()
        assert sube in ("derecha", "izquierda")


class TestElVientoDeLaFase3:
    def test_hay_una_zona_de_viento_en_la_fase_3(self, escena) -> None:
        from src.framework.ecs import ZonaDeViento
        from src.stages.stage4_1 import trazado

        vientos = [z for _, z in escena._mundo.cada(ZonaDeViento)]
        assert len(vientos) == 1
        rect = vientos[0].rect
        fila_media = (rect.centery) // settings.TILE_SIZE
        assert trazado.fase_de_la_fila(fila_media) == 3


class TestElSilencioYElShake:
    """A mitad de la Fase 4, el clima calla de golpe y la cámara sacude una
    sola vez — sin causa visible."""

    def test_no_dispara_antes_de_mitad_de_tramo(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        _llevar_a(escena, fase4.desde_fila + 5)  # bien al principio
        assert escena._shake_disparado is False

    def test_dispara_una_vez_pasada_la_mitad(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        objetivo = fase4.desde_fila + int(0.6 * 48)
        _llevar_a(escena, objetivo)
        assert escena._shake_disparado is True
        assert escena._weather.climate == "clear"
        assert escena._ambient_particles.rate == 0.0

    def test_no_dispara_en_otras_fases(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            if fase.numero == 4:
                continue
            _llevar_a(escena, fase.desde_fila + int(0.6 * 48))
            assert escena._shake_disparado is False, (
                f"la Fase {fase.numero} disparó el shake y no le toca"
            )


class TestElCicloDeLaLuna:
    """La Fase 5 (La Planicie de los Muertos) es la única con luz ambiente
    que oscila en vez de quedarse fija."""

    def test_solo_la_fase_5_oscila(self) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            assert fase.luna_intermitente == (fase.numero == 5)

    def test_el_ambiente_se_mueve_dentro_de_los_limites(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase5 = FASES[4]
        _llevar_a(escena, fase5.desde_fila + 2)
        valores = []
        for _ in range(400):
            escena.update(1 / 60)
            valores.append(escena._ambiente_base)
        assert min(valores) < 0.15
        assert max(valores) > 0.35
        assert max(valores) - min(valores) > 0.2, (
            "el ambiente de la Fase 5 no osciló: la luna no hace nada"
        )


class TestLasGrietasDeLaFase6:
    """Se encienden al paso y se apagan solas — un rastro, no una barra de
    progreso acumulada."""

    def test_hay_una_luz_por_grieta(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        assert len(escena._grietas) == len(trazado.grietas_de_pisada())

    def test_se_encienden_al_acercarse(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        cx, fila = trazado.grietas_de_pisada()[0]
        _llevar_a(escena, fila, columna=cx)
        assert escena._grietas[0].intensity > 0.1, (
            "la grieta no se encendió con el jugador encima"
        )

    def test_se_apagan_al_alejarse(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        cx, fila = trazado.grietas_de_pisada()[0]
        _llevar_a(escena, fila, columna=cx)
        assert escena._grietas[0].intensity > 0.1
        # Se aleja mucho: al otro lado del pozo y muchas filas más abajo.
        escena._player.rect.topleft = (
            5 * settings.TILE_SIZE, (fila + 40) * settings.TILE_SIZE,
        )
        escena._player.position.update(*escena._player.rect.topleft)
        for _ in range(240):
            escena.update(1 / 60)
        assert escena._grietas[0].intensity < 0.05, (
            "la grieta se quedó encendida: no es un rastro, es un progreso"
        )


class TestCabeEnElPresupuestoDeFotograma:
    """60 fps son 16,6 ms para todo. El rediseño quitó la visión espectral y
    los efectos del diseño anterior, así que el presupuesto se recalibra:
    ver la medición en el comentario de `PRESUPUESTO_MS`.
    """

    #: Sin visión espectral ni losas fantasma/rítmicas que revelar, dibujar
    #: este nivel es más barato que el diseño anterior (que medía 14,5 ms en
    #: el peor caso, con la visión puesta). 15 ms deja el mismo margen que
    #: usaba el diseño anterior mientras no haya una medición propia.
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
        _llevar_a(escena, 44)
        assert self._medir(escena) < self.PRESUPUESTO_MS


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
    """AUD-162 — sin él, el espíritu se dibujaría encima del jugador."""

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
        escena.draw(lienzo)  # no debe lanzar
