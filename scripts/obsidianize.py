#!/usr/bin/env python3
"""
Obsidian Vault Generator for Legacy of InFest Documentation.

Transforms the flat docs/ folder into an Obsidian-compatible vault with:
1. YAML frontmatter (aliases, tags, document IDs) for every .md file
2. Wikilink [[cross-references]] between related documents
3. Proper metadata for Obsidian Graph View navigation
4. A landing page (Obsidian_Home.md) as the vault entry point

Usage:
    python scripts/obsidianize.py          # Process docs/ in-place
    python scripts/obsidianize.py --dry-run  # Preview changes without writing
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# AUD-177: imprime emoji y flechas, y la consola de Windows usa cp1252, que no
# los tiene.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DOCS_DIR = Path("docs")
PY_FILES = {"34_LIVE_CODE_u02_vector_class.py", "34_LIVE_CODE_u07_convolution.py"}

# ── Document registry: metadata for each .md file ──────────────────────────
# (id, category_tags, aliases, description)
DOC_REGISTRY = {
    # ── Core Index & Syllabus ──
    "00_MASTER_INDEX": (
        "LOI-INDEX-000", ["index", "entry-point"],
        ["Master Index", "Documentation Index"],
        "Single authoritative entry point for all documentation"
    ),
    "77_SYLLABUS_ALIGNMENT_AUDIT": (
        "LOI-SYLLABUS-000", ["syllabus", "audit", "academic"],
        ["Syllabus Alignment Audit", "Syllabus Audit"],
        "Audit reconciling documentation against official syllabus"
    ),
    "01_PROJECT_CHARTER": (
        "LOI-CHARTER-001", ["project", "charter", "academic"],
        ["Project Charter"],
        "Project scope, vision, stakeholders, repository structure"
    ),
    "02_CODEX_CONTEXT": (
        "LOI-CODEX-002", ["codex", "rules", "architecture"],
        ["Codex Context", "Coding Rules"],
        "Project philosophy, coding rules, architecture rules"
    ),

    # ── Architecture & Specifications ──
    "03_ARCHITECTURE": (
        "LOI-ARCH-003", ["architecture", "engine", "structure"],
        ["Architecture", "Engine Architecture"],
        "Full folder structure, module responsibilities, data flow"
    ),
    "04_PLAYER_SPEC": (
        "LOI-PLAYER-004", ["player", "specification", "entity"],
        ["Player Specification", "Player Spec"],
        "Player physics, states, combat — complete behavioral spec"
    ),
    "05_ENEMY_SPEC": (
        "LOI-ENEMY-005", ["enemy", "specification", "entity"],
        ["Enemy Specification", "Enemy Spec"],
        "Enemy base class and 8 enemy types"
    ),
    "06_TMX_SPEC": (
        "LOI-TMX-006", ["tmx", "tiled", "map", "format"],
        ["TMX Specification", "Map Format"],
        "Map file format, layers, object types"
    ),
    "07_STAGE0_DESIGN": (
        "LOI-STAGE0-007", ["stage0", "reference", "design"],
        ["Stage 0 Design", "Reference Stage"],
        "Professor's reference-implementation stage"
    ),

    # ── Academic Mapping ──
    "08_SYLLABUS_MAPPING": (
        "LOI-SYLLABUS-008", ["syllabus", "mapping", "academic"],
        ["Syllabus Mapping"],
        "Framework component to syllabus unit mapping"
    ),
    "09_HUD_SPEC": (
        "LOI-HUD-009", ["hud", "ui", "specification"],
        ["HUD Specification", "HUD Spec"],
        "HUD layout, hearts, timer, messages, Game Over"
    ),
    "10_LIBRARIES_AND_DEPENDENCIES": (
        "LOI-DEPS-010", ["dependencies", "libraries", "setup"],
        ["Libraries and Dependencies"],
        "Every third-party library, purpose, integration rules"
    ),

    # ── Processing Tools ──
    "11_FILTER_TOOLS_SPEC": (
        "LOI-FILTER-011", ["filter", "processing", "image"],
        ["Filter Tools Spec"],
        "Unit VII image processing subsystem"
    ),
    "12_VISION_TOOLS_SPEC": (
        "LOI-VISION-012", ["vision", "segmentation", "processing"],
        ["Vision Tools Spec"],
        "Unit VIII segmentation subsystem"
    ),
    "13_PATTERN_RECOGNITION_SPEC": (
        "LOI-PATTERN-013", ["pattern", "recognition", "ml"],
        ["Pattern Recognition Spec"],
        "Unit IX machine learning subsystem"
    ),
    "14_PROFESSOR_DELIVERABLE_MATRIX": (
        "LOI-DELIVERABLE-014", ["deliverable", "academic", "matrix"],
        ["Professor Deliverable Matrix"],
        "Full syllabus-to-framework-to-assessment traceability"
    ),

    # ── Content & World ──
    "15_ACADEMIC_DEMO_SCENES": (
        "LOI-DEMO-015", ["demo", "lab", "academic", "interactive"],
        ["Academic Demo Scenes", "Demo Labs"],
        "10 interactive demo/lab scenes"
    ),
    "16_WORLD_DESIGN": (
        "LOI-WORLD-016", ["world", "design", "narrative"],
        ["World Design"],
        "4 zones, 14 stages, narrative-to-gameplay mapping"
    ),
    "17_BOSS_SPEC": (
        "LOI-BOSS-017", ["boss", "specification", "entity"],
        ["Boss Specification", "Boss Spec"],
        "All 4 boss designs, phase-by-phase"
    ),
    "18_ENEMY_ROSTER": (
        "LOI-ENEMIES-018", ["enemy", "roster", "entities"],
        ["Enemy Roster"],
        "Every standard enemy, by zone"
    ),
    "19_NARRATIVE_AND_LORE": (
        "LOI-LORE-019", ["narrative", "lore", "story"],
        ["Narrative and Lore"],
        "Story, characters, cultural grounding (Tilawa)"
    ),
    "20_ASSET_BIBLE": (
        "LOI-ASSET-020", ["asset", "bible", "art", "audio"],
        ["Asset Bible"],
        "Every visual/audio asset, path, dimensions, palette"
    ),

    # ── Course & Schedule ──
    "21_COURSE_SCHEDULE": (
        "LOI-SCHEDULE-021", ["course", "schedule", "academic"],
        ["Course Schedule"],
        "11 classes + Invenio Fest schedule"
    ),

    # ── Contracts & Data ──
    "22_API_CONTRACTS": (
        "LOI-API-022", ["api", "contracts", "syntax"],
        ["API Contracts"],
        "Exact function/class signatures"
    ),
    "23_DATA_SCHEMAS": (
        "LOI-SCHEMA-023", ["data", "schemas", "types"],
        ["Data Schemas"],
        "Exact data shapes crossing module boundaries"
    ),
    "24_TEST_PLAN": (
        "LOI-TEST-024", ["test", "testing", "qa"],
        ["Test Plan"],
        "Exact test cases per module"
    ),
    "25_IMPLEMENTATION_ROADMAP": (
        "LOI-ROADMAP-025", ["implementation", "roadmap", "build"],
        ["Implementation Roadmap"],
        "16-phase build order with Definition of Done"
    ),
    "26_STUDENT_TEMPLATE_SPEC": (
        "LOI-TEMPLATE-026", ["template", "student", "starter"],
        ["Student Template Spec"],
        "Exact starter files every student copies"
    ),

    # ── Rubrics & Grading ──
    "27_ACADEMIC_RUBRICS": (
        "LOI-RUBRIC-027", ["rubric", "grading", "academic"],
        ["Academic Rubrics"],
        "Scoring criteria for every graded instrument"
    ),
    "28_DECISION_LOG": (
        "LOI-DECISION-028", ["decision", "adr", "architecture"],
        ["Decision Log", "ADR Log"],
        "Architecture Decision Records"
    ),
    "78_SAMPLE_SYLLABUS": (
        "LOI-SYLLABUS-028B", ["syllabus", "sample", "academic"],
        ["Sample Syllabus"],
        "Sample course syllabus"
    ),

    # ── Workflow ──
    "29_GIT_WORKFLOW_AND_STANDARDS": (
        "LOI-GIT-029", ["git", "workflow", "standards"],
        ["Git Workflow", "Git Standards"],
        "Branching, commits, PRs, code review"
    ),
    "79_TA_GUIDE": (
        "LOI-TA-029B", ["ta", "teaching", "assistant", "guide"],
        ["TA Guide"],
        "Teaching assistant guide"
    ),

    # ── Assignments ──
    "80_TICKET_BACKLOG": (
        "LOI-TICKET-030", ["ticket", "backlog", "tasks"],
        ["Ticket Backlog"],
        "Every roadmap phase decomposed into atomic tickets"
    ),
    "30_ASSIGNMENT_01_STAGE_DESIGN": (
        "LOI-ASGN01-030B", ["assignment", "stage", "design", "academic"],
        ["Assignment 1: Stage Design"],
        "Stage design assignment"
    ),
    "81_RISK_REGISTER": (
        "LOI-RISK-031", ["risk", "register", "management"],
        ["Risk Register"],
        "Academic/pedagogical risks and mitigation"
    ),
    "31_ASSIGNMENT_02_BOSS_DESIGN": (
        "LOI-ASGN02-031B", ["assignment", "boss", "design", "academic"],
        ["Assignment 2: Boss Design"],
        "Boss design assignment"
    ),
    "82_ENVIRONMENT_SETUP_GUIDE": (
        "LOI-SETUP-032", ["setup", "environment", "guide"],
        ["Environment Setup Guide"],
        "Step-by-step machine setup, troubleshooting"
    ),
    "32_ASSIGNMENT_03_LAB_EXERCISES": (
        "LOI-ASGN03-032B", ["assignment", "lab", "exercises", "academic"],
        ["Assignment 3: Lab Exercises"],
        "Lab exercises assignment"
    ),
    "83_SCOPE_ADJUSTMENT": (
        "LOI-SCOPE-033", ["scope", "adjustment", "academic"],
        ["Scope Adjustment"],
        "Scope adjustment documentation"
    ),
    "33_ASSIGNMENT_04_FINAL_PROJECT": (
        "LOI-ASGN04-033B", ["assignment", "final", "project", "academic"],
        ["Assignment 4: Final Project"],
        "Final project assignment"
    ),

    # ── Class Materials ──
    "34_CLASS_MATERIALS": (
        "LOI-CLASS-034", ["class", "materials", "academic"],
        ["Class Materials"],
        "Class materials and resources"
    ),
    "84_EDUCATIONAL_ROADMAP": (
        "LOI-EDU-034B", ["educational", "roadmap", "pedagogy"],
        ["Educational Roadmap"],
        "Educational roadmap"
    ),

    # ── Manuals & Guides ──
    "35_USER_MANUAL": (
        "LOI-USER-035", ["user", "manual", "guide"],
        ["User Manual", "Manual de Usuario"],
        "User manual for players and evaluators"
    ),
    "36_STUDENT_MANUAL": (
        "LOI-STUDENT-036", ["student", "manual", "guide"],
        ["Student Manual", "Manual de Estudiante"],
        "Complete student manual"
    ),
    "37_DEMO_QUICK_GUIDE": (
        "LOI-DEMO-037", ["demo", "quick", "guide"],
        ["Demo Quick Guide"],
        "Quick reference for using the demos"
    ),
    "38_STAGE_BOSS_GUIDE": (
        "LOI-GUIDE-038", ["stage", "boss", "guide", "creation"],
        ["Stage Boss Guide"],
        "Quick reference for building stages/bosses"
    ),

    # ── Analysis Reports ──
    "39_REPORTE_ANALISIS_CODIGO": (
        "LOI-ANALYSIS-039", ["analysis", "code", "report"],
        ["Code Analysis Report", "Reporte Analisis Codigo"],
        "Code analysis report"
    ),

    # ── V10 Feature Docs ──
    "40_DIALOGUE_SYSTEM": (
        "LOI-DIALOGUE-040", ["dialogue", "system", "ui"],
        ["Dialogue System"],
        "Branching dialogue with portraits"
    ),
    "41_BESTIARY_CODEX": (
        "LOI-BESTIARY-041", ["bestiary", "codex", "enemy"],
        ["Bestiary Codex"],
        "Enemy tracking system"
    ),
    "42_CUTSCENE_SYSTEM": (
        "LOI-CUTSCENE-042", ["cutscene", "system", "cinematic"],
        ["Cutscene System"],
        "Scripted cutscene system"
    ),
    "43_SPEEDRUN_MODE": (
        "LOI-SPEEDRUN-043", ["speedrun", "mode", "gameplay"],
        ["Speedrun Mode"],
        "Speedrun timer + ghost data"
    ),
    "44_BOSS_RUSH_MODE": (
        "LOI-BOSSRUSH-044", ["boss", "rush", "mode", "gameplay"],
        ["Boss Rush Mode"],
        "Boss gauntlet mode"
    ),
    "45_SWIMMING_SPEC": (
        "LOI-SWIMMING-045", ["swimming", "mechanics", "player"],
        ["Swimming Spec"],
        "Swimming mechanics"
    ),
    "46_FOG_OF_WAR": (
        "LOI-FOG-046", ["fog", "war", "vfx", "visibility"],
        ["Fog of War"],
        "Fog of war overlay"
    ),
    "47_WATER_EFFECT": (
        "LOI-WATER-047", ["water", "effect", "vfx"],
        ["Water Effect"],
        "Water VFX"
    ),
    "48_SCREEN_TRANSITIONS": (
        "LOI-TRANSITION-048", ["transition", "screen", "vfx"],
        ["Screen Transitions"],
        "Fade/wipe/slide/circle transitions"
    ),
    "49_AMBIENT_AUDIO": (
        "LOI-AUDIO-049", ["ambient", "audio", "sound"],
        ["Ambient Audio"],
        "Ambient audio system"
    ),

    # ── Planning & Audit ──
    "50_IMPROVEMENT_ROADMAP": (
        "LOI-ROADMAP-050", ["improvement", "roadmap", "planning"],
        ["Improvement Roadmap", "50 Improvement Roadmap"],
        "Consolidated improvement opportunities from evaluations"
    ),
    "51_IMPLEMENTATION_AUDIT": (
        "LOI-AUDIT-051", ["audit", "implementation", "gap"],
        ["Implementation Audit", "51 Implementation Audit"],
        "Evidence-based gap analysis"
    ),

    # ── Creation Guides ──
    "BOSS_CREATION": (
        "LOI-GUIDE-BOSS", ["boss", "creation", "guide", "tutorial"],
        ["Boss Creation Guide"],
        "Boss creation tutorial"
    ),
    "ENEMY_CREATION": (
        "LOI-GUIDE-ENEMY", ["enemy", "creation", "guide", "tutorial"],
        ["Enemy Creation Guide"],
        "Enemy creation tutorial"
    ),
    "SCENE_CREATION": (
        "LOI-GUIDE-SCENE", ["scene", "creation", "guide", "tutorial"],
        ["Scene Creation Guide"],
        "Scene creation tutorial"
    ),
    "STAGE_CREATION": (
        "LOI-GUIDE-STAGE", ["stage", "creation", "guide", "tutorial"],
        ["Stage Creation Guide"],
        "Stage creation tutorial"
    ),
    "README": (
        "LOI-README-DOCS", ["readme", "intro", "documentation"],
        ["Docs README", "Documentation README"],
        "Documentation package overview"
    ),
}

# ── Cross-reference mapping: source -> list of target filenames (without .md) ──
CROSS_REFS = {
    "00_MASTER_INDEX": [
        "77_SYLLABUS_ALIGNMENT_AUDIT", "01_PROJECT_CHARTER", "02_CODEX_CONTEXT",
        "03_ARCHITECTURE", "04_PLAYER_SPEC", "05_ENEMY_SPEC", "06_TMX_SPEC",
        "07_STAGE0_DESIGN", "08_SYLLABUS_MAPPING", "09_HUD_SPEC",
        "10_LIBRARIES_AND_DEPENDENCIES", "11_FILTER_TOOLS_SPEC", "12_VISION_TOOLS_SPEC",
        "13_PATTERN_RECOGNITION_SPEC", "14_PROFESSOR_DELIVERABLE_MATRIX",
        "15_ACADEMIC_DEMO_SCENES", "16_WORLD_DESIGN", "17_BOSS_SPEC",
        "18_ENEMY_ROSTER", "19_NARRATIVE_AND_LORE", "20_ASSET_BIBLE",
        "21_COURSE_SCHEDULE", "22_API_CONTRACTS", "23_DATA_SCHEMAS",
        "24_TEST_PLAN", "25_IMPLEMENTATION_ROADMAP", "26_STUDENT_TEMPLATE_SPEC",
        "27_ACADEMIC_RUBRICS", "28_DECISION_LOG", "78_SAMPLE_SYLLABUS",
        "29_GIT_WORKFLOW_AND_STANDARDS", "79_TA_GUIDE",
        "80_TICKET_BACKLOG", "30_ASSIGNMENT_01_STAGE_DESIGN",
        "81_RISK_REGISTER", "31_ASSIGNMENT_02_BOSS_DESIGN",
        "82_ENVIRONMENT_SETUP_GUIDE", "32_ASSIGNMENT_03_LAB_EXERCISES",
        "83_SCOPE_ADJUSTMENT", "33_ASSIGNMENT_04_FINAL_PROJECT",
        "34_CLASS_MATERIALS", "84_EDUCATIONAL_ROADMAP",
        "35_USER_MANUAL", "36_STUDENT_MANUAL", "37_DEMO_QUICK_GUIDE",
        "38_STAGE_BOSS_GUIDE", "39_REPORTE_ANALISIS_CODIGO",
        "40_DIALOGUE_SYSTEM", "41_BESTIARY_CODEX", "42_CUTSCENE_SYSTEM",
        "43_SPEEDRUN_MODE", "44_BOSS_RUSH_MODE", "45_SWIMMING_SPEC",
        "46_FOG_OF_WAR", "47_WATER_EFFECT", "48_SCREEN_TRANSITIONS",
        "49_AMBIENT_AUDIO", "50_IMPROVEMENT_ROADMAP", "51_IMPLEMENTATION_AUDIT",
        "BOSS_CREATION", "ENEMY_CREATION", "SCENE_CREATION", "STAGE_CREATION",
    ],
    "36_STUDENT_MANUAL": [
        "82_ENVIRONMENT_SETUP_GUIDE", "26_STUDENT_TEMPLATE_SPEC",
        "16_WORLD_DESIGN", "17_BOSS_SPEC", "18_ENEMY_ROSTER",
        "08_SYLLABUS_MAPPING", "15_ACADEMIC_DEMO_SCENES",
        "37_DEMO_QUICK_GUIDE", "38_STAGE_BOSS_GUIDE",
        "27_ACADEMIC_RUBRICS", "29_GIT_WORKFLOW_AND_STANDARDS",
    ],
    "35_USER_MANUAL": [
        "82_ENVIRONMENT_SETUP_GUIDE", "03_ARCHITECTURE",
        "04_PLAYER_SPEC", "09_HUD_SPEC", "40_DIALOGUE_SYSTEM",
    ],
    "50_IMPROVEMENT_ROADMAP": [
        "51_IMPLEMENTATION_AUDIT", "03_ARCHITECTURE",
        "04_PLAYER_SPEC", "05_ENEMY_SPEC",
    ],
    "51_IMPLEMENTATION_AUDIT": [
        "50_IMPROVEMENT_ROADMAP", "03_ARCHITECTURE",
    ],
    "40_DIALOGUE_SYSTEM": ["42_CUTSCENE_SYSTEM", "09_HUD_SPEC"],
    "42_CUTSCENE_SYSTEM": ["40_DIALOGUE_SYSTEM", "48_SCREEN_TRANSITIONS"],
    "43_SPEEDRUN_MODE": ["44_BOSS_RUSH_MODE", "09_HUD_SPEC"],
    "44_BOSS_RUSH_MODE": ["43_SPEEDRUN_MODE", "17_BOSS_SPEC"],
    "45_SWIMMING_SPEC": ["04_PLAYER_SPEC", "47_WATER_EFFECT"],
    "46_FOG_OF_WAR": ["47_WATER_EFFECT", "48_SCREEN_TRANSITIONS"],
    "47_WATER_EFFECT": ["45_SWIMMING_SPEC", "46_FOG_OF_WAR"],
    "48_SCREEN_TRANSITIONS": ["42_CUTSCENE_SYSTEM", "46_FOG_OF_WAR"],
    "49_AMBIENT_AUDIO": ["40_DIALOGUE_SYSTEM", "42_CUTSCENE_SYSTEM"],
    "03_ARCHITECTURE": [
        "04_PLAYER_SPEC", "05_ENEMY_SPEC", "06_TMX_SPEC",
        "10_LIBRARIES_AND_DEPENDENCIES", "22_API_CONTRACTS",
    ],
    "04_PLAYER_SPEC": ["45_SWIMMING_SPEC", "09_HUD_SPEC", "03_ARCHITECTURE"],
    "05_ENEMY_SPEC": ["18_ENEMY_ROSTER", "17_BOSS_SPEC", "03_ARCHITECTURE"],
    "17_BOSS_SPEC": ["44_BOSS_RUSH_MODE", "05_ENEMY_SPEC"],
    "16_WORLD_DESIGN": ["18_ENEMY_ROSTER", "19_NARRATIVE_AND_LORE", "07_STAGE0_DESIGN"],
    "19_NARRATIVE_AND_LORE": ["16_WORLD_DESIGN", "17_BOSS_SPEC"],
    "11_FILTER_TOOLS_SPEC": ["12_VISION_TOOLS_SPEC", "13_PATTERN_RECOGNITION_SPEC"],
    "12_VISION_TOOLS_SPEC": ["11_FILTER_TOOLS_SPEC", "13_PATTERN_RECOGNITION_SPEC"],
    "13_PATTERN_RECOGNITION_SPEC": ["11_FILTER_TOOLS_SPEC", "12_VISION_TOOLS_SPEC"],
    "BOSS_CREATION": ["17_BOSS_SPEC", "ENEMY_CREATION"],
    "ENEMY_CREATION": ["05_ENEMY_SPEC", "BOSS_CREATION"],
    "SCENE_CREATION": ["STAGE_CREATION", "03_ARCHITECTURE"],
    "STAGE_CREATION": ["SCENE_CREATION", "06_TMX_SPEC", "07_STAGE0_DESIGN"],
    "30_ASSIGNMENT_01_STAGE_DESIGN": ["07_STAGE0_DESIGN", "06_TMX_SPEC", "27_ACADEMIC_RUBRICS"],
    "31_ASSIGNMENT_02_BOSS_DESIGN": ["17_BOSS_SPEC", "27_ACADEMIC_RUBRICS"],
    "32_ASSIGNMENT_03_LAB_EXERCISES": ["15_ACADEMIC_DEMO_SCENES", "27_ACADEMIC_RUBRICS"],
    "33_ASSIGNMENT_04_FINAL_PROJECT": ["16_WORLD_DESIGN", "27_ACADEMIC_RUBRICS"],
    "27_ACADEMIC_RUBRICS": [
        "30_ASSIGNMENT_01_STAGE_DESIGN", "31_ASSIGNMENT_02_BOSS_DESIGN",
        "32_ASSIGNMENT_03_LAB_EXERCISES", "33_ASSIGNMENT_04_FINAL_PROJECT",
    ],
    "21_COURSE_SCHEDULE": [
        "30_ASSIGNMENT_01_STAGE_DESIGN", "31_ASSIGNMENT_02_BOSS_DESIGN",
        "32_ASSIGNMENT_03_LAB_EXERCISES", "33_ASSIGNMENT_04_FINAL_PROJECT",
    ],
    "25_IMPLEMENTATION_ROADMAP": ["80_TICKET_BACKLOG", "24_TEST_PLAN"],
    "80_TICKET_BACKLOG": ["25_IMPLEMENTATION_ROADMAP"],
    "24_TEST_PLAN": ["22_API_CONTRACTS", "23_DATA_SCHEMAS"],
    "22_API_CONTRACTS": ["23_DATA_SCHEMAS", "03_ARCHITECTURE"],
    "23_DATA_SCHEMAS": ["22_API_CONTRACTS"],
    "29_GIT_WORKFLOW_AND_STANDARDS": ["28_DECISION_LOG"],
    "28_DECISION_LOG": ["29_GIT_WORKFLOW_AND_STANDARDS", "03_ARCHITECTURE"],
    "82_ENVIRONMENT_SETUP_GUIDE": ["10_LIBRARIES_AND_DEPENDENCIES"],
    "08_SYLLABUS_MAPPING": ["14_PROFESSOR_DELIVERABLE_MATRIX", "21_COURSE_SCHEDULE"],
    "14_PROFESSOR_DELIVERABLE_MATRIX": ["08_SYLLABUS_MAPPING", "27_ACADEMIC_RUBRICS"],
    "37_DEMO_QUICK_GUIDE": ["15_ACADEMIC_DEMO_SCENES"],
    "38_STAGE_BOSS_GUIDE": ["STAGE_CREATION", "BOSS_CREATION"],
    "39_REPORTE_ANALISIS_CODIGO": ["51_IMPLEMENTATION_AUDIT", "50_IMPROVEMENT_ROADMAP"],
    "34_CLASS_MATERIALS": ["84_EDUCATIONAL_ROADMAP", "21_COURSE_SCHEDULE"],
    "84_EDUCATIONAL_ROADMAP": ["34_CLASS_MATERIALS", "08_SYLLABUS_MAPPING"],
    "20_ASSET_BIBLE": ["06_TMX_SPEC", "07_STAGE0_DESIGN", "16_WORLD_DESIGN"],
    "15_ACADEMIC_DEMO_SCENES": [
        "11_FILTER_TOOLS_SPEC", "12_VISION_TOOLS_SPEC", "13_PATTERN_RECOGNITION_SPEC",
        "37_DEMO_QUICK_GUIDE",
    ],
    "09_HUD_SPEC": ["40_DIALOGUE_SYSTEM", "04_PLAYER_SPEC"],
    "06_TMX_SPEC": ["07_STAGE0_DESIGN", "STAGE_CREATION"],
    "07_STAGE0_DESIGN": ["06_TMX_SPEC", "30_ASSIGNMENT_01_STAGE_DESIGN"],
    "10_LIBRARIES_AND_DEPENDENCIES": ["82_ENVIRONMENT_SETUP_GUIDE"],
}


def has_frontmatter(text: str) -> bool:
    """Check if text already has YAML frontmatter."""
    return text.startswith("---")


def extract_title(text: str) -> str:
    """Extract the first # title from markdown."""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("##"):
            return line[2:].strip()
    return ""


