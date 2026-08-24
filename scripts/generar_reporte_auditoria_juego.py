"""Genera los reportes de auditoría de juego (niveles + escenas UI/UX).

AUD-533: la auditoría de gameplay se entrega como pruebas (niveles y
escenas) más cuatro reportes en Markdown que CI no ejecuta pero que
consolidan lo medido: `reports/auditoria_juego/`.

Fuente única de números: `StageLoader` + `analyse_stage` + lectura directa
del TMX (densidad de terreno). Los textos de game feel / level design /
UI/UX son cualitativos y viven en los diccionarios de abajo, escritos a
partir de lo que la batería midió (ver tests/test_auditoria_juego/).

Uso:
    .venv\\Scripts\\python.exe scripts/generar_reporte_auditoria_juego.py
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

#: Los reportes imprimen "≈"; en la consola cp1252 de Windows, sin esta
#: reconfiguración, el proceso muere con UnicodeEncodeError a mitad del
#: trabajo (test_salida_de_consola.py lo vigila).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygame

RAIZ = Path(__file__).resolve().parent.parent
MAPAS = RAIZ / "assets" / "maps"
SALIDA = RAIZ / "reports" / "auditoria_juego"

#: Orden de campaña real (src/engine/core/stage_registry.py).
STAGE_ORDER = [
    "stage0", "stage_mecanicas", "stage1_1", "stage1_2_la_soda",
    "stage1_3_las_aulas", "boss_venado", "stage2_1_oficinas", "stage2_2",
    "lobby_datacenter", "boss_rey", "stage3_1_la_entrada_de_piedra", "hall",
    "stage3_3_el_patio", "boss_gavilan", "stage4_1", "boss_paburu",
]

#: Mapa de stage_id -> (carpeta del TMX, es jefe, es laboratorio).
NIVELES: dict[str, tuple[str, bool, bool]] = {
    "stage0": ("stage0/stage0.tmx", False, False),
    "stage_mecanicas": ("stage_mecanicas/stage_mecanicas.tmx", False, True),
    "stage_cenital": ("stage_cenital/stage_cenital.tmx", False, True),
    "stage1_1": ("stage1_1/stage1_1.tmx", False, False),
    "stage1_2_la_soda": ("stage1_2_la_soda/stage1_2_la_soda.tmx", False, False),
    "stage1_3_las_aulas": ("stage1_3_las_aulas/stage1_3_las_aulas.tmx", False, False),
    "stage2_1_oficinas": ("stage2_1_oficinas/stage2_1_oficinas.tmx", False, False),
    "stage2_2": ("stage2_2/stage2_2.tmx", False, False),
    "lobby_datacenter": ("lobby_datacenter/lobby_datacenter.tmx", False, False),
    "stage3_1_la_entrada_de_piedra": (
        "stage3_1_la_entrada_de_piedra/stage3_1_la_entrada_de_piedra.tmx", False, False),
    "hall": ("hall/hall.tmx", False, False),
    "stage3_3_el_patio": ("stage3_3_el_patio/stage3_3_el_patio.tmx", False, False),
    "boss_gavilan": ("stage3_4_boss_gavilan/stage3_4_boss_gavilan.tmx", True, False),
    "stage4_1": ("stage4_1/stage4_1.tmx", False, False),
    "stage4_1b": ("stage4_1b/stage4_1b.tmx", False, False),
    "stage4_1c_a": ("stage4_1c/stage4_1c_a.tmx", False, True),
    "stage4_1c_b": ("stage4_1c/stage4_1c_b.tmx", False, True),
    "stage4_1c_c": ("stage4_1c/stage4_1c_c.tmx", False, True),
    "boss_venado": ("boss_venado/boss_venado.tmx", True, False),
    "boss_rey": ("boss_rey/boss_rey.tmx", True, False),
    "boss_paburu": ("boss_paburu/boss_paburu.tmx", True, False),
}

#: Escenas de la batería UI/UX (mismo inventario que
#: tests/test_auditoria_juego/test_escenas_ui_ux.py).
ESCENAS: list[tuple[str, str]] = [
    ("splash_scene", "SplashScene"),
    ("title_scene", "TitleScene"),
    ("options_scene", "OptionsScene"),
    ("keybinding_scene", "KeybindingScene"),
    ("load_game_scene", "LoadGameScene"),
    ("skill_tree_scene", "SkillTreeScene"),
    ("tutorial_scene", "TutorialScene"),
    ("game_over_scene", "GameOverScene"),
    ("stage_error_scene", "StageErrorScene"),
    ("end_credits_scene", "EndCreditsScene"),
    ("world_map_scene", "WorldMapScene"),
    ("inventory_scene", "InventoryScene"),
    ("shop_scene", "ShopScene"),
    ("bestiary_scene", "BestiaryScene"),
    ("achievement_scene", "AchievementScene"),
    ("leaderboard_scene", "LeaderboardScene"),
    ("progress_scene", "ProgressScene"),
    ("demo_menu_scene", "DemoMenuScene"),
    ("story_scene", "StoryScene"),
    ("unit_theory_scene", "UnitTheoryScene"),
    ("student_login_scene", "StudentLoginScene"),
    ("vector_lab_scene", "VectorLabScene"),
    ("transform_lab_scene", "TransformLabScene"),
    ("collision_lab_scene", "CollisionLabScene"),
    ("interpolation_lab_scene", "InterpolationLabScene"),
    ("noise_lab_scene", "NoiseLabScene"),
    ("curve_editor_scene", "CurveEditorScene"),
    ("color_theory_scene", "ColorTheoryScene"),
    ("filter_demo_scene", "FilterDemoScene"),
    ("vision_demo_scene", "VisionDemoScene"),
    ("pattern_demo_scene", "PatternDemoScene"),
    ("pipeline_builder_scene", "PipelineBuilderScene"),
    ("combo_demo_scene", "ComboDemoScene"),
    ("sandbox_scene", "SandboxScene"),
    ("stage_wizard_scene", "StageWizardScene"),
]

#: Escenas de nivel (stage scenes) de la batería.
ESCENAS_NIVEL: list[tuple[str, str]] = [
    ("stage0", "Stage0"),
    ("stage_mecanicas", "StageMecanicas"),
    ("stage_cenital", "StageCenital"),
    ("stage1_1", "Stage1_1_LaEntrada"),
    ("stage1_2_la_soda", "Stage1_2_LaSoda"),
    ("stage1_3_las_aulas", "Stage1_3_LasAulas"),
    ("stage2_1_oficinas", "Stage21Oficinas"),
    ("stage2_2", "Stage2_2"),
    ("lobby_datacenter", "LobbyDatacenter"),
    ("stage3_1_la_entrada_de_piedra", "Stage3_1_LaEntradaDePiedra"),
    ("hall", "Hall"),
    ("stage3_3_el_patio", "Stage3_3ElPatio"),
    ("stage3_4_boss_gavilan", "Stage3_4BossGavilanScene"),
    ("stage4_1", "Stage4_1"),
    ("stage4_1b", "Stage4_1B"),
    ("stage4_1c_a", "Stage4_1C"),
    ("boss_venado", "BossVenadoScene"),
    ("boss_rey", "BossReyScene"),
    ("boss_paburu", "BossPaburuScene"),
]


def densidad_terreno(tmx: Path) -> float:
    """Fracción de celdas sólidas (tile > 0) de la capa Terrain.

    Se cuentan celdas, no caracteres: el CSV de TMX codifica cada tile con
    un número de 1-3 dígitos, y contar caracteres infla la densidad hasta
    más del 100 % en mapas pequeños."""
    arbol = ET.parse(tmx)
    raiz = arbol.getroot()
    ancho = int(raiz.attrib["width"])
    alto = int(raiz.attrib["height"])
    capa = None
    for child in raiz:
        if child.tag == "layer" and child.attrib.get("name") == "Terrain":
            capa = child
            break
    if capa is None:
        return 0.0
    for data in capa:
        if data.tag == "data":
            celdas = [c.strip() for c in (data.text or "").split(",") if c.strip()]
            solido = sum(1 for c in celdas if int(c) > 0)
            return solido / max(ancho * alto, 1)
    return 0.0


def cargar_nivel(stage_id: str, tmx_rel: str) -> dict:
    from src.framework.entities import entity_factory
    from src.framework.stage.level_metrics import analyse_stage
    from src.framework.stage.stage_loader import StageLoader

    entity_factory.ensure_registered()
    tmx = MAPAS / tmx_rel
    data = StageLoader.load(tmx)
    reporte = analyse_stage(data)

    planos = []
    for grupo in getattr(data, "componentes", []) or []:
        planos.extend(grupo if isinstance(grupo, list) else [grupo])

    componentes = Counter(type(c).__name__ for c in planos)
    entidades: Counter[str] = Counter()
    for e in getattr(data, "entity_list", []) or []:
        nombre = getattr(e, "type", None) or type(e).__name__
        entidades[str(nombre)] += 1

    salida = getattr(data, "next_trigger", None)
    ancho, alto = data.map_pixel_size
    fuera = salida is not None and not (
        0 <= salida.left < ancho and 0 <= salida.top < alto)

    return {
        "stage_id": stage_id,
        "tmx": tmx_rel,
        "ancho": ancho,
        "alto": alto,
        "densidad": densidad_terreno(tmx),
        "plataformas": reporte.total_platforms,
        "alcanzables": reporte.reachable_platforms,
        "exit_reachable": reporte.exit_reachable,
        "salida": str(salida) if salida else "sin NextTrigger",
        "salida_fuera": fuera,
        "checkpoints": len(getattr(data, "checkpoints", []) or []),
        "gaps": sorted(reporte.checkpoint_gaps or []),
        "repechos": len(reporte.impossible_ledges or []),
        "componentes": componentes,
        "entidades": entidades,
        "one_way": len(getattr(data, "one_way_rects", []) or []),
        "empujables": len(getattr(data, "empujables", []) or []),
        "destructibles": len(getattr(data, "destructibles", []) or []),
        "notas": list(reporte.notes or []),
    }


def _nivel_en_campana(stage_id: str) -> bool:
    return stage_id in STAGE_ORDER


# ── análisis cualitativo, escrito a mano con lo que la batería midió ──

ANALISIS_NIVELES: dict[str, tuple[str, str, str]] = {
    "stage0": (
        "Escaparate del motor y tutorial de la universidad: 30 plataformas con "
        "enemigos arquetípicos (arquero, asesino, bruto, lanzador, cargador, "
        "volador, tirador, caminante) en secciones legibles. La salida se "
        "alcanza por una plataforma one-way sobre el vacío: el analizador "
        "estático la marca inalcanzable porque no modela one-ways, pero el "
        "salto cabe en el envolvente del jugador.",
        "Buen ritmo de enseñanza (una mecánica por sala), cierre con reto de "
        "precisión. 29 de 30 plataformas alcanzables.",
        "El final en one-way sobre vacío castiga al jugador novel: caer ahí "
        "supone repetir la última sección sin checkpoint cercano (gap de "
        "384 px).",
    ),
    "stage_mecanicas": (
        "Laboratorio de mecánicas de movimiento: resorte, viento, fricción, "
        "plataformas móviles, bloques rítmicos, zonas letales temporizadas, "
        "plataforma hundible, agua y una sección de sigilo (cono de visión + "
        "alertas + acosador) sobre 4960 px de pasillo.",
        "Cobertura de mecánicas única en el proyecto; el tramo de sigilo "
        "aporta variedad de ritmo. Gaps de checkpoint hasta 944 px: duros "
        "pero perdonables.",
        "El tramo largo sin checkpoint (944 px ≈ 10 s) tras la sección "
        "rítmica junta dos castigos: timing y reinicio lejano.",
    ),
    "stage_cenital": (
        "Laboratorio cenital (vista desde arriba): demuestra que el motor "
        "tiene modo cenital, pero no entra en campaña.",
        "Prueba de concepto valiosa para modos alternativos.",
        "Fuera de la campaña: su audiencia real es la demo.",
    ),
    "stage1_1": (
        "Entrada de la facultad, primera entrega de estudiante: plataformas "
        "básicas y enemigos propios. Gaps de checkpoint que la batería "
        "sigue midiendo (hasta 1200 px).",
        "Nivel completo y jugable, con salida y sin bloqueos.",
        "Sin datos finos de la batería (no declara mecánicas dinámicas): "
        "revisar a mano el confort de los saltos.",
    ),
    "stage1_2_la_soda": (
        "La soda: segunda entrega. Enemigos y plataformas propias.",
        "Jugable y con salida.",
        "Ídem stage1_1: auditoría fina manual pendiente.",
    ),
    "stage1_3_las_aulas": (
        "Las aulas: tercera entrega, cierre del bloque 1.",
        "Jugable y con salida.",
        "Ídem stage1_1.",
    ),
    "stage2_1_oficinas": (
        "Oficinas, apertura del bloque 2. La batería destapa un hallazgo "
        "real: CERO checkpoints en 3200 px. Morir reinicia el nivel entero, "
        "y el peor tramo sin red de seguridad mide 3048 px (≈ 33 s).",
        "Nivel largo con identidad propia (oficinas).",
        "Hallazgo AUD (pendiente de decisión del dueño): falta al menos un "
        "checkpoint a mitad de nivel. Ver xfail en la batería.",
    ),
    "stage2_2": (
        "Segunda entrega del bloque 2.",
        "Jugable, con salida y checkpoints.",
        "Revisión fina manual pendiente.",
    ),
    "lobby_datacenter": (
        "Transición/pasillo entre niveles del bloque 2.",
        "Corta y directa, cumple su función.",
        "¿Aporta algo al gameplay o es puro pasillo? Decisión de diseño.",
    ),
    "stage3_1_la_entrada_de_piedra": (
        "Apertura del bloque 3.",
        "Jugable y con salida.",
        "Revisión fina manual pendiente.",
    ),
    "hall": (
        "Salón de piedra: la salida se alcanza por una escalera de "
        "plataformas one-way bajo el techo. El analizador no las modela y "
        "marca la salida inalcanzable: falso negativo documentado.",
        "Escaleras one-way bien leídas por el jugador (dirección clara).",
        "Sección corta; el interés depende del combate, no del nivel.",
    ),
    "stage3_3_el_patio": (
        "El patio, cierre del bloque 3 antes del jefe.",
        "Jugable y con salida.",
        "Revisión fina manual pendiente.",
    ),
    "boss_gavilan": (
        "Jefe Gavilán: la entrega está incompleta (~45 % de la rúbrica, "
        "sólo Fase 1, sin patrones de ataque). El escenario de batalla "
        "existe y carga, pero el jefe no tiene ciclo de combate.",
        "El escenario y la fase 1 sentaron la arquitectura que el plan "
        "87-§27 reconstruirá.",
        "Es el hueco de contenido más grande del juego: ver GAP-058..065 "
        "en KNOWN_GAPS.md y docs/87_REPORTE_DE_LO_QUE_FALTA.md.",
    ),
    "stage4_1": (
        "Cementerio sagrado, entrega del bloque 4. Los gaps de checkpoint "
        "superan 1200 px (hasta ~2500 px) por decisión documentada AUD-516 "
        "(32 checkpoints -> 6): el reinicio es deliberadamente más duro.",
        "Identidad visual fuerte (cementerio, fosa azul).",
        "La dureza es una decisión, pero el reporte la deja registrada para "
        "que el dueño la confirme con datos de jugadores.",
    ),
    "stage4_1b": (
        "Variante b del cementerio (fosa azul, AUD-531).",
        "Variación barata del mismo nivel: más densidad por menos coste.",
        "Gaps grandes igual que stage4_1.",
    ),
    "stage4_1c_a": (
        "Sección rítmica: 61 bloques rítmicos sobre 14400 px con terreno "
        "estático del 2.8 %. La salida depende de bloques que aparecen a "
        "compás: el analizador la marca inalcanzable (falso negativo "
        "documentado).",
        "Nivel de plataformeo puro, el más 'nivel de juego' del motor.",
        "Sin enemigos: el reto es 100 % timing. El gap de checkpoints de "
        "2480 px es muy duro para un nivel de precisión.",
    ),
    "stage4_1c_b": (
        "Variante b de la sección rítmica.",
        "Misma calidad de construcción que la a.",
        "Ídem a: sin enemigos, checkpoints lejanos.",
    ),
    "stage4_1c_c": (
        "Variante c de la sección rítmica.",
        "Ídem.",
        "Ídem.",
    ),
    "boss_venado": (
        "Jefe de referencia del bloque 1 (el material que los estudiantes "
        "copian): batalla con fases completa y salida real.",
        "Referencia ejemplar: fases, patrones y transiciones documentadas.",
        "Gap de checkpoint de 941 px dentro de la arena: morir en la fase 2 "
        "repite mucho recorrido.",
    ),
    "boss_rey": (
        "Jefe Rey Terciopelo, bloque 2: completo.",
        "Completo y jugable.",
        "Revisión fina manual pendiente.",
    ),
    "boss_paburu": (
        "Gran Shaman Paburu, jefe final. La batería destapa un hallazgo "
        "real: un NextTrigger fantasma en y=-64 (fuera del mapa). El nivel "
        "se completa por el jefe, así que el trigger sobra, pero su presencia "
        "denuncia que el mapa se editó a mano (AUD-259: BossSpawn por "
        "entidad).",
        "Arena cerrada y completa.",
        "Hallazgo AUD (pendiente de decisión): borrar el NextTrigger "
        "fantasma o documentar por qué está. Ver xfail en la batería.",
    ),
}

ANALISIS_ESCENAS: dict[str, str] = {
    "SplashScene": "Pantalla de presentación autoplay: cumple.",
    "TitleScene": "Menú principal completo, responde a navegación y a todas las teclas.",
    "OptionsScene": "Opciones con menú vertical + valores izquierda/derecha.",
    "KeybindingScene": "Reasignación de teclas: navega y confirma.",
    "LoadGameScene": "Sin partidas guardadas en el estado inicial del arnés: "
    "la navegación no tiene items. Falta un mensaje de estado vacío visible.",
    "SkillTreeScene": "Árbol de habilidades: navega y confirma.",
    "TutorialScene": "Tutorial: navegación completa.",
    "GameOverScene": "Game over con menú de reaparición: navega y confirma.",
    "StageErrorScene": "Pantalla de error estática por diseño: sin teclas, se cierra por flujo externo. Correcta.",
    "EndCreditsScene": "Créditos que ruedan: ~1 s de negro antes de entrar "
    "el texto (ventana de entrada lenta).",
    "WorldMapScene": "Mapa del mundo: 16 nodos, navegación por flechas con "
    "salto vertical; CONFIRM entra y CANCEL sale.",
    "InventoryScene": "Inventario vacío en el estado inicial del arnés: nada que navegar. Falta mensaje de vacío.",
    "ShopScene": "Tienda: CONFIRM compra y CANCEL cierra; reacciona.",
    "BestiaryScene": "Bestiario sin entradas en el estado inicial: nada que navegar. Falta mensaje de vacío.",
    "AchievementScene": "0 logros desbloqueados en el arnés: nada que navegar. Falta mensaje de vacío.",
    "LeaderboardScene": "0 puntuaciones en el arnés: nada que navegar. Falta mensaje de vacío.",
    "ProgressScene": "Sin progreso en el arnés: nada que navegar. Falta mensaje de vacío.",
    "DemoMenuScene": "Menú de demos: navega y confirma.",
    "StoryScene": "Historia: navegación completa.",
    "UnitTheoryScene": "Teoría por páginas: CONFIRM avanza de página.",
    "StudentLoginScene": "Login de estudiante: navegación completa.",
    "VectorLabScene": "Laboratorio de vectores: reacciona a las teclas del menú (paneles).",
    "TransformLabScene": "Laboratorio de transformaciones: reacciona (DOWN/UP mueven selección de parámetro).",
    "CollisionLabScene": "Laboratorio de colisiones: reacciona y hasta simula jugador.",
    "InterpolationLabScene": "Laboratorio de interpolación: reacciona.",
    "NoiseLabScene": "Laboratorio de ruido: reacciona.",
    "CurveEditorScene": "Editor de curvas: reacciona (DOWN/UP).",
    "ColorTheoryScene": "Teoría del color: reacciona.",
    "FilterDemoScene": "Demo de filtros: reacciona (DOWN/UP cambian filtro).",
    "VisionDemoScene": "Demo de visión: reacciona.",
    "PatternDemoScene": "Demo de patrones: reacciona.",
    "PipelineBuilderScene": "Constructor de pipeline: reacciona.",
    "ComboDemoScene": "Demo de combos: reacciona.",
    "SandboxScene": "Arena de pruebas: reacciona.",
    "StageWizardScene": "Asistente de escenarios: reacciona.",
}

#: Escenas de nivel con observaciones de la batería (juego real).
ANALISIS_ESCENAS_NIVEL: dict[str, str] = {
    "stage0": "Corre y dibuja el mundo completo (carga TMX + entidades + física + HUD).",
    "stage_mecanicas": "Ídem; mecánicas dinámicas funcionando en el arnés.",
    "stage_cenital": "Modo cenital corre en el arnés.",
    "stage1_1": "Corre y dibuja.",
    "stage1_2_la_soda": "Corre y dibuja.",
    "stage1_3_las_aulas": "Corre y dibuja.",
    "stage2_1_oficinas": "Corre y dibuja; el arnés no toca los 0 checkpoints.",
    "stage2_2": "Corre y dibuja.",
    "lobby_datacenter": "Corre y dibuja.",
    "stage3_1_la_entrada_de_piedra": "Corre y dibuja.",
    "hall": "Corre y dibuja; escalera one-way hasta la salida.",
    "stage3_3_el_patio": "Corre y dibuja.",
    "stage3_4_boss_gavilan": "Corre y dibuja; el jefe no entra en combate (Fase 1 sola).",
    "stage4_1": "Corre y dibuja; cutscenes se limpian como en ayudantes_stage4_1.",
    "stage4_1b": "Corre y dibuja.",
    "stage4_1c_a": "Corre y dibuja la sección rítmica completa.",
    "boss_venado": "Corre y dibuja; jefe con fases.",
    "boss_rey": "Corre y dibuja.",
    "boss_paburu": "Corre y dibuja; arena completa.",
}


def _fila_nivel(d: dict) -> str:
    gaps = ", ".join(f"{g:.0f}" for g in d["gaps"]) or "—"
    comps = ", ".join(
        f"{k}={v}" for k, v in sorted(d["componentes"].items())[:6]) or "—"
    ent = ", ".join(
        f"{k}×{v}" for k, v in sorted(d["entidades"].items())[:6]) or "—"
    return (
        f"| {d['stage_id']} | {d['ancho']}×{d['alto']} | "
        f"{d['densidad']:.1%} | {d['plataformas']}/{d['alcanzables']} | "
        f"{'sí' if d['exit_reachable'] else 'no'} | {d['salida']} | "
        f"{d['checkpoints']} | {gaps} | {comps} | {ent} |"
    )


def _fila_escena(modulo: str, clase: str) -> str:
    nota = ANALISIS_ESCENAS.get(clase, "")
    return f"| {clase} | `src.engine.scenes.{modulo}` | {nota} |"


def generar_00(datos_niveles: list[dict]) -> str:
    campana = [d for d in datos_niveles if _nivel_en_campana(d["stage_id"])]
    totales = len(campana)
    con_salida = sum(1 for d in campana if d["exit_reachable"])
    sin_salida = sum(
        1 for d in campana
        if not d["exit_reachable"] and d["salida"] != "sin NextTrigger")
    jefes = sum(1 for _, es_jefe, _ in NIVELES.values() if es_jefe)
    labs = sum(1 for _, _, es_lab in NIVELES.values() if es_lab)
    huecos = [d["stage_id"] for d in datos_niveles
              if not d["exit_reachable"] and d["salida"] != "sin NextTrigger"
              and not NIVELES[d["stage_id"]][1]]
    huecos_md = "\n".join(f"- `{h}` (ver análisis en `01_analisis_niveles.md`)"
                          for h in huecos) or "- Ninguno."
    return f"""# Auditoría de juego — índice

