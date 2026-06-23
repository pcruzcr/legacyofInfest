"""
Module: main
System: engine
Academic Unit: Framework scaffold
Description: Application entry point.  Constructs the App (which
initialises pygame and all subsystems) but does NOT call App.run()
during Phase 1 — that will be wired in Phase 3 once the scene
system is complete.
"""

import sys

# Importing App triggers pygame init via App.__init__ when constructed.
from src.engine.core.app import App


def main() -> None:
    """Construct the App instance and enter the main loop."""
    _app = App()
    _app.run()


if __name__ == "__main__":
    main()
    sys.exit(0)
