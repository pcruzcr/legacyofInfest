"""
La vista cenital: desde arriba, sin gravedad y con dos ejes.

AUD-129 — qué es y por qué se pudo hacer barato
================================================
Cenital es la vista en planta de Zelda, Hotline Miami o la sala de cámaras que
César Ubáu escribió para `stage2_2`. El motor ya tenía casi todo lo necesario
—colisión AABB por ejes separados, `gravity_multiplier`, el cono de visión, la
patrulla sobre B-Spline— y lo único que faltaba era **dejar de aplicar
gravedad y aceptar entrada vertical**.

Se implementa como una bandera del jugador, no como un estado nuevo. Los 26
estados existentes —atacar, recibir daño, morir, parry— valen igual desde
arriba; lo único que cambia es cómo se integra el movimiento. Un
`PlayerState.CENITAL` habría obligado a duplicar media máquina de estados sin
ganar nada.

Las tres trampas de la vista cenital
-------------------------------------
Las tres están probadas aquí porque las tres se olvidan siempre:

1. **La diagonal más rápida.** Sin normalizar, moverse en diagonal da 1,41×
   la velocidad y todo el mundo acaba andando en zigzag porque es
   objetivamente mejor.
2. **El jugador cayendo para siempre.** Si `is_grounded` no se fuerza, el
   primer fotograma entra en `FALLING`, el sonido de aterrizaje se repite en
   bucle y el salto se recarga sin parar.
3. **Las plataformas de un solo sentido convertidas en muros invisibles.**
   Vista en planta, una repisa atravesable es un rectángulo que frena por un
   lado y no por el otro, sin nada en pantalla que lo explique.
"""
from __future__ import annotations

import pygame
import pytest

from src.engine.core import settings
from src.engine.input.action_map import Action
from src.engine.input.input_manager import InputManager
from src.framework.entities.player import Player
from src.framework.stage.stage_loader import VISTAS_VALIDAS

DT = 1.0 / 60.0


def _Entrada(*mantenidas: Action) -> InputManager:
    """Un `InputManager` **real** con esas teclas bajadas.

    La primera versión de esto era una clase de mentira con tres métodos, y
    falló al primer intento: `_InputSnapshot` también llama a
    `is_action_pressed`, que al doble le faltaba. Un doble incompleto no es
    un doble, es una fuente de `AttributeError` que oculta el fallo real.

    Con el gestor de verdad la prueba recorre el mismo camino que el juego
    —enlaces de teclas incluidos— y si mañana `_InputSnapshot` consulta una
    acción más, esto sigue funcionando.
    """
    im = InputManager()
    for accion in mantenidas:
        for tecla in im._bindings.get(accion, []):
            im._held.add(tecla)
    return im


@pytest.fixture
def jugador() -> Player:
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
    p = Player(pygame.Vector2(100.0, 100.0))
    p.vista_cenital = True
    return p


class TestSinGravedad:
    def test_quieto_no_cae(self, jugador) -> None:
        """La prueba más básica, y la que define la vista."""
        y0 = jugador.position.y
        for _ in range(120):
            jugador.update(DT, [], _Entrada())
        assert jugador.position.y == pytest.approx(y0, abs=1.0), (
            f"el jugador cayó de {y0} a {jugador.position.y}: sigue habiendo "
            f"gravedad en la vista cenital"
        )

    def test_en_lateral_si_cae(self, jugador) -> None:
        """Sin esto, la prueba de arriba pasaría con la gravedad rota.

        Es la prueba de control: comprueba que el jugador **sí** cae cuando
        toca. Sin ella, `test_quieto_no_cae` seguiría verde aunque alguien
        rompiera la gravedad para todo el juego.
        """
        jugador.vista_cenital = False
        y0 = jugador.position.y
        for _ in range(60):
            jugador.update(DT, [], _Entrada())
        assert jugador.position.y > y0 + 100.0, (
            f"en un segundo de caída libre el jugador debería bajar unos "
            f"400 px y bajó {jugador.position.y - y0:.0f}"
        )

    def test_siempre_esta_en_el_suelo(self, jugador) -> None:
        """Desde arriba no existe «en el aire»: el suelo es el plano de juego."""
        for _ in range(10):
            jugador.update(DT, [], _Entrada())
        assert jugador.is_grounded


class TestMovimientoEnDosEjes:
    def test_arriba_sube(self, jugador) -> None:
        y0 = jugador.position.y
        for _ in range(30):
            jugador.update(DT, [], _Entrada(Action.MOVE_UP))
        assert jugador.position.y < y0 - 10.0

    def test_abajo_baja(self, jugador) -> None:
        y0 = jugador.position.y
        for _ in range(30):
            jugador.update(DT, [], _Entrada(Action.MOVE_DOWN))
        assert jugador.position.y > y0 + 10.0

    def test_soltar_para_en_seco(self, jugador) -> None:
        """En cenital no hay inercia de caída que respetar."""
        for _ in range(20):
            jugador.update(DT, [], _Entrada(Action.MOVE_DOWN))
        jugador.update(DT, [], _Entrada())
        assert jugador.velocity.y == pytest.approx(0.0)

    def test_arriba_y_abajo_a_la_vez_se_anulan(self, jugador) -> None:
        """Se comprueba la **velocidad**, no la posición.

        `MOVE_DOWN` comparte enlace de teclas con `CROUCH` (`↓` y `S`), así
        que pulsar abajo también agacha al jugador, y agacharse cambia el alto
        del rectángulo — lo que mueve `position.y` unos píxeles sin que se
        haya movido nadie. Medir la posición aquí probaría el tamaño de la
        caja de agachado, no la anulación de las dos direcciones.
        """
        for _ in range(30):
            jugador.update(
                DT, [], _Entrada(Action.MOVE_UP, Action.MOVE_DOWN))
        assert jugador.velocity.y == pytest.approx(0.0), (
            "arriba y abajo a la vez deberían anularse"
        )


