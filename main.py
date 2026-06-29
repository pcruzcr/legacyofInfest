"""Legacy of InFest — Entry Point"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from src.engine.core.app import App

if __name__ == "__main__":
    App().run()
