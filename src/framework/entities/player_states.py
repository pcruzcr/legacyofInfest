"""
Compat shim — delegates to the states/ package.
Originally a 1622-line God file, now split into:
  states/base.py, states/helpers.py, states/grounded.py,
  states/airborne.py, states/attack.py, states/ability.py,
  states/wall.py, states/damage.py, states/swim.py
"""
from __future__ import annotations

from src.framework.entities.states import *  # noqa: F403
