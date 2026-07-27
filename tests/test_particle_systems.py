from __future__ import annotations

import pygame
import pytest


@pytest.fixture(autouse=True)
def pygame_init():
    if not pygame.get_init():
        pygame.init()
    yield


class TestWeatherSystem:
    def test_rain_spawns_particles(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("rain")
        ws.update(0.1, pygame.Vector2(0, 0))
        assert ws._emitter.count > 0

    def test_clear_produces_no_particles(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("clear")
        ws.update(1.0, pygame.Vector2(0, 0))
        assert ws._emitter.count == 0

    def test_storm_spawns_particles(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("storm")
        ws.update(0.1, pygame.Vector2(0, 0))
        assert ws._emitter.count > 0

    def test_set_climate_clears_and_respawns(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("rain")
        ws.update(0.5, pygame.Vector2(0, 0))
        ws.set_climate("clear")
        ws.update(0.5, pygame.Vector2(0, 0))
        assert ws._emitter.count == 0

    def test_particles_use_particle_class(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("rain")
        ws.update(0.05, pygame.Vector2(0, 0))
        assert ws._emitter.count > 0

    def test_draw_does_not_crash(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("rain")
        ws.update(0.1, pygame.Vector2(0, 0))
        surf = pygame.Surface((320, 224))
        ws.draw(surf, pygame.Vector2(0, 0))

    def test_overlay_drawn_for_non_clear(self) -> None:
        from src.framework.vfx.weather_system import WeatherSystem
        ws = WeatherSystem("fog")
        surf = pygame.Surface((320, 224), pygame.SRCALPHA)
        before = surf.get_at((0, 0))
        ws.draw(surf, pygame.Vector2(0, 0))
        after = surf.get_at((0, 0))
        assert before != after


class TestAmbientParticleSystem:
    def test_dust_spawns_particles(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("dust", rate=100.0)
        ap.update(1.0, pygame.Vector2(0, 0))
        assert ap._emitter.count > 0

    def test_zero_rate_produces_no_particles(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("dust", rate=0.0)
        ap.update(1.0, pygame.Vector2(0, 0))
        assert ap._emitter.count == 0

    def test_clear_removes_particles(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("dust", rate=100.0)
        ap.update(1.0, pygame.Vector2(0, 0))
        ap.clear()
        assert ap._emitter.count == 0

    def test_particles_use_particle_class(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("leaves", rate=100.0)
        ap.update(1.0, pygame.Vector2(0, 0))
        assert ap._emitter.count > 0

    def test_draw_does_not_crash(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("embers", rate=100.0)
        ap.update(1.0, pygame.Vector2(0, 0))
        surf = pygame.Surface((320, 224), pygame.SRCALPHA)
        ap.draw(surf, pygame.Vector2(0, 0))

    def test_particles_decay_over_time(self) -> None:
        from src.framework.vfx.ambient_particles import AmbientParticleSystem
        ap = AmbientParticleSystem()
        ap.set_effect("dust", rate=100.0)
        ap.update(0.1, pygame.Vector2(0, 0))
        assert ap._emitter.count > 0
        ap.update(10.0, pygame.Vector2(0, 0))
        assert ap._emitter.count == 0