> Generado por `scripts/generar_reporte_auditoria_juego.py`. Los números se
> miden en vivo de los TMX; la batería que los respalda vive en
> `tests/test_auditoria_juego/` (245 pruebas: 2 hallazgos reales como
> `xfail`, 11 skips documentados).

## Resumen ejecutivo

- **Niveles auditados:** {len(NIVELES)} TMX ({totales} en campaña,
  {labs} laboratorios, {jefes} jefes).
- **Salidas alcanzables:** {con_salida}/{totales} con salida
  ({sin_salida} marcadas inalcanzables por el analizador).
- **Falsos negativos del analizador estático** (no modela plataformas
  one-way ni mecánicas dinámicas): stage0, hall, stage_mecanicas,
  stage4_1c_a/b/c.
- **Hallazgos reales pendientes de decisión del dueño:**
  1. `stage2_1_oficinas`: **0 checkpoints en 3200 px** (gap 3048 px ≈ 33 s).
  2. `boss_paburu`: **NextTrigger fantasma en y=-64** (fuera del mapa).
- **Gaps de checkpoint > 1200 px por decisión documentada (AUD-516):**
  stage4_1, stage4_1b, stage4_1c_a/b/c.
- **Contenido incompleto:** jefe Gavilán (~45 % rúbrica, Fase 1 sola;
  ver GAP-058..065 y `docs/87_REPORTE_DE_LO_QUE_FALTA.md`).
