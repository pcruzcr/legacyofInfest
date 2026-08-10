"""
Bloques que se empujan y bloques que se rompen — AUD-140.

Las dos últimas filas del catálogo de mecánicas. Lo que aportan al diseño:

* **Empujable**: es el único objeto del motor que el jugador puede *colocar*.
  Con eso se hacen puentes sobre pinchos, escalones para llegar a una cornisa
  y parapetos contra proyectiles. Convierte una sala en un problema.
* **Destructible**: convierte una pared en una pregunta. Un muro que cede a
  golpes premia probar cosas, que es lo contrario de un muro normal.

Los tres fallos que estas pruebas vigilan
------------------------------------------
1. **El redondeo.** El `rect` va en enteros y la velocidad en float: a 45 px/s
   y 60 fps son 0,75 px por fotograma, que redondeados a 1 harían al bloque ir
   a 60 px/s. Es el mismo defecto de la inundación (AUD-135), y aquí se nota
   más porque el jugador está calculando a ojo dónde va a quedar el bloque.
2. **Empujar de lado, no desde arriba.** Sin esa condición, quedarse quieto
   encima de un bloque lo iría desplazando: el suelo se movería solo.
3. **Volver a su sitio al morir.** Un bloque empujado a un foso deja el nivel
   sin solución, y el jugador no tiene cómo saber que ya no se puede pasar.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.bloques import (
    BloqueDestructible,
    BloqueEmpujable,
    SistemaDeBloques,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []

    def emit(self, evento: str, **_datos) -> None:
        self.emitidos.append(evento)


def _suelo(y: int = 200, ancho: int = 400) -> list[pygame.Rect]:
    return [pygame.Rect(0, y, ancho, 16)]


class TestEmpujar:
    def _montaje(self, x_bloque: int = 100):
        bloque = BloqueEmpujable(rect=pygame.Rect(x_bloque, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(x_bloque - 20, 170, 20, 30)
        return sistema, bloque, jugador

    def test_el_bloque_se_mueve_al_empujarlo(self) -> None:
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        assert bloque.rect.x > antes

    def test_a_la_velocidad_declarada_y_no_a_la_del_redondeo(self) -> None:
        """45 px/s a 60 fps son 0,75 px por fotograma.

        Redondeando cada fotograma a 1 px, el bloque iría a 60 px/s: un tercio
        más rápido de lo que dice su propiedad, y el diseñador que midió el
        salto sobre el papel se encuentra otra cosa.
        """
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
            # El jugador camina pegado al bloque, que es lo que hace la
            # resolución de colisión cuando se anda contra un sólido.
            jugador.right = bloque.rect.left
        recorrido = bloque.rect.x - antes
        assert recorrido == pytest.approx(45, abs=2), (
            f"recorrió {recorrido} px en un segundo a 45 px/s"
        )

    def test_sin_direccion_no_se_mueve(self) -> None:
        sistema, bloque, jugador = self._montaje()
        antes = bloque.rect.x
        sistema.empujar(jugador, 0, 1 / 60, _suelo())
        assert bloque.rect.x == antes

    def test_desde_arriba_no_se_empuja(self) -> None:
        """Si pisarlo lo arrastrara, el suelo se movería solo."""
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        encima = pygame.Rect(105, 138, 20, 30)      # justo sobre el bloque
        antes = bloque.rect.x
        for _ in range(30):
            sistema.empujar(encima, 1, 1 / 60, _suelo())
        assert bloque.rect.x == antes

    def test_no_se_empuja_a_traves_de_una_pared(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(80, 170, 20, 30)
        pared = pygame.Rect(140, 100, 16, 120)
        for _ in range(120):
            sistema.empujar(jugador, 1, 1 / 60, [*_suelo(), pared])
        assert bloque.rect.right <= pared.left

    def test_un_bloque_no_empuja_a_otro_a_traves(self) -> None:
        uno = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        dos = BloqueEmpujable(rect=pygame.Rect(140, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[uno, dos])
        jugador = pygame.Rect(80, 170, 20, 30)
        for _ in range(120):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        assert not uno.rect.colliderect(dos.rect)

    def test_se_empuja_hacia_la_izquierda(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(132, 170, 20, 30)
        for _ in range(60):
            sistema.empujar(jugador, -1, 1 / 60, _suelo())
        assert bloque.rect.x < 100


class TestCaer:
    def test_el_bloque_cae_hasta_el_suelo(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        for _ in range(180):
            sistema.caer(1 / 60, _suelo())
        assert bloque.rect.bottom == 200

    def test_no_atraviesa_el_suelo_con_un_dt_grande(self) -> None:
        """Un `dt` grande —una carga, un tirón— no puede meter el bloque
        dentro del suelo: la caída se resuelve por pasos de un píxel."""
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        sistema.caer(2.0, _suelo())
        assert bloque.rect.bottom <= 200

    def test_sin_gravedad_se_queda_flotando(self) -> None:
        """Para escenarios cenitales, donde «abajo» no significa nada."""
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32),
                                 con_gravedad=False)
        sistema = SistemaDeBloques(empujables=[bloque])
        for _ in range(60):
            sistema.caer(1 / 60, _suelo())
        assert bloque.rect.y == 50


class TestRomper:
    def test_un_golpe_rompe_un_bloque_de_un_golpe(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        assert sistema.golpear(pygame.Rect(96, 96, 24, 24)) == 1
        assert bloque.roto

    def test_uno_de_tres_golpes_aguanta_dos(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16), golpes=3)
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        assert sistema.golpear(caja) == 0
        assert sistema.golpear(caja) == 0
        assert sistema.golpear(caja) == 1

    def test_un_golpe_que_no_toca_no_cuenta(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        assert sistema.golpear(pygame.Rect(300, 300, 24, 24)) == 0
        assert not bloque.roto

    def test_sin_caja_de_golpe_no_pasa_nada(self) -> None:
        """`active_hitbox` es `None` casi todos los fotogramas."""
        sistema = SistemaDeBloques(
            destructibles=[BloqueDestructible(rect=pygame.Rect(0, 0, 16, 16))])
        assert sistema.golpear(None) == 0

    def test_un_bloque_roto_no_se_vuelve_a_romper(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16))
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        sistema.golpear(caja)
        assert sistema.golpear(caja) == 0

    def test_al_romperse_emite_su_evento(self) -> None:
        """Cierra el circuito con el resto: abrir una puerta (AUD-132),
        arrancar una inundación (AUD-135), lanzar una escena (AUD-136)."""
        bus = _Bus()
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16),
                                    evento_al_romper="ABRIR_EL_PASO")
        SistemaDeBloques(destructibles=[bloque], bus=bus).golpear(
            pygame.Rect(96, 96, 24, 24))
        assert bus.emitidos == ["ABRIR_EL_PASO"]

    def test_sin_evento_no_emite_nada(self) -> None:
        bus = _Bus()
        SistemaDeBloques(
            destructibles=[BloqueDestructible(rect=pygame.Rect(0, 0, 16, 16))],
            bus=bus,
        ).golpear(pygame.Rect(0, 0, 16, 16))
        assert bus.emitidos == []


class TestLoQueLaMutacionDestapo:
    """AUD-181 / GAP-023 — once cambios que la suite no detectaba.

    `scripts/mutation_check.py` puntuó este módulo con un 56 %: se le podían
    cambiar once cosas y ninguna prueba se enteraba. Lo interesante no es el
    número, sino **por qué** sobrevivían tres de ellos.

    `test_no_se_empuja_a_traves_de_una_pared` y
    `test_un_bloque_no_empuja_a_otro_a_traves` pasaban por la razón
    equivocada. En las dos, el jugador se queda quieto en su sitio mientras el
    bloque avanza; en cuanto el bloque se aleja lo suficiente, `_toca_de_lado`
    deja de dar contacto y el bloque **se para solo**, mucho antes de llegar a
    la pared. La rama que comprueba la colisión no llegaba a ejecutarse nunca,
    así que se podía invertir entera y las dos pruebas seguían en verde.

    Aquí el jugador sigue al bloque —`jugador.right = bloque.rect.left`, que es
    lo que hace la resolución de colisión de verdad cuando se camina contra un
    sólido—, y entonces sí se llega a empujar contra algo.

    El que sigue vivo, y por qué no se persigue
    -------------------------------------------
    Queda 1 de 25 (96 %): la línea 204, `if dt <= 0.0` → `if dt < 0.0` en
    `caer`. Es **equivalente**. Con `dt == 0.0` el cuerpo se ejecuta pero no
    hace nada: la velocidad crece `GRAVEDAD_BLOQUE * 0`, y los píxeles a
    recorrer son `int(_vy * 0)` = 0, que sale por el `continue`. Comprobado
    sobre 5.000 secuencias aleatorias de `dt` —sembradas de ceros a
    propósito— comparando posición, velocidad y posición en coma flotante de
    los tres bloques: **0 diferencias**. Una prueba que lo matara tendría que
    afirmar que un fotograma de duración cero cambia algo.
    """

    def _empujar_siguiendo(self, sistema, bloque, jugador, solidos,
                           fotogramas: int = 600) -> None:
        """Empuja hacia la derecha manteniendo el contacto, como en el juego."""
        for _ in range(fotogramas):
            sistema.empujar(jugador, 1, 1 / 60, solidos)
            jugador.right = bloque.rect.left

    def test_empujando_sin_soltar_el_bloque_no_entra_en_la_pared(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(80, 170, 20, 30)
        pared = pygame.Rect(140, 100, 16, 120)

        self._empujar_siguiendo(sistema, bloque, jugador,
                                [*_suelo(), pared])

        assert bloque.rect.right <= pared.left, (
            f"el bloque acabó en x={bloque.rect.right} y la pared empieza en "
            f"{pared.left}: lo ha atravesado"
        )

    def test_empujando_sin_soltar_el_bloque_no_atraviesa_a_otro(self) -> None:
        uno = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        dos = BloqueEmpujable(rect=pygame.Rect(140, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[uno, dos])
        jugador = pygame.Rect(80, 170, 20, 30)

        self._empujar_siguiendo(sistema, uno, jugador, _suelo())

        assert not uno.rect.colliderect(dos.rect), (
            "un bloque empujado se ha metido dentro de otro"
        )
        assert uno.rect.right <= dos.rect.left

    def test_empujando_sin_soltar_el_bloque_no_atraviesa_un_destructible(
        self,
    ) -> None:
        """Un destructible entero es una pared: se rompe, no se aparta."""
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        muro = BloqueDestructible(rect=pygame.Rect(140, 168, 32, 32), golpes=3)
        sistema = SistemaDeBloques(empujables=[bloque], destructibles=[muro])
        jugador = pygame.Rect(80, 170, 20, 30)

        self._empujar_siguiendo(sistema, bloque, jugador, _suelo())

        assert bloque.rect.right <= muro.rect.left

    def test_un_destructible_roto_deja_pasar_al_bloque(self) -> None:
        """La contraparte: si sólo se comprobara «hay un destructible», un
        bloque roto seguiría estorbando y el paso quedaría cerrado para
        siempre."""
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        muro = BloqueDestructible(rect=pygame.Rect(140, 168, 32, 32))
        muro.golpear()
        sistema = SistemaDeBloques(empujables=[bloque], destructibles=[muro])
        jugador = pygame.Rect(80, 170, 20, 30)

        self._empujar_siguiendo(sistema, bloque, jugador, _suelo(ancho=600))

        assert bloque.rect.left > muro.rect.left, (
            "el bloque se paró ante un destructible ya roto"
        )

    # ── el reloj no va hacia atrás ────────────────────────────────
    def test_un_dt_negativo_no_arrastra_el_bloque_hacia_atras(self) -> None:
        """La guarda es `direccion == 0 or dt <= 0`. Con un `and` en vez del
        `or`, un `dt` negativo —un reloj que retrocede tras una pausa— empuja
        el bloque en sentido contrario al que camina el jugador."""
        sistema, bloque, jugador = TestEmpujar()._montaje()
        antes = bloque.rect.x

        movidos = sistema.empujar(jugador, 1, -0.1, _suelo())

        assert movidos == 0
        assert bloque.rect.x == antes

    # ── las fronteras del solape vertical ─────────────────────────
    def test_rozar_el_canto_de_arriba_no_empuja(self) -> None:
        """Se exigen más de 2 px de solape. Con 1 px, el jugador está de hecho
        de pie sobre el canto, y ver el suelo deslizarse bajo los pies es
        justo lo que la condición existe para evitar."""
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        # bottom = top + 1: un píxel de solape, un roce.
        jugador = pygame.Rect(80, 168 + 1 - 30, 20, 30)
        antes = bloque.rect.x

        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())

        assert bloque.rect.x == antes

    def test_rozar_el_canto_de_abajo_no_empuja(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        # top exactamente en bottom - 2: la frontera, que no cuenta.
        jugador = pygame.Rect(80, bloque.rect.bottom - 2, 20, 30)
        antes = bloque.rect.x

        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo(y=260))

        assert bloque.rect.x == antes

    def test_con_solape_de_sobra_si_empuja(self) -> None:
        """La contraparte de las dos de arriba: si la tolerancia se fuera al
        otro extremo, no se podría empujar nada."""
        sistema, bloque, jugador = TestEmpujar()._montaje()
        antes = bloque.rect.x

        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())

        assert bloque.rect.x > antes

    # ── la caída se integra, no se teletransporta ─────────────────
    def test_un_fotograma_de_caida_son_pocos_pixeles(self) -> None:
        """`int(_vy * dt)` frente a `int(_vy / dt)`.

        A 60 fps, dividir en vez de multiplicar convierte 11 px/s en 700
        píxeles de caída **en un solo fotograma**: el bloque desaparece de la
        pantalla entre dos dibujados. Como `caer` avanza de píxel en píxel
        hasta chocar, el desplome no atraviesa el suelo y ninguna de las
        pruebas de «no atraviesa» se enteraba.
        """
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 50, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        antes = bloque.rect.y

        sistema.caer(1 / 60, [])

        caido = bloque.rect.y - antes
        assert caido <= 2, (
            f"cayó {caido} px en un fotograma; a 700 px/s² el primer "
            f"fotograma no llega ni a un píxel"
        )

    def test_la_caida_acelera_en_vez_de_ir_a_velocidad_fija(self) -> None:
        """Si `_vy` no creciera, el bloque caería como una piedra de papel."""
        bloque = BloqueEmpujable(rect=pygame.Rect(50, 0, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])

        for _ in range(10):
            sistema.caer(1 / 60, [])
        primer_tramo = bloque.rect.y
        for _ in range(10):
            sistema.caer(1 / 60, [])
        segundo_tramo = bloque.rect.y - primer_tramo

        assert segundo_tramo > primer_tramo, (
            f"cayó {primer_tramo} px en los primeros 10 fotogramas y "
            f"{segundo_tramo} en los siguientes: no está acelerando"
        )

    # ── el estado de un destructible ya roto ──────────────────────
    def test_golpear_un_bloque_ya_roto_devuelve_false(self) -> None:
        """`sistema.golpear` cuenta roturas y devuelve 0 en los dos casos, así
        que la prueba que ya existía no distinguía `return False` de
        `return True` aquí dentro. El método sí lo distingue, y de él depende
        que el evento de rotura no se emita dos veces."""
        bloque = BloqueDestructible(rect=pygame.Rect(0, 0, 16, 16), golpes=1)

        assert bloque.golpear() is True
        assert bloque.golpear() is False
        assert bloque.golpear() is False

    def test_el_repr_de_un_empujable_no_arrastra_su_copia_inicial(self) -> None:
        """`repr=False` en el campo `inicial`. Un dataclass que vuelca dos
        rects en cada repr duplica el ruido de todo mensaje de fallo de pytest
        que lo mencione, y `inicial` no aporta nada para identificarlo."""
        bloque = BloqueEmpujable(rect=pygame.Rect(10, 20, 32, 32))

        assert "inicial" not in repr(bloque)


class TestLosSolidos:
    def test_los_dos_tipos_estorban_el_paso(self) -> None:
        sistema = SistemaDeBloques(
            empujables=[BloqueEmpujable(rect=pygame.Rect(0, 0, 16, 16))],
            destructibles=[BloqueDestructible(rect=pygame.Rect(32, 0, 16, 16))],
        )
        assert len(sistema.rects_solidos()) == 2

    def test_un_bloque_roto_deja_de_estorbar(self) -> None:
        roto = BloqueDestructible(rect=pygame.Rect(32, 0, 16, 16))
        sistema = SistemaDeBloques(destructibles=[roto])
        roto.golpear()
        assert sistema.rects_solidos() == []


class TestReiniciarAlMorir:
    def test_el_empujable_vuelve_a_su_sitio(self) -> None:
        bloque = BloqueEmpujable(rect=pygame.Rect(100, 168, 32, 32))
        sistema = SistemaDeBloques(empujables=[bloque])
        jugador = pygame.Rect(80, 170, 20, 30)
        for _ in range(60):
            sistema.empujar(jugador, 1, 1 / 60, _suelo())
        sistema.reiniciar()
        assert bloque.rect.topleft == (100, 168)

    def test_el_destructible_vuelve_entero(self) -> None:
        bloque = BloqueDestructible(rect=pygame.Rect(100, 100, 16, 16), golpes=2)
        sistema = SistemaDeBloques(destructibles=[bloque])
        caja = pygame.Rect(96, 96, 24, 24)
        sistema.golpear(caja)
        sistema.golpear(caja)
        sistema.reiniciar()
        assert not bloque.roto
        assert sistema.golpear(caja) == 0, "conservó los golpes de la vida anterior"


class TestLoQueLlegaDesdeTiled:
    def _cargar(self, tipo: str, props: dict, ancho: int = 32, alto: int = 32):
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("Obj", (), {"x": 64, "y": 96, "width": ancho, "height": alto})()
        StageLoader._handle_bloque(stage, obj, props,
                                   empujable=(tipo == "PushBlock"))
        return stage

    def test_el_empujable_llega_con_su_velocidad(self) -> None:
        stage = self._cargar("PushBlock", {"velocidad": 80})
        assert stage.empujables and stage.empujables[0].velocidad == 80

    def test_el_destructible_llega_con_sus_golpes_y_su_evento(self) -> None:
        stage = self._cargar("BreakableBlock",
                             {"golpes": 3, "evento_al_romper": "PASO"})
        bloque = stage.destructibles[0]
        assert bloque.golpes == 3
        assert bloque.evento_al_romper == "PASO"

    def test_un_bloque_sin_tamano_se_descarta(self) -> None:
        """0×0 sería un sólido invisible de área nula: no estorba, no se ve, y
        el estudiante creería haberlo puesto."""
        stage = self._cargar("PushBlock", {}, ancho=0, alto=0)
        assert stage.empujables == []

    def test_cero_golpes_se_trata_como_uno(self) -> None:
        """Dato hostil: `golpes = 0` sería un bloque imposible de romper por
        contar mal, no por diseño."""
        stage = self._cargar("BreakableBlock", {"golpes": 0})
        assert stage.destructibles[0].golpes >= 1

    def test_una_velocidad_de_basura_no_rompe_la_carga(self) -> None:
        stage = self._cargar("PushBlock", {"velocidad": "rápido"})
        assert stage.empujables[0].velocidad > 0

    @pytest.mark.parametrize("tipo", ["PushBlock", "BreakableBlock"])
    def test_los_dos_tipos_los_conoce_el_validador(self, tipo) -> None:
        """Si no están en la lista, el validador le dice al estudiante que su
        objeto es de un tipo desconocido — y el objeto funciona."""
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert tipo in known_object_types(())


class TestLleganAlJuegoDeVerdad:
    """La comprobación que este proyecto ha necesitado nueve veces este mes.

    Que el sistema funcione aislado no significa que la escena lo construya,
    lo actualice y lo dibuje. Aquí se arranca el laboratorio de mecánicas
    entero y se mira lo que hay dentro.
    """

    def _escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage_mecanicas.stage_mecanicas import StageMecanicas

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(),
            audio_manager=AudioManager(),
            scene_manager=None,
            event_bus=EventBus(),
            clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = StageMecanicas(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        return escena

    def test_el_laboratorio_tiene_los_dos_tipos(self) -> None:
        escena = self._escena()
        try:
            assert escena._stage_data.empujables, (
                "ningún mapa usa PushBlock: la mecánica existe y nadie la verá"
            )
            assert escena._stage_data.destructibles
        finally:
            escena.on_exit()

    def test_la_escena_construye_su_sistema(self) -> None:
        escena = self._escena()
        try:
            assert escena._bloques is not None
            assert escena._bloques.rects_solidos(), (
                "los bloques del mapa no estorban el paso: son decoración"
            )
        finally:
            escena.on_exit()

    def test_correr_y_dibujar_no_lanza(self) -> None:
        escena = self._escena()
        pantalla = pygame.display.get_surface()
        try:
            for _ in range(10):
                escena.update(1 / 60)
                escena.draw(pantalla)
        finally:
            escena.on_exit()

    def test_empujar_y_caer_comparten_la_misma_lista_de_solidos(self) -> None:
        """AUD-349 — la lista que pasa la escena se componía DOS veces por
        fotograma: `empujar` recibía `stage.collision_rects + cerradas` y
        `caer` lo recomponía. Con miles de rectángulos por mapa (stage 4-1)
        son dos copias O(n) por frame de pura churn.

        La prueba vigila por identidad, que es lo que detecta la doble
        composición: `empujar` y `caer` deben recibir el MISMO objeto, no dos
        copias iguales.
        """
        escena = self._escena()
        try:
            bloques = escena._bloques
            assert bloques is not None
            if escena._player is not None:
                escena._player.is_grounded = True

            marcos: dict[int, dict[str, list]] = {}
            marco_actual = [0]
            original_empujar = bloques.empujar
            original_caer = bloques.caer

            def _espia(nombre, original):
                def espia(*args):
                    marcos.setdefault(
                        marco_actual[0], {})[nombre] = args[-1]
                    return original(*args)
                return espia

            bloques.empujar = _espia("empujar", original_empujar)  # type: ignore[method-assign]
            bloques.caer = _espia("caer", original_caer)  # type: ignore[method-assign]

            for _ in range(10):
                marco_actual[0] += 1
                escena.update(1 / 60)

            con_ambos = [m for m in marcos.values()
                         if "empujar" in m and "caer" in m]
            assert con_ambos, (
                "ningún fotograma empujó y dejó caer bloques a la vez: la "
                "prueba no está tocando el bloque empujable del laboratorio"
            )
            assert con_ambos[0]["empujar"] is con_ambos[0]["caer"], (
                "empujar y caer recibieron listas DISTINTAS: la escena "
                "compone `stage.collision_rects + cerradas` una vez por "
                "método, dos copias O(n) por fotograma"
            )
        finally:
            escena.on_exit()