def build_frontmatter(meta: tuple, filename_stem: str, title: str, relative_path: str = "") -> str:
    """Build YAML frontmatter string."""
    doc_id, tags, aliases, description = meta
    yaml_lines = ["---"]
    yaml_lines.append(f'document_id: "{doc_id}"')
    yaml_lines.append(f"title: \"{title}\"")
    yaml_lines.append(f"aliases: {json.dumps(aliases)}")
    yaml_lines.append(f"tags: {json.dumps(tags)}")
    yaml_lines.append(f"description: \"{description}\"")
    yaml_lines.append(f"source: \"docs/{relative_path}{filename_stem}.md\"")
    yaml_lines.append(f"date_processed: \"{datetime.now(timezone.utc).date().isoformat()}\"")
    yaml_lines.append("---")
    return "\n".join(yaml_lines)


def add_wikilinks(text: str, filename_stem: str, cross_refs: dict) -> str:
    """Add Obsidian wikilink references section at the end of document."""
    if filename_stem not in cross_refs:
        return text

    targets = cross_refs[filename_stem]
    if not targets:
        return text

    # Build wikilinks section
    links_section = "\n\n---\n## 🔗 Documentos Relacionados\n\n"
    for target in targets:
        display_name = target.replace("_", " ").title()
        # Get alias from registry if available
        if target in DOC_REGISTRY:
            aliases = DOC_REGISTRY[target][2]
            if aliases:
                display_name = aliases[0]
        links_section += f"- [[{target}.md|{display_name}]]\n"

    return text + links_section