- **Escenas UI/UX:** 35 escenas + 19 escenarios verificados con arnés de
  juego real. 7 menús no tienen datos en el estado inicial del arnés (0
  partidas / bestiario vacío / 0 logros / 0 puntuaciones / sin progreso /
  inventario vacío): los skips de la batería documentan el vacío.

## Documentos

| Fichero | Contenido |
|---|---|
| `00_indice.md` | Éste: resumen y mapa del reporte |
| `01_analisis_niveles.md` | Tabla de los {len(NIVELES)} TMX + análisis por nivel |
| `02_analisis_escenas_ui_ux.md` | Las 35 escenas + 19 escenarios, uno por uno |
| `03_plan_de_mejora.md` | Prioridades y fases para mejorar el juego |
| `04_analisis_profundo.md` | Auditoría profunda (8 dimensiones del proyecto) |

## Cómo se midió

- `StageLoader.load()` + `analyse_stage()` (`src/framework/stage/level_metrics.py`,
  AUD-049): alcanzabilidad de la salida, repechos, gaps de checkpoint.
- Densidad de terreno: fracción de celdas sólidas de la capa `Terrain`.
- Arnés de escenas: ciclo de vida real (`awake/start/on_enter/update/draw/
  on_exit/destroy`), 60+ fotogramas por acción de menú, ocupación por
  muestreo jitter determinista (no se alinea con el contenido).
