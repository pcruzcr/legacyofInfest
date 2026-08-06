"""AUD-293 — lo único que no existía en absoluto.

El hueco
--------
`docs/87` §3: no había clase de árbol, ni nodos, ni pantalla, y
`ExperienceSystem` repartía puntos que **no se podían gastar en nada** — ni
siquiera existía el método. Era la última pieza entera del bucle de progresión.

Las decisiones que hay que defender
-----------------------------------
1. **Sólo estadísticas.** Las mecánicas las sueltan los jefes. Lo que puedes
   *hacer* lo abre derrotar a alguien; lo que *aguantas o pegas*, jugar.
2. **Diez corazones y ni uno más**, y el tope se aplica en `Player.max_health`,
   que es por donde pasan todos los sumandos. Recortarlo en el árbol dejaría
   que las reliquias se lo saltaran.
3. **El coste sube con el rango.** Con coste plano la ruta óptima es siempre
   subir la rama más barata, y el árbol deja de ser una decisión.
4. **Nada toca la física.** Un nodo que subiera el salto recalificaría los
   dieciséis mapas que mide `grade_stage`.
"""
from __future__ import annotations

import pytest

from src.engine.core.experience import ExperienceSystem
from src.engine.core.skill_tree import (
    CATALOGO,
    CORAZONES_MAXIMOS,
    ArbolDeHabilidades,
)


@pytest.fixture
def arbol():
    ArbolDeHabilidades._reset_instance()
    ExperienceSystem.get_instance().reset()
    return ArbolDeHabilidades.get_instance()


def _con_puntos(n: int) -> None:
    """Concede al menos `n` puntos de habilidad."""
    exp = ExperienceSystem.get_instance()
    while exp.puntos < n:
        exp.grant(500)


class TestElCatalogo:
    def test_hay_tres_ramas(self, arbol) -> None:
        assert {n.id for n in CATALOGO} == {"vitalidad", "fuerza", "impetu"}

    def test_ninguna_toca_la_fisica(self, arbol) -> None:
        """Vida, daño y duración del ultimate. Nada que mueva al jugador: un
        nodo de salto recalificaría los dieciséis mapas."""
        metodos = {"bonus_corazones", "bonus_dano", "bonus_ultimate"}
        assert {m for m in dir(arbol) if m.startswith("bonus_")} == metodos

    def test_la_vitalidad_llega_justo_a_diez_corazones(self, arbol) -> None:
        from src.engine.core import settings

        vitalidad = next(n for n in CATALOGO if n.id == "vitalidad")
        tope = settings.PLAYER_MAX_HEALTH + vitalidad.rangos * vitalidad.por_rango
        assert tope == CORAZONES_MAXIMOS

    def test_el_coste_sube_con_el_rango(self, arbol) -> None:
        fuerza = next(n for n in CATALOGO if n.id == "fuerza")
        assert fuerza.coste_del_rango(0) < fuerza.coste_del_rango(3)


class TestComprar:
    def test_sin_puntos_no_se_puede(self, arbol) -> None:
        assert not arbol.puede_comprar("vitalidad")
        assert "puntos" in arbol.motivo_para_no_comprar("vitalidad")

    def test_con_puntos_sí(self, arbol) -> None:
        _con_puntos(1)
        assert arbol.comprar("vitalidad")
        assert arbol.rango("vitalidad") == 1

    def test_comprar_gasta_los_puntos(self, arbol) -> None:
        _con_puntos(1)
        antes = ExperienceSystem.get_instance().puntos
        coste = arbol.coste("vitalidad")
        arbol.comprar("vitalidad")
        assert ExperienceSystem.get_instance().puntos == antes - coste

    def test_no_se_pasa_del_maximo(self, arbol) -> None:
        _con_puntos(100)
        vitalidad = next(n for n in CATALOGO if n.id == "vitalidad")
        for _ in range(vitalidad.rangos + 5):
            arbol.comprar("vitalidad")
        assert arbol.rango("vitalidad") == vitalidad.rangos
        assert arbol.al_maximo("vitalidad")
        assert "máximo" in arbol.motivo_para_no_comprar("vitalidad")

    def test_un_nodo_bloqueado_dice_por_qué(self, arbol) -> None:
        """Un botón apagado sin explicación es la forma más rápida de que
        alguien concluya que el juego está roto."""
        _con_puntos(100)
        motivo = arbol.motivo_para_no_comprar("impetu")
        assert "Fuerza" in motivo

    def test_y_se_abre_al_cumplir_el_requisito(self, arbol) -> None:
        _con_puntos(100)
        arbol.comprar("fuerza")
        assert arbol.puede_comprar("impetu")

    def test_un_nodo_inventado_no_revienta(self, arbol) -> None:
        assert not arbol.comprar("volar")
        assert arbol.rango("volar") == 0


