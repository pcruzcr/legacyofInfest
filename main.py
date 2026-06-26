"""
Legacy of InFest — main.py
Entry point. Instantiates App and calls run().
"""
from src.engine.core.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()