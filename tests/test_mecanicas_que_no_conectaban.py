"""
Tres mecánicas que estaban a medio construir y no conectaban.

AUD-131 — resortes
===================
No existían. Es la mecánica más barata del catálogo pendiente —una hora— y
abre el vocabulario vertical del nivel: Sonic, Hollow Knight y Ori la usan
para lo mismo, dar altura sin dar una habilidad nueva al jugador.

AUD-132 — interruptores que no abrían nada
===========================================
`Disparador` **emitía su evento al bus y nadie escuchaba**. Un estudiante podía
poner un `EventTrigger` en Tiled, verlo aparecer en el registro y no conseguir
que abriera una puerta sin escribir Python. El circuito estaba cortado en el
último tramo.

Es la misma familia que el sistema de diálogo (AUD-127): una pieza correcta,
alcanzable, y sin la mitad que la hace servir para algo. Aquí faltaba el
**receptor**, y el receptor natural es la cerradura.

De regalo, la puerta cronometrada: `Cerradura` ya existía y sólo le faltaba un
temporizador. Un interruptor sin cuenta atrás abre una puerta; con cuenta
atrás plantea una carrera, que es el 90 % de lo que se hace con un interruptor.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import Resorte, Transform, Velocidad, World
from src.framework.ecs.systems import sistema_resortes
from src.framework.stage.interactable_system import InteractableSystem
from src.framework.stage.interactables import Cerradura, Disparador

DT = 1.0 / 60.0


def _cuerpo(mundo: World, x: int, y: int, vy: float) -> int:
    rect = pygame.Rect(x, y, 20, 32)
    return mundo.crear(
        Transform(posicion=pygame.Vector2(rect.topleft), rect=rect),
        Velocidad(pygame.Vector2(0.0, vy)),
    )


class TestElResorte:
    def test_rebota_a_quien_cae_encima(self) -> None:
        m = World()
        muelle = Resorte(rect=pygame.Rect(0, 100, 32, 8), impulso=-500.0)
        m.crear(muelle)
        e = _cuerpo(m, 5, 80, vy=200.0)

        sistema_resortes(m, DT)
        assert m.obtener(e, Velocidad).v.y == pytest.approx(-500.0)

    def test_no_rebota_a_quien_sube(self) -> None:
        """Tocarlo de lado o desde abajo no hace nada.

        Sin esta comprobación, pasar rozando el resorte desde una cornisa te
        lanza sin haberlo pisado, y el jugador no entiende de dónde vino.
        """
        m = World()
        m.crear(Resorte(rect=pygame.Rect(0, 100, 32, 8)))
        e = _cuerpo(m, 5, 80, vy=-120.0)

        sistema_resortes(m, DT)
        assert m.obtener(e, Velocidad).v.y == pytest.approx(-120.0)

    def test_no_rebota_a_quien_no_lo_toca(self) -> None:
        m = World()
        m.crear(Resorte(rect=pygame.Rect(400, 100, 32, 8)))
        e = _cuerpo(m, 5, 80, vy=200.0)

        sistema_resortes(m, DT)
        assert m.obtener(e, Velocidad).v.y == pytest.approx(200.0)

    def test_no_se_dispara_dos_veces_seguidas(self) -> None:
        """El rearme evita el doble rebote.

        El jugador sigue solapando el rectángulo el fotograma siguiente al
        rebote. Sin rearme, el segundo fotograma vuelve a imponer el impulso
        —esta vez sobre una velocidad que ya sube— y el rebote se dobla de
        forma impredecible.
        """
        m = World()
        muelle = Resorte(rect=pygame.Rect(0, 100, 32, 8),
                         impulso=-500.0, rearme=0.5)
        m.crear(muelle)
        e = _cuerpo(m, 5, 80, vy=200.0)

        sistema_resortes(m, DT)
        m.obtener(e, Velocidad).v.y = 200.0          # vuelve a caer al instante
        sistema_resortes(m, DT)
        assert m.obtener(e, Velocidad).v.y == pytest.approx(200.0), (
            "el resorte se disparó dos veces sin haberse rearmado"
        )

    def test_se_rearma_con_el_tiempo(self) -> None:
        """Se comprueba si **llegó a dispararse**, no cómo acaba.

        La primera versión miraba la velocidad al final del bucle y fallaba:
        el resorte se rearma a mitad de camino, dispara una vez, y vuelve a
        quedarse esperando. El último fotograma le pone 200 otra vez y la
        prueba veía 200.

        Es el mismo error que AUD-116, donde una patrulla parecía inmóvil por
        muestrear justo al final de su período. Medir el estado final de un
        proceso periódico mide la fase, no el proceso.
        """
        m = World()
        muelle = Resorte(rect=pygame.Rect(0, 100, 32, 8),
                         impulso=-500.0, rearme=0.2)
        m.crear(muelle)
        e = _cuerpo(m, 5, 80, vy=200.0)

        sistema_resortes(m, DT)
        rebotes = 0
        for _ in range(20):                          # 0,33 s
            m.obtener(e, Velocidad).v.y = 200.0
            sistema_resortes(m, DT)
            if m.obtener(e, Velocidad).v.y < 0.0:
                rebotes += 1
        assert rebotes == 1, (
            f"con 0,2 s de rearme y 0,33 s de ventana debería rearmarse una "
            f"sola vez, y se disparó {rebotes}"
        )

    def test_la_altura_no_depende_de_la_caida(self) -> None:
        """`impulso` se **impone**, no se suma.

        Si se sumara, caer desde más alto rebotaría más alto y la altura del
        rebote dejaría de ser una constante del nivel: el diseñador ya no
        podría colocar una plataforma sabiendo si se alcanza.
        """
        alturas = []
        for caida in (100.0, 400.0):
            m = World()
            m.crear(Resorte(rect=pygame.Rect(0, 100, 32, 8), impulso=-500.0))
            e = _cuerpo(m, 5, 80, vy=caida)
            sistema_resortes(m, DT)
            alturas.append(m.obtener(e, Velocidad).v.y)
        assert alturas[0] == pytest.approx(alturas[1])


class TestElInterruptorAbreLaPuerta:
    """AUD-132 — el receptor que faltaba."""

    @staticmethod
    def _sistema(**extra) -> InteractableSystem:
        puerta = Cerradura(
            rect=pygame.Rect(200, 0, 16, 48), key_id="",
            abre_con_evento="ABRIR_COMPUERTA", **extra,
        )
        interruptor = Disparador(
            rect=pygame.Rect(0, 0, 32, 32), evento="ABRIR_COMPUERTA",
        )
        return InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[],
            disparadores=[interruptor],
        )

    def test_pisar_el_interruptor_abre_la_puerta(self) -> None:
        s = self._sistema()
        assert not s.cerraduras[0].abierta
        s.update(DT, pygame.Rect(0, 0, 20, 32))
        assert s.cerraduras[0].abierta, (
            "el interruptor emitió su evento al bus y la puerta no se enteró: "
            "es el circuito que llevaba cortado desde F4.1"
        )

    def test_la_puerta_deja_de_bloquear_al_abrirse(self) -> None:
        """Abrirse tiene que significar algo para la colisión."""
        s = self._sistema()
        assert s.rects_solidos()
        s.update(DT, pygame.Rect(0, 0, 20, 32))
        assert not s.rects_solidos()

    def test_un_evento_que_nadie_escucha_no_rompe_nada(self) -> None:
        s = InteractableSystem(
            recogibles=[], cerraduras=[], cofres=[],
            disparadores=[Disparador(rect=pygame.Rect(0, 0, 32, 32),
                                     evento="NADIE_ESCUCHA")],
        )
        s.update(DT, pygame.Rect(0, 0, 20, 32))

    def test_una_puerta_sin_abre_con_no_se_abre_sola(self) -> None:
        """La regresión que importa: no abrir las puertas de los quince mapas."""
        puerta = Cerradura(rect=pygame.Rect(200, 0, 16, 48), key_id="llave")
        s = InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[],
            disparadores=[Disparador(rect=pygame.Rect(0, 0, 32, 32),
                                     evento="CUALQUIERA")],
        )
        s.update(DT, pygame.Rect(0, 0, 20, 32))
        assert not puerta.abierta


class TestLaPuertaCronometrada:
    def test_se_cierra_sola_al_agotarse(self) -> None:
        puerta = Cerradura(rect=pygame.Rect(200, 0, 16, 48), key_id="",
                           abre_con_evento="X", cierra_en=0.5)
        s = InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[], disparadores=[])
        s.abrir_por_evento("X")
        assert puerta.abierta

        lejos = pygame.Rect(0, 0, 20, 32)
        for _ in range(40):                          # 0,66 s
            s.update(DT, lejos)
        assert not puerta.abierta

    def test_no_se_cierra_con_el_jugador_dentro(self) -> None:
        """Cerrar encima del jugador lo aplasta contra la geometría.

        El temporizador se prorroga hasta que salga. No hace falta que el
        jugador lo entienda: hace falta que no le pase.
        """
        puerta = Cerradura(rect=pygame.Rect(200, 0, 16, 48), key_id="",
                           abre_con_evento="X", cierra_en=0.2)
        s = InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[], disparadores=[])
        s.abrir_por_evento("X")

        dentro = pygame.Rect(200, 0, 16, 32)
        for _ in range(60):
            s.update(DT, dentro)
        assert puerta.abierta, "la puerta se cerró sobre el jugador"

    def test_sin_temporizador_se_queda_abierta(self) -> None:
        puerta = Cerradura(rect=pygame.Rect(200, 0, 16, 48), key_id="",
                           abre_con_evento="X")
        s = InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[], disparadores=[])
        s.abrir_por_evento("X")
        for _ in range(300):
            s.update(DT, pygame.Rect(0, 0, 20, 32))
        assert puerta.abierta

    def test_abrir_con_llave_no_arranca_el_temporizador(self) -> None:
        """Una puerta abierta con llave se queda abierta.

        El temporizador es la mecánica del interruptor. Aplicarlo también a
        la llave convertiría cada puerta cerrada del juego en una carrera sin
        que el diseñador lo hubiera pedido.
        """
        puerta = Cerradura(rect=pygame.Rect(0, 0, 16, 48), key_id="llave",
                           cierra_en=0.2)
        s = InteractableSystem(
            recogibles=[], cerraduras=[puerta], cofres=[], disparadores=[])
        s.llavero.coger("llave")
        s.update(DT, pygame.Rect(0, 0, 20, 32), usar=True)
        assert puerta.abierta

        for _ in range(60):
            s.update(DT, pygame.Rect(400, 0, 20, 32))
        assert puerta.abierta


class TestElTipoNuevoEstaDeclarado:
    """Los tres registros que hay que tocar a la vez, o el tipo no existe."""

    def test_spring_es_un_tipo_conocido(self) -> None:
        from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

        assert "Spring" in BUILTIN_OBJECT_TYPES

    def test_spring_se_construye_como_componente(self) -> None:
        from src.framework.stage.stage_loader import _TIPOS_DE_COMPONENTE

        assert "Spring" in _TIPOS_DE_COMPONENTE

    def test_el_sistema_esta_en_el_planificador(self) -> None:
        """Un componente sin sistema es el noveno huérfano del mes."""
        import inspect

        from src.framework.scenes.stage_scene import StageScene

        fuente = inspect.getsource(StageScene._construir_planificador)
        assert "sistema_resortes" in fuente


class TestElPogo:
    """AUD-134 — `AERIAL_SLAM` existía y acertar no significaba nada.

    El estado ya tenía caja de golpe y ya empujaba al jugador hacia abajo. Lo
    que faltaba era el rebote al conectar, y sin él el ataque aéreo hacia abajo
    es un ataque normal con otra animación: se cae igual tanto si acierta como
    si no.

    Con el rebote, encadenar golpes sobre enemigos mantiene al jugador en el
    aire y una fila de enemigos se convierte en un camino. Es la mecánica
    entera de Ducktales, Shovel Knight y Hollow Knight.
    """

    @staticmethod
    def _en_slam():
        import pygame as _pg

        from src.framework.entities.player import Player
        from src.framework.entities.states import AerialSlamState

        _pg.init()
        if _pg.display.get_surface() is None:
            _pg.display.set_mode((320, 240))
        p = Player(_pg.Vector2(100.0, 100.0))
        p.is_grounded = False
        estado = AerialSlamState()
        p._change_state_instance(estado)
        return p, estado

    def test_sin_acertar_se_sigue_cayendo(self) -> None:
        """La prueba de control: el pogo no debe activarse solo."""
        p, estado = self._en_slam()
        estado.update(p, DT, None)
        assert p.velocity.y > 0.0

    def test_acertar_devuelve_impulso_hacia_arriba(self) -> None:
        from src.framework.entities.states.airborne import POGO_IMPULSO

        p, estado = self._en_slam()
        p._hitbox_consumed = True                    # el golpe conectó
        estado.update(p, DT, None)
        assert p.velocity.y == pytest.approx(POGO_IMPULSO)
        assert p.velocity.y < 0.0

    def test_el_rebote_es_menor_que_el_salto(self) -> None:
        """El pogo no debe ser mejor que saltar, o nadie salta.

        Basta con que dé tiempo a alinearse con el siguiente enemigo.
        """
        from src.engine.core import settings
        from src.framework.entities.states.airborne import POGO_IMPULSO

        assert abs(POGO_IMPULSO) < abs(settings.PLAYER_JUMP_FORCE)

    def test_rebotar_recupera_el_dash_aereo(self) -> None:
        """Sin esto, el segundo enemigo de la fila queda fuera de alcance."""
        p, estado = self._en_slam()
        p._air_dash_count = 1
        p._hitbox_consumed = True
        estado.update(p, DT, None)
        assert p._air_dash_count == 0

    def test_solo_rebota_una_vez_por_golpe(self) -> None:
        """`_has_hit` evita que el mismo impacto rebote en cada fotograma."""
        p, estado = self._en_slam()
        p._hitbox_consumed = True
        estado.update(p, DT, None)
        p.velocity.y = 300.0
        estado.update(p, DT, None)
        assert p.velocity.y == pytest.approx(300.0)
