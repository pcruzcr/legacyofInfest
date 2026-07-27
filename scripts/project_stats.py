"""Quick project statistics for Legacy of InFest V1 assessment."""
import importlib
import inspect
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

src = list(Path('src').rglob('*.py'))
tests = list(Path('tests').rglob('*.py'))
scripts = list(Path('scripts').rglob('*.py'))
print(f'Source .py files: {len(src)}')
print(f'Test .py files: {len(tests)}')
print(f'Total LOC: {sum(len(p.read_text().splitlines()) for p in src + tests + scripts)}')

from src.engine.scene.base_scene import BaseScene

scene_count = 0
scene_dir = Path('src/engine/scenes')
for f in sorted(scene_dir.glob('*.py')):
    if f.name.startswith('__'): continue
    mod = importlib.import_module('src.engine.scenes.' + f.stem)
    for _name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, BaseScene) and obj is not BaseScene:
            scene_count += 1
print(f'Scene classes: {scene_count}')

from src.framework.entities.enemy_base import EnemyBase

enemy_names = []
entity_dir = Path('src/framework/entities')
for f in sorted(entity_dir.glob('*.py')):
    if f.stem in ('__init__', 'base_entity', 'player', 'player_states', 'entity_factory', 'bestiary', 'ai_predictor', 'flight_strategies', 'boss_base', 'enemy_base'):
        continue
    mod = importlib.import_module('src.framework.entities.' + f.stem)
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, EnemyBase) and obj is not EnemyBase:
            enemy_names.append(name)
print(f'Enemy types: {len(enemy_names)} - {enemy_names}')

from src.framework.entities.boss_base import BossBase

boss_names = []
for f in sorted(Path('src/stages').rglob('**/*.py')):
    if f.name.startswith('__'): continue
    mod_name = str(f.relative_to(Path.cwd())).replace(os.sep, '.')[:-3]
    mod = importlib.import_module(mod_name)
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, BossBase) and obj is not BossBase:
            boss_names.append(name)
print(f'Boss types: {len(boss_names)} - {boss_names}')

from src.engine.core.achievements import AchievementSystem

ach = AchievementSystem.get_instance()
print('Achievements: TODO')

print()
for label, d in [('Engine', 'src/engine'), ('Framework', 'src/framework'), ('Stages', 'src/stages')]:
    subs = sorted([str(p.relative_to(Path(d).parent)) for p in Path(d).glob('*') if p.is_dir()])
    print(f'{label} subdirs: {subs}')
