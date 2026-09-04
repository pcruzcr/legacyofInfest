"""Batería de auditoría de nivel: carga cada TMX real, mide su diseño y
verifica invariantes de completabilidad y alcance.

Qué mide y qué no (mismo pacto que `level_metrics`):
--------------------------------------------------------
Estas pruebas responden preguntas con respuesta comprobable: ¿el nivel carga?
¿tiene spawn y salida? ¿se puede llegar de uno a otra con la física real del
jugador? ¿hay tramos sin checkpoint que castiguen el reintento? El "fun
factor" no se mide aquí: se reporta en `reports/auditoria_juego/` a partir de
estos números más el análisis de diseño.

Los umbrales de salto salen de `settings` (vía `JumpEnvelope`), así que si
cambia la física las conclusiones se recalculan solas.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

from src.framework.entities import entity_factory
from src.framework.entities.boss_base import BossBase
from src.framework.stage.level_metrics import JumpEnvelope, analyse_stage
from src.framework.stage.stage_loader import StageLoader

RAIZ = Path(__file__).resolve().parent.parent.parent
MAPAS = RAIZ / "assets" / "maps"


# ── inventario de niveles ────────────────────────────────────────

#: (id, ruta TMX relativa, ¿tiene NextTrigger?, ¿tiene jefe?, es_laboratorio)
NIVELES: list[tuple[str, str, bool, bool, bool]] = [
    ("stage0", "stage0/stage0.tmx", True, False, False),
    ("stage_mecanicas", "stage_mecanicas/stage_mecanicas.tmx", True, False, True),
    ("stage_cenital", "stage_cenital/stage_cenital.tmx", False, False, True),
    ("stage1_1", "stage1_1/stage1_1.tmx", True, False, False),
    ("stage1_2_la_soda", "stage1_2_la_soda/stage1_2_la_soda.tmx", True, False, False),
    ("stage1_3_las_aulas", "stage1_3_las_aulas/stage1_3_las_aulas.tmx", True, False, False),
    ("stage2_1_oficinas", "stage2_1_oficinas/stage2_1_oficinas.tmx", True, False, False),
    ("stage2_2", "stage2_2/stage2_2.tmx", True, False, False),
    ("lobby_datacenter", "lobby_datacenter/lobby_datacenter.tmx", True, False, False),
    (
        "stage3_1_la_entrada_de_piedra",
        "stage3_1_la_entrada_de_piedra/stage3_1_la_entrada_de_piedra.tmx",
        True,
        False,
        False,
    ),
    # AUD-595 — corrige a AUD-586: el NextTrigger de hall NO era un
    # fantasma. El hook de la escena era un `pass`, pero la completación no
    # pasa por él: `ProgressionSystem.check_next_trigger` marca el nivel al
    # tocar el rectángulo, y `hall` es la ranura lineal 3-2 de STAGE_ORDER —
    # sin salida, la campaña entera queda bloqueada ahí (lo gritan
    # `test_guardado_y_cadena` y `test_los_next_trigger`). El trigger volvió
    # al TMX tal estaba; lo que AUD-586 arregló de verdad fue el env del
    # subprocess del grader y el texto del aviso.
    ("hall", "hall/hall.tmx", True, False, False),
    ("stage3_3_el_patio", "stage3_3_el_patio/stage3_3_el_patio.tmx", True, False, False),
    ("stage3_4_boss_gavilan", "stage3_4_boss_gavilan/stage3_4_boss_gavilan.tmx", False, True, False),
    ("boss_venado", "boss_venado/boss_venado.tmx", False, True, False),
    ("boss_rey", "boss_rey/boss_rey.tmx", False, True, False),
    ("boss_paburu", "boss_paburu/boss_paburu.tmx", False, True, False),
]

NIVELES_IDS = [n[0] for n in NIVELES]

#: Mecánicas de transporte que el analizador estático de `level_metrics` no
#: modela: si la salida depende de ellas, "salida inalcanzable" es un falso
#: negativo del analizador, no un nivel roto (documentado en level_metrics).
#: Nombres reales de las dataclasses ECS (components.py), en español.
_MECANICAS_DINAMICAS = {
    "PlataformaMovil", "PlataformaHundible", "BloqueRitmico", "Resorte",
    "ZonaDeViento", "Liana", "Tirolesa",
}

#: Niveles con tramos largos sin checkpoint POR DECISIÓN documentada del
#: dueño (AUD-516: checkpoints 32→6 en el slot 4-1, 14 km de mapa).
_SIN_CHECKPOINT_POR_DECISION = {
    }


@pytest.fixture(scope="module")
def _video():
    pygame.init()
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))
    yield


@pytest.fixture(autouse=True)
def _entidades(_video):
    entity_factory.ensure_registered()
    yield
    # AUD-601 — mismo motivo que el desmontaje de test_cadena_de_niveles:
    # este módulo construye los 16 escenarios y llena la caché de
    # `AssetLoader` con hojas de sprites escaladas a cada uno. Sin esta
    # limpieza, la SUITE COMPLETA (que ya trae memoria ocupada por los
    # módulos anteriores) llegaba al viñeteado de `PostProcessing` con el
    # equipo thrasheando: el `np.sqrt` de una matriz de 480k entradas pasó
    # de microsegundos a minutos y el run entero parecía colgado.
    from src.engine.utils.asset_loader import AssetLoader
    from src.framework.stage.stage_loader import StageLoader

    AssetLoader.clear_cache()
    StageLoader.clear_tmx_cache()


# ── lectura del TMX crudo (densidad y capas) ─────────────────────


def _leer_tmx(tmx_path: Path) -> ET.Element:
    return ET.parse(tmx_path).getroot()


def _densidad_terreno(tmx_path: Path) -> float:
    """Celdas no vacías de la capa Terrain / total de celdas."""
    root = _leer_tmx(tmx_path)
    for layer in root.findall(".//layer"):
        if layer.get("name") == "Terrain":
            data = layer.find("data")
            if data is None or data.get("encoding") != "csv" or data.text is None:
                return 0.0
            celdas = [int(c) for c in data.text.strip().split(",") if c.strip()]
            if not celdas:
                return 0.0
            no_vacias = sum(1 for gid in celdas if gid != 0)
            return no_vacias / len(celdas)
    return 0.0


def _capas(tmx_path: Path) -> list[str]:
    root = _leer_tmx(tmx_path)
    return [layer.get("name", "") for layer in root.findall(".//layer")]


def _componentes_planos(data) -> list[object]:
    """`stage.componentes` son grupos (listas) de dataclasses ECS: se
    aplanan para contar por tipo y buscar cerca de la salida."""
    planos: list[object] = []
    for grupo in getattr(data, "componentes", []) or ():
        if isinstance(grupo, (list, tuple)):
            planos.extend(grupo)
        else:
            planos.append(grupo)
    return planos


def _excusa_de_salida(data, radio: int = 400) -> str:
    """Motivo por el que el analizador estático puede no ver la ruta a la
    salida, o cadena vacía si no hay excusa (hallazgo real)."""
    salida = getattr(data, "next_trigger", None)
    if salida is None:
        return ""
    # Plataformas one-way (Platform) cerca de la salida: el analizador no
    # las modela (sólo ve `collision_rects`, no `one_way_rects`).
    cerca_ow = [
        r for r in getattr(data, "one_way_rects", []) or ()
        if abs(r.centerx - salida.centerx) < radio
    ]
    if cerca_ow:
        return f"{len(cerca_ow)} plataforma(s) one-way cerca de la salida"
    # Mecánicas dinámicas cerca de la salida: mismo motivo. Las dataclasses
    # ECS de transporte (Resorte, PlataformaMovil...) sí exponen rect;
    # BloqueRitmico no (la posición vive en su Transform hermano).
    dinamicas = [
        type(c).__name__ for c in _componentes_planos(data)
        if hasattr(c, "rect") and abs(c.rect.centerx - salida.centerx) < radio
        and type(c).__name__ in _MECANICAS_DINAMICAS
    ]
    # Bloques empujables/destructibles: también abren caminos que el
    # analizador estático no ve.
    empujables = [
        type(e).__name__ for e in getattr(data, "empujables", []) or ()
        if hasattr(e, "rect") and abs(e.rect.centerx - salida.centerx) < radio
    ] + [
        type(e).__name__ for e in getattr(data, "destructibles", []) or ()
        if hasattr(e, "rect") and abs(e.rect.centerx - salida.centerx) < radio
    ]
    if dinamicas or empujables:
        return "mecánicas dinámicas cerca de la salida: " + ", ".join(
            sorted(set(dinamicas + empujables)))
    # Nivel de plataformas rítmicas: si el terreno estático es casi inexistente
    # (<5 %) y el mapa declara bloques rítmicos, la salida depende de ellos
    # por construcción (stage4_1c: densidad 2.8 %, 61 BloqueRitmico).
    planos = _componentes_planos(data)
    if any(type(c).__name__ == "BloqueRitmico" for c in planos):
        dens = _densidad_terreno(_tmx_de(data))
        if dens < 0.05:
            return f"nivel de bloques rítmicos (terreno estático {dens:.1%})"
    return ""


def _tmx_de(data) -> Path:
    """Ruta del TMX que cargó este StageData (para re-leer densidad)."""
    mapa = getattr(data, "mapa", None) or getattr(data, "_tmx", None)
    if mapa is not None:
        return Path(str(mapa))
    ruta = getattr(data, "tmx_path", None)
    if ruta is not None:
        return Path(str(ruta))
    # Fallback: buscar por stage_id en el inventario.
    stage_id = getattr(data, "stage_id", "")
    for _, tmx_rel, _, _, _ in NIVELES:
        if tmx_rel.startswith(stage_id):
            return MAPAS / tmx_rel
    return MAPAS / "stage0" / "stage0.tmx"


# ── 1. carga e invariantes básicas ───────────────────────────────


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_el_nivel_carga(stage_id, tmx_rel, _, __, ___) -> None:
    data = StageLoader.load(MAPAS / tmx_rel)
    assert data.spawn_point is not None
    assert data.map_pixel_size[0] > 0 and data.map_pixel_size[1] > 0


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_el_nivel_tiene_terreno_jugable(stage_id, tmx_rel, _, __, ___) -> None:
    """La capa Terrain no puede estar vacía: un nivel sin suelo no se juega."""
    assert _densidad_terreno(MAPAS / tmx_rel) > 0.0
    assert "Terrain" in _capas(MAPAS / tmx_rel)


@pytest.mark.parametrize("stage_id,tmx_rel,tiene_salida,tiene_jefe,_", NIVELES, ids=NIVELES_IDS)
def test_el_nivel_es_completable(stage_id, tmx_rel, tiene_salida, tiene_jefe, _) -> None:
    """Todo nivel declara salida (NextTrigger) o jefe (BossBase): sin uno de
    los dos, el nivel no se puede completar."""
    data = StageLoader.load(MAPAS / tmx_rel)
    tiene_next = data.next_trigger is not None
    # Los jefes entran por dos caminos: `BossSpawn` con propiedad `boss`
    # (venado, rey, paburu) o entidad registrada directamente (gavilán,
    # AUD-106). `isinstance(BossBase)` los detecta a todos.
    jefes = [e for e in data.entity_list if isinstance(e, BossBase)]
    assert tiene_next == tiene_salida, (
        f"{stage_id}: NextTrigger esperado={tiene_salida}, real={tiene_next}"
    )
    assert (len(jefes) > 0) == tiene_jefe, (
        f"{stage_id}: jefe esperado={tiene_jefe}, real={len(jefes)}"
    )


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_el_next_trigger_no_esta_fuera_del_mapa(stage_id, tmx_rel, _, __, ___) -> None:
    """Un NextTrigger fuera de los límites del mapa no se puede tocar nunca:
    o sobra o está mal puesto. (AUD-538: boss_paburu tenía uno fantasma en
    y=-64 que ni el código ni el flujo de victoria usaban; se eliminó y
    NIVELES quedó consistente: sin salida declarada.)"""
    data = StageLoader.load(MAPAS / tmx_rel)
    salida = data.next_trigger
    if salida is None:
        return
    ancho, alto = data.map_pixel_size
    assert 0 <= salida.left < ancho and 0 <= salida.top < alto, (
        f"{stage_id}: NextTrigger fuera del mapa: {salida}"
    )


# ── 2. análisis de diseño con la física real ─────────────────────


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_salida_alcanzable_desde_spawn(stage_id, tmx_rel, _, __, ___) -> None:
    """Si el nivel declara salida, debe existir una cadena de saltos/rampas
    del spawn a ella — salvo que la ruta dependa de mecánicas que el
    analizador estático no modela (one-way platforms, bloques rítmicos,
    resortes, vinas...), lo que se registra como excusa documentada."""
    data = StageLoader.load(MAPAS / tmx_rel)
    if data.next_trigger is None:
        pytest.skip(f"{stage_id} no declara NextTrigger")
    report = analyse_stage(data)
    if report.exit_reachable:
        return
    excusa = _excusa_de_salida(data)
    assert excusa, (
        f"{stage_id}: salida inalcanzable desde el spawn y sin excusa "
        f"conocida del analizador estático"
    )


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_huecos_y_repechos_reportados(stage_id, tmx_rel, _, __, ___) -> None:
    """Registra la geometría del nivel en el reporte: huecos exigentes,
    repechos imposibles y plataformas sin ruta."""
    data = StageLoader.load(MAPAS / tmx_rel)
    report = analyse_stage(data)
    env = JumpEnvelope.from_settings()
    assert report.total_platforms > 0 or not data.collision_rects, (
        f"{stage_id}: sin geometría de colisión declarada"
    )
    # La envolvente de salto debe ser físicamente coherente (AUD-504).
    assert env.max_height > 0 and env.max_gap > 0


def test_los_niveles_de_referencia_no_bloquean() -> None:
    """stage0 y stage_mecanicas son la referencia que los estudiantes copian:
    no pueden tener repechos imposibles ni salida inalcanzable sin excusa."""
    for tmx_rel in ("stage0/stage0.tmx", "stage_mecanicas/stage_mecanicas.tmx"):
        data = StageLoader.load(MAPAS / tmx_rel)
        report = analyse_stage(data)
        assert len(report.impossible_ledges) == 0, (
            f"{tmx_rel}: repechos imposibles={len(report.impossible_ledges)}"
        )
        if not report.exit_reachable:
            assert _excusa_de_salida(data), f"{tmx_rel}: salida rota sin excusa"


# ── 3. ritmo de reintento (checkpoints) ──────────────────────────


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_checkpoint_gaps_registrados(stage_id, tmx_rel, _, __, ___) -> None:
    """Los tramos entre checkpoints quedan registrados en el reporte. El
    umbral de 1200 px (~13 s caminando) es el punto donde repetir un tramo
    deja de enseñar y empieza a castigar (level_metrics). AUD-537: stage2_1
    pasó de 0 checkpoints en 3200 px a 7 (≤424 px de tramo)."""
    data = StageLoader.load(MAPAS / tmx_rel)
    report = analyse_stage(data)
    if not report.checkpoint_gaps:
        return  # sin checkpoints es una decisión de diseño (arenas de boss)
    peor = max(report.checkpoint_gaps)
    if peor <= 1200.0:
        return
    assert stage_id in _SIN_CHECKPOINT_POR_DECISION, (
        f"{stage_id}: tramo sin checkpoint de {peor:.0f} px (>1200 px "
        f"≈ 13 s de reintento) y sin decisión documentada"
    )


# ── 4. densidad y población (para el reporte) ────────────────────


@pytest.mark.parametrize("stage_id,tmx_rel,_,__,___", NIVELES, ids=NIVELES_IDS)
def test_densidad_y_poblacion_medidas(stage_id, tmx_rel, _, __, ___) -> None:
    """Mediciones que alimentan el reporte de level design. Los niveles sin
    enemigos deben estar justificados (laboratorio o traversal puro)."""
    data = StageLoader.load(MAPAS / tmx_rel)
    dens = _densidad_terreno(MAPAS / tmx_rel)
    enemigos = [e for e in data.entity_list if not isinstance(e, BossBase)]
    jefes = [e for e in data.entity_list if isinstance(e, BossBase)]
    assert 0.0 < dens <= 1.0
    sin_enemigos_esperados = {
        "stage_cenital",
        "boss_venado", "boss_rey", "boss_paburu",
    }
    if stage_id in sin_enemigos_esperados:
        assert len(enemigos) == 0, f"{stage_id}: se esperaba 0 enemigos"
    else:
        assert len(enemigos) > 0, f"{stage_id}: nivel de campaña sin enemigos"
    assert len(jefes) <= 1, f"{stage_id}: más de un jefe"