"""
Module: base_entity
System: framework.entities
Academic Unit: N/A
Description: Abstract base class for all game entities. Defines the lifecycle
contract (update/draw) that every entity in the framework must implement.

F5.2 — qué cambió por dentro y qué no cambió por fuera
=======================================================
Desde la fase 5, `position`, `rect`, `facing` y `velocity` **ya no son
atributos**: son propiedades que leen y escriben componentes ECS
(`framework.ecs`). Por fuera no se nota nada, y ése es todo el objetivo::

    self.rect.centerx = 40         # sigue funcionando
    self.position.x += v * dt      # sigue funcionando
    self.rect = pygame.Rect(...)   # sigue funcionando

Funciona porque las propiedades devuelven **el objeto de verdad** que vive
dentro del componente `Transform`, no una copia. El razonamiento largo está en
`framework/ecs/bridge.py`; es el que sostiene las 18.054 líneas de código de
estudiantes que hay hoy en `src/stages/`.

Lo que se gana: un sistema puede empujar con viento, arrastrar sobre una
plataforma móvil o meter bajo el agua a **cualquier** entidad que tenga
`Transform` y `Velocidad`, sin preguntar de qué clase es y sin obligar a nadie a
heredar de nada nuevo.
"""
from abc import ABC, abstractmethod

import pygame

from src.framework.ecs.bridge import ComponentesDeEntidad


class BaseEntity(ComponentesDeEntidad, ABC):
    """
    Root class for all game objects in the Legacy of InFest framework.
    Manages world position, a Pygame Rect for collision, visibility,
    active state, and the basic update/draw lifecycle.
    """

    def __init__(self, position: pygame.Vector2, event_bus=None) -> None:
        """Initialize the entity at the given world-space position."""
        # El cuerpo ECS va primero: `position` y `rect` son propiedades que
        # leen el componente `Transform`, así que tiene que existir antes de
        # que nadie las toque.
        self._iniciar_componentes(position, pygame.Rect(0, 0, 0, 0))
        self.is_active: bool = True
        self.is_visible: bool = True
        self.layer: int = 4
        # AUD-019: entities used to fall back to a module-level singleton bus
        # when none was injected. In production App wired that singleton to the
        # real bus so it worked; under test it silently diverged, so an entity
        # emitted into one bus while the scene listened to another. Entities now
        # get an inert bus by default and must be given the real one explicitly
        # (StageScene does this for every entity it loads).
        from src.engine.core.event_bus import EventBus
        self._event_bus = event_bus if event_bus is not None else EventBus()

    def set_event_bus(self, bus) -> None:
        """Set the EventBus instance for this entity (late injection)."""
        self._event_bus = bus

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update entity state. Must be overridden by subclasses.
        dt is delta time in seconds.
        """
        ...

    @abstractmethod
    def draw(self, surface: pygame.Surface,
             camera_offset: pygame.Vector2) -> None:
        """
        Draw the entity to the given surface.
        camera_offset must be subtracted from world position
        to compute screen position.
        """
        ...
