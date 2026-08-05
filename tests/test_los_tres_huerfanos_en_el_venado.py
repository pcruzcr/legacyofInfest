"""AUD-263 — los tres huérfanos que quedaban, demostrados en el jefe de referencia.

La decisión, y por qué no fue «borrarlos»
=========================================
`EnjambreDeBalas`, `skill_parry` y `play_voz` llevaban meses en la lista de
huérfanos, y la salida fácil era retirarlos. **No se retiran**: los estudiantes
los van a usar en su segunda entrega, así que lo que hacían falta no era menos
API sino un sitio donde verlos funcionar.

Ese sitio es `boss_venado`, el jefe de referencia del profesor — el único que
podemos tocar (invariante 1 de `CLAUDE.md`) y, justamente, el que los
estudiantes copian. Un patrón que no está en el material que se copia, no
existe para el curso.

Los tres, uno por uno
---------------------
* **`EnjambreDeBalas`** — 0 usos fuera de su módulo. Ahora la fase 2 del venado
  abre un abanico de esporas. Medido en su día: 2.000 balas de 12,94 ms a
  0,072 ms.
* **`skill_parry`** — estaba en el catálogo y **ningún jefe lo soltaba**, porque
  `skill_drop` era un solo `str` y el venado ya suelta el dash. Ahora acepta
  varias habilidades sin romper la forma antigua: una entrega que escriba
  `skill_drop = "skill_dash"` sigue funcionando igual.
* **`play_voz`** — el motor sabía reproducir voz y no había **ni un archivo**
  (GAP-031). Ahora el venado habla al cambiar de fase. Las líneas se sintetizan
  con el mismo generador que produce todos los demás sonidos del proyecto
  (`tools/generate_all_assets.py`): no es cableado de mentira, es exactamente
  cómo existe cada sonido de este juego.
"""
from __future__ import annotations

from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def venado(event_bus):
    from src.stages.boss_venado.boss_venado import BossVenado

    jefe = BossVenado(pygame.Vector2(100, 100))
    jefe.set_event_bus(event_bus)
    return jefe


class TestElEnjambreDeBalas:
    def test_el_venado_lo_tiene(self, venado) -> None:
        from src.framework.ecs.bullet_swarm import EnjambreDeBalas

        assert isinstance(venado.esporas, EnjambreDeBalas)

    def test_la_fase_dos_abre_un_abanico(self, venado) -> None:
        antes = venado.esporas.contador

        venado._soltar_abanico_de_esporas()

        assert venado.esporas.contador > antes

    def test_las_esporas_hacen_dano_al_jugador(self, venado) -> None:
        venado._soltar_abanico_de_esporas()
        # Un rect enorme centrado en el jefe atrapa balas vayan donde vayan.
        objetivo = pygame.Rect(int(venado.rect.centerx) - 200,
                               int(venado.rect.centery) - 200, 400, 400)

        assert venado.esporas.dano_total_contra(objetivo) > 0.0

    def test_tiene_uso_fuera_de_su_modulo(self) -> None:
        """La comprobación que lo saca de GAP-032."""
        usos = [
            p.name for p in (RAIZ / "src").rglob("*.py")
            if p.name != "bullet_swarm.py"
            and "EnjambreDeBalas" in p.read_text(encoding="utf-8")
        ]
        assert usos, "EnjambreDeBalas sigue sin usarse fuera de su módulo"


class TestSkillParry:
    def test_el_venado_suelta_las_dos_habilidades(self, venado) -> None:
        sueltas = venado.habilidades_que_suelta()

        assert "skill_dash" in sueltas
        assert "skill_parry" in sueltas

    def test_la_forma_antigua_sigue_valiendo(self) -> None:
        """Una entrega con `skill_drop = "x"` no puede romperse."""
        from src.framework.entities.boss_base import BossBase

        class _JefeDeEntrega(BossBase):
            skill_drop = "skill_dash"

            def _get_animation_key(self) -> str: return "idle"
            def _patrol_behavior(self, dt: float) -> None: pass
            def _alert_behavior(self, dt: float) -> None: pass
            def _build_hitbox(self): return self.rect.copy()
            def _build_hurtbox(self): return self.rect.copy()

        jefe = _JefeDeEntrega(pygame.Vector2(0, 0))

        assert jefe.habilidades_que_suelta() == ["skill_dash"]

    def test_un_jefe_sin_habilidad_no_suelta_nada(self) -> None:
        from src.framework.entities.boss_base import BossBase

        class _JefeMudo(BossBase):
            def _get_animation_key(self) -> str: return "idle"
            def _patrol_behavior(self, dt: float) -> None: pass
            def _alert_behavior(self, dt: float) -> None: pass
            def _build_hitbox(self): return self.rect.copy()
            def _build_hurtbox(self): return self.rect.copy()

        assert _JefeMudo(pygame.Vector2(0, 0)).habilidades_que_suelta() == []

    def test_alguien_suelta_skill_parry(self) -> None:
        """Estaba en el catálogo y no lo soltaba nadie (doc 60 §11)."""
        sueltan = [
            p.name for p in (RAIZ / "src" / "stages").rglob("*.py")
            if "skill_parry" in p.read_text(encoding="utf-8", errors="replace")
        ]
        assert sueltan, "skill_parry sigue sin dueño: es contenido inalcanzable"


class TestLaVozDelVenado:
    def test_existen_los_archivos_de_voz(self) -> None:
        """GAP-031 decía «ni un solo fichero de voz en assets/»."""
        voces = list((RAIZ / "assets" / "sfx" / "voz").glob("*.wav"))

        assert voces, "sigue sin haber un solo archivo de voz"

    def test_el_venado_habla_al_cambiar_de_fase(self, venado, monkeypatch) -> None:
        dichas: list[str] = []

        class _Audio:
            def play_voz(self, name: str, **_kw: object) -> None:
                dichas.append(name)

        venado.audio_de_voz = _Audio()
        venado._finish_phase_transition()

        assert dichas, "el cambio de fase no dice ninguna línea"

    def test_sin_audio_no_revienta(self, venado) -> None:
        """Una entrega puede construir el jefe sin gestor de audio."""
        venado._finish_phase_transition()      # no debe lanzar

    def test_play_voz_tiene_llamante_en_produccion(self) -> None:
        llamantes = [
            p.name for p in (RAIZ / "src").rglob("*.py")
            if p.name != "audio_manager.py"
            and "play_voz(" in p.read_text(encoding="utf-8")
        ]
        assert llamantes, "play_voz sigue sin llamante: GAP-031 sin cerrar"