def guess_meta_from_path(filepath: Path):
    """Generate basic metadata for unregistered files based on directory location."""
    stem = filepath.stem
    rel = filepath.relative_to(DOCS_DIR)
    parent = rel.parent

    if str(parent) == ".":
        return None

    # Map directory to tags
    dir_tag_map = {
        "labs": ["lab", "academic", "exercise"],
        "quizzes": ["quiz", "academic", "evaluation"],
        "rubricas": ["rubric", "academic", "grading", "spanish"],
        "entregable01": ["deliverable", "assignment", "entregable"],
        "entregable02": ["deliverable", "assignment", "entregable"],
        "entregable03": ["deliverable", "assignment", "entregable"],
        "entregables": ["deliverable", "assignment"],
        "eval": ["evaluation", "academic"],
        "eval_practica": ["evaluation", "practical", "academic"],
        "exam_bank": ["exam", "bank", "academic"],
        "exams": ["exam", "academic"],
        "lore": ["lore", "narrative", "world"],
    }

    dir_name = parent.parts[0] if parent.parts else ""
    tags = dir_tag_map.get(dir_name, ["documentation"])
    aliases = [stem.replace("_", " ").title(), stem]
    desc = f"{dir_name.replace('_', ' ').title()} document: {stem}"
    doc_id = f"LOI-{dir_name.upper()}-{stem.upper()}"

    return (doc_id, tags, aliases, desc)


