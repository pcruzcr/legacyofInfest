"""
Stage Pokemon Cenital — ejemplo monster-tamer 100% cenital.

Vista cenital estilo Pokemon: hierba alta con encuentros aleatorios,
captura con Recogible (Pokeball), y PC (Cofre) para guardar.
Usa solo sistemas existentes: vista=cenital, Efectos, Inventory, Dialogue.
"""

from __future__ import annotations

import random
from pathlib import Path

import pygame

from src.engine.core import settings
from src.engine.core.experience import get_experience
from src.engine.core.inventory import get_inventory
from src.engine.input.action_map import Action
from src.framework.scenes.stage_scene import StageScene

# Reusa enemigos existentes como "monstruos salvajes" — sin IP
# WalkerInsect = planta, FlyingBoa = volador, ShooterSerpienteArbol = fuego
MONSTRUOS_SALVAJES = ["WalkerInsect", "FlyingBoa", "ShooterSerpienteArbol"]


class StagePokemonCenital(StageScene):
    """Escenario cenital demo — hierba alta + captura + progresion RPG.

    Vista 100% cenital (top-down sin gravedad) y bucle RPG completo:
    captura -> XP -> nivel -> puntos de habilidad -> skill tree.
    Todo vía sistemas existentes: ExperienceSystem, Inventory, Efectos,
    Dialogue y Objetivos. Sin IP.
    """

    STAGE_ID = "stage_pokemon_cenital"
    STAGE_NAME = "BOSQUE MONSTRUOS — CENITAL"
    TMX_PATH = settings.ASSETS_DIR / "maps/stage_pokemon_cenital/stage_pokemon_cenital.tmx"
    ZONE = 1

    # XP que da capturar (equivalente a walker+ bonus)
    XP_POR_CAPTURA: int = 15
    XP_POR_ENCUENTRO: int = 5

    def __init__(self, context) -> None:
        super().__init__(context, Path(self.TMX_PATH))
        self._encuentros = 0
        self._capturas = 0
        self._mensaje_captura_timer: float = 0.0
        self._texto_captura: str = ""

    def on_stage_start(self) -> None:
        super().on_stage_start()
        # Asegura 5 Pokeballs iniciales si el inventario está vacío
        try:
            from src.engine.core.inventory import get_inventory
            inv = get_inventory()
            if inv.count("pokeball") == 0:
                inv.collect("pokeball", 5)
        except Exception:
            pass
        # Mensaje tutorial (también explica progresión RPG)
        try:
            self.context.event_bus.emit(
                "SHOW_MESSAGE",
                text="¡Hierba alta! Z=capturar (gasta Pokeball, +15 XP), X=PC, I=Inventario, K=Árbol de habilidades",
                duration=7.0,
            )
        except Exception:
            pass

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._player is None or self._stage_data is None:
            return
        if self._mensaje_captura_timer > 0:
            self._mensaje_captura_timer -= dt
        # Hierba alta = HazardZone rect; si player dentro, puede capturar con Z
        im = self.input
        quiere_capturar = False
        if im is not None:
            try:
                quiere_capturar = im.is_action_just_pressed(Action.ATTACK) or im.is_action_just_pressed(Action.CONFIRM)
            except Exception:
                quiere_capturar = False

        en_hierba = False
        for hz in self._stage_data.hazard_zones:
            if hz.rect.colliderect(self._player.rect):
                en_hierba = True
                break

        # Encuentro pasivo: estar en hierba tiene chance de "¡Un salvaje apareció!" + XP pequeña
        if en_hierba and random.random() < 0.008:
            self._encuentros += 1
            try:
                from src.framework.combate import efectos
                if hasattr(self._player, "efectos"):
                    efectos.aplicar(self._player.efectos, "lentitud", duracion=1.0)
            except Exception:
                pass
            try:
                self.context.event_bus.emit("SFX_HAZARD_ZONE", pos=self._player.rect.center)
                self.context.event_bus.emit("VFX_POISON", pos=self._player.rect.center)
            except Exception:
                pass
            # XP pasiva por explorar hierba
            try:
                exp = get_experience()
                nuevos = exp.grant(self.XP_POR_ENCUENTRO)
                if nuevos > 0:
                    self.context.event_bus.emit(
                        "SHOW_MESSAGE",
                        text=f"¡Subiste a nivel {exp.nivel}! +{nuevos} pt(s) árbol (K)",
                        duration=3.0,
                    )
            except Exception:
                pass
            # Si además pulsa Z en el mismo frame, se cuenta como captura activa
            if quiere_capturar:
                quiere_capturar = False  # evita doble conteo
                self._intentar_captura()

        # Captura activa con Z / Confirm dentro de hierba
        if en_hierba and quiere_capturar:
            self._intentar_captura()
        elif quiere_capturar and not en_hierba:
            # Fuera de hierba, avisa una vez cada 2s para no spamear
            if self._mensaje_captura_timer <= 0:
                self._texto_captura = "Ve a la hierba alta (zona verde) para capturar"
                self._mensaje_captura_timer = 2.0

    def _intentar_captura(self) -> None:
        """Consume 1 pokeball, otorga XP y avanza objetivo."""
        from src.engine.core.experience import get_experience

        inv = get_inventory()
        if inv.count("pokeball") <= 0:
            self._texto_captura = "¡Sin Pokeballs! Recoge más en el mapa"
            self._mensaje_captura_timer = 2.5
            try:
                self.context.event_bus.emit("SHOW_MESSAGE", text=self._texto_captura, duration=2.5)
            except Exception:
                pass
            return
        # Gasta 1
        inv._items["pokeball"] = inv.count("pokeball") - 1
        if inv._items["pokeball"] <= 0:
            inv._items.pop("pokeball", None)
        inv.save()
        self._capturas += 1
        # XP + nivel
        try:
            exp = get_experience()
            antes = exp.nivel
            nuevos = exp.grant(self.XP_POR_CAPTURA)
            # Sonido + VFX
            self.context.event_bus.emit("SFX_ENEMY_DIE_SMALL", pos=self._player.rect.center)
            self.context.event_bus.emit("VFX_KILL_FLASH", pos=self._player.rect.center)
            # Mensaje
            mon = MONSTRUOS_SALVAJES[(self._capturas - 1) % len(MONSTRUOS_SALVAJES)]
            self._texto_captura = f"¡Capturaste {mon}! +{self.XP_POR_CAPTURA} XP"
            if nuevos > 0:
                self._texto_captura += f" -> ¡Nivel {exp.nivel}! (K para gastar {nuevos} punto(s))"
            self._mensaje_captura_timer = 3.0
            self.context.event_bus.emit("SHOW_MESSAGE", text=self._texto_captura, duration=3.0)
            # Emitir ENEMY_DIED sintético para que Objetivos "derrotar" cuente
            self.context.event_bus.emit(
                "ENEMY_DIED",
                entity_id=f"WalkerInsect_{self._capturas}",
                position=self._player.rect.center,
            )
            # Si subió de nivel, también emite para logros / HUD
            if exp.nivel > antes:
                self.context.event_bus.emit("SFX_BOSS_PHASE_CHANGE", pos=self._player.rect.center)
        except Exception:
            self._texto_captura = f"¡Capturado! ({self._capturas})"
            self._mensaje_captura_timer = 2.0

    def on_next_trigger_entered(self) -> None:
        # No NextTrigger en cenital sala — usa PC (Cofre) para guardar
        super().on_next_trigger_entered()

    def draw(self, surface: pygame.Surface) -> None:
        super().draw(surface)
        # Overlay RPG: nivel, XP y Pokeballs — siempre visible, estilo Pokemon
        try:
            from src.engine.core.experience import get_experience
            from src.engine.core.inventory import get_inventory
            exp = get_experience()
            inv = get_inventory()
            nivel = exp.nivel
            dentro, total = exp.progreso_del_nivel()
            pct = (dentro / total) if total > 0 else 0
            balls = inv.count("pokeball")
            # Barra pequeña arriba
            font = pygame.font.Font(None, 18)
            txt = font.render(
                f"Nv.{nivel} XP {dentro}/{total} Balls:{balls} Cap:{self._capturas}",
                True, (255, 255, 210),
            )
            # Fondo semitransparente
            bg = pygame.Surface((txt.get_width()+12, txt.get_height()+8), pygame.SRCALPHA)
            bg.fill((20,20,30,180))
            surface.blit(bg, (8, 8))
            surface.blit(txt, (14, 12))
            # Barra de XP
            bar_w, bar_h = 180, 8
            bx, by = 14, 30
            pygame.draw.rect(surface, (40,40,50), (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, (90,180,255), (bx, by, int(bar_w * pct), bar_h))
            pygame.draw.rect(surface, (200,200,220), (bx, by, bar_w, bar_h), 1)
            if self._mensaje_captura_timer > 0:
                f2 = pygame.font.Font(None, 16)
                t2 = f2.render(self._texto_captura, True, (255,240,120))
                surface.blit(t2, (14, 42))
        except Exception:
            pass

    @property
    def debug_stats(self) -> dict:
        try:
            from src.engine.core.experience import get_experience
            exp = get_experience()
            return {
                "encuentros": self._encuentros,
                "capturas": self._capturas,
                "nivel": exp.nivel,
                "xp": exp.exp,
                "puntos": exp.puntos,
            }
        except Exception:
            return {"encuentros": self._encuentros, "capturas": self._capturas}