class TestLoQueDa:
    def test_los_corazones(self, arbol) -> None:
        _con_puntos(100)
        arbol.comprar("vitalidad")
        arbol.comprar("vitalidad")
        assert arbol.bonus_corazones() == pytest.approx(1.0)

    def test_el_daño(self, arbol) -> None:
        _con_puntos(100)
        arbol.comprar("fuerza")
        assert arbol.bonus_dano() == pytest.approx(0.08)

    def test_el_ultimate(self, arbol) -> None:
        _con_puntos(100)
        arbol.comprar("fuerza")
        arbol.comprar("impetu")
        assert arbol.bonus_ultimate() == pytest.approx(0.15)


class TestElTopeDeDiezCorazones:
    def test_el_arbol_solo_no_lo_pasa(self, arbol) -> None:
        _con_puntos(100)
        for _ in range(20):
            arbol.comprar("vitalidad")
        from src.engine.core import settings

        assert (settings.PLAYER_MAX_HEALTH
                + arbol.bonus_corazones()) <= CORAZONES_MAXIMOS

    def test_ni_sumándole_reliquias(self, arbol) -> None:
        """El tope se aplica en `Player.max_health` justamente para esto."""
        import pygame

        from src.framework.entities.player import Player

        pygame.init()
        jugador = Player(pygame.Vector2(0, 0))
        _con_puntos(100)
        for _ in range(20):
            arbol.comprar("vitalidad")
        jugador._bonus_max_health = 50.0
        jugador._bonus_arbol_salud = arbol.bonus_corazones()
        assert jugador.max_health == CORAZONES_MAXIMOS


class TestPersistencia:
    def test_ida_y_vuelta(self, arbol) -> None:
        _con_puntos(100)
        arbol.comprar("vitalidad")
        arbol.comprar("fuerza")
        datos = arbol.to_dict()

        otro = ArbolDeHabilidades()
        otro.from_dict(datos)
        assert otro.rango("vitalidad") == 1
        assert otro.rango("fuerza") == 1

    def test_una_partida_editada_a_mano_no_da_veinte_corazones(self, arbol) -> None:
        arbol.from_dict({"vitalidad": 999})
        vitalidad = next(n for n in CATALOGO if n.id == "vitalidad")
        assert arbol.rango("vitalidad") == vitalidad.rangos

    def test_ni_inventa_nodos(self, arbol) -> None:
        arbol.from_dict({"volar": 3})
        assert arbol.to_dict() == {}

    def test_viaja_con_el_slot(self, arbol) -> None:
        from src.engine.core.save_data import SaveData
        from src.engine.core.save_manager import aplicar_estado_de, volcar_estado_en

        _con_puntos(100)
        arbol.comprar("vitalidad")
        data = SaveData()
        volcar_estado_en(data)
        assert data.arbol.get("vitalidad") == 1

        arbol.reset()
        aplicar_estado_de(data)
        assert ArbolDeHabilidades.get_instance().rango("vitalidad") == 1


class TestLaPantalla:
    def test_está_en_el_menú_principal(self) -> None:
        """Una pantalla que existe y nadie encuentra es el defecto favorito de
        este repositorio."""
        import inspect

        from src.engine.scenes import title_scene

        fuente = inspect.getsource(title_scene)
        assert "SKILL TREE" in fuente
        assert "SkillTreeScene" in fuente

    def test_se_dibuja(self, arbol) -> None:
        import pygame

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.skill_tree_scene import SkillTreeScene

        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((800, 600))
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = SkillTreeScene(ctx)
        escena.on_enter()
        escena.update(0.016)
        escena.draw(pygame.Surface((800, 600)))