class TestLaDiagonalNoEsMasRapida:
    """La trampa número uno de toda vista cenital."""

    def _recorrido(self, jugador, *acciones) -> float:
        inicio = pygame.Vector2(jugador.position)
        for _ in range(30):
            jugador.update(DT, [], _Entrada(*acciones))
        return (pygame.Vector2(jugador.position) - inicio).length()

    def test_la_diagonal_recorre_lo_mismo_que_la_recta(self, jugador) -> None:
        recto = self._recorrido(jugador, Action.MOVE_RIGHT)

        otro = Player(pygame.Vector2(100.0, 100.0))
        otro.vista_cenital = True
        diagonal = self._recorrido(otro, Action.MOVE_RIGHT, Action.MOVE_UP)

        assert diagonal == pytest.approx(recto, rel=0.08), (
            f"en diagonal se recorren {diagonal:.1f} px y en recta "
            f"{recto:.1f}. Sin normalizar la diagonal da 1,41× y el jugador "
            f"aprende a andar en zigzag porque es objetivamente más rápido"
        )


class TestLasPlataformasDeUnSentidoSeIgnoran:
    """Vista en planta, una repisa atravesable es un muro invisible."""

    def test_no_frenan_al_bajar(self, jugador) -> None:
        repisa = pygame.Rect(80, 140, 96, 8)
        for _ in range(40):
            jugador.update(DT, [], _Entrada(Action.MOVE_DOWN),
                           one_way_rects=[repisa])
        assert jugador.position.y > repisa.bottom, (
            f"la repisa de un solo sentido detuvo al jugador en "
            f"{jugador.position.y}: desde arriba es un muro invisible"
        )

    def test_en_lateral_si_frenan(self, jugador) -> None:
        """El contrato de la vista lateral no se toca."""
        jugador.vista_cenital = False
        repisa = pygame.Rect(80, 200, 96, 8)
        for _ in range(90):
            jugador.update(DT, [], _Entrada(), one_way_rects=[repisa])
        assert jugador.is_grounded


class TestLosSolidosSiguenBloqueando:
    """Lo único que separa una sala de un rectángulo vacío."""

    @pytest.mark.parametrize(
        ("accion", "eje", "signo"),
        [
            (Action.MOVE_RIGHT, "x", 1),
            (Action.MOVE_LEFT, "x", -1),
            (Action.MOVE_DOWN, "y", 1),
            (Action.MOVE_UP, "y", -1),
        ],
    )
    def test_un_muro_detiene_en_los_cuatro_sentidos(
        self, jugador, accion, eje, signo,
    ) -> None:
        """En lateral sólo se prueban dos: desde arriba hacen falta los cuatro."""
        if eje == "x":
            muro = pygame.Rect(100 + signo * 60, 60, 16, 120)
        else:
            muro = pygame.Rect(60, 100 + signo * 60, 120, 16)

        for _ in range(90):
            jugador.update(DT, [muro], _Entrada(accion))

        assert not jugador.rect.colliderect(muro), (
            f"el jugador atravesó el muro yendo hacia {accion.name}: acabó en "
            f"{tuple(jugador.rect)} y el muro está en {tuple(muro)}"
        )


class TestLaVistaSaleDelMapa:
    def test_las_dos_vistas_estan_declaradas(self) -> None:
        assert VISTAS_VALIDAS == {"lateral", "cenital"}

    def test_el_cargador_acepta_cenital_en_los_dos_idiomas(self) -> None:
        """`vista` y `view`: el proyecto es bilingüe en propiedades desde F3.1."""
        import inspect

        from src.framework.stage import stage_loader

        fuente = inspect.getsource(stage_loader.StageLoader)
        assert 'props.get("vista")' in fuente
        assert 'props.get("view")' in fuente

    def test_una_vista_desconocida_cae_a_lateral(self) -> None:
        """Un mapa con `vista = isometrica` se juega, con aviso."""
        import inspect

        from src.framework.stage import stage_loader

        fuente = inspect.getsource(stage_loader.StageLoader)
        assert 'vista = "lateral"' in fuente

    def test_por_defecto_los_quince_mapas_siguen_siendo_laterales(self) -> None:
        """La regresión que importa: no cambiar quince mapas sin querer."""
        from src.framework.stage.stage_loader import StageData

        assert StageData.__dataclass_fields__["vista"].default == "lateral"
