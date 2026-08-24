# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for Legacy of InFest.

Usage:
    pyinstaller build.spec

Builds a single-folder deployment with all assets included.
"""

import sys
from pathlib import Path

import PyInstaller.config

PROJECT_ROOT = Path(__file__).resolve().parent

# Collect all asset directories
ASSET_DIRS = [
    "assets",
]

# Add assets as binary trees so they are bundled alongside the executable
a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / d), d)
        for d in ASSET_DIRS
        if (PROJECT_ROOT / d).exists()
    ],
    hiddenimports=[
        "src.engine.audio.audio_manager",
        "src.engine.audio.sound_bank",
        "src.engine.audio.audio_pipeline",
        "src.engine.core.app",
        "src.engine.core.settings",
        "src.engine.core.save_manager",
        "src.engine.core.difficulty",
        "src.engine.core.achievements",
        "src.engine.core.inventory",
        "src.engine.core.event_bus",
        "src.engine.core.game_context",
        "src.engine.core.clock",
        "src.engine.core.events",
        "src.engine.core.stage_registry",
        "src.engine.input.action_map",
        "src.engine.input.input_manager",
        "src.engine.scene.scene_manager",
        "src.engine.scenes.title_scene",
        "src.engine.scenes.options_scene",
        "src.engine.scenes.demo_common",
        "src.engine.render.gl_pipeline",
        "src.engine.render.shaders",
        "src.engine.utils.math_utils",
        "src.engine.utils.asset_loader",
        "src.framework.entities.player",
        "src.framework.entities.enemy_base",
        "src.framework.entities.enemy_walker",
        "src.framework.entities.enemy_shooter",
        "src.framework.entities.enemy_flying",
        "src.framework.entities.enemy_charger",
        "src.framework.entities.enemy_caster",
        "src.framework.entities.enemy_brute",
        "src.framework.entities.enemy_assassin",
        "src.framework.entities.enemy_archer",
        "src.framework.entities.boss_base",
        "src.framework.entities.base_entity",
        "src.framework.entities.ai_predictor",
        "src.framework.entities.bestiary",
        "src.framework.entities.flight_strategies",
        "src.framework.stage.collision_system",
        "src.framework.stage.stage_loader",
        "src.framework.stage.camera",
        "src.framework.scenes.stage_scene",
        "src.framework.vfx.particle_system",
        "src.framework.vfx.weather_system",
        "src.framework.vfx.ambient_particles",
        "src.framework.ui.hud",
        "src.framework.ui.combo_system",
        "src.framework.items.item_defs",
        "src.framework.ai.lua_script",
        "pydantic",
        "orjson",
        "numba",
        "pymunk",
        "lupa",
        "pygame_gui",
        "pytmx",
        "pyscroll",
        "pytweening",
        "cv2",
        "sklearn",
        "skimage",
        "scipy",
        "PIL",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib.tests",
        "numpy.testing",
        "scipy.tests",
        "PIL.ImageShow",
        "setuptools",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LegacyOfInfest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / "assets" / "icon.ico") if (PROJECT_ROOT / "assets" / "icon.ico").exists() else None,
)

# Also generate a COLLECT for folder-based deployment
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LegacyOfInfest_dist",
)
