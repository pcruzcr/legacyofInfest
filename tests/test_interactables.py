"""
Recoger objetos, abrir puertas y jaulas, cofres y disparadores de evento.

F4.1
====
Petición literal de los estudiantes tras jugar la fase 1: *«si se podía
agarrar objetos y llevar[los], abrir jaulas o puertas, además de abrir cofres
misteriosos o activar eventos»*.

El motor tenía un `Inventory` con seis mejoras permanentes y **nada recogible
en el mapa**: no había forma de poner un objeto en Tiled y que el jugador lo
cogiera.

Qué se comprueba aquí
---------------------
La mecánica completa de llave y puerta, que es el patrón que pedían, y los
casos que se equivocan al diseñar un nivel: una puerta sin llave alcanzable,
un cofre abierto dos veces, un disparador que se repite.

Todo sin abrir una ventana: la lógica vive en `interactable_system`, separada
del dibujado, precisamente para poder comprobarla así.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.interactable_system import (
    EVENTO_ABIERTA,
    EVENTO_BLOQUEADA,
    EVENTO_COFRE,
    EVENTO_RECOGIDO,
    InteractableSystem,
)
from src.framework.stage.interactables import (
    ALCANCE_DE_USO,
    Cerradura,
    Cofre,
    Disparador,
    Llavero,
    Recogible,
    alcanza,
)

DT = 1.0 / 60.0


class _BusEspia:
    """Registra lo que se emite. Más fiable que un mock para lo que interesa."""

    def __init__(self) -> None:
        self.emitidos: list[tuple[str, dict]] = []

    def emit(self, evento: str, **datos: object) -> None:
        self.emitidos.append((evento, dict(datos)))

    def nombres(self) -> list[str]:
        return [n for n, _ in self.emitidos]


def _jugador(x: int = 0, y: int = 0) -> pygame.Rect:
    return pygame.Rect(x, y, 20, 32)


class TestRecogerObjetos:
    def test_uno_automatico_se_coge_al_tocarlo(self):
        llave = Recogible(rect=pygame.Rect(10, 10, 16, 16), item_id="llave_roja")
        bus = _BusEspia()
        s = InteractableSystem(recogibles=[llave], bus=bus)

        s.update(DT, _jugador(500, 500))
        assert not llave.recogido, "se cogió sin que el jugador estuviera cerca"

        s.update(DT, _jugador(10, 10))
        assert llave.recogido
        assert s.llavero.tiene("llave_roja")
        assert EVENTO_RECOGIDO in bus.nombres()

    def test_uno_manual_necesita_el_boton(self):
        """Distinguirlos importa: una moneda se coge sola, una palanca no."""
        objeto = Recogible(
            rect=pygame.Rect(10, 10, 16, 16), item_id="palanca", automatico=False,
        )
        s = InteractableSystem(recogibles=[objeto])

        s.update(DT, _jugador(10, 10), usar=False)
        assert not objeto.recogido

        s.update(DT, _jugador(10, 10), usar=True)
        assert objeto.recogido

    def test_no_se_coge_dos_veces(self):
        objeto = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="moneda")
        bus = _BusEspia()
        s = InteractableSystem(recogibles=[objeto], bus=bus)

        for _ in range(5):
            s.update(DT, _jugador(0, 0))
        assert bus.nombres().count(EVENTO_RECOGIDO) == 1

    def test_avisa_al_jugador(self):
        objeto = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="llave_azul")
        s = InteractableSystem(recogibles=[objeto])
        s.update(DT, _jugador(0, 0))
        assert "llave_azul" in s.mensaje

    def test_el_mensaje_se_apaga_solo(self):
        objeto = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="x")
        s = InteractableSystem(recogibles=[objeto])
        s.update(DT, _jugador(0, 0))
        assert s.mensaje
        for _ in range(200):
            s.update(DT, _jugador(900, 900))
        assert not s.mensaje, "el aviso se quedó fijo en pantalla"


class TestPuertasYJaulas:
    def test_sin_llave_no_se_abre_y_se_dice_por_que(self):
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="llave_roja")
        bus = _BusEspia()
        s = InteractableSystem(cerraduras=[puerta], bus=bus)

        s.update(DT, _jugador(40, 0), usar=True)
        assert not puerta.abierta
        assert "llave_roja" in s.mensaje
        assert EVENTO_BLOQUEADA in bus.nombres()

    def test_con_la_llave_se_abre(self):
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="llave_roja")
        bus = _BusEspia()
        s = InteractableSystem(cerraduras=[puerta], bus=bus)
        s.llavero.coger("llave_roja")

        s.update(DT, _jugador(40, 0), usar=True)
        assert puerta.abierta
        assert EVENTO_ABIERTA in bus.nombres()

    def test_una_puerta_cerrada_bloquea_el_paso_y_abierta_no(self):
        """Es toda la mecánica: el rectángulo sólido aparece y desaparece."""
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="k")
        s = InteractableSystem(cerraduras=[puerta])

        assert s.rects_solidos() == [puerta.rect]
        s.llavero.coger("k")
        s.update(DT, _jugador(40, 0), usar=True)
        assert s.rects_solidos() == []

    def test_sin_key_id_se_abre_sin_llave(self):
        """Una puerta sin llave es un interruptor, y es un uso legítimo."""
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="")
        s = InteractableSystem(cerraduras=[puerta])
        s.update(DT, _jugador(40, 0), usar=True)
        assert puerta.abierta

    def test_la_llave_no_se_gasta_por_defecto(self):
        """Gastarla obliga a contar, y el fallo no se ve hasta jugar el nivel."""
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="k")
        s = InteractableSystem(cerraduras=[puerta])
        s.llavero.coger("k")
        s.update(DT, _jugador(40, 0), usar=True)
        assert s.llavero.tiene("k")

    def test_si_se_pide_consumir_la_llave_desaparece(self):
        puerta = Cerradura(rect=pygame.Rect(50, 0, 16, 48), key_id="k", consume_llave=True)
        s = InteractableSystem(cerraduras=[puerta])
        s.llavero.coger("k")
        s.update(DT, _jugador(40, 0), usar=True)
        assert not s.llavero.tiene("k")

    def test_la_jaula_se_distingue_en_el_mensaje(self):
        jaula = Cerradura(rect=pygame.Rect(50, 0, 32, 32), key_id="k", clase="jaula")
        s = InteractableSystem(cerraduras=[jaula])
        s.update(DT, _jugador(40, 0), usar=True)
        assert "jaula" in s.mensaje.lower()

    def test_emite_el_evento_que_pidio_el_disenador(self):
        puerta = Cerradura(
            rect=pygame.Rect(50, 0, 16, 48), key_id="", evento_al_abrir="SUBE_EL_AGUA",
        )
        bus = _BusEspia()
        s = InteractableSystem(cerraduras=[puerta], bus=bus)
        s.update(DT, _jugador(40, 0), usar=True)
        assert "SUBE_EL_AGUA" in bus.nombres()


class TestCofres:
    def test_se_abre_y_entrega_su_contenido(self):
        cofre = Cofre(rect=pygame.Rect(30, 0, 24, 20), contenido="llave_dorada")
        bus = _BusEspia()
        s = InteractableSystem(cofres=[cofre], bus=bus)

        s.update(DT, _jugador(20, 0), usar=True)
        assert cofre.abierto
        assert s.llavero.tiene("llave_dorada")
        assert EVENTO_COFRE in bus.nombres()

    def test_solo_una_vez(self):
        cofre = Cofre(rect=pygame.Rect(30, 0, 24, 20), contenido="x")
        bus = _BusEspia()
        s = InteractableSystem(cofres=[cofre], bus=bus)
        for _ in range(4):
            s.update(DT, _jugador(20, 0), usar=True)
        assert bus.nombres().count(EVENTO_COFRE) == 1

    def test_un_cofre_cerrado_con_llave_la_pide(self):
        cofre = Cofre(rect=pygame.Rect(30, 0, 24, 20), contenido="premio", key_id="maestra")
        s = InteractableSystem(cofres=[cofre])
        s.update(DT, _jugador(20, 0), usar=True)
        assert not cofre.abierto
        s.llavero.coger("maestra")
        s.update(DT, _jugador(20, 0), usar=True)
        assert cofre.abierto

    def test_un_cofre_vacio_lo_dice(self):
        cofre = Cofre(rect=pygame.Rect(30, 0, 24, 20))
        s = InteractableSystem(cofres=[cofre])
        s.update(DT, _jugador(20, 0), usar=True)
        assert "vacío" in s.mensaje.lower()


class TestDisparadoresDeEvento:
    def test_se_dispara_al_entrar(self):
        d = Disparador(rect=pygame.Rect(0, 0, 40, 40), evento="CAE_EL_PUENTE")
        bus = _BusEspia()
        s = InteractableSystem(disparadores=[d], bus=bus)

        s.update(DT, _jugador(10, 10))
        assert d.disparado
        assert "CAE_EL_PUENTE" in bus.nombres()

    def test_una_vez_significa_una_vez(self):
        d = Disparador(rect=pygame.Rect(0, 0, 40, 40), evento="E", una_vez=True)
        bus = _BusEspia()
        s = InteractableSystem(disparadores=[d], bus=bus)
        for _ in range(6):
            s.update(DT, _jugador(10, 10))
        assert bus.nombres().count("E") == 1

    def test_repetible_se_dispara_cada_vez(self):
        d = Disparador(rect=pygame.Rect(0, 0, 40, 40), evento="E", una_vez=False)
        bus = _BusEspia()
        s = InteractableSystem(disparadores=[d], bus=bus)
        for _ in range(3):
            s.update(DT, _jugador(10, 10))
        assert bus.nombres().count("E") == 3

    def test_uno_con_llave_no_se_dispara_sin_ella(self):
        d = Disparador(rect=pygame.Rect(0, 0, 40, 40), evento="E", key_id="k")
        bus = _BusEspia()
        s = InteractableSystem(disparadores=[d], bus=bus)

        s.update(DT, _jugador(10, 10))
        assert not d.disparado
        s.llavero.coger("k")
        s.update(DT, _jugador(10, 10))
        assert d.disparado


class TestElBusNoTumbaLaPartida:
    def test_un_suscriptor_que_lanza_no_rompe_el_juego(self):
        """Un escenario de estudiante puede tener un manejador con un fallo.

        Que su error tumbe la partida entera sería desproporcionado. Que
        desaparezca sin rastro, peor: se registra con traza.
        """
        class BusRoto:
            def emit(self, evento, **datos):
                raise RuntimeError("el manejador del estudiante falló")

        objeto = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="x")
        s = InteractableSystem(recogibles=[objeto], bus=BusRoto())
        s.update(DT, _jugador(0, 0))  # no debe lanzar
        assert objeto.recogido, "el fallo del suscriptor impidió recoger el objeto"


class TestElAlcance:
    def test_no_hay_que_estar_encima_exacto(self):
        objetivo = pygame.Rect(100, 0, 16, 16)
        assert alcanza(_jugador(100 - ALCANCE_DE_USO + 4, 0), objetivo)

    def test_pero_tampoco_vale_desde_la_otra_punta(self):
        objetivo = pygame.Rect(100, 0, 16, 16)
        assert not alcanza(_jugador(400, 0), objetivo)


class TestElLlavero:
    def test_una_llave_vacia_siempre_se_tiene(self):
        """`key_id=""` significa «sin llave», no «con una llave sin nombre»."""
        assert Llavero().tiene("")

    def test_duplicar_una_llave_no_hace_nada(self):
        ll = Llavero()
        ll.coger("k")
        ll.coger("k")
        assert ll.llaves == {"k"}


class TestQuedaAlgoPorHacer:
    """Lo consulta el calificador para saber si un nivel tiene puzles."""

    def test_un_escenario_vacio_no_tiene_nada(self):
        assert not InteractableSystem().hay_algo_que_hacer

    def test_con_algo_pendiente_lo_dice(self):
        s = InteractableSystem(
            recogibles=[Recogible(rect=pygame.Rect(0, 0, 8, 8), item_id="k")],
        )
        assert s.hay_algo_que_hacer

    def test_una_vez_resuelto_todo_ya_no(self):
        objeto = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="k")
        puerta = Cerradura(rect=pygame.Rect(20, 0, 16, 48), key_id="k")
        s = InteractableSystem(recogibles=[objeto], cerraduras=[puerta])

        s.update(DT, _jugador(0, 0))
        s.update(DT, _jugador(10, 0), usar=True)
        assert not s.hay_algo_que_hacer


class TestElPuzleCompletoDeLlaveYPuerta:
    """El recorrido que los estudiantes describieron, de principio a fin."""

    def test_coger_la_llave_abre_la_jaula_y_dispara_el_evento(self):
        llave = Recogible(rect=pygame.Rect(0, 0, 16, 16), item_id="llave_jaula")
        jaula = Cerradura(
            rect=pygame.Rect(200, 0, 32, 32), key_id="llave_jaula", clase="jaula",
            evento_al_abrir="LIBERADO_EL_PRISIONERO",
        )
        bus = _BusEspia()
        s = InteractableSystem(recogibles=[llave], cerraduras=[jaula], bus=bus)

        # 1. La jaula bloquea y no se abre sin la llave.
        s.update(DT, _jugador(190, 0), usar=True)
        assert not jaula.abierta
        assert s.rects_solidos() == [jaula.rect]

        # 2. El jugador va a por la llave.
        s.update(DT, _jugador(0, 0))
        assert s.llavero.tiene("llave_jaula")

        # 3. Vuelve y la abre.
        s.update(DT, _jugador(190, 0), usar=True)
        assert jaula.abierta
        assert s.rects_solidos() == []
        assert "LIBERADO_EL_PRISIONERO" in bus.nombres()


class TestElTmxLosCarga:
    """Sin esto, todo lo anterior sería inalcanzable desde Tiled."""

    @pytest.fixture(autouse=True)
    def _pygame(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((64, 64))

    @pytest.mark.parametrize("tipo", [
        "Pickup", "Key", "Door", "LockedDoor", "Cage", "Chest", "EventTrigger",
    ])
    def test_el_validador_conoce_el_tipo(self, tipo):
        from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

        assert tipo in BUILTIN_OBJECT_TYPES, (
            f"'{tipo}' no está en la lista de tipos válidos: el validador "
            f"rechazaría un mapa que lo use"
        )

    def test_stage_data_tiene_las_cuatro_listas(self):
        from src.framework.stage.stage_loader import StageData

        campos = StageData.__dataclass_fields__
        for nombre in ("recogibles", "cerraduras", "cofres", "disparadores"):
            assert nombre in campos, f"StageData no expone '{nombre}'"

    def test_el_cargador_tiene_un_manejador_por_tipo(self):
        from src.framework.stage.stage_loader import StageLoader

        for metodo in (
            "_handle_recogible", "_handle_cerradura",
            "_handle_cofre", "_handle_disparador",
        ):
            assert hasattr(StageLoader, metodo), f"falta {metodo}"

    @pytest.mark.parametrize(("valor", "esperado"), [
        (True, True), (False, False), ("true", True), ("false", False),
        ("1", True), ("0", False), ("sí", True), ("", None), (None, None),
    ])
    def test_los_booleanos_de_tiled_se_entienden(self, valor, esperado):
        """Tiled entrega booleanos como bool, como 'true' o como '1'."""
        from src.framework.stage.stage_loader import StageLoader

        por_defecto = object()
        resultado = StageLoader._bool_de(valor, por_defecto=por_defecto)
        assert resultado is (por_defecto if esperado is None else esperado)
