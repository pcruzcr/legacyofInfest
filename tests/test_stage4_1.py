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
    la fase, la gradación y la viñeta (AUD-566) — para las pruebas que
    necesitan un `avance` exacto dentro de la sección, sin depender de
    que la física real (gravedad, colisión) termine en la posición
    esperada."""
    from src.stages.stage4_1 import trazado

    if fila is None:
        fila = trazado.altura_de_colision(int(columna))
    x = columna * settings.TILE_SIZE
    y = fila * settings.TILE_SIZE
    escena._player.rect.center = (int(x), int(y))
    escena._player.position.update(float(x), float(y))
    escena._actualizar_fase()
    escena._actualizar_gradacion()
    escena._actualizar_vignette()


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


class TestLasPresenciasErrantes:
    """AUD-562 — pedido del dueño: más figuras de fondo, y fauna que no
    haga daño pero llene de estrés. `presencias.PRESENCIAS` no son
    entidades — la regla de oro (arriba) sigue en verde con ellas
    activas."""

    def test_no_agregan_ninguna_entidad(self, escena) -> None:
        """La misma prueba que `TestLaReglaDeOro`, pero con al menos una
        presencia forzada a visible — para que quede constancia de que
        esto no depende de que ninguna esté activa en el momento medido."""
        from src.stages.stage4_1 import presencias

        for p in presencias.PRESENCIAS:
            escena._presencia_visible[p.id] = 5.0
        assert list(escena._stage_data.entity_list) == []

    def test_cada_presencia_solo_vive_en_su_fase(self) -> None:
        from src.stages.stage4_1 import presencias
        from src.stages.stage4_1.fases import FASES

        fases_con_presencia = {p.fase for p in presencias.PRESENCIAS}
        assert fases_con_presencia <= {f.numero for f in FASES}

    def test_eventualmente_aparece(self, escena) -> None:
        """Forzando el temporizador a cero, igual que ya hace
        `TestLaSombraDelGavilan.test_cruza_tras_el_silencio`."""
        from src.stages.stage4_1 import presencias

        p = presencias.PRESENCIAS[0]
        _posicionar_sin_fisica(escena, p.columna_centro)
        escena._presencia_proxima[p.id] = 0.0
        escena._actualizar_presencias_errantes(1 / 60)
        assert escena._presencia_visible[p.id] > 0.0

    def test_no_se_dibuja_fuera_de_su_fase(self, escena) -> None:
        from src.stages.stage4_1 import presencias
        from src.stages.stage4_1.fases import FASES

        p = presencias.PRESENCIAS[0]
        otra_fase = next(f for f in FASES if f.numero != p.fase)
        _posicionar_sin_fisica(escena, otra_fase.desde_columna + 10)
        escena._presencia_visible[p.id] = 5.0
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        escena._dibujar_presencias_errantes(lienzo, pygame.Vector2())
        arr = pygame.surfarray.pixels_alpha(lienzo)
        assert arr.max() == 0, "se dibujó una presencia fuera de su fase"

    def test_se_dibuja_visible_dentro_de_su_fase(self, escena) -> None:
        """Sin monkeypatch: corre la ruta real (incluye el sprite del
        infestado, que usa `tipo='infestado'`) y comprueba que algo no
        transparente terminó en el lienzo."""
        from src.stages.stage4_1 import presencias

        p = next(pr for pr in presencias.PRESENCIAS if pr.tipo == "infestado")
        _posicionar_sin_fisica(escena, p.columna_centro)
        escena._presencia_visible[p.id] = 5.0
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        # La cámara real centraría al jugador en pantalla; aquí se imita a
        # mano para que `columna_centro` caiga dentro del lienzo en vez de
        # a miles de píxeles de un offset (0, 0).
        centro_mundo = pygame.Vector2(
            p.columna_centro * settings.TILE_SIZE - 400, 0)
        escena._dibujar_presencias_errantes(lienzo, centro_mundo)
        arr = pygame.surfarray.pixels_alpha(lienzo)
        assert arr.max() > 0, "el infestado errante no se dibujó"


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
        """AUD-473 — ninguna de las dos superficies usa `arrastre`.

        `arrastre` es la cinta transportadora de `ZonaDeFriccion`
        (`components.py`, AUD-236): mueve `posicion.x` sin mirar la entrada
        del jugador. La primera versión lo usaba para el musgo pensando en
        «te arrastra» — el jugador cruzaba el tramo como pasajero, sin
        soltar el control en ningún otro momento del nivel, lo que en una
        partida real se veía exactamente como el nivel congelado.

        AUD-522 — desde entonces las dos superficies dejaron de ser «la
        misma mecánica, distinta intensidad»: el musgo resbala
        (`inercia`), el lodo frena (`multiplicador < 1`).
        """
        from src.stages.stage4_1 import trazado

        musgo = sum(1 for _i, _a, m in trazado.SEGMENTOS_FASE2 if m == "musgo")
        lodo = sum(1 for _i, _a, m in trazado.SEGMENTOS_FASE2 if m == "lodo")
        zonas = self._zonas(escena)
        arrastres = [z for z in zonas if z.arrastre]
        resbalones_de_musgo = [z for z in zonas if z.inercia == trazado.RESBALON_DEL_MUSGO]
        frenos_de_lodo = [z for z in zonas if z.multiplicador == trazado.FRENO_DEL_LODO]

        assert arrastres == [], (
            f"ninguna superficie de la Fase 2 debe usar arrastre (cinta "
            f"transportadora): {arrastres}"
        )
        assert len(resbalones_de_musgo) == musgo
        assert len(frenos_de_lodo) == lodo
        assert all(z.multiplicador == 1.0 for z in resbalones_de_musgo), (
            "el musgo resbala con `inercia`, no debería tocar `multiplicador`"
        )
        assert all(z.inercia == 0.0 for z in frenos_de_lodo), (
            "el lodo frena con `multiplicador`, no debería tocar `inercia`"
        )
        assert all(0.0 < z.multiplicador < 1.0 for z in frenos_de_lodo), (
            "AUD-236: multiplicador > 1 se dispara sin tope en este motor — "
            "el lodo no debería usarlo"
        )
        assert all(0.0 < z.inercia < 1.0 for z in resbalones_de_musgo), (
            "la inercia tiene que quedarse acotada entre 0 (sin resbalón) y "
            "1 (resbalón total)"
        )

    def test_el_musgo_no_mueve_a_nadie_sin_velocidad(self) -> None:
        """AUD-473, actualizada en AUD-522 — regresión directa del defecto,
        contra el sistema real.

        Mismo patrón que ya prueba la cinta transportadora de verdad
        (`tests/test_ecs.py::test_la_cinta_arrastra_sin_acumular_velocidad`),
        con la zona de musgo tal como la declara `stage4_1` — para que quede
        constancia de que, a diferencia de una cinta, el musgo **no** mueve
        a quien está quieto encima: la inercia amortigua hacia la velocidad
        que pide la entrada, y con la entrada pidiendo 0 desde el principio
        no hay nada de lo que resbalar.
        """
        import pygame

        from src.framework.ecs import Transform, Velocidad, World, ZonaDeFriccion
        from src.framework.ecs import systems as S
        from src.stages.stage4_1 import trazado

        m = World()
        m.crear(ZonaDeFriccion(pygame.Rect(0, 0, 200, 200),
                                inercia=trazado.RESBALON_DEL_MUSGO))
        e = m.crear(Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
                    Velocidad(pygame.Vector2(0, 0)))
        for _ in range(120):  # 2 s
            S.sistema_friccion(m, 1 / 60)

        assert m.obtener(e, Transform).posicion.x == 10.0, (
            "el musgo movió a un jugador quieto — eso es arrastre, no fricción"
        )
        assert m.obtener(e, Velocidad).v.x == 0.0

    def test_los_segmentos_caen_en_la_fase_2(self) -> None:
        from src.stages.stage4_1 import trazado

        for inicio, ancho, _material in trazado.SEGMENTOS_FASE2:
            assert trazado.fase_de_la_columna(inicio) == 2
            assert trazado.fase_de_la_columna(inicio + ancho - 1) == 2


class TestLaFriccionEscalaConLaLluvia:
    """AUD-513, GAP-060 punto 14: *«al principio, musgo = ligeramente
    resbaladizo; después de lluvia intensa, mucho más»* — antes
    `multiplicador` era una constante por material, igual en toda la
    sección.

    AUD-522 divide la mecánica en dos campos que escalan en sentidos
    opuestos: el lodo frena más fuerte con más lluvia (`multiplicador` se
    acerca a 0), el musgo resbala más fuerte con más lluvia (`inercia` se
    aleja de 0) — por eso las pruebas de aquí en adelante separan las
    zonas por tipo en vez de tratarlas como una sola lista.
    """

    def _zonas(self, escena):
        from src.framework.ecs import ZonaDeFriccion

        return list(escena._mundo.cada(ZonaDeFriccion))

    def _musgo_y_lodo(self, escena):
        """Separa las zonas de la Fase 2 por tipo — leyendo la propia
        clasificación que ya calculó y cachea `_actualizar_friccion_de_
        la_lluvia` en `escena._frenos_de_fabrica` (requiere haberla
        llamado antes), en vez de adivinar por el valor actual de
        `inercia`/`multiplicador`.

        AUD-554 rompió la versión anterior (`inercia > 0.0` → musgo, si
        no → lodo): las zonas nuevas de grava/ahogado también tienen
        `inercia == 0.0` y caían al bote de "lodo" por accidente aunque
        `_actualizar_friccion_de_la_lluvia` las ignora (no son ni musgo ni
        lodo de fábrica — `tipo is None` → `continue`, ver el propio
        método). Se prefiere la caché (exacta incluso después de que la
        lluvia reescale los valores); si está vacía —fuera de la Fase 2,
        `_actualizar_friccion_de_la_lluvia` vuelve antes de llenarla—, se
        cae al mismo criterio de tolerancia que usa la propia escena
        contra los valores de fábrica, que ahí todavía no se han tocado."""
        from src.stages.stage4_1 import trazado

        musgo, lodo = [], []
        for eid, z in self._zonas(escena):
            tipo = escena._frenos_de_fabrica.get(eid)
            if tipo is None:
                tol = escena.TOLERANCIA_FRENO_DE_FABRICA
                if abs(z.inercia - trazado.RESBALON_DEL_MUSGO) <= tol:
                    tipo = "musgo"
                elif abs(z.multiplicador - trazado.FRENO_DEL_LODO) <= tol:
                    tipo = "lodo"
            if tipo == "musgo":
                musgo.append((eid, z))
            elif tipo == "lodo":
                lodo.append((eid, z))
        return musgo, lodo

    def test_resbala_menos_al_entrar_que_al_final(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase2 = FASES[1]
        _posicionar_sin_fisica(escena, fase2.desde_columna + 1)
        escena._actualizar_friccion_de_la_lluvia()
        musgo_temprano = {eid: z.inercia for eid, z in self._musgo_y_lodo(escena)[0]}
        lodo_temprano = {eid: z.multiplicador for eid, z in self._musgo_y_lodo(escena)[1]}

        _posicionar_sin_fisica(escena, fase2.desde_columna + 140)
        escena._actualizar_friccion_de_la_lluvia()
        musgo_tardio = {eid: z.inercia for eid, z in self._musgo_y_lodo(escena)[0]}
        lodo_tardio = {eid: z.multiplicador for eid, z in self._musgo_y_lodo(escena)[1]}

        assert musgo_temprano.keys() == musgo_tardio.keys()
        for eid in musgo_temprano:
            assert musgo_tardio[eid] > musgo_temprano[eid], (
                f"el musgo {eid} no resbala más avanzada la sección: "
                f"{musgo_temprano[eid]} -> {musgo_tardio[eid]}"
            )
        assert lodo_temprano.keys() == lodo_tardio.keys()
        for eid in lodo_temprano:
            assert lodo_tardio[eid] < lodo_temprano[eid], (
                f"el lodo {eid} no frena más avanzada la sección: "
                f"{lodo_temprano[eid]} -> {lodo_tardio[eid]}"
            )

    def test_las_zonas_siguen_siendo_solo_musgo_y_lodo(self, escena) -> None:
        """La fricción escalada no debe dejar de frenar ni empezar a
        acelerar (AUD-236: `multiplicador > 1` se dispara sin tope), y el
        musgo no debe pasar de resbaloso a arrastrar (`inercia` acotada)."""
        from src.stages.stage4_1.fases import FASES

        _posicionar_sin_fisica(escena, FASES[1].desde_columna + 149)
        escena._actualizar_friccion_de_la_lluvia()
        musgo, lodo = self._musgo_y_lodo(escena)
        for _eid, zona in lodo:
            assert 0.0 < zona.multiplicador < 1.0
        for _eid, zona in musgo:
            assert 0.0 < zona.inercia < 1.0

    def test_no_toca_nada_fuera_de_la_fase_2(self, escena) -> None:
        from src.stages.stage4_1 import trazado

        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        escena._actualizar_friccion_de_la_lluvia()
        musgo, lodo = self._musgo_y_lodo(escena)
        assert {round(z.inercia, 6) for _eid, z in musgo} == {
            round(trazado.RESBALON_DEL_MUSGO, 6),
        }
        assert {round(z.multiplicador, 6) for _eid, z in lodo} == {
            round(trazado.FRENO_DEL_LODO, 6),
        }

    def test_la_fisica_vuelve_a_la_normalidad_tras_liberar_al_venado(
        self, escena,
    ) -> None:
        """Punto 21: *«la física vuelve a la normalidad»* tras liberar al
        espíritu — no porque el jugador siguiera caminando, sino porque el
        Venado ya no está atrapado. «Normalidad» es distinta por campo: el
        lodo frena menos (`multiplicador` sube), el musgo resbala menos
        (`inercia` baja)."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase2 = FASES[1]
        col = fase2.desde_columna + trazado.DESVIO_COLUMNA_LIBERACION
        _posicionar_sin_fisica(escena, col)
        escena._actualizar_friccion_de_la_lluvia()
        musgo_antes = {eid: z.inercia for eid, z in self._musgo_y_lodo(escena)[0]}
        lodo_antes = {eid: z.multiplicador for eid, z in self._musgo_y_lodo(escena)[1]}

        evento = trazado.evento_de_liberacion(fase2.numero)
        liberado = next(
            d for d in escena._stage_data.disparadores if d.evento == evento)
        liberado.disparado = True

        escena._actualizar_friccion_de_la_lluvia()
        musgo_despues = {eid: z.inercia for eid, z in self._musgo_y_lodo(escena)[0]}
        lodo_despues = {eid: z.multiplicador for eid, z in self._musgo_y_lodo(escena)[1]}

        for eid in musgo_antes:
            assert musgo_despues[eid] < musgo_antes[eid], (
                "liberar al Venado debería calmar el musgo (menos "
                "resbaladizo), no dejarlo igual"
            )
        for eid in lodo_antes:
            assert lodo_despues[eid] > lodo_antes[eid], (
                "liberar al Venado debería calmar el lodo (menos "
                "denso), no dejarlo igual"
            )