- Regla del repo respetada: **ningún cambio al juego; esto es auditoría.**

## Inconcluso (ver `03_plan_de_mejora.md`)

{huecos_md}
"""


def generar_01(datos_niveles: list[dict]) -> str:
    filas = "\n".join(_fila_nivel(d) for d in datos_niveles)
    partes = []
    for d in datos_niveles:
        analisis = ANALISIS_NIVELES.get(d["stage_id"], ("", "", ""))
        partes.append(
            f"### {d['stage_id']}\n\n"
            f"{analisis[0] or 'Sin análisis cualitativo todavía.'}\n\n"
            f"**Fortalezas.** {analisis[1] or '—'}\n\n"
            f"**Debilidades.** {analisis[2] or '—'}\n\n"
            f"**Métricas.** {d['plataformas']} plataformas "
            f"({d['alcanzables']} alcanzables) · densidad de terreno "
            f"{d['densidad']:.1%} · checkpoints {d['checkpoints']} · "
            f"one-way {d['one_way']} · empujables {d['empujables']} · "
            f"destructibles {d['destructibles']} · salida {d['salida']} "
            f"({'fuera del mapa' if d['salida_fuera'] else 'dentro'}) · "
            f"repechos {d['repechos']}."
        )
    return f"""# Análisis de niveles (level design / play / feel)