def process_file(filepath: Path, dry_run: bool = False) -> bool:
    """Process a single markdown file and return True if changes were made."""
    filename_stem = filepath.stem

    # Try registry first, then guess from path
    if filename_stem in DOC_REGISTRY:
        meta = DOC_REGISTRY[filename_stem]
    else:
        meta = guess_meta_from_path(filepath)
        if meta is None:
            print(f"  ⚠️  SKIP (no registry entry): {filename_stem}")
            return False

    original_text = filepath.read_text(encoding="utf-8")

    # Check if already has frontmatter
    if has_frontmatter(original_text):
        print(f"  ✓ Already has frontmatter: {filename_stem}")
        # Still might need wikilinks section
        if filename_stem in CROSS_REFS:
            if "## 🔗 Documentos Relacionados" not in original_text:
                new_text = add_wikilinks(original_text, filename_stem, CROSS_REFS)
                if new_text != original_text:
                    if not dry_run:
                        filepath.write_text(new_text, encoding="utf-8")
                    print(f"  ➕ Added wikilinks to: {filename_stem}")
                    return True
        return False

    # Compute relative path for source field (relative to project root)
    rel = filepath.relative_to(DOCS_DIR) if DOCS_DIR in filepath.parents else filepath
    rel_path = str(rel.parent) + "/" if rel.parent and str(rel.parent) != "." else ""

    title = extract_title(original_text) or filename_stem.replace("_", " ").title()
    frontmatter = build_frontmatter(meta, filename_stem, title, relative_path=rel_path)

    # Remove any existing frontmatter-like content at start
    text = original_text
    if text.startswith("---"):
        end_idx = text.find("---", 3)
        if end_idx != -1:
            text = text[end_idx + 3:].strip()

    new_text = frontmatter + "\n\n" + text

    # Add wikilinks section
    new_text = add_wikilinks(new_text, filename_stem, CROSS_REFS)

    if new_text != original_text:
        if not dry_run:
            filepath.write_text(new_text, encoding="utf-8")
        print(f"  ✅ Processed: {filename_stem} (in {filepath.parent})")
        return True
    else:
        print(f"  − No changes needed: {filename_stem}")
        return False


