Legacy of InFest — Entry Point
main.py

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.engine.core.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ ==  __main__:
    main()