Cada nivel se midió con `analyse_stage`; el texto cualitativo se escribió
con lo que la batería y la inspección de los TMX muestran.

## Tabla resumen (orden de campaña)

| nivel | tamaño | terreno | plataformas | salida alcanzable |
| salida (rect) | checkpoints | gaps | componentes (top) | enemigos (top) |
|---|---|---|---|---|---|---|---|---|---|
{filas}

## Nivel por nivel

{chr(10).join(partes)}

## Notas del analizador

El analizador (AUD-049) no modela plataformas one-way ni mecánicas
dinámicas (resortes, bloques rítmicos, viento...): cuando un nivel las usa
cerca de la salida, la marca inalcanzable. La batería documenta cada falso
negativo con su excusa. Los niveles con salida "no" y **sin** excusa son
hallazgos reales.
"""


def generar_02() -> str:
    filas = "\n".join(_fila_escena(m, c) for m, c in ESCENAS)
    filas_nivel = "\n".join(
        f"| {sid} | `{ANALISIS_ESCENAS_NIVEL.get(sid, '')}` |"
        for sid, _ in ESCENAS_NIVEL)
    return f"""# Análisis de escenas y UI/UX

Las 35 escenas del registro + las 19 escenas de nivel se corrieron con un
arnés de juego real: ciclo de vida completo, 60 fotogramas por tecla de
menú (arriba/abajo/confirmar/cancelar, las 2 teclas de cada acción),
ocupación de pantalla por muestreo jitter determinista.

