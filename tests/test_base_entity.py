"""Tests for BaseEntity abstract class.

Minimal coverage: BaseEntity is abstract and requires update/draw.
"""

import pytest

from src.framework.entities.base_entity import BaseEntity


class ConcreteEntity(BaseEntity):
    """Minimal concrete implementation of BaseEntity for testing."""

    def __init__(self) -> None:
        self.updated: float = -1.0
        self.drawn: bool = False

    def update(self, dt: float) -> None:
        self.updated = dt

    def draw(self, surface: object) -> None:
        self.drawn = True


def test_cannot_instantiate_abstract():
    """BaseEntity is abstract and cannot be directly instantiated."""
    with pytest.raises(TypeError):
        BaseEntity()  # type: ignore[abstract]


def test_concrete_entity_has_default_lifecycle_noop():
    """ConcreteEntity inherits no-op on_enter/on_exit by default."""
    e = ConcreteEntity()
    e.on_enter()
    e.on_exit()


def test_concrete_entity_update_and_draw_run():
    """ConcreteEntity update/draw update internal test tracking."""
    e = ConcreteEntity()
    e.update(0.016)
    assert e.updated == 0.016
    e.draw(None)
    assert e.drawn is True