class TestLasAparicionesPreviasDelVenado:
    """GAP-060/AUD-479 — puntos 6 y 9-12 de la crítica de diseño del dueño
    para la Fase 2 (2026-08-14): antes de hablar, el Venado se deja ver y
    desaparece — «se detiene, mira, desaparece» —, no queda encendido todo
    el tramo como un letrero. Después del punto donde habla (mismo punto
    que usa `DESVIO_COLUMNA_DIALOGO` para el `MessageTrigger`), vuelve al
    comportamiento normal de fundido de entrada/salida que ya usan el Rey
    Terciopelo y el Gavilán."""

    def _antes_del_dialogo(self, escena):
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase2 = FASES[1]
        col = fase2.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO - 5
        _posicionar_sin_fisica(escena, col)
        assert escena.fase.numero == 2
        return escena

    def test_solo_la_fase_2_lo_activa(self) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            assert fase.apariciones_previas == (fase.numero == 2)

    def test_no_se_dibuja_sin_destello(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import siluetas

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_silueta_de_sprite",
            lambda *a, **kw: llamadas.append(a) or True,
        )
        self._antes_del_dialogo(escena)
        escena._venado_visible = 0.0
        escena._dibujar_espiritu(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == []

    def test_se_dibuja_durante_el_destello(self, escena, monkeypatch) -> None:
        """AUD-561 — el arte real del jefe sustituyó al contorno de
        polígono; se comprueba el archivo del Venado, no la forma."""
        from src.stages.stage4_1 import siluetas

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_silueta_de_sprite",
            lambda *a, **kw: llamadas.append(a[1]) or True,  # 2º posicional: archivo
        )
        self._antes_del_dialogo(escena)
        escena._venado_visible = 1.0
        escena._dibujar_espiritu(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == [siluetas.SPRITE_DE_ESPIRITU[0][0]]

    def test_eventualmente_asoma_antes_del_dialogo(self, escena) -> None:
        """Forzando el temporizador a cero, igual que ya hace
        `TestLaSombraDelGavilan.test_cruza_tras_el_silencio`."""
        self._antes_del_dialogo(escena)
        escena._proxima_aparicion_venado = 0.0
        escena._actualizar_apariciones_previas_del_venado(1 / 60)
        assert escena._venado_visible > 0.0

    def test_se_apaga_al_salir_de_la_fase_2(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        self._antes_del_dialogo(escena)
        escena._venado_visible = 2.0
        _posicionar_sin_fisica(escena, FASES[2].desde_columna)
        escena._actualizar_apariciones_previas_del_venado(1 / 60)
        assert escena._venado_visible == 0.0

    def test_despues_del_dialogo_vuelve_al_fundido_normal(self, escena) -> None:
        """Pasado `DESVIO_COLUMNA_DIALOGO`, el Venado ya no depende de
        `_venado_visible` — se ve con el mismo fundido continuo que usan
        el Rey Terciopelo y el Gavilán, aunque el destello esté apagado."""
        from src.stages.stage4_1 import siluetas, trazado
        from src.stages.stage4_1.fases import FASES

        fase2 = FASES[1]
        col = fase2.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO + 10
        _posicionar_sin_fisica(escena, col)
        escena._venado_visible = 0.0  # el destello está apagado a propósito
        llamadas = []
        import unittest.mock

        with unittest.mock.patch.object(
            siluetas, "dibujar_silueta_de_sprite",
            lambda *a, **kw: llamadas.append(a[1]) or True,
        ):
            escena._dibujar_espiritu(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == [siluetas.SPRITE_DE_ESPIRITU[0][0]], (
            "después del diálogo debe verse igual sin destello activo"
        )

    def test_no_afecta_a_otras_fases_con_espiritu(self) -> None:
        from src.stages.stage4_1.fases import FASES

        rey_terciopelo, gavilan = FASES[2], FASES[3]
        assert rey_terciopelo.apariciones_previas is False
        assert gavilan.apariciones_previas is False


class TestLosEspiritusUsanSuArteReal:
    """AUD-561 — jugado, las siluetas de polígono «se veían raras»: no se
    leían como venado, serpiente o gavilán. Los tres fueron jefes de una
    zona anterior y el proyecto ya tiene su arte real
    (`assets/sprites/bosses/boss_venado_*.png` etc.); esto comprueba que
    `_dibujar_espiritu` de verdad usa ese arte, no el contorno de respaldo,
    cuando el archivo existe — que es el caso normal del repositorio."""

    def test_los_tres_archivos_de_sprite_existen(self) -> None:
        from src.engine.core import settings
        from src.stages.stage4_1 import siluetas

        for ruta_relativa, _fw, _fh in siluetas.SPRITE_DE_ESPIRITU:
            ruta = settings.ASSETS_DIR / ruta_relativa
            assert ruta.exists(), f"falta el sprite de espíritu: {ruta}"

    def test_silueta_desde_sprite_da_una_superficie_pintada(self, _video) -> None:
        """La silueta no puede quedar completamente transparente: eso
        sería indistinguible de que el recorte falló en silencio."""
        from src.stages.stage4_1 import siluetas

        archivo, fw, fh = siluetas.SPRITE_DE_ESPIRITU[0]
        silueta = siluetas.silueta_desde_sprite(archivo, fw, fh, siluetas.VERDE_ESPECTRAL)
        assert silueta is not None
        assert silueta.get_size() == (fw, fh)
        pixeles_pintados = sum(
            1 for px in range(fw) for py in range(fh)
            if silueta.get_at((px, py))[3] > 0
        )
        assert pixeles_pintados > 0, "la silueta del Venado quedó vacía"

    def test_el_color_de_la_silueta_es_el_pedido(self, _video) -> None:
        """Todo píxel opaco debe llevar exactamente el color pedido — es una
        silueta plana, no el sprite a todo color."""
        from src.stages.stage4_1 import siluetas

        archivo, fw, fh = siluetas.SPRITE_DE_ESPIRITU[2]
        color = (10, 200, 30)
        silueta = siluetas.silueta_desde_sprite(archivo, fw, fh, color)
        assert silueta is not None
        colores_opacos = {
            tuple(silueta.get_at((px, py)))[:3]
            for px in range(fw) for py in range(fh)
            if silueta.get_at((px, py))[3] > 0
        }
        assert colores_opacos == {color}

    def test_dibujar_silueta_de_sprite_devuelve_false_si_falta_el_archivo(self) -> None:
        import pygame

        from src.stages.stage4_1 import siluetas

        lienzo = pygame.Surface((64, 64), pygame.SRCALPHA)
        dibujado = siluetas.dibujar_silueta_de_sprite(
            lienzo, "no_existe_de_verdad.png", 40, 40, 0, 0, 40, 40,
            siluetas.VERDE_ESPECTRAL, 200,
        )
        assert dibujado is False

    def test_dibujar_espiritu_usa_el_sprite_cuando_esta_disponible(self, escena) -> None:
        """Sin monkeypatch: corre la ruta real de principio a fin y
        comprueba que algo no transparente terminó en el lienzo.

        Fase 3 (Rey Terciopelo) y no la 1 o la 2: la Fase 1 no tiene
        espíritu y la Fase 2 sólo se ve a destellos antes de su diálogo
        (`apariciones_previas`) — la 3 usa el fundido continuo normal sin
        ninguna condición extra."""
        import pygame

        from src.stages.stage4_1.fases import FASES

        _posicionar_sin_fisica(escena, FASES[2].desde_columna + 10)
        assert escena.fase.numero == 3
        lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
        escena._dibujar_espiritu(lienzo, pygame.Vector2())
        arr = pygame.surfarray.pixels_alpha(lienzo)
        assert arr.max() > 0, "no se dibujó nada del espíritu en el lienzo"


class TestElResplandorAntesDelDialogo:
    """AUD-567 — segunda propuesta "nivel cine" aprobada: un resplandor
    breve justo antes de que hable cada espíritu, para que el momento se
    lea como una revelación dirigida y no como fondo animado de siempre."""

    def test_es_cero_lejos_del_punto_del_dialogo(self, escena) -> None:
        assert escena._intensidad_resplandor_dialogo(0.0) == 0.0
        assert escena._intensidad_resplandor_dialogo(0.5) == 0.0

    def test_es_maximo_justo_en_el_punto_del_dialogo(self, escena) -> None:
        objetivo = escena.AVANCE_ANTES_DEL_DIALOGO
        assert escena._intensidad_resplandor_dialogo(objetivo) == pytest.approx(1.0)

    def test_crece_al_acercarse(self, escena) -> None:
        objetivo = escena.AVANCE_ANTES_DEL_DIALOGO
        lejos = escena._intensidad_resplandor_dialogo(
            objetivo - escena.VENTANA_RESPLANDOR_ANTES * 0.9)
        cerca = escena._intensidad_resplandor_dialogo(
            objetivo - escena.VENTANA_RESPLANDOR_ANTES * 0.1)
        assert 0.0 <= lejos < cerca <= 1.0

    def test_se_apaga_despues_del_punto(self, escena) -> None:
        objetivo = escena.AVANCE_ANTES_DEL_DIALOGO
        fin = objetivo + escena.VENTANA_RESPLANDOR_DESPUES
        assert escena._intensidad_resplandor_dialogo(fin) == pytest.approx(0.0, abs=1e-6)
        assert escena._intensidad_resplandor_dialogo(fin + 0.01) == 0.0

    def test_no_se_dibuja_con_intensidad_cero(self, escena) -> None:
        import pygame

        lienzo = pygame.Surface((200, 200), pygame.SRCALPHA)
        escena._dibujar_resplandor_de_dialogo(lienzo, 50, 50, 40, 40, 0.0)
        arr = pygame.surfarray.pixels_alpha(lienzo)
        assert arr.max() == 0

    def test_se_dibuja_con_intensidad_positiva(self, escena) -> None:
        import pygame

        lienzo = pygame.Surface((200, 200), pygame.SRCALPHA)
        escena._dibujar_resplandor_de_dialogo(lienzo, 50, 50, 40, 40, 1.0)
        arr = pygame.surfarray.pixels_alpha(lienzo)
        assert arr.max() > 0


class TestElPlanoDeCamaraPorEspiritu:
    """AUD-569 — cuarta propuesta "nivel cine" aprobada: un barrido de
    cámara pequeño hacia arriba, hacia donde flota el espíritu, en la
    misma ventana en que ya crece su resplandor (AUD-567)."""

    def test_no_desplaza_la_camara_lejos_del_dialogo(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        _posicionar_sin_fisica(escena, fase_venado.desde_columna + 5)
        antes = escena._camera.offset.y
        escena._actualizar_plano_de_dialogo()
        assert escena._camera.offset.y == pytest.approx(antes)

    def test_sube_la_camara_justo_antes_del_dialogo(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        objetivo_columna = fase_venado.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO
        _posicionar_sin_fisica(escena, objetivo_columna)
        antes = escena._camera.offset.y
        escena._actualizar_plano_de_dialogo()
        assert escena._camera.offset.y < antes

    def test_no_se_acumula_entre_llamadas(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        objetivo_columna = fase_venado.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO
        _posicionar_sin_fisica(escena, objetivo_columna)
        escena._actualizar_plano_de_dialogo()
        primera = escena._camera.offset.y
        escena._actualizar_plano_de_dialogo()
        segunda = escena._camera.offset.y
        assert primera == pytest.approx(segunda)

    def test_vuelve_a_su_sitio_al_alejarse(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        objetivo_columna = fase_venado.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO
        _posicionar_sin_fisica(escena, fase_venado.desde_columna + 5)
        linea_base = escena._camera.offset.y
        _posicionar_sin_fisica(escena, objetivo_columna)
        escena._actualizar_plano_de_dialogo()
        assert escena._camera.offset.y < linea_base

        _posicionar_sin_fisica(escena, fase_venado.desde_columna + 5)
        escena._actualizar_plano_de_dialogo()
        assert escena._camera.offset.y == pytest.approx(linea_base)


class TestLasLomasDeLaFase3:
    """AUD-297/470/477 — dos lomas de verdad (`Slope`, una pareja subida-
    bajada cada una), no una sola joroba. El punto 6 de la crítica de
    diseño (2026-08-14) pedía que el escenario «se enrolle» alrededor del
    jugador en vez de leerse como una sola montaña; la colisión bajo cada
    rampa se queda plana por el mismo motivo que ya documentó AUD-470."""

    def test_hay_exactamente_seis_pendientes(self, escena) -> None:
        """Dos lomas × (subida, cima llana, bajada) cada una (AUD-477: la
        cima también es `Pendiente`, no bloque sólido — ver
        `trazado.altura_de_colision`)."""
        assert len(escena._stage_data.pendientes) == 6

    def test_todas_estan_en_la_fase_3(self) -> None:
        from src.stages.stage4_1 import trazado

        for col, _fila, _ancho, _alto, _sube in trazado.loma():
            assert trazado.fase_de_la_columna(col) == 3

    def test_la_segunda_loma_es_mas_alta_que_la_primera(self) -> None:
        """El «cuello» de la serpiente, no dos jorobas iguales."""
        from src.stages.stage4_1 import trazado

        primera, segunda = trazado.LOMAS_FASE3
        fila_cima_primera = primera[4]
        fila_cima_segunda = segunda[4]
        assert fila_cima_segunda < fila_cima_primera, (
            "la segunda loma debería subir más (fila más pequeña) que la "
            "primera, no al revés ni igual"
        )

    def test_la_colision_bajo_cada_rampa_es_plana(self) -> None:
        """El bug real que encontró jugarlo (AUD-470): un escalón sólido
        por columna bloqueaba el paso antes de que el `Slope` interviniera.
        Se comprueba en las dos lomas, no sólo en la primera."""
        from src.stages.stage4_1 import trazado

        for inicio_subida, ancho_subida, *_resto in trazado.LOMAS_FASE3:
            alturas = {
                trazado.altura_de_colision(c)
                for c in range(inicio_subida, inicio_subida + ancho_subida)
            }
            assert alturas == {trazado.FILA_SUELO}, (
                f"la colisión bajo la rampa que empieza en {inicio_subida} "
                f"no es plana: {alturas}"
            )

    def test_hay_llano_de_verdad_entre_las_dos_lomas(self) -> None:
        """Si no hay un tramo llano entre la bajada de la primera y la
        subida de la segunda, son una sola joroba con un bache en medio,
        no dos lomas separadas."""
        from src.stages.stage4_1 import trazado

        primera, segunda = trazado.LOMAS_FASE3
        fin_primera = primera[0] + primera[1] + primera[2] + primera[3]
        inicio_segunda = segunda[0]
        assert inicio_segunda > fin_primera, (
            f"la segunda loma (columna {inicio_segunda}) empieza antes de "
            f"que termine la primera (columna {fin_primera})"
        )
        llano = {
            trazado.altura_de_colision(c)
            for c in range(fin_primera, inicio_segunda)
        }
        assert llano == {trazado.FILA_SUELO}, (
            f"el tramo entre las dos lomas no es llano: {llano}"
        )

    def test_se_sube_y_se_baja_dos_veces_caminando(self, escena) -> None:
        """Recorrido real con física, no teletransportado: entra antes de
        la primera loma y camina a la derecha sin soltar el botón hasta
        pasar las dos. Mide la forma de verdad —sube, baja al llano, sube
        más, baja— en vez de sólo comprobar un delta al final, que es
        exactamente lo que se le habría escapado a una sola muestra final
        si las dos lomas se hubieran fundido en una.

        Corta la serie por **columna de mundo conocida**, no por el valor
        mínimo: `LOMAS_FASE3` ya dice exactamente dónde empieza y termina
        cada loma, así que no hace falta adivinar dónde está el pico de
        cada una con un detector genérico — y un detector genérico salió
        mal en el primer intento (`git log`, este mismo AUD): con la cima
        de una loma llana durante muchos fotogramas seguidos, buscar
        `min() + .index()` sólo encuentra el *primer* fotograma de esa
        meseta, y todo lo anterior ya incluye la subida de la loma
        siguiente si las dos comparten la misma altura de fondo.
        """
        from src.stages.stage4_1 import trazado

        primera, segunda = trazado.LOMAS_FASE3
        col_entrada = primera[0] - 6

        _llevar_a(escena, col_entrada)

        im = escena.context.input_manager
        im.pump([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)])
        muestras: list[tuple[float, int]] = []
        for _ in range(1800):  # de sobra para cruzar las dos lomas caminando
            escena.update(1 / 60)
            col = escena._player.rect.centerx / settings.TILE_SIZE
            muestras.append((col, escena._player.rect.centery))
        im.pump([pygame.event.Event(pygame.KEYUP, key=pygame.K_RIGHT)])

        def _minimo_entre(desde: float, hasta: float) -> int:
            en_rango = [cy for col, cy in muestras if desde <= col <= hasta]
            assert en_rango, (
                f"el recorrido nunca llegó a las columnas {desde}-{hasta} "
                f"en los fotogramas medidos — súbele el presupuesto"
            )
            return min(en_rango)

        base = muestras[0][1]
        fin_primera = primera[0] + primera[1] + primera[2] + primera[3]
        inicio_segunda = segunda[0]
        fin_segunda = segunda[0] + segunda[1] + segunda[2] + segunda[3]

        cima_primera_loma = _minimo_entre(primera[0], fin_primera)
        valle = _minimo_entre(fin_primera + 2, inicio_segunda - 2)
        cima_segunda_loma = _minimo_entre(inicio_segunda, fin_segunda)

        assert cima_primera_loma < base - 40, (
            f"no subió de verdad en la primera loma: base={base}, "
            f"mínimo={cima_primera_loma}"
        )
        assert valle > cima_primera_loma + 40, (
            f"no bajó de vuelta al llano entre las dos lomas — se leería "
            f"como una sola joroba, no dos: valle={valle} vs "
            f"primera loma={cima_primera_loma}"
        )
        assert cima_segunda_loma < cima_primera_loma - 20, (
            f"la segunda loma debería subir más que la primera: "
            f"{cima_segunda_loma} vs {cima_primera_loma}"
        )


class TestElVientoDeLaFase3:
    def test_hay_una_zona_de_viento_en_la_fase_3(self, escena) -> None:
        from src.framework.ecs import ZonaDeViento
        from src.stages.stage4_1 import trazado

        vientos = [z for _, z in escena._mundo.cada(ZonaDeViento)]
        assert len(vientos) == 1
        centro_col = vientos[0].rect.centerx // settings.TILE_SIZE
        assert trazado.fase_de_la_columna(centro_col) == 3


class TestLaPausaDelDialogoDeLaSerpiente:
    """GAP-061/AUD-480 — punto 19 de la crítica de diseño para la Fase 3
    (2026-08-14): *«el jugador alcanza un descanso. El viento se detiene.
    La tormenta baja. La Serpiente habla. Después: el viento vuelve.»*
    No es el silencio total de la Fase 4 (eso tiene su propio mecanismo);
    aquí el viento baja a una fracción de su fuerza alrededor del punto
    donde habla el Rey Terciopelo."""

    def _viento(self, escena):
        from src.framework.ecs import ZonaDeViento

        return next(z for _, z in escena._mundo.cada(ZonaDeViento))

    def test_se_reduce_alrededor_del_dialogo(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase3 = FASES[2]
        original = pygame.Vector2(self._viento(escena).fuerza)
        col = fase3.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO
        _posicionar_sin_fisica(escena, col)
        escena._actualizar_pausa_de_la_serpiente()
        reducida = self._viento(escena).fuerza
        assert reducida.length() < original.length() * 0.5

    def test_vuelve_a_su_fuerza_normal_lejos_del_dialogo(self, escena) -> None:
        """"Normal" ya no es la fuerza fija del TMX (AUD-513, GAP-061 punto
        5: la escalada progresiva) — es la fuerza declarada, multiplicada
        por la curva de esta columna. Lejos de la pausa, vuelve a esa
        curva, no a la constante del mapa."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase3 = FASES[2]
        original = pygame.Vector2(self._viento(escena).fuerza)
        col_dialogo = fase3.desde_columna + trazado.DESVIO_COLUMNA_DIALOGO
        _posicionar_sin_fisica(escena, col_dialogo)
        escena._actualizar_pausa_de_la_serpiente()
        assert self._viento(escena).fuerza.length() < original.length()

        columna_lejos = fase3.desde_columna + 5
        _posicionar_sin_fisica(escena, columna_lejos)
        escena._actualizar_pausa_de_la_serpiente()
        factor = escena._factor_de_viento(escena._avance_en_fase(fase3))
        esperado = original * factor
        assert self._viento(escena).fuerza.x == pytest.approx(esperado.x, abs=0.5)

    def test_no_toca_el_viento_fuera_de_la_fase_3(self, escena) -> None:
        original = pygame.Vector2(self._viento(escena).fuerza)
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        escena._actualizar_pausa_de_la_serpiente()
        assert self._viento(escena).fuerza == original


class TestLaBrujaEsUnaPercepcionFalsa:
    """AUD-475 — dos relámpagos de la Fase 3 traen a la Bruja, sin sonido,
    sin diálogo, sin ningún efecto sobre el estado del nivel. Es la pieza
    que pide el punto 3 de la crítica de diseño (2026-08-14): sembrar
    alguna percepción que nunca se confirma, para que el jugador deje de
    fiarse del patrón antes de que importe de verdad (Fase 4)."""

    def _entrar_a_fase_3(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(3))
        assert escena.fase.numero == 3

    def test_no_se_dibuja_sin_relampago(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import siluetas

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_contorno",
            lambda *a, **kw: llamadas.append(a),
        )
        self._entrar_a_fase_3(escena)
        escena._rayo = 0.0
        escena._bruja_este_rayo = True  # aunque esté marcado, sin luz no se ve
        escena._dibujar_bruja(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == []

    def test_se_dibuja_solo_en_los_relampagos_marcados(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import siluetas

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_contorno",
            lambda *a, **kw: llamadas.append(a[1]),  # la forma es el 2º posicional
        )
        self._entrar_a_fase_3(escena)
        escena._rayo = escena.DURACION_DEL_RAYO
        escena._bruja_este_rayo = False
        escena._dibujar_bruja(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == [], "no debería dibujarse en un relámpago sin marcar"

        escena._bruja_este_rayo = True
        escena._dibujar_bruja(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == [siluetas._bruja]

    def test_solo_dos_relampagos_de_toda_la_fase_la_traen(self, escena) -> None:
        """Recorre la fase entera disparando relámpagos a mano y cuenta
        cuántos de ellos quedan marcados — tiene que ser exactamente
        `len(RAYOS_CON_BRUJA)`, ni más ni menos, y sólo dentro de la
        Fase 3."""
        self._entrar_a_fase_3(escena)
        marcados = 0
        for _ in range(8):  # más relámpagos de los que trae RAYOS_CON_BRUJA
            escena._rayo = 0.0
            escena._proximo_rayo = 0.0
            escena._actualizar_rayos(1 / 60)
            if escena._bruja_este_rayo:
                marcados += 1
        assert marcados == len(escena.RAYOS_CON_BRUJA)

    def test_fuera_de_la_fase_3_nunca_se_marca(self, escena) -> None:
        """Aunque el contador interno coincida por casualidad, sólo cuenta
        dentro de la Fase 3 — `_actualizar_fase` lo reinicia al entrar."""
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        escena._rayos_en_fase3 = next(iter(escena.RAYOS_CON_BRUJA)) - 1
        escena._rayo = 0.0
        escena._proximo_rayo = 0.0
        escena._actualizar_rayos(1 / 60)
        assert escena._bruja_este_rayo is False

    def test_no_toca_sonido_ni_dialogo_ni_disparadores(self, escena) -> None:
        """Es exactamente lo que la vuelve «falsa»: ni un evento del bus, ni
        un `Disparador`, ni un `MessageTrigger` — sólo dibujo."""
        self._entrar_a_fase_3(escena)
        antes = len(escena._stage_data.disparadores)
        disparados_antes = [mt.triggered for mt in escena._stage_data.message_triggers]
        escena._rayo = escena.DURACION_DEL_RAYO
        escena._bruja_este_rayo = True
        escena._dibujar_bruja(pygame.Surface((800, 600)), pygame.Vector2())
        assert len(escena._stage_data.disparadores) == antes
        assert [mt.triggered for mt in escena._stage_data.message_triggers] == disparados_antes


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


class TestLaVinetaRespiraPorFase:
    """AUD-566 — primera propuesta "nivel cine" que el dueño aprobó
    construir: la viñeta ya existía en el motor (`PostProcessing.
    set_vignette`, base fija de 0,4 desde siempre) pero ningún escenario
    la tocaba por fase. Mismo mecanismo de interpolación por avance que
    ya prueba `TestLaGradacionYElSonidoPorFase` para la gradación."""

    def test_se_aproxima_al_objetivo_al_final_del_tramo(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import Stage4_1

        for fase in FASES:
            _posicionar_sin_fisica(
                escena, fase.desde_columna + trazado.ANCHO_SECCION - 1)
            objetivo = Stage4_1.VIGNETTE_POR_FASE[fase.numero]
            actual = escena._post_processing._vignette_strength
            assert abs(actual - objetivo) <= 0.02, (
                f"Fase {fase.numero}: viñeta {actual} lejos de {objetivo}"
            )

    def test_no_salta_de_golpe_al_entrar(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import Stage4_1

        fase1, fase2 = FASES[0], FASES[1]
        _posicionar_sin_fisica(escena, fase1.desde_columna + 10)
        _posicionar_sin_fisica(escena, fase2.desde_columna)
        actual = escena._post_processing._vignette_strength
        assert abs(actual - Stage4_1.VIGNETTE_POR_FASE[1]) < 0.05

    def test_todas_las_fases_declaran_un_valor_valido(self) -> None:
        """Dentro del rango que de verdad acepta `set_vignette` (0-0,6)."""
        from src.stages.stage4_1.fases import FASES
        from src.stages.stage4_1.stage4_1 import Stage4_1

        for fase in FASES:
            valor = Stage4_1.VIGNETTE_POR_FASE[fase.numero]
            assert 0.0 <= valor <= 0.6, f"Fase {fase.numero}: {valor} fuera de rango"

    def test_la_tormenta_y_la_noche_son_las_mas_cerradas(self, escena) -> None:
        """Lectura directa de la propuesta: la Fase 3 (tormenta) y la
        Fase 5 (noche) tienen que pedir más viñeta que la Fase 1 y la
        Fase 6, las dos sin terror activo."""
        from src.stages.stage4_1.stage4_1 import Stage4_1

        v = Stage4_1.VIGNETTE_POR_FASE
        assert v[3] > v[1] and v[3] > v[6]
        assert v[5] > v[1] and v[5] > v[6]


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


class TestElGritoDelGavilanTieneDireccion:
    """GAP-062/AUD-481 — puntos 4-5 y 23 de la crítica de diseño para la
    Fase 4: *«pájaro → izquierda... ahora desde otra dirección»*. El motor
    ya sabía hacer paneo estéreo por posición (`_play_sfx_spatial`,
    `AudioManager.play_sfx_at`); el grito aislado del Gavilán llamaba al
    canal ciego (`_play_sfx_named`) en su lugar."""

    def _tras_el_silencio(self, escena):
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        objetivo = fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION)
        _llevar_a(escena, objetivo)
        assert escena._shake_disparado is True
        return escena

    def test_usa_el_canal_espacial_no_el_ciego(self, escena, monkeypatch) -> None:
        # `_play_sfx_named` sigue en uso para OTROS sonidos de la Fase 4
        # (el silencio súbito, `_actualizar_silencio_y_shake`) — sólo
        # importa que el grito en concreto no pase por ahí.
        espaciales = []
        ciegos = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda *a, **kw: espaciales.append(a),
        )
        monkeypatch.setattr(
            escena, "_play_sfx_named",
            lambda *a, **kw: ciegos.append(a),
        )
        self._tras_el_silencio(escena)
        escena._proximo_grito = 0.0
        escena._actualizar_grito_del_gavilan(1 / 60)
        assert len(espaciales) == 1
        assert espaciales[0][0] == "sfx_environment_grito_de_gavilan"
        assert "sfx_environment_grito_de_gavilan" not in [c[0] for c in ciegos]

    def test_la_direccion_varia_entre_gritos(self, escena, monkeypatch) -> None:
        posiciones = []
        monkeypatch.setattr(
            escena, "_play_sfx_spatial",
            lambda nombre, world_x, volume=1.0: posiciones.append(world_x),
        )
        self._tras_el_silencio(escena)
        for _ in range(8):
            escena._proximo_grito = 0.0
            escena._actualizar_grito_del_gavilan(1 / 60)
        assert len(set(posiciones)) > 1, "el grito siempre sonó desde el mismo sitio"


class TestLaLunaSincronizaLaSombraConElGrito:
    """AUD-563 — pedido del dueño: *«que aparezca el Gavilán por la luna
    cuando suena»*. Antes el grito y la sombra corrían en temporizadores
    independientes, sin relación entre sí."""

    def _tras_el_silencio(self, escena):
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase4 = FASES[3]
        objetivo = fase4.desde_columna + int(0.6 * trazado.ANCHO_SECCION)
        _llevar_a(escena, objetivo)
        assert escena._shake_disparado is True
        return escena

    def test_la_luna_solo_se_ve_en_la_fase_4(self, escena) -> None:
        from src.stages.stage4_1.fases import FASES

        for fase in FASES:
            _posicionar_sin_fisica(escena, fase.desde_columna + 5)
            lienzo = pygame.Surface((800, 600), pygame.SRCALPHA)
            escena._dibujar_luna_de_fase4(lienzo, pygame.Vector2())
            arr = pygame.surfarray.pixels_alpha(lienzo)
            if fase.numero == 4:
                assert arr.max() > 0, "la luna no se dibujó en la Fase 4"
            else:
                assert arr.max() == 0, f"la luna se dibujó en la Fase {fase.numero}"

    def test_el_grito_dispara_la_sombra(self, escena) -> None:
        self._tras_el_silencio(escena)
        escena._sombra_progreso = -1.0  # nada cruzando todavía
        escena._proximo_grito = 0.0
        escena._actualizar_grito_del_gavilan(1 / 60)
        assert escena._sombra_progreso >= 0.0

    def test_no_solapa_si_ya_hay_una_sombra_cruzando(self, escena) -> None:
        """El guardián `_sombra_progreso < 0.0` de `_actualizar_grito_del_
        gavilan`: si ya hay un cruce en marcha, el grito no lo reinicia a
        mitad de camino."""
        self._tras_el_silencio(escena)
        escena._sombra_progreso = 0.5
        escena._proximo_grito = 0.0
        escena._actualizar_grito_del_gavilan(1 / 60)
        assert escena._sombra_progreso == 0.5


class TestElPisoDeVisibilidadDeLaLuna:
    """AUD-476 — puntos 9-10 de la crítica de diseño: *«no puedo ver bien»
    no es lo mismo que «no puedo jugar»*. `AMBIENTE_MIN_LUNA` era 0,06 —
    casi negro de verdad, sostenido medio ciclo cada 6 s, no un instante."""

    def test_el_minimo_no_baja_del_piso_declarado(self, escena) -> None:
        """Recorre un ciclo completo de la luna y comprueba que
        `_ambiente_base` nunca baja de `AMBIENTE_MIN_LUNA` — la propia
        constante, no un número repetido a mano, para que esta prueba siga
        protegiendo lo mismo si algún día cambia el valor."""
        from src.stages.stage4_1.fases import FASES

        fase5 = FASES[4]
        _posicionar_sin_fisica(escena, fase5.desde_columna + 6)
        assert escena.fase.numero == 5

        minimo_visto = 1.0
        for _ in range(int(escena.PERIODO_DE_LA_LUNA * 60) + 10):
            escena._actualizar_ambiente_de_fase()
            minimo_visto = min(minimo_visto, escena._ambiente_base)
            escena._tiempo += 1 / 60

        assert minimo_visto >= escena.AMBIENTE_MIN_LUNA - 1e-6

    def test_el_piso_no_es_mas_oscuro_que_la_referencia_de_paburu(self) -> None:
        """El propio proyecto ya define cuánto es «casi negro» para un solo
        instante dramático: la introducción de Paburu baja hasta 0,18
        (`boss_paburu/intro.py`). El piso de la luna se sostiene mucho más
        que un instante, así que no debería ser más oscuro que esa
        referencia — sería un «casi negro» peor que el que el propio juego
        reserva para su momento más solemne."""
        from src.stages.stage4_1.stage4_1 import Stage4_1

        REFERENCIA_CASI_NEGRO_DE_PABURU = 0.18
        assert Stage4_1.AMBIENTE_MIN_LUNA >= REFERENCIA_CASI_NEGRO_DE_PABURU

    def test_el_ciclo_sigue_oscilando_de_verdad(self, escena) -> None:
        """El arreglo no debe aplanar el ciclo — la luna tiene que seguir
        subiendo y bajando, sólo que sin tocar fondo."""
        from src.stages.stage4_1.fases import FASES

        fase5 = FASES[4]
        _posicionar_sin_fisica(escena, fase5.desde_columna + 6)

        valores = []
        for _ in range(int(escena.PERIODO_DE_LA_LUNA * 60) + 10):
            escena._actualizar_ambiente_de_fase()
            valores.append(escena._ambiente_base)
            escena._tiempo += 1 / 60

        assert max(valores) == pytest.approx(escena.AMBIENTE_MAX_LUNA, abs=1e-3)
        assert min(valores) == pytest.approx(escena.AMBIENTE_MIN_LUNA, abs=1e-3)


class TestLasGrietasAdelantadasDeLaFase5:
    """GAP-063/AUD-482 — puntos 29-30 del documento de la Fase 5 (2026-08-14):
    *«pequeñas luces verdes que empiezan a sustituir a la luna como guía»*.
    El mecanismo ya existe (`GRIETAS_FASE6`, encendido por proximidad) pero
    vivía enteramente dentro de la Fase 6 — el corte era seco en la
    columna 750. Ahora unas pocas asoman antes, en el tramo final de la
    Fase 5."""

    def test_algunas_grietas_caen_en_la_fase_5(self) -> None:
        from src.stages.stage4_1 import trazado

        fases_de_las_grietas = {
            trazado.fase_de_la_columna(c) for c in trazado.GRIETAS_FASE6
        }
        assert 5 in fases_de_las_grietas, (
            "ninguna grieta anticipa la transición dentro de la Fase 5"
        )
        assert 6 in fases_de_las_grietas, (
            "las grietas no deberían desaparecer de la Fase 6"
        )

    def test_las_grietas_de_la_fase_5_siguen_cerca_del_final(self) -> None:
        """No deberían adelantarse tanto que aparezcan a mitad de la
        Planicie de los Muertos — sólo en el tramo final, como anticipo."""
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase5 = FASES[4]
        mitad_del_tramo = fase5.desde_columna + trazado.ANCHO_SECCION // 2
        for col in trazado.GRIETAS_FASE6:
            if trazado.fase_de_la_columna(col) == 5:
                assert col > mitad_del_tramo


class TestElTinteDeLaFase6:
    """GAP-065 §11/AUD-483 — el documento de síntesis pide que la Fase 6
    termine en «full color / verde sobrenatural», no sólo en color pleno
    sin más: *«el verde debe tener significado... no lo usaría como simple
    iluminación decorativa»*. Antes `tinte=None`; ahora se intensifica con
    el avance, igual que ya hace el tinte vintage de la Fase 4."""

    def test_la_fase_6_declara_un_tinte_verde(self) -> None:
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        assert fase6.tinte is not None
        (r, g, b), alfa = fase6.tinte
        assert g > r and g > b, f"el tinte del despertar debería ser verde: {(r, g, b)}"
        assert 0.0 < alfa <= 0.2, "demasiado fuerte para no leerse como un filtro"

    def test_se_intensifica_al_avanzar_el_tramo(self, escena) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase6 = FASES[5]
        _posicionar_sin_fisica(escena, fase6.desde_columna + 3)
        temprano = escena._post_processing._tint_alpha
        _posicionar_sin_fisica(escena, fase6.desde_columna + trazado.ANCHO_SECCION - 1)
        tarde = escena._post_processing._tint_alpha
        assert tarde > temprano


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


class TestLaAnomaliaAmbiguaDeLaFase1:
    """GAP-059/AUD-478 — el punto 7 de la crítica de diseño del dueño
    (2026-08-14): «si el jugador no la vio, no pasa nada; si la vio, ¿qué
    fue eso?». Distinta del fantasma de Teresa —ésa se confirma con un
    `MessageTrigger` y un nombre; esta anomalía no se confirma nunca: sin
    sonido, sin disparador, sin diálogo, y visible menos de un segundo."""

    def _entrar_a_fase_1(self, escena) -> None:
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(1))
        assert escena.fase.numero == 1

    def test_dura_menos_de_un_segundo(self, escena) -> None:
        assert escena.DURACION_ANOMALIA_FASE1 < 1.0

    def test_no_se_dibuja_si_no_esta_activa(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import siluetas

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_contorno",
            lambda *a, **kw: llamadas.append(a),
        )
        self._entrar_a_fase_1(escena)
        escena._anomalia_fase1 = 0.0
        escena._dibujar_anomalia_fase1(pygame.Surface((800, 600)), pygame.Vector2())
        assert llamadas == []

    def test_se_dibuja_mientras_esta_activa(self, escena, monkeypatch) -> None:
        from src.stages.stage4_1 import siluetas, trazado

        llamadas = []
        monkeypatch.setattr(
            siluetas, "dibujar_contorno",
            lambda *a, **kw: llamadas.append(a[1]),  # la forma es el 2º posicional
        )
        self._entrar_a_fase_1(escena)
        escena._anomalia_fase1 = escena.DURACION_ANOMALIA_FASE1
        # La figura se ancla al mundo, no a la pantalla (a diferencia de la
        # Bruja) — hay que centrar la cámara sobre su columna para que
        # caiga dentro de los límites de pantalla que comprueba el dibujo.
        centro_x = trazado.COLUMNA_ANOMALIA_FASE1 * trazado.TS - settings.INTERNAL_WIDTH / 2
        escena._dibujar_anomalia_fase1(
            pygame.Surface((800, 600)), pygame.Vector2(centro_x, 0))
        assert llamadas == [siluetas._figura_lejana]

    def test_solo_ocurre_dentro_de_la_fase_1(self, escena) -> None:
        """Al salir de la Fase 1 el contador se apaga — no se queda a
        medias esperando volver, igual que `_bruja_este_rayo` se reinicia
        al salir de la Fase 3."""
        self._entrar_a_fase_1(escena)
        escena._anomalia_fase1 = escena.DURACION_ANOMALIA_FASE1
        _posicionar_sin_fisica(escena, _dentro_de_la_fase(2))
        escena._actualizar_anomalia_fase1(1 / 60)
        assert escena._anomalia_fase1 == 0.0

    def test_eventualmente_ocurre_dentro_de_la_fase(self, escena) -> None:
        """Forzando el temporizador a cero —igual que ya hace
        `TestLaSombraDelGavilan.test_cruza_tras_el_silencio`—, sin
        depender de cuánto tarde el azar de verdad."""
        self._entrar_a_fase_1(escena)
        escena._proxima_anomalia_fase1 = 0.0
        escena._actualizar_anomalia_fase1(1 / 60)
        assert escena._anomalia_fase1 > 0.0

    def test_no_toca_sonido_ni_dialogo_ni_disparadores(self, escena) -> None:
        """Es lo que la vuelve «ambigua» y no un evento: sin bus, sin
        `Disparador`, sin `MessageTrigger` — sólo dibujo, igual que la
        Bruja de la Fase 3 (AUD-475)."""
        self._entrar_a_fase_1(escena)
        antes = len(escena._stage_data.disparadores)
        disparados_antes = [mt.triggered for mt in escena._stage_data.message_triggers]
        escena._anomalia_fase1 = escena.DURACION_ANOMALIA_FASE1
        escena._dibujar_anomalia_fase1(pygame.Surface((800, 600)), pygame.Vector2())
        assert len(escena._stage_data.disparadores) == antes
        assert [mt.triggered for mt in escena._stage_data.message_triggers] == disparados_antes

    def test_no_revienta_dibujandola(self, escena) -> None:
        self._entrar_a_fase_1(escena)
        escena._anomalia_fase1 = escena.DURACION_ANOMALIA_FASE1
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


def _generador():
    """El módulo del generador, importable desde `tools/`."""
    import sys
    from pathlib import Path

    raiz = Path(__file__).resolve().parent.parent
    if str(raiz / "tools") not in sys.path:
        sys.path.insert(0, str(raiz / "tools"))
    import generate_stage4_1

    return generate_stage4_1


class TestElMapaSigueAtadoASuGenerador:
    """AUD-495 — esto comparaba el TMX con `generar()` **byte a byte**, y
    dejó de funcionar en cuanto el mapa se abrió en Tiled para pintarle el
    arte de la Fase 1: al guardar, Tiled sube su `tiledversion`, reordena
    las propiedades alfabéticamente, normaliza los flotantes (`70.0` → `70`)
    y cierra los objetos vacíos con `/>`. Ninguna de esas diferencias
    cambia el nivel, y perseguirlas sería reimplementar el serializador de
    Tiled — que volvería a cambiar en la versión siguiente.

    Lo que AUD-115 quería proteger de verdad sigue protegido aquí, y con
    los mismos dientes: que la geometría no se separe de `trazado.py`.
    """

    def test_la_geometria_es_la_del_generador(self) -> None:
        fallos = _generador().comparar_geometria()
        assert not fallos, (
            "la geometría del mapa ya no es la de trazado.py: "
            + "; ".join(fallos)
        )

    def test_el_arte_pintado_a_mano_no_se_compara(self) -> None:
        """La otra mitad del contrato: las capas de arte son de quien las
        pinta en Tiled, y el generador no opina sobre ellas."""
        gen = _generador()
        geo = gen.geometria_de(gen.DESTINO.read_text(encoding="utf-8"))
        for capa in gen.CAPAS_DE_ARTE:
            assert capa not in geo["capas"]
        assert "Terrain" in geo["capas"], (
            "el suelo SÍ es del generador y tiene que seguir comparándose"
        )

    def test_una_diferencia_real_de_geometria_se_nota(self) -> None:
        """Sin esto, la prueba de arriba pasaría aunque no comparara nada."""
        gen = _generador()
        original = gen.geometria_de(gen.generar())
        movido = gen.geometria_de(gen.generar().replace(
            '<layer id="4" name="Terrain"', '<layer id="4" name="Terrain" ',
        ).replace(",2,2,2,2,2,2", ",0,0,0,0,0,0", 1))
        assert movido != original


class TestRegenerarNoBorraElArte:
    """AUD-495 — el pie de plomo. El 4-1 tiene 13 240 celdas pintadas a
    mano; `generar()` escribe esas capas a ceros, así que ejecutar el
    generador sin más las borraba todas y sin aviso."""

    def test_el_mapa_actual_tiene_arte_que_proteger(self) -> None:
        assert _generador().tiene_arte_pintado() is True

    def test_un_mapa_sin_arte_no_dispara_el_seguro(self, tmp_path) -> None:
        import xml.etree.ElementTree as ET

        gen = _generador()
        crudo = gen.generar()
        raiz = ET.fromstring(crudo)
        pintadas = [
            c.get("name") for c in raiz.findall("layer")
            if c.get("name") in gen.CAPAS_DE_ARTE
            and any(g.strip() not in ("", "0")
                    for g in (c.findtext("data") or "").split(","))
        ]
        assert pintadas == [], (
            "lo que produce el generador no debería traer arte pintado"
        )


class TestElNivelSePuedeJugar:
    def test_tiene_salida_spawn_y_checkpoints(self, escena) -> None:
        assert escena._stage_data.next_trigger is not None
        assert escena._stage_data.spawn_point is not None
        assert len(escena._stage_data.checkpoints) >= 1

    def test_hay_seis_checkpoints_uno_por_fase(self, escena) -> None:
        """AUD-516 — antes había 32 (cada 28 columnas, 448 px), muy por
        debajo de los 700-1200 px que recomienda `66_GUIA_DE_LEVEL_DESIGN.md`
        §1 para el caso general. Reaparecer casi al instante anulaba la
        tensión que pide un escenario *psicológico de terror*: morir no
        costaba nada. Bajado a uno por fase (6 en total), a propósito muy
        por encima de esa recomendación general — la propia guía ya admite
        el tramo «deliberadamente duro» (el foso de Stage 0 es el
        precedente) y aquí el guion entero es ese tramo."""
        from src.stages.stage4_1 import trazado

        puntos = trazado.checkpoints()
        assert len(puntos) <= 6
        fases_cubiertas = {trazado.fase_de_la_columna(c) for c, _f in puntos}
        assert fases_cubiertas == {1, 2, 3, 4, 5, 6}, (
            "cada fase debe tener su propio checkpoint, no dos en la misma "
            "y ninguna sin cubrir"
        )

    def test_la_escena_y_el_mapa_dicen_la_misma_zona(self, escena) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        assert Stage4_1.ZONE == 4
        assert escena._stage_data.zone == Stage4_1.ZONE


class TestLaLiberacionDeLosEspiritus:
    """AUD-474 — ascender no es sólo caminar hasta el final de la sección.

    Antes de este lote, `_fundido_del_espiritu` sólo miraba `avance`: quien
    cruzaba corriendo sin detenerse liberaba al espíritu exactamente igual
    que quien se paraba a interactuar. La crítica de diseño pegada por el
    dueño (2026-08-14, puntos 15-16) señaló justo esto: la ascensión debía
    sentirse como algo que el jugador **hace**, no algo que pasa solo.
    """

    def test_el_generador_coloca_un_disparador_no_automatico_por_espiritu(
        self,
    ) -> None:
        """Sin `automatico=False` esto no exige ninguna acción — sería el
        mismo defecto con otro nombre."""
        import re
        from pathlib import Path

        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        tmx = Path("assets/maps/stage4_1/stage4_1.tmx").read_text(encoding="utf-8")
        con_espiritu = [f for f in FASES if f.espiritu is not None]
        assert len(con_espiritu) == 3
        for fase in con_espiritu:
            evento = trazado.evento_de_liberacion(fase.numero)
            bloque = re.search(
                rf'<object[^>]*type="EventTrigger"[^>]*>.*?'
                rf'name="evento" value="{evento}".*?</object>',
                tmx, re.S,
            )
            assert bloque is not None, f"no hay EventTrigger para {evento}"
            assert 'name="automatico" type="bool" value="false"' in bloque.group(0), (
                f"el disparador de {evento} debe exigir el botón de usar"
            )

    def test_sin_liberar_el_espiritu_no_asciende(self, escena) -> None:
        """Control: cruzar la sección entera sin pulsar nada dej al
        espíritu visible hasta el borde — nunca se desvanece."""
        from src.stages.stage4_1.stage4_1 import Stage4_1

        fundido_al_final = Stage4_1._fundido_del_espiritu(0.98, liberado=False)
        assert fundido_al_final == 1.0

    def test_liberado_el_espiritu_asciende_igual_que_antes(self) -> None:
        from src.stages.stage4_1.stage4_1 import Stage4_1

        fundido_al_final = Stage4_1._fundido_del_espiritu(0.98, liberado=True)
        assert fundido_al_final == pytest.approx(min(1.0, 0.02 / 0.15))

    def test_espiritu_liberado_lee_el_disparador_correcto(self, escena) -> None:
        from src.framework.stage.interactables import Disparador
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        assert escena._espiritu_liberado(fase_venado) is False

        escena._stage_data.disparadores.append(Disparador(
            rect=pygame.Rect(0, 0, 1, 1),
            evento=trazado.evento_de_liberacion(fase_venado.numero),
            automatico=False,
            disparado=True,
        ))
        assert escena._espiritu_liberado(fase_venado) is True

    def test_el_acorde_de_liberacion_suena_una_vez_al_liberar(self, escena, monkeypatch) -> None:
        """AUD-568 — propuesta "nivel cine": un acorde propio, distinto
        de la voz, en el mismo instante en que se libera de verdad."""
        from src.framework.stage.interactables import Disparador
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        fase_venado = next(f for f in FASES if f.espiritu == 0)
        _posicionar_sin_fisica(escena, fase_venado.desde_columna + 5)

        sonidos = []
        monkeypatch.setattr(
            escena, "_play_sfx_named",
            lambda nombre, **kw: sonidos.append(nombre),
        )
        escena._actualizar_voz_del_espiritu()
        assert "sfx_environment_liberacion_espiritu" not in sonidos, (
            "no debería sonar antes de liberarlo"
        )

        escena._stage_data.disparadores.append(Disparador(
            rect=pygame.Rect(0, 0, 1, 1),
            evento=trazado.evento_de_liberacion(fase_venado.numero),
            automatico=False,
            disparado=True,
        ))
        escena._actualizar_voz_del_espiritu()
        assert sonidos.count("sfx_environment_liberacion_espiritu") == 1

        # Una segunda pasada del mismo fotograma no debería repetirlo.
        escena._actualizar_voz_del_espiritu()
        assert sonidos.count("sfx_environment_liberacion_espiritu") == 1

    def test_el_archivo_del_acorde_de_liberacion_existe(self) -> None:
        from src.engine.core import settings

        ruta = settings.ASSETS_DIR / "sfx" / "environment" / "sfx_environment_liberacion_espiritu.wav"
        assert ruta.exists()

    def test_el_mensaje_final_cuenta_cuantos_se_liberaron(self, escena) -> None:
        from src.framework.stage.interactables import Disparador
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES

        def _final() -> str:
            escena._actualizar_mensaje_final()
            return next(
                mt.text for mt in escena._stage_data.message_triggers
                if mt.text.startswith(trazado.TEXTO_FINAL_BASE)
            )

        assert _final() == f"{trazado.TEXTO_FINAL_BASE} Ninguno de los espíritus encontró descanso."

        con_espiritu = [f for f in FASES if f.espiritu is not None]
        escena._stage_data.disparadores.append(Disparador(
            rect=pygame.Rect(0, 0, 1, 1),
            evento=trazado.evento_de_liberacion(con_espiritu[0].numero),
            automatico=False, disparado=True,
        ))
        assert "Sólo 1 de 3" in _final()

        for fase in con_espiritu[1:]:
            escena._stage_data.disparadores.append(Disparador(
                rect=pygame.Rect(0, 0, 1, 1),
                evento=trazado.evento_de_liberacion(fase.numero),
                automatico=False, disparado=True,
            ))
        assert _final() == (
            f"{trazado.TEXTO_FINAL_BASE} Los tres espíritus descansan por fin."
        )

    def test_el_mensaje_no_se_toca_una_vez_disparado(self, escena) -> None:
        """No hay que cambiarle el texto a un cartel que el jugador ya
        está leyendo."""
        from src.stages.stage4_1 import trazado

        objetivo = next(
            mt for mt in escena._stage_data.message_triggers
            if mt.text == trazado.TEXTO_FINAL_BASE
        )
        objetivo.triggered = True
        objetivo.text = "ya se mostró esto"
        escena._actualizar_mensaje_final()
        assert objetivo.text == "ya se mostró esto"


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