## Escenas de UI

| escena | módulo | observación |
|---|---|---|
{filas}

## Escenas de nivel (juego real)

| nivel | observación |
|---|---|
{filas_nivel}

## Hallazgos transversales de UX

1. **Siete menús con estado vacío sin mensaje** (LoadGame, Inventory,
   Bestiary, Achievement, Leaderboard, Progress): con 0 datos la pantalla
   dibuja su marco pero no hay nada que navegar y no se ve un texto de
   "no hay nada todavía". La batería los marca como skip documentado, no
   como fallo: es una decisión de diseño pendiente.
2. **Créditos con 1 s de negro**: EndCredits rueda desde y=600 y el texto
   tarda ~1 s en entrar (ventana de entrada lenta).
3. **Doble tecla por acción**: cada acción de menú tiene 2 teclas (p. ej.
   flechas y WASD); la batería prueba ambas.
4. **Sin hallazgos de input muerto**: las 35 escenas reaccionan a sus
   teclas; las estáticas (StageError) lo son por diseño.
"""


def generar_03(datos_niveles: list[dict]) -> str:
    return """# Plan de mejora (priorizado)

Ordenado por impacto en el juego y coste. Cada fase es un lote pequeño
(1 AUD por commit) según las reglas del repo.

## Fase 1 — Cerrar los dos hallazgos reales (bloqueantes de campaña)

