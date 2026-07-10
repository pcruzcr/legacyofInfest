"""Legacy of InFest — Entry Point"""
import sys
import os
import argparse

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

    if args.stage:
        # Direct stage launch: import the module and push its scene
        from src.engine.core.app import App
        app = App()
        import importlib
        mod = importlib.import_module(f"src.stages.{args.stage}.{args.stage}")
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
        # Skip splash/title and go straight to the stage via scene manager
        app.scene_manager.push(scene_cls(app.context))
        app.run()

    elif args.boss:
        # Direct boss launch: import the _scene module
        from src.engine.core.app import App
        app = App()
        import importlib
        mod = importlib.import_module(f"src.stages.{args.boss}.{args.boss}_scene")
        from src.framework.scenes.stage_scene import StageScene
        scene_cls = None
        for name in dir(mod):
            obj = getattr(mod, name)
            if isinstance(obj, type) and issubclass(obj, StageScene) and obj is not StageScene:
                scene_cls = obj
                break
        if scene_cls is None:
            print(f"ERROR: No StageScene subclass found in src.stages.{args.boss}.{args.boss}_scene")
            sys.exit(1)
        app.scene_manager.push(scene_cls(app.context))
        app.run()

    else:
        from src.engine.core.app import App
        App().run()
