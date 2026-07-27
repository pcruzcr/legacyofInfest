"""Legacy of InFest — Entry Point"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Legacy of InFest")
    parser.add_argument(
        "--stage", type=str, default=None,
        help="Launch a specific stage by ID (e.g., --stage stage1_2_la_soda)",
    )
    parser.add_argument(
        "--boss", type=str, default=None,
        help="Launch a specific boss by ID (e.g., --boss boss_rey)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    import importlib

    if args.stage:
        # Validate stage module exists before initializing pygame
        try:
            mod = importlib.import_module(f"src.stages.{args.stage}.{args.stage}")
        except ModuleNotFoundError:
            print(f"ERROR: Stage module not found: src.stages.{args.stage}")
            sys.exit(1)
        from src.framework.scenes.stage_scene import StageScene
        scene_cls = None
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, StageScene) and obj is not StageScene:
                scene_cls = obj
                break
        if scene_cls is None:
            print(f"ERROR: No StageScene subclass found in src.stages.{args.stage}")
            sys.exit(1)
        from src.engine.core.app import App
        app = App()
        app.scene_manager.push(scene_cls(app.context))
        app.run()

    elif args.boss:
        # Validate boss module exists before initializing pygame
        try:
            mod = importlib.import_module(f"src.stages.{args.boss}.{args.boss}_scene")
        except ModuleNotFoundError:
            print(f"ERROR: Boss module not found: src.stages.{args.boss}")
            sys.exit(1)
        from src.framework.scenes.stage_scene import StageScene
        scene_cls = None
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, StageScene) and obj is not StageScene:
                scene_cls = obj
                break
        if scene_cls is None:
            print(
                f"ERROR: No StageScene subclass found in "
                f"src.stages.{args.boss}.{args.boss}_scene"
            )
            sys.exit(1)
        from src.engine.core.app import App
        app = App()
        app.scene_manager.push(scene_cls(app.context))
        app.run()

    else:
        from src.engine.core.app import App
        App().run()
