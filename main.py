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


#: Paquetes de terceros sin los que el juego no puede arrancar. El nombre del
#: módulo importable no siempre coincide con el de instalación, así que se
#: guardan los dos.
_REQUIRED_PACKAGES: tuple[tuple[str, str], ...] = (
    ("pygame", "pygame-ce"),
    ("pytmx", "pytmx"),
    ("pyscroll", "pyscroll"),
    ("pydantic", "pydantic"),
    ("orjson", "orjson"),
    ("numpy", "numpy"),
)


def _preflight() -> None:
    """Comprueba las dependencias antes de tocar pygame.

    Sin esto, lanzar el juego con el intérprete equivocado —el Python global en
    lugar del `.venv` del proyecto— produce un ``ModuleNotFoundError: orjson``
    a mitad de una cadena de importaciones, sin ninguna pista de que el
    problema sea el intérprete. Es un fallo fácil de diagnosticar mal: parece
    que falta código del juego cuando lo que falta es el entorno.

    El mensaje incluye la ruta del ejecutable en uso a propósito. Saber *qué*
    Python está corriendo es la mitad del diagnóstico, y es justo el dato que
    no aparece en la traza.
    """
    import importlib.util

    missing = [
        install_name
        for module_name, install_name in _REQUIRED_PACKAGES
        if importlib.util.find_spec(module_name) is None
    ]
    if not missing:
        return

    venv = os.path.join(os.path.dirname(__file__), ".venv")
    activate = (
        os.path.join(venv, "Scripts", "activate")
        if os.name == "nt"
        else f"source {os.path.join(venv, 'bin', 'activate')}"
    )
    print("ERROR: faltan dependencias:", ", ".join(missing), file=sys.stderr)
    print(f"       intérprete en uso: {sys.executable}", file=sys.stderr)
    if os.path.isdir(venv):
        print(
            f"       hay un entorno virtual en {venv}; actívalo con:\n"
            f"           {activate}",
            file=sys.stderr,
        )
    else:
        print(
            "       instálalas con:\n"
            "           pip install -r requirements.txt",
            file=sys.stderr,
        )
    sys.exit(1)


if __name__ == "__main__":
    args = _parse_args()
    _preflight()

    import importlib

    if args.stage:
        # Validate stage module exists before initializing pygame
        try:
            mod = importlib.import_module(f"src.stages.{args.stage}.{args.stage}")
        except ModuleNotFoundError as exc:
            # Distinguir "no existe ese escenario" de "el escenario existe pero
            # una de sus importaciones falla". Antes las dos decían lo mismo, y
            # un fallo de dependencia se reportaba como escenario inexistente:
            # el mensaje mandaba a buscar en el sitio equivocado.
            target = f"src.stages.{args.stage}.{args.stage}"
            if exc.name is not None and not target.startswith(exc.name):
                print(f"ERROR: {target} no se pudo importar: falta '{exc.name}'")
            else:
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
        except ModuleNotFoundError as exc:
            target = f"src.stages.{args.boss}.{args.boss}_scene"
            if exc.name is not None and not target.startswith(exc.name):
                print(f"ERROR: {target} no se pudo importar: falta '{exc.name}'")
            else:
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