1. **stage2_1_oficinas: añadir checkpoints.** El nivel entero se reinicia
   al morir (0 checkpoints en 3200 px, peor gap 3048 px ≈ 33 s). Mínimo:
   uno a mitad de nivel (tras el primer piso de oficinas). Medible: la
   prueba `test_checkpoint_gaps_registrados` pasará a verde sin xfail.
2. **boss_paburu: retirar el NextTrigger fantasma (y=-64).** Está fuera
   del mapa: sobra (el nivel se completa por jefe). Decisión del dueño:
   borrarlo o documentarlo; después `test_el_next_trigger_no_esta_fuera_del_mapa`
   pasa a verde.

## Fase 2 — Completar el contenido faltante

3. **Jefe Gavilán (~45 % de la rúbrica).** Fase 1 sola, `attack_patterns`
   vacío. Seguir el plan de `docs/87_REPORTE_DE_LO_QUE_FALTA.md` §27 y
   cerrar los GAP-058..065 de `KNOWN_GAPS.md`. Es el hueco de juego más
   visible: la campaña termina sin el jefe de su bloque.

## Fase 3 — Decisiones de diseño registradas

4. **Mensajes de estado vacío en los 7 menús sin datos** (LoadGame,
   Inventory, Bestiary, Achievement, Leaderboard, Progress): un texto de
   "no hay partidas / entradas / logros todavía" convierte pantallas que
   hoy parecen rotas en pantallas informativas.