def create_obsidian_home(dry_run: bool = False):
    """Create the Obsidian vault landing page."""
    home_content = (
        '---\n'
        'document_id: "LOI-OBSIDIAN-HOME"\n'
        'title: "Legacy of InFest — Obsidian Vault"\n'
        'aliases: ["Vault Home", "Brain", "Knowledge Base"]\n'
        'tags: ["index", "home", "obsidian", "entry-point"]\n'
        'description: "Main entry point for the Legacy of InFest Obsidian knowledge base"\n'
        'source: "docs/Obsidian_Home.md"\n'
        f'date_processed: "{datetime.now(timezone.utc).date().isoformat()}"\n'
        '---\n'
        '\n'
        '# 🧠 Legacy of InFest — Obsidian Knowledge Base\n'
        '\n'
        'Bienvenido al **cerebro digital** del proyecto Legacy of InFest. '
        'Este vault de Obsidian contiene toda la documentación del framework '
        'académico de Gráficas por Computadora, Procesamiento de Imágenes, '
        'Visión por Computadora y Reconocimiento de Patrones.\n'
        '\n'
        '---\n'
        '\n'
        '## 📚 Capas de Documentación\n'
        '\n'
        'El conocimiento está organizado en **4 capas**. Explora según tu rol:\n'
        '\n'
        '### 🎓 Académica — *"¿Qué es este curso y cómo se evalúa?"*\n'
        '\n'
        '| Documento | Descripción |\n'
        '|-----------|-------------|\n'
        '| [[77_SYLLABUS_ALIGNMENT_AUDIT.md|Syllabus Alignment Audit]] | Auditoría de alineación con el sílabo oficial |\n'
        '| [[08_SYLLABUS_MAPPING.md|Syllabus Mapping]] | Mapeo de componentes del framework a unidades del sílabo |\n'
        '| [[14_PROFESSOR_DELIVERABLE_MATRIX.md|Deliverable Matrix]] | Trazabilidad sílabo-framework-evaluación |\n'
        '| [[21_COURSE_SCHEDULE.md|Course Schedule]] | Calendario de 11 clases + Invenio Fest |\n'
        '| [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]] | Criterios de calificación detallados |\n'
        '\n'
        '### 🏗️ Análisis y Diseño — *"¿Qué estamos construyendo y por qué?"*\n'
        '\n'
        '| Documento | Descripción |\n'
        '|-----------|-------------|\n'
        '| [[01_PROJECT_CHARTER.md|Project Charter]] | Alcance, visión, stakeholders |\n'
        '| [[02_CODEX_CONTEXT.md|Codex Context]] | Filosofía del proyecto, reglas de código |\n'
        '| [[16_WORLD_DESIGN.md|World Design]] | 4 zonas, 14 etapas, mapeo narrativo |\n'
        '| [[17_BOSS_SPEC.md|Boss Spec]] | Diseño de los 4 jefes, fase por fase |\n'
        '| [[18_ENEMY_ROSTER.md|Enemy Roster]] | Todos los enemigos estándar por zona |\n'
        '| [[19_NARRATIVE_AND_LORE.md|Narrative & Lore]] | Historia, personajes, cultura Tilawa |\n'
        '| [[20_ASSET_BIBLE.md|Asset Bible]] | Cada asset visual/auditivo, ruta, dimensiones |\n'
        '| [[28_DECISION_LOG.md|Decision Log]] | ADRs: por qué cada decisión técnica |\n'
        '\n'
        '### ⚙️ Implementación y Arquitectura — *"¿Cómo está estructurado el sistema?"*\n'
        '\n'
        '| Documento | Descripción |\n'
        '|-----------|-------------|\n'
        '| [[03_ARCHITECTURE.md|Architecture]] | Estructura de carpetas, responsabilidades, flujo de datos |\n'
        '| [[04_PLAYER_SPEC.md|Player Spec]] | Física, estados (25), combate |\n'
        '| [[05_ENEMY_SPEC.md|Enemy Spec]] | Clase base + 8 tipos de enemigo |\n'
        '| [[06_TMX_SPEC.md|TMX Spec]] | Formato de mapas, capas, objetos |\n'
        '| [[07_STAGE0_DESIGN.md|Stage 0 Design]] | Escenario de referencia del profesor |\n'
        '| [[09_HUD_SPEC.md|HUD Spec]] | Layout del HUD, corazones, timer |\n'
        '| [[10_LIBRARIES_AND_DEPENDENCIES.md|Libraries]] | Cada librería externa, propósito, reglas |\n'
        '| [[11_FILTER_TOOLS_SPEC.md|Filter Tools]] | Subsys. procesamiento de imágenes (Unidad VII) |\n'
        '| [[12_VISION_TOOLS_SPEC.md|Vision Tools]] | Subsys. segmentación (Unidad VIII) |\n'
        '| [[13_PATTERN_RECOGNITION_SPEC.md|Pattern Recognition]] | Subsys. ML (Unidad IX) |\n'
        '| [[15_ACADEMIC_DEMO_SCENES.md|Academic Demos]] | 10+ laboratorios interactivos |\n'
        '\n'
        '### 💻 Código y Build — *"¿Qué escribo, en qué orden, y cómo sé que está correcto?"*\n'
        '\n'
        '| Documento | Descripción |\n'
        '|-----------|-------------|\n'
        '| [[22_API_CONTRACTS.md|API Contracts]] | Firmas exactas de funciones/clases |\n'
        '| [[23_DATA_SCHEMAS.md|Data Schemas]] | Formas de datos entre módulos |\n'
        '| [[24_TEST_PLAN.md|Test Plan]] | Casos de prueba por módulo |\n'
        '| [[25_IMPLEMENTATION_ROADMAP.md|Implementation Roadmap]] | 16 fases de construcción con DoD |\n'
        '| [[26_STUDENT_TEMPLATE_SPEC.md|Student Templates]] | Archivos iniciales que cada estudiante copia |\n'
        '| [[29_GIT_WORKFLOW_AND_STANDARDS.md|Git Workflow]] | Ramas, commits, PRs, code review |\n'
        '| [[80_TICKET_BACKLOG.md|Ticket Backlog]] | Tickets atómicos por fase del roadmap |\n'
        '\n'
        '---\n'
        '\n'
        '## 🧭 Lectura por Rol\n'
        '\n'
        '### 👨‍🎓 Estudiante\n'
        '```mermaid\n'
        'flowchart LR\n'
        '    A[Setup Guide] --> B[Student Template]\n'
        '    B --> C[World Design]\n'
        '    C --> D[Enemy Roster]\n'
        '    D --> E[Syllabus Mapping]\n'
        '    E --> F[Student Manual]\n'
        '    F --> G[Demos]\n'
        '    G --> H[Rubrics]\n'
        '```\n'
        '\n'
        '- Comienza en: [[82_ENVIRONMENT_SETUP_GUIDE.md|Environment Setup Guide]]\n'
        '- Sigue con: [[36_STUDENT_MANUAL.md|Student Manual]]\n'
        '- Revisa: [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]\n'
        '\n'
        '### 👨‍🏫 Profesor\n'
        '- [[21_COURSE_SCHEDULE.md|Course Schedule]]\n'
        '- [[27_ACADEMIC_RUBRICS.md|Academic Rubrics]]\n'
        '- [[81_RISK_REGISTER.md|Risk Register]]\n'
        '\n'
        '### 🤖 AI Coding Assistant\n'
        '- [[00_MASTER_INDEX.md|Master Index]]\n'
        '- [[02_CODEX_CONTEXT.md|Codex Context]]\n'
        '- [[25_IMPLEMENTATION_ROADMAP.md|Implementation Roadmap]]\n'
        '\n'
        '---\n'
        '\n'
        '## 🗺️ Mapa de Tags\n'
        '\n'
        '| Tag | Documentos Relacionados |\n'
        '|-----|------------------------|\n'
        '| `#academic` | Syllabus, rubrics, assignments, course schedule |\n'
        '| `#architecture` | Architecture, codex, decision log |\n'
        '| `#entity` | Player, enemy, boss specs |\n'
        '| `#processing` | Filter tools, vision tools, pattern recognition |\n'
        '| `#vfx` | Fog of war, water, transitions, cutscenes |\n'
        '| `#student` | Student manual, templates, setup guide |\n'
        '| `#assignment` | 4 assignments, rubrics |\n'
        '\n'
        '---\n'
        '\n'
        f'*Este vault fue generado automáticamente el {datetime.now(timezone.utc).date().isoformat()}. Para actualizar, ejecuta:*\n'
        '```bash\n'
        'python scripts/obsidianize.py\n'
        '```\n'
    )

    home_path = DOCS_DIR / "Obsidian_Home.md"
    if not dry_run:
        home_path.write_text(home_content, encoding="utf-8")
    print(f"  ✅ Created/Updated: {home_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate Obsidian vault from docs/")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    dry_run = args.dry_run
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  Legacy of InFest — Obsidian Vault Generator ({mode})")
    print(f"{'='*60}\n")

    # Collect all .md files recursively
    md_files = sorted(DOCS_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} .md files in docs/ (recursive)\n")

    processed = 0
    changed = 0
    skipped = 0

    for filepath in md_files:
        filename_stem = filepath.stem
        # Skip the home page we generate
        if filename_stem == "Obsidian_Home":
            continue

        result = process_file(filepath, dry_run=dry_run)
        processed += 1
        if result:
            changed += 1
        else:
            skipped += 1

    # Create Obsidian Home
    create_obsidian_home(dry_run=dry_run)

    print(f"\n{'='*60}")
    print(f"  Summary ({mode}):")
    print(f"  - Processed: {processed} files")
    print(f"  - Changed:   {changed} files")
    print(f"  - Skipped:   {skipped} files")
    print("  - Created:   Obsidian_Home.md (landing page)")
    print(f"{'='*60}\n")

    if dry_run:
        print("  Run without --dry-run to apply changes.\n")
    else:
        print("  ✅ Vault is ready! Open the docs/ folder in Obsidian.\n")


if __name__ == "__main__":
    main()