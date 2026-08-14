"""AUD-297 — suelo inclinado, dentro de la resolución de colisión.

La decisión, y quién la tomó
----------------------------
`docs/87` §11 recomendó hacerlo **aditivo** —un tipo nuevo con su propia
resolución— o no hacerlo, porque tocar la resolución de colisión es tocar el
sistema del que dependen las veintiséis entregas. Se pidió integrado, y así se
hizo, con la calificación de los dieciséis mapas como control.

Lo que hace que sea seguro no es el cuidado: es que **una pendiente es un tipo
de objeto nuevo y ningún mapa entregado tiene ninguno**. La lista llega vacía y
el paso entero se salta.

Lo que se fija aquí
-------------------
1. La geometría: dónde está la superficie, en cada sentido y en los bordes.
2. Que subir funcione, que **bajar** funcione —el caso que se rompe solo si
   nadie lo prueba— y que saltar despegue.
3. Que sin pendientes el jugador se comporte exactamente igual que antes.
4. La pared lateral (AUD-323): la cara empinada y la hipotenusa a media
   altura se frenan, y nadie que esté **pisando** la cuesta —subiendo,
   bajando o en el pie— se ve frenado por su propia esquina.
5. La proyección de velocidad (AUD-324): caer sobre una cuesta desliza
   cuesta abajo en vez de parar en seco.
6. El deslizamiento sostenido (AUD-326): quieto en la cuesta, la gravedad
   desliza al jugador cuesta abajo a velocidad constante y acotada —
   sin aceleración en fuga — y andar, subiendo o bajando, manda.
7. La vista cenital (AUD-328): sin gravedad no hay cuesta que resolver.
   En planta la rampa es terreno pintado: ni pega a la hipotenusa ni frena
   el paso; eso lo decide la capa Collision, como siempre.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.pendientes import (
    MARGEN_DE_PEGADO,
    Pendiente,
    componente_de_deslizamiento,
    resolver,
    resolver_con_ganadora,
    resolver_lateral,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((800, 600))


class TestLaGeometria:
    def test_sube_a_la_derecha(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50), sube_a_la_derecha=True)
        assert p.altura_en(0) == pytest.approx(50)      # pie, abajo
        assert p.altura_en(100) == pytest.approx(0)     # cima, arriba
        assert p.altura_en(50) == pytest.approx(25)

    def test_sube_a_la_izquierda(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50), sube_a_la_derecha=False)
        assert p.altura_en(0) == pytest.approx(0)
        assert p.altura_en(100) == pytest.approx(50)

    def test_fuera_del_rango_no_hay_superficie(self) -> None:
        p = Pendiente(pygame.Rect(0, 0, 100, 50))
        assert p.altura_en(-1) is None
        assert p.altura_en(101) is None

    def test_el_borde_derecho_entra(self) -> None:
        """Dos pendientes seguidas comparten el píxel del borde: excluirlo deja
        un hueco de un píxel por el que el jugador se cuela."""
        p = Pendiente(pygame.Rect(0, 0, 100, 50))
        assert p.altura_en(100) is not None

    def test_una_pendiente_sin_ancho_no_divide_por_cero(self) -> None:
        p = Pendiente(pygame.Rect(10, 0, 0, 50))
        assert p.altura_en(10) == pytest.approx(0)


class TestResolver:
    @staticmethod
    def _cuesta():
        # Sube a la derecha, de y=100 (pie) a y=50 (cima).
        return [Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)]

    def test_los_pies_dentro_de_la_cuesta_suben(self) -> None:
        rect = pygame.Rect(40, 80, 20, 20)   # centro x=50, pies en 100
        assert resolver(rect, 0.0, True, self._cuesta()) == pytest.approx(75.0)

    def test_volando_por_encima_no_pasa_nada(self) -> None:
        rect = pygame.Rect(40, 0, 20, 20)    # pies en 20, muy por encima
        assert resolver(rect, 5.0, False, self._cuesta()) is None

    def test_por_debajo_del_triangulo_no_hay_suelo(self) -> None:
        """El jugador pasa por dentro de la roca, no sobre ella."""
        rect = pygame.Rect(40, 200, 20, 20)
        assert resolver(rect, 5.0, False, self._cuesta()) is None

    def test_subiendo_no_se_pega(self) -> None:
        """Saltar desde una cuesta tiene que despegar, no re-pegar al
        fotograma siguiente."""
        rect = pygame.Rect(40, 80, 20, 20)
        assert resolver(rect, -200.0, True, self._cuesta()) is None

    def test_al_bajar_se_pega_con_margen(self) -> None:
        """Sin esto, bajar una cuesta se hace a saltitos."""
        cuesta = self._cuesta()
        # Pies un poco por encima de la superficie, ya en el suelo.
        rect = pygame.Rect(40, 80 - int(MARGEN_DE_PEGADO / 2), 20, 20)
        assert resolver(rect, 0.0, True, cuesta) is not None

    def test_en_el_aire_el_margen_es_mucho_menor(self) -> None:
        """Volando **por encima** de la cuesta no hay que engancharse a ella.

        Los pies quedan unos píxeles por encima de la superficie: en el suelo
        eso es bajar una cuesta y hay que pegarse; en el aire es sobrevolarla.
        """
        cuesta = self._cuesta()
        superficie = 75.0                      # la cuesta en x=50
        arriba = int(superficie - MARGEN_DE_PEGADO / 2)
        rect = pygame.Rect(40, arriba - 20, 20, 20)
        assert resolver(rect, 5.0, False, cuesta) is None
        # Y en el suelo, la misma posición sí se pega: es bajar la cuesta.
        assert resolver(rect, 0.0, True, cuesta) == pytest.approx(superficie)

    def test_sin_pendientes_no_hay_nada_que_resolver(self) -> None:
        assert resolver(pygame.Rect(0, 0, 20, 20), 0.0, True, []) is None

    def test_con_dos_solapadas_gana_la_mas_alta(self) -> None:
        """Es la que el jugador está pisando de verdad."""
        baja = Pendiente(pygame.Rect(0, 100, 100, 20), sube_a_la_derecha=True)
        alta = Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)
        rect = pygame.Rect(40, 80, 20, 20)
        assert resolver(rect, 0.0, True, [baja, alta]) == pytest.approx(75.0)


class TestResolverConGanadora:
    def test_devuelve_la_pendiente_ganadora(self) -> None:
        """AUD-324: quien proyecta la velocidad al aterrizar necesita saber
        **sobre qué** aterriza, no sólo a qué altura."""
        baja = Pendiente(pygame.Rect(0, 100, 100, 20), sube_a_la_derecha=True)
        alta = Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)
        rect = pygame.Rect(40, 80, 20, 20)
        superficie, ganadora = resolver_con_ganadora(
            rect, 0.0, True, [baja, alta])
        assert superficie == pytest.approx(75.0)
        assert ganadora is alta

    def test_sin_superficie_no_hay_ganadora(self) -> None:
        assert resolver_con_ganadora(
            pygame.Rect(0, 0, 20, 20), 5.0, False, []) == (None, None)


class TestResolverLateral:
    """AUD-323 — las entradas laterales a la rampa.

    El eje X se mueve libre y el eje Y coloca sobre la hipotenusa; eso deja
    dos huecos: la **cara empinada** (el segmento vertical del extremo alto,
    que se atraviesa y luego el eje Y absorbe hacia arriba) y la hipotenusa
    a media altura. Lo que frena aquí no es la roca entera, es la pared que
    queda sin resolver.
    """

    @staticmethod
    def _cuesta():
        # Sube a la derecha, de y=100 (pie) a y=50 (cima).
        return [Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)]

    def test_la_cara_empinada_frena(self) -> None:
        """Atravesar la rampa por el lado alto: la pared vertical la frena."""
        rect = pygame.Rect(96, 54, 20, 20)   # centro x=106, pies en 74
        assert resolver_lateral(rect,self._cuesta()) == pytest.approx(100.0)

    def test_la_cara_empinada_mirror(self) -> None:
        """Sube a la izquierda: la cara está en el otro extremo."""
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=False)]
        rect = pygame.Rect(-15, 54, 20, 20)  # centro x=-5, fuera de la rampa
        assert resolver_lateral(rect,cuesta) == pytest.approx(-20.0)

    def test_el_centro_sobre_la_rampa_no_tiene_pared(self) -> None:
        """Pisando la cuesta, la esquina se hunde unos píxeles en la roca al
        subir y al bajar: frenarla aquí rompería la marcha. Es el precio
        normal de un suelo de un solo punto de apoyo."""
        cuesta = self._cuesta()
        # Bajando: centro x=94, pies en 54 == superficie en 94.
        rect = pygame.Rect(84, 34, 20, 20)
        assert resolver_lateral(rect,cuesta) is None
        # Subiendo: centro x=88, pies en 56 == superficie en 88.
        rect2 = pygame.Rect(78, 36, 20, 20)
        assert resolver_lateral(rect2,cuesta) is None

    def test_sobrevolando_la_cima_no_hay_pared(self) -> None:
        rect = pygame.Rect(96, 20, 20, 20)   # pies en 40, sobre la cima
        assert resolver_lateral(rect,self._cuesta()) is None

    def test_bajo_el_pie_no_hay_pared(self) -> None:
        rect = pygame.Rect(96, 84, 20, 20)   # pies en 104, bajo el triángulo
        assert resolver_lateral(rect,self._cuesta()) is None

    def test_el_pie_de_la_cuesta_no_es_pared(self) -> None:
        """Subir desde el suelo llano del pie lo resuelve el eje Y con el
        margen de pegado: frenar aquí dejaría al jugador congelado al pie."""
        rect = pygame.Rect(-8, 80, 20, 20)   # pies en 100, nivel del pie
        assert resolver_lateral(rect,self._cuesta()) is None

    def test_sin_pendientes_no_hay_pared(self) -> None:
        assert resolver_lateral(pygame.Rect(96, 54, 20, 20), []) is None

    def test_pegado_a_la_cara_no_hay_nada_que_empujar(self) -> None:
        """Flush contra la pared: sin incrustación no hay corrección."""
        rect = pygame.Rect(100, 54, 20, 20)  # centro x=110, pies en 74
        assert resolver_lateral(rect, self._cuesta()) is None

    def test_la_hipotenusa_a_media_altura(self) -> None:
        """Una rampa más estrecha que el jugador: la roca a la altura de los
        pies tiene huella, y entrar por su diagonal se frena en el cruce."""
        cuesta = [Pendiente(pygame.Rect(0, 50, 10, 100), sube_a_la_derecha=True)]
        rect = pygame.Rect(-12, 55, 20, 20)  # centro x=-2, pies en 75
        assert resolver_lateral(rect, cuesta) == pytest.approx(-12.5)


class TestComponenteDeDeslizamiento:
    """AUD-324 — la proyección de la caída sobre la hipotenusa."""

    @staticmethod
    def _cuarenta_y_cinco():
        return Pendiente(pygame.Rect(0, 50, 100, 100), sube_a_la_derecha=True)

    def test_45_grados_la_mitad_de_la_caida(self) -> None:
        """Sin(45)·cos(45) = 0,5: caer a 400 px/s empuja a 200 px/s cuesta
        abajo. Es la misma cuenta de la Unidad II, vista en el suelo."""
        assert componente_de_deslizamiento(
            self._cuarenta_y_cinco(), 400.0) == pytest.approx(-200.0)

    def test_mirror_desliza_hacia_el_otro_lado(self) -> None:
        p = Pendiente(pygame.Rect(0, 50, 100, 100), sube_a_la_derecha=False)
        assert componente_de_deslizamiento(p, 400.0) == pytest.approx(200.0)

    def test_no_cae_no_desliza(self) -> None:
        p = self._cuarenta_y_cinco()
        assert componente_de_deslizamiento(p, 0.0) == 0.0
        assert componente_de_deslizamiento(p, -5.0) == 0.0


class TestElJugadorEnLaCuesta:
    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_subir_una_cuesta_lo_levanta(self) -> None:
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 200, 100), sube_a_la_derecha=True)]
        # Primero se le deja caer sobre la cuesta: comparar el primer fotograma
        # con el último mediría la caída, no la subida.
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded, "no llegó a posarse en la cuesta"
        posado = jugador.rect.bottom

        # Se avanza la posición a mano en vez de dar velocidad: sin
        # `InputManager`, la máquina de estados pone `velocity.x` a cero cada
        # fotograma y el jugador no se movería. Lo que se mide es la cuesta, no
        # la entrada.
        for _ in range(20):
            jugador.position.x += 3.0
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.rect.bottom < posado, "la cuesta no levantó al jugador"
        assert jugador.is_grounded

    def test_bajar_no_va_a_saltitos(self) -> None:
        """El caso que se rompe solo si nadie lo prueba."""
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 200, 100), sube_a_la_derecha=False)]
        jugador.position.update(20.0, 40.0)
        # Se le deja posarse antes de contar: la caída inicial no es traqueteo.
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded

        despegues = 0
        for _ in range(30):
            jugador.position.x += 3.0
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
            if not jugador.is_grounded:
                despegues += 1
        assert despegues == 0, (
            f"el jugador despegó {despegues} veces bajando: eso es el "
            "traqueteo que `MARGEN_DE_PEGADO` existe para evitar"
        )

    def test_sin_pendientes_todo_sigue_igual(self) -> None:
        """La condición para no romper las veintiséis entregas."""
        jugador = self._jugador()
        suelo = [pygame.Rect(0, 200, 400, 20)]
        for _ in range(40):
            jugador.update(1 / 60.0, suelo, None)
        assert jugador.is_grounded
        assert jugador.rect.bottom == 200


class TestLaParedLateral:
    """AUD-323, a través del jugador."""

    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_no_atraviesa_la_cara_empinada(self) -> None:
        """Caminando contra la cara de la rampa se frena en su x, y el eje Y
        no lo absorbe hacia la superficie de la cuesta."""
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 50), sube_a_la_derecha=True)]
        suelo = [pygame.Rect(100, 100, 200, 20)]   # llano al nivel del pie
        jugador.position.update(160.0, 60.0)
        for _ in range(60):
            jugador.update(1 / 60.0, suelo, None, pendientes=cuesta)
        assert jugador.is_grounded
        assert jugador.rect.bottom == 100

        for _ in range(30):
            jugador.position.x -= 3.0
            jugador.update(1 / 60.0, suelo, None, pendientes=cuesta)
        assert jugador.rect.left >= 100.0 - 1.0, (
            "la cara de la rampa no frenó al jugador"
        )
        assert jugador.rect.bottom == 100, (
            "el jugador fue absorbido hacia la superficie de la cuesta"
        )


class TestDeslizamientoAlAterrizar:
    """AUD-324, a través del jugador."""

    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_caer_en_vertical_sobre_una_cuesta_de_45_grados_desliza(self) -> None:
        """Caer en vertical sobre una cuesta no debe parar al jugador en
        seco: el impulso de la caída se proyecta y lo empuja cuesta abajo.
        Es la proyección de velocidad que `docs/87` §11 pidió por escrito."""
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100), sube_a_la_derecha=True)]
        # Aterriza cerca de la cima: el deslizamiento (AUD-326) lo lleva
        # hacia el pie sin sacarlo de la rampa durante la ventana de 90
        # fotogramas.
        jugador.position.update(80.0, 40.0)
        deslizo = False
        for _ in range(90):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
            if jugador.is_grounded and jugador.velocity.x < 0:
                deslizo = True
        assert jugador.is_grounded
        assert deslizo, "al aterrizar en la cuesta el jugador no deslizó cuesta abajo"

    def test_la_cuesta_mirror_desliza_al_otro_lado(self) -> None:
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100), sube_a_la_derecha=False)]
        jugador.position.update(20.0, 40.0)
        deslizo = False
        for _ in range(90):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
            if jugador.is_grounded and jugador.velocity.x > 0:
                deslizo = True
        assert jugador.is_grounded
        assert deslizo

    def test_aterrizar_en_suelo_llano_no_cambia_la_fisica(self) -> None:
        """Sin pendiente no hay proyección: es la vieja física, intacta."""
        jugador = self._jugador()
        suelo = [pygame.Rect(0, 150, 200, 20)]
        piso = False
        for _ in range(90):
            jugador.update(1 / 60.0, suelo, None)
            if jugador.is_grounded and not piso:
                piso = True
                assert jugador.velocity.x == 0.0
        assert piso


class TestDeslizamientoSostenido:
    """AUD-326 — quieto en la cuesta, la gravedad desliza.

    El aterrizaje ya proyecta el impulso de la caída (AUD-324); falta lo
    que pasa **después**: sin entrada horizontal el jugador no se queda
    clavado en la cuesta, se desliza cuesta abajo. El deslizamiento es de
    velocidad constante — la que da `PLAYER_SLOPE_SLIDE_SPEED` por el
    factor de la pendiente — no una aceleración en fuga. Y andar, subiendo
    o bajando, manda: la entrada ya puso `velocity.x` y el deslizamiento
    no se la discute.
    """

    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_quieto_en_cuesta_se_desliza_cuesta_abajo(self) -> None:
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100),
                            sube_a_la_derecha=False)]
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded
        x0 = jugador.position.x
        for _ in range(60):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.position.x > x0, \
            "quieto en la cuesta no se deslizó hacia el pie"

    def test_mirror_desliza_hacia_el_otro_lado(self) -> None:
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100),
                            sube_a_la_derecha=True)]
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        x0 = jugador.position.x
        for _ in range(60):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.position.x < x0, \
            "quieto en la cuesta no se deslizó hacia el pie"

    def test_el_deslizamiento_es_de_velocidad_constante(self) -> None:
        """Sin aceleración en fuga: el mismo `velocity.x` fotograma tras
        fotograma, cuesta abajo."""
        jugador = self._jugador()
        cuesta = [Pendiente(pygame.Rect(0, 50, 200, 100),
                            sube_a_la_derecha=True)]
        jugador.position.update(160.0, 40.0)
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.is_grounded
        v1 = jugador.velocity.x
        for _ in range(60):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        v2 = jugador.velocity.x
        assert v1 == v2 and v1 < 0, \
            "el deslizamiento sostenido no es de velocidad constante"

    def test_en_suelo_llano_no_desliza(self) -> None:
        jugador = self._jugador()
        suelo = [pygame.Rect(0, 150, 200, 20)]
        for _ in range(30):
            jugador.update(1 / 60.0, suelo, None)
        x0 = jugador.position.x
        for _ in range(30):
            jugador.update(1 / 60.0, suelo, None)
        assert jugador.position.x == pytest.approx(x0)


class TestPendientesEnCenital:
    """AUD-328 — en la vista cenital no hay gravedad, y sin gravedad no hay
    cuesta que resolver: la mecánica es de la vista lateral.

    En planta la rampa es terreno pintado: ni pega al jugador a su
    hipotenusa ni frena su paso. Lo que frena en cenital es la capa
    Collision, como siempre.
    """

    @staticmethod
    def _jugador():
        from src.framework.entities.player import Player

        return Player(pygame.Vector2(50, 40))

    def test_no_se_pega_a_la_hipotenusa(self) -> None:
        jugador = self._jugador()
        jugador.vista_cenital = True
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100),
                            sube_a_la_derecha=True)]
        jugador.position.update(50.0, 60.0)
        for _ in range(30):
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.position.y == pytest.approx(60.0), \
            "en cenital la rampa pegó al jugador a su superficie"

    def test_no_bloquea_el_paso_por_la_cara(self) -> None:
        jugador = self._jugador()
        jugador.vista_cenital = True
        cuesta = [Pendiente(pygame.Rect(0, 50, 100, 100),
                            sube_a_la_derecha=True)]
        jugador.position.update(160.0, 60.0)
        for _ in range(30):
            jugador.position.x -= 3.0
            jugador.update(1 / 60.0, [], None, pendientes=cuesta)
        assert jugador.rect.left <= 90.0, \
            "en cenital la cara de la rampa frenó el paso"


class TestDesdeElMapa:
    def test_slope_es_un_tipo_conocido(self) -> None:
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert "Slope" in known_object_types([])

    def test_el_cargador_lo_lee(self) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "cuesta", 32.0, 64.0, 48.0, 48.0

        stage = StageData(map_layer=None)
        StageLoader._handle_pendiente(stage, _Obj(), {"sube": "izquierda"})
        assert len(stage.pendientes) == 1
        assert stage.pendientes[0].sube_a_la_derecha is False

    def test_un_sube_ilegible_no_revienta(self) -> None:
        from src.framework.stage.stage_loader import StageData, StageLoader

        class _Obj:
            id, name, x, y, width, height = 1, "cuesta", 32.0, 64.0, 48.0, 48.0

        stage = StageData(map_layer=None)
        StageLoader._handle_pendiente(stage, _Obj(), {"sube": "arriba"})
        assert stage.pendientes[0].sube_a_la_derecha is True

    def test_el_laboratorio_tiene_una_de_cada(self) -> None:
        """Subir y bajar, pegadas: bajar es el caso que hay que poder probar."""
        import re
        from pathlib import Path

        from src.engine.core import settings

        tmx = (Path(settings.ASSETS_DIR) / "maps" / "stage_mecanicas"
               / "stage_mecanicas.tmx").read_text(encoding="utf-8")
        assert len(re.findall(r'type="Slope"', tmx)) >= 2
        assert 'value="izquierda"' in tmx

    #: Mapas donde `Slope` puede aparecer sin que sea una fuga accidental
    #: hacia una entrega calificada: `stage_mecanicas` es el laboratorio que
    #: lo estrenó, y `stage4_1` es contenido de profesorado — «Entregable:
    #: profesorado (no se asigna a estudiantes)», `docs/niveles/
    #: 13_STAGE_4_1.md` — que usa un slope de verdad para la loma de su Fase
    #: 3 (AUD-463). Lo que esta prueba de verdad protege es que el tipo no
    #: aparezca en ninguna de las 26 entregas de estudiantes.
    _MAPAS_CON_PENDIENTE_ESPERADOS = frozenset({"stage_mecanicas", "stage4_1"})

    def test_ningun_mapa_entregado_tiene_pendientes(self) -> None:
        """Lo que hace segura una integración en la resolución de colisión: el
        paso nuevo no se ejecuta en ninguna entrega de estudiante calificada."""
        from pathlib import Path

        from src.engine.core import settings

        con_pendiente = {
            tmx.parent.name
            for tmx in Path(settings.ASSETS_DIR).joinpath("maps").rglob("*.tmx")
            if 'type="Slope"' in tmx.read_text(encoding="utf-8")
        }
        assert con_pendiente == self._MAPAS_CON_PENDIENTE_ESPERADOS, (
            f"{con_pendiente - self._MAPAS_CON_PENDIENTE_ESPERADOS} usa Slope "
            f"sin estar en la lista de mapas de profesorado esperados"
        )