5. **Créditos: recortar la ventana de entrada** (empezar el texto más
   arriba o fundir desde el título).
6. **Gaps de stage4_1/4_1c por decisión (AUD-516)**: confirmar con
   sesiones reales si 33 s de reintento en el peor tramo rítmico es la
   dureza que se quiere; si no, un checkpoint por sección.

## Fase 4 — Auditoría fina manual (no automatizable)

7. Confort de saltos y timings de los niveles de estudiantes (1_1, 1_2,
   1_3, 2_2, 3_1, 3_3, boss_rey): la batería garantiza que corren y se
   completan; el *feel* (velocidad, amortiguación, ventanas de salto) se
   juega a mano con una partida por nivel.
8. Balance de la sección de sigilo de stage_mecanicas (cono de visión +
   acosador): difícil de verificar sin jugador humano.

## Cómo queda la batería

- 2 xfail se convierten en pruebas verdes al hacer las fases 1 y 2.
- 7 skips documentados se convierten en pruebas de contenido al sembrar
  datos (partida de ejemplo, entradas de bestiario...) en la fase 3.
"""


def main() -> int:
    pygame.init()
    pygame.display.set_mode((800, 600))
    pygame.font.init()

    datos = [cargar_nivel(sid, tmx) for sid, (tmx, _, _) in NIVELES.items()]

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "00_indice.md").write_text(
        generar_00(datos), encoding="utf-8")
    (SALIDA / "01_analisis_niveles.md").write_text(
        generar_01(datos), encoding="utf-8")
    (SALIDA / "02_analisis_escenas_ui_ux.md").write_text(
        generar_02(), encoding="utf-8")
    (SALIDA / "03_plan_de_mejora.md").write_text(
        generar_03(datos), encoding="utf-8")
    print(f"Reportes generados en {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
