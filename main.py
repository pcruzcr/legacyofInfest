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
    # AUD-268: los avisos van a un fichero junto a las partidas. Esta bandera
    # los devuelve a la consola, que es lo que quiere quien está diagnosticando
    # y nadie más.
    parser.add_argument(
        "--debug", action="store_true",
        help="Muestra los avisos del motor en la consola (por defecto van al "
             "registro, junto a las partidas)",
    )
    # AUD-375 — la otra mitad de la semilla. El motor la escribe en el registro
    # de cada partida; esto es cómo se devuelve. Sin la bandera, un informe con
    # la semilla dentro no sirve de nada: se sabría con qué azar pasó y no
    # habría forma de repetirlo.
    parser.add_argument(
        "--semilla", type=int, default=None, metavar="N",
        help="Arranca con una semilla concreta para repetir una partida. La "
             "del arranque queda anotada en el registro como «semilla del "
             "azar»",
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
        from src.framework.entities.precarga_ia import precargar_ia
        # AUD-457 — la carga de la IA va ANTES del bucle, síncrona. La splash
        # no se actualiza en este flujo (el escenario se empuja encima), y si
        # la carga cayera en el primer lote de `SquadBrain` congelaría la
        # partida cuando un enemigo está encima. Un import en paralelo
        # deadlockea (scipy 1.9 + CPython 3.14), así que aquí es el único
        # importador: el coste (2-3 s) se paga antes de abrir la ventana.
        precargar_ia()
        app = App(depurar=args.debug, semilla=args.semilla)
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
        from src.framework.entities.precarga_ia import precargar_ia
        # AUD-457 — la carga de la IA va ANTES del bucle, síncrona (ver el
        # comentario homólogo en la rama `--stage`).
        precargar_ia()
        app = App(depurar=args.debug, semilla=args.semilla)
        app.scene_manager.push(scene_cls(app.context))
        app.run()

    else:
        from src.engine.core.app import App
        App(depurar=args.debug, semilla=args.semilla).run()
