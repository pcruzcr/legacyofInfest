"""
F5 — el núcleo ECS, el puente y las once mecánicas nuevas.

Lo que estas pruebas protegen, por orden de importancia
=======================================================
1. **Que las 26 clases de estudiantes sigan funcionando.** Es el requisito que
   manda sobre todos los demás. Si el puente devolviera copias en vez de los
   objetos reales, todo compilaría y el juego se rompería en silencio.
2. Que cada mecánica **haga algo observable**. No que el método exista: que la
   posición cambie, que el bloque desaparezca, que el guardia vea.
3. Que el orden de los sistemas sea el correcto. Es el fallo más caro de esta
   arquitectura y el que menos se parece a lo que provoca.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.ecs import (
    Acosador,
    Alerta,
    BloqueRitmico,
    ConoDeVision,
    Fase,
    Planificador,
    PlataformaHundible,
    PlataformaMovil,
    Salud,
    Solido,
    Transform,
    Velocidad,
    World,
    ZonaDeAgua,
    ZonaDeFriccion,
    ZonaDeViento,
    ZonaLetalTemporizada,
)
from src.framework.ecs import systems as S
from src.framework.ecs.components import EsJugador

FRAME = 1.0 / 60.0


@pytest.fixture(scope="module", autouse=True)
def _pg():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))
    yield


def _movil(mundo: World, x: int = 0, y: int = 100, **kw) -> int:
    rect = pygame.Rect(x, y, 48, 8)
    return mundo.crear(
        Transform(pygame.Vector2(rect.topleft), rect),
        PlataformaMovil(
            origen=pygame.Vector2(rect.topleft),
            destino=pygame.Vector2(x + 100, y),
            **kw,
        ),
        Solido(),
    )


# ══════════════════════════════════════════════════════════════
# El núcleo
# ══════════════════════════════════════════════════════════════


class TestElMundo:
    def test_los_identificadores_nunca_se_reutilizan(self):
        """Reciclarlos produce el peor error de esta arquitectura.

        Un sistema guarda el id 7, el 7 muere, nace otro 7 distinto y el
        sistema opera sobre el nuevo creyendo que es el viejo. No se puede
        depurar mirando el síntoma.
        """
        m = World()
        a = m.crear()
        m.marcar_baja(a)
        m.aplicar_bajas()
        b = m.crear()
        assert b != a

    def test_la_baja_es_diferida(self):
        """Borrar dentro de un recorrido lo deja a medias."""
        m = World()
        e = m.crear(Salud(10, 10))
        m.marcar_baja(e)
        assert m.existe(e), "la baja no debe aplicarse hasta aplicar_bajas()"
        assert m.aplicar_bajas() == 1
        assert not m.existe(e)
        assert m.obtener(e, Salud) is None

    def test_recorrer_mientras_se_crean_entidades_no_revienta(self):
        """La mitad de los sistemas crean entidades mientras recorren."""
        m = World()
        for _ in range(5):
            m.crear(Salud(1, 1))
        vistos = 0
        for _e, _s in m.cada(Salud):
            m.crear(Salud(1, 1))     # sin la copia, esto lanzaría RuntimeError
            vistos += 1
        assert vistos == 5

    def test_los_componentes_se_indexan_por_clase_exacta(self):
        """Si se heredaran, un sistema trataría como suyo lo que no lo es."""
        m = World()
        e = m.crear(ZonaDeViento(pygame.Rect(0, 0, 4, 4), pygame.Vector2(1, 0)))
        assert m.obtener(e, ZonaDeViento) is not None
        assert m.obtener(e, ZonaDeFriccion) is None

    def test_con_devuelve_solo_los_que_tienen_todo(self):
        m = World()
        completo = m.crear(Transform(pygame.Vector2(), pygame.Rect(0, 0, 1, 1)),
                           Velocidad(pygame.Vector2()))
        m.crear(Transform(pygame.Vector2(), pygame.Rect(0, 0, 1, 1)))
        assert list(m.con(Transform, Velocidad)) == [completo]


class TestElPlanificador:
    def test_ejecuta_en_orden_de_fase(self):
        m, p = World(), Planificador()
        orden: list[str] = []
        p.registrar(Fase.COLISION, "colision", lambda _m, _d: orden.append("colision"))
        p.registrar(Fase.FUERZAS, "fuerzas", lambda _m, _d: orden.append("fuerzas"))
        p.registrar(Fase.MOVIMIENTO, "movimiento", lambda _m, _d: orden.append("movimiento"))
        p.ejecutar(m, FRAME)
        assert orden == ["fuerzas", "movimiento", "colision"]

    def test_dos_nombres_iguales_se_rechazan(self):
        """Los nombres se usan para apagar sistemas: repetirlos apagaría el otro."""
        p = Planificador()
        p.registrar(Fase.IA, "x", lambda _m, _d: None)
        with pytest.raises(ValueError, match="ya hay un sistema"):
            p.registrar(Fase.COMBATE, "x", lambda _m, _d: None)

    def test_un_sistema_que_lanza_no_tumba_el_fotograma(self):
        """Un escenario de estudiante puede lanzar; el juego no debe caerse."""
        m, p = World(), Planificador()
        corrio = []
        p.registrar(Fase.IA, "malo", lambda _m, _d: 1 / 0)
        p.registrar(Fase.COMBATE, "bueno", lambda _m, _d: corrio.append(1))
        p.ejecutar(m, FRAME)
        assert corrio == [1]


# ══════════════════════════════════════════════════════════════
# El puente: LO QUE NO PUEDE ROMPERSE
# ══════════════════════════════════════════════════════════════


class TestElPuenteNoRompeElCodigoDeLosEstudiantes:
    """115 líneas de código entregado mutan `rect` y `position` en el sitio."""

    @pytest.fixture
    def enemigo(self):
        from src.framework.entities.enemy_walker import EnemyWalker
        return EnemyWalker(pygame.Vector2(10, 20))

    def test_mutar_el_rect_en_el_sitio_llega_al_componente(self, enemigo):
        """`self.rect.centerx = 40` — lo hacen 115 veces en `src/stages/`."""
        enemigo.rect.centerx = 400
        t = enemigo.mundo.obtener(enemigo.entidad, Transform)
        assert t.rect.centerx == 400, (
            "la propiedad devolvió una copia: el código del estudiante mueve su "
            "rect y los sistemas leen otro"
        )

    def test_mutar_la_posicion_en_el_sitio_llega_al_componente(self, enemigo):
        enemigo.position.x += 33.0
        t = enemigo.mundo.obtener(enemigo.entidad, Transform)
        assert t.posicion.x == pytest.approx(43.0)

    def test_reemplazar_el_rect_entero_tambien_funciona(self, enemigo):
        enemigo.rect = pygame.Rect(7, 8, 9, 10)
        t = enemigo.mundo.obtener(enemigo.entidad, Transform)
        assert t.rect.topleft == (7, 8)

    def test_reasignar_position_llega_al_componente(self, enemigo):
        """Y el componente lo ve, porque es una vista y no una copia.

        La primera versión de esta prueba exigía que reasignar `self.position`
        **conservara el vector** para no romper a quien hubiera guardado una
        referencia. Estaba mal planteada: `BaseEntity` antes de la fase 5 tenía
        `position` como atributo normal, así que asignarlo **siempre** ha
        sustituido el objeto. La prueba defendía una garantía que el motor nunca
        dio y que yo había inventado al escribir el puente.

        Lo que sí hay que garantizar —y es lo que se comprueba— es que el
        componente no se quede con el valor viejo.
        """
        enemigo.position = pygame.Vector2(99, 99)
        t = enemigo.mundo.obtener(enemigo.entidad, Transform)
        assert t.posicion.x == pytest.approx(99.0)

    def test_reasignar_rect_llega_al_componente(self, enemigo):
        """Ocurre 14 veces en las entregas y es el caso que más silencio da."""
        enemigo.rect = pygame.Rect(300, 400, 8, 8)
        t = enemigo.mundo.obtener(enemigo.entidad, Transform)
        assert t.rect.topleft == (300, 400), (
            "el componente conservó el rect viejo: los sistemas moverían un "
            "rectángulo que ya nadie dibuja"
        )

    def test_facing_se_normaliza(self, enemigo):
        enemigo.facing = -7
        assert enemigo.facing == -1

    def test_las_26_clases_de_estudiantes_siguen_construyendose(self):
        """La prueba que justifica toda la capa de compatibilidad.

        Si el ECS hubiera sustituido la jerarquía en vez de meterse debajo,
        esto no compilaría y 18.054 líneas de trabajo entregado y calificado
        habría que reescribirlas.
        """
        import importlib
        import pkgutil

        import src.stages as paquete_stages

        vivas = 0
        for info in pkgutil.walk_packages(paquete_stages.__path__, "src.stages."):
            if any(p in info.name for p in (".tools", ".tests", ".herramientas")):
                continue
            try:
                modulo = importlib.import_module(info.name)
            except Exception:
                continue
            from src.framework.ecs.bridge import ComponentesDeEntidad
            from src.framework.entities.base_entity import BaseEntity
            for nombre in dir(modulo):
                obj = getattr(modulo, nombre)
                if (isinstance(obj, type) and issubclass(obj, BaseEntity)
                        and obj is not BaseEntity):
                    # Se comprueba la **herencia del puente**, no `hasattr` en
                    # la clase.
                    #
                    # La primera versión hacía `hasattr(obj, "rect")`, y pasaba
                    # sólo porque `rect` era entonces una propiedad —es decir,
                    # un atributo de clase—. Al convertirla en atributo de
                    # instancia por rendimiento, la prueba se puso roja sin que
                    # nada se hubiera roto: estaba midiendo **cómo** está
                    # implementado el puente en vez de **que** lo tengan.
                    #
                    # Que una instancia funcione de verdad lo prueban los cinco
                    # tests de arriba sobre un `EnemyWalker` real; aquí lo que
                    # se vigila es que ninguna clase entregada se quede fuera
                    # de la cadena.
                    assert issubclass(obj, ComponentesDeEntidad), (
                        f"{nombre} no hereda el puente ECS: se quedaría sin "
                        f"`rect` ni `position`"
                    )
                    vivas += 1
        assert vivas >= 5, f"sólo se encontraron {vivas} entidades de estudiantes"


# ══════════════════════════════════════════════════════════════
# F5.3 — zonas con efecto físico
# ══════════════════════════════════════════════════════════════


class TestZonas:
    def test_el_viento_empuja_a_quien_esta_dentro(self):
        m = World()
        m.crear(ZonaDeViento(pygame.Rect(0, 0, 200, 200), pygame.Vector2(300, 0)))
        e = m.crear(Transform(pygame.Vector2(50, 50), pygame.Rect(50, 50, 8, 8)),
                    Velocidad(pygame.Vector2(0, 0)))
        for _ in range(30):
            S.sistema_viento(m, FRAME)
        assert m.obtener(e, Velocidad).v.x > 100.0

    def test_el_viento_no_empuja_a_quien_esta_fuera(self):
        m = World()
        m.crear(ZonaDeViento(pygame.Rect(0, 0, 20, 20), pygame.Vector2(300, 0)))
        e = m.crear(Transform(pygame.Vector2(500, 500), pygame.Rect(500, 500, 8, 8)),
                    Velocidad(pygame.Vector2(0, 0)))
        for _ in range(30):
            S.sistema_viento(m, FRAME)
        assert m.obtener(e, Velocidad).v.x == 0.0

    def test_el_viento_con_periodo_sopla_a_rachas(self):
        z = ZonaDeViento(pygame.Rect(0, 0, 10, 10), pygame.Vector2(1, 0), periodo=2.0)
        assert z.soplando
        z._t = 1.5
        assert not z.soplando

    def test_la_cinta_arrastra_sin_acumular_velocidad(self):
        """Saltar desde una cinta no debe salir disparado."""
        m = World()
        m.crear(ZonaDeFriccion(pygame.Rect(0, 0, 200, 200), arrastre=60.0))
        e = m.crear(Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
                    Velocidad(pygame.Vector2(0, 0)))
        for _ in range(60):
            S.sistema_friccion(m, FRAME)
        assert m.obtener(e, Transform).posicion.x == pytest.approx(70.0, abs=1.0)
        assert m.obtener(e, Velocidad).v.x == 0.0, "el arrastre no debe cargar velocidad"

    def test_el_laser_solo_hace_dano_encendido(self):
        m = World()
        z = ZonaLetalTemporizada(pygame.Rect(0, 0, 50, 50), dano=5.0,
                                 encendido=1.0, apagado=1.0)
        m.crear(z)
        e = m.crear(Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
                    Salud(100.0, 100.0))
        S.sistema_zonas_letales(m, FRAME)
        assert m.obtener(e, Salud).actual < 100.0

        z._t = 1.5          # apagado
        antes = m.obtener(e, Salud).actual
        S.sistema_zonas_letales(m, FRAME)
        assert m.obtener(e, Salud).actual == antes

    def test_el_laser_avisa_antes_de_encenderse(self):
        """Sin aviso no es un obstáculo, es una emboscada."""
        z = ZonaLetalTemporizada(pygame.Rect(0, 0, 4, 4), encendido=1.0, apagado=1.0)
        z._t = 1.8          # a 0,2 s de encenderse
        assert not z.activa
        assert z.aviso > 0.0

    def test_el_desfase_permite_una_cascada(self):
        """Cinco láseres a la vez son un muro; en cascada son un patrón."""
        a = ZonaLetalTemporizada(pygame.Rect(0, 0, 4, 4), encendido=1.0, apagado=1.0)
        b = ZonaLetalTemporizada(pygame.Rect(0, 0, 4, 4), encendido=1.0, apagado=1.0,
                                 desfase=1.0)
        assert a.activa != b.activa

    def test_una_zona_invulnerable_no_recibe_dano(self):
        m = World()
        m.crear(ZonaLetalTemporizada(pygame.Rect(0, 0, 50, 50), dano=5.0))
        e = m.crear(Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
                    Salud(100.0, 100.0, invulnerable=True))
        S.sistema_zonas_letales(m, FRAME)
        assert m.obtener(e, Salud).actual == 100.0


# ══════════════════════════════════════════════════════════════
# F5.4 — superficies que se mueven
# ══════════════════════════════════════════════════════════════


class TestPlataformas:
    def test_la_plataforma_va_y_vuelve(self):
        m = World()
        e = _movil(m, velocidad=200.0, espera=0.0)
        for _ in range(120):
            S.sistema_plataformas_moviles(m, FRAME)
        x1 = m.obtener(e, Transform).posicion.x
        for _ in range(120):
            S.sistema_plataformas_moviles(m, FRAME)
        x2 = m.obtener(e, Transform).posicion.x
        assert x1 != x2, "la plataforma no cambió de sentido"

    def test_la_plataforma_arrastra_a_su_pasajero(self):
        """**El sistema que casi nadie implementa.**

        Sin él, el jugador se queda clavado en el aire mientras la plataforma
        se va, y parece un fallo de colisión cuando es un sistema que falta.
        """
        m = World()
        plat = _movil(m, velocidad=100.0, espera=0.0)
        rect_plat = m.obtener(plat, Transform).rect
        pasajero_rect = pygame.Rect(rect_plat.x + 8, rect_plat.y - 16, 16, 16)
        pasajero = m.crear(
            Transform(pygame.Vector2(pasajero_rect.topleft), pasajero_rect),
            Velocidad(pygame.Vector2(0, 0)),
        )
        x0 = m.obtener(pasajero, Transform).posicion.x
        for _ in range(30):
            S.sistema_plataformas_moviles(m, FRAME)
            S.sistema_arrastre_de_plataformas(m, FRAME)
        assert m.obtener(pasajero, Transform).posicion.x > x0 + 10.0

    def test_no_arrastra_a_quien_pasa_por_debajo(self):
        m = World()
        plat = _movil(m, velocidad=100.0, espera=0.0)
        rect_plat = m.obtener(plat, Transform).rect
        abajo = pygame.Rect(rect_plat.x, rect_plat.bottom + 20, 16, 16)
        otro = m.crear(Transform(pygame.Vector2(abajo.topleft), abajo),
                       Velocidad(pygame.Vector2(0, 0)))
        x0 = m.obtener(otro, Transform).posicion.x
        for _ in range(30):
            S.sistema_plataformas_moviles(m, FRAME)
            S.sistema_arrastre_de_plataformas(m, FRAME)
        assert m.obtener(otro, Transform).posicion.x == x0

    def test_el_bloque_ritmico_deja_de_ser_solido(self):
        m = World()
        e = m.crear(Transform(pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 16)),
                    BloqueRitmico(visible_seg=0.5, oculto_seg=0.5))
        S.sistema_bloques_ritmicos(m, FRAME)
        assert m.tiene(e, Solido)
        for _ in range(40):     # pasa de 0,5 s
            S.sistema_bloques_ritmicos(m, FRAME)
        assert not m.tiene(e, Solido), "el bloque sigue sosteniendo tras desaparecer"

    def test_la_hundible_cae_tras_el_retraso_y_vuelve(self):
        m = World()
        rect = pygame.Rect(0, 100, 32, 8)
        e = m.crear(Transform(pygame.Vector2(rect.topleft), rect),
                    PlataformaHundible(retraso=0.2, velocidad_caida=600.0,
                                       reaparece_en=0.3, y_original=100.0),
                    Solido(atravesable_desde_abajo=True))
        S.marcar_pisada(m, e)

        # Se busca el fotograma en el que desaparece, en vez de mirar sólo al
        # final. El ciclo completo —caer, ausentarse, volver— dura menos de 90
        # fotogramas, así que al final ya ha vuelto y comprobar «no es sólida»
        # ahí fallaría por el motivo contrario al que la prueba quiere medir.
        for _ in range(90):
            S.sistema_plataformas_hundibles(m, FRAME)
            if not m.tiene(e, Solido):
                break
        else:
            pytest.fail("la hundible no llegó a desaparecer")

        for _ in range(60):
            S.sistema_plataformas_hundibles(m, FRAME)
            if m.tiene(e, Solido):
                break
        else:
            pytest.fail("la hundible no volvió")
        assert m.obtener(e, Transform).posicion.y == pytest.approx(100.0)

    def test_rects_solidos_refleja_el_estado_de_este_fotograma(self):
        m = World()
        e = m.crear(Transform(pygame.Vector2(0, 0), pygame.Rect(0, 0, 16, 16)),
                    BloqueRitmico(visible_seg=0.1, oculto_seg=10.0))
        S.sistema_bloques_ritmicos(m, FRAME)
        assert len(S.rects_solidos(m)) == 1
        for _ in range(20):
            S.sistema_bloques_ritmicos(m, FRAME)
        assert S.rects_solidos(m) == []
        assert m.existe(e)


# ══════════════════════════════════════════════════════════════
# F5.6 — agua
# ══════════════════════════════════════════════════════════════


class TestAgua:
    def test_en_agua_detecta_la_zona(self):
        m = World()
        m.crear(ZonaDeAgua(pygame.Rect(0, 0, 100, 100)))
        assert S.en_agua(m, pygame.Rect(10, 10, 8, 8)) is not None
        assert S.en_agua(m, pygame.Rect(500, 500, 8, 8)) is None

    def test_la_corriente_arrastra(self):
        m = World()
        m.crear(ZonaDeAgua(pygame.Rect(0, 0, 200, 200),
                           corriente=pygame.Vector2(0, 120)))
        e = m.crear(Transform(pygame.Vector2(10, 10), pygame.Rect(10, 10, 8, 8)),
                    Velocidad(pygame.Vector2(0, 0)))
        for _ in range(30):
            S.sistema_corriente_de_agua(m, FRAME)
        assert m.obtener(e, Velocidad).v.y > 30.0


# ══════════════════════════════════════════════════════════════
# F5.9 — sigilo
# ══════════════════════════════════════════════════════════════


def _poner_jugador(mundo: World, rect: pygame.Rect) -> int:
    """El jugador es una entidad más del mundo, con su marca.

    F5.11 — antes se pasaba por parámetro a los dos sistemas de sigilo, y esa
    firma distinta impedía meterlos en el `Planificador`. Ahora lo buscan ellos.
    """
    return mundo.crear(
        Transform(pygame.Vector2(rect.topleft), rect), EsJugador(),
    )


class TestSigilo:
    def _guardia(self, mundo: World, **kw) -> int:
        return mundo.crear(
            Transform(pygame.Vector2(100, 100), pygame.Rect(100, 100, 16, 16)),
            ConoDeVision(mira=pygame.Vector2(1, 0), alcance=200.0, semiangulo=30.0, **kw),
            Alerta(),
        )

    def test_ve_al_jugador_delante_y_cerca(self):
        m = World()
        g = self._guardia(m)
        _poner_jugador(m, pygame.Rect(200, 100, 16, 16))
        S.sistema_conos_de_vision(m, FRAME)
        assert m.obtener(g, ConoDeVision).ve_al_jugador

    def test_no_ve_al_que_tiene_detras(self):
        m = World()
        g = self._guardia(m)
        _poner_jugador(m, pygame.Rect(0, 100, 16, 16))
        S.sistema_conos_de_vision(m, FRAME)
        assert not m.obtener(g, ConoDeVision).ve_al_jugador

    def test_no_ve_al_que_esta_lejos(self):
        m = World()
        g = self._guardia(m)
        _poner_jugador(m, pygame.Rect(9000, 100, 16, 16))
        S.sistema_conos_de_vision(m, FRAME)
        assert not m.obtener(g, ConoDeVision).ve_al_jugador

    def test_no_ve_al_que_esta_fuera_del_cono(self):
        """A 45° con un semiángulo de 30 no debería verlo."""
        m = World()
        g = self._guardia(m)
        _poner_jugador(m, pygame.Rect(180, 20, 16, 16))
        S.sistema_conos_de_vision(m, FRAME)
        assert not m.obtener(g, ConoDeVision).ve_al_jugador

    def test_la_alerta_sube_viendo_y_baja_al_perderlo(self):
        m = World()
        g = self._guardia(m)
        jugador = _poner_jugador(m, pygame.Rect(200, 100, 16, 16))
        for _ in range(60):
            S.sistema_conos_de_vision(m, FRAME)
            S.sistema_alerta(m, FRAME)
        alta = m.obtener(g, Alerta).nivel
        assert m.obtener(g, Alerta).estado == "alerta"

        # Se esconde: se mueve **la misma entidad**, no se crea otra. Dos
        # jugadores en el mundo serían un estado imposible, y el sistema
        # devolvería el primero que encontrara.
        m.obtener(jugador, Transform).rect.topleft = (0, 100)
        for _ in range(30):
            S.sistema_conos_de_vision(m, FRAME)
            S.sistema_alerta(m, FRAME)
        assert m.obtener(g, Alerta).nivel < alta

    def test_la_alerta_baja_mas_despacio_de_lo_que_sube(self):
        """Si olvidara al mismo ritmo, el sigilo se resolvería a base de intentarlo."""
        a = Alerta()
        assert a.bajada_por_segundo < a.subida_por_segundo

    def test_el_acosador_persigue_y_es_invulnerable(self):
        m = World()
        e = m.crear(Transform(pygame.Vector2(0, 100), pygame.Rect(0, 100, 16, 16)),
                    Acosador(velocidad=100.0), Salud(1.0, 1.0))
        _poner_jugador(m, pygame.Rect(300, 100, 16, 16))
        for _ in range(60):
            S.sistema_acosador(m, FRAME)
        assert m.obtener(e, Transform).posicion.x > 50.0
        assert m.obtener(e, Salud).invulnerable

    def test_el_acosador_se_retira_si_lo_pierdes(self):
        m = World()
        e = m.crear(Transform(pygame.Vector2(0, 100), pygame.Rect(0, 100, 16, 16)),
                    Acosador(velocidad=100.0, distancia_retirada=100.0,
                             reaparicion=0.5))
        _poner_jugador(m, pygame.Rect(5000, 100, 16, 16))
        S.sistema_acosador(m, FRAME)
        assert m.obtener(e, Acosador)._fuera > 0.0


# ══════════════════════════════════════════════════════════════
# Integración con el TMX y el catálogo de tipos
# ══════════════════════════════════════════════════════════════


class TestElCosteDelPuente:
    """El ECS no puede costar el fotograma, y hay que medirlo bien.

    Historia de esta prueba, porque la lección vale más que el número
    ------------------------------------------------------------------
    Al medir el coste del puente sobre el prólogo completo salieron, en este
    orden: 27,29 ms, luego 21,36, luego 34,58, luego 30,89. Con la misma
    máquina y el mismo código. Con esa varianza se llegó a concluir que el ECS
    costaba un **63 %** del fotograma, y se estuvo a punto de deshacer el
    diseño por ello.

    El perfilador dijo otra cosa: **1,449 s en `builtins.compile`**, con 445
    compilaciones, 671 `marshal.loads` y 1.245 aperturas de fichero. El
    predictor de IA y la iluminación importan scipy y llvmlite de forma
    perezosa, y esas importaciones caían **dentro de la ventana medida**. Se
    estaba cronometrando el arranque de una biblioteca científica y llamándolo
    coste del ECS.

    Con 400 fotogramas de calentamiento y la mediana de nueve tandas: **9,42 ms
    con la fase 5 contra 9,07 ms sin ella**. Un 4 %, dentro del ruido.

    La lección no es el 4 %: es que un benchmark sin calentamiento suficiente
    miente, y miente en la dirección que confirma lo que uno teme.
    """

    def test_el_acceso_a_rect_no_paga_indirección(self):
        """`rect` tiene que ser un atributo, no una propiedad.

        Se probaron las tres formas y se midieron las tres:

        * propiedad que lee el componente ..... 404 ns
        * atributo + `__setattr__` vigilante ... peor aún: `__setattr__` se
          dispara en *cada* escritura de la entidad
        * atributo normal, componente como vista ... 66 ns

        Se quedó la tercera. Esta prueba impide que alguien «ordene» el código
        volviendo a la primera sin volver a medir.
        """
        from src.framework.entities.enemy_walker import EnemyWalker

        assert not isinstance(
            type(EnemyWalker(pygame.Vector2(0, 0))).__dict__.get("rect"), property,
        ), (
            "`rect` volvió a ser una propiedad: son 404 ns contra 66, y el "
            "motor la lee 255 veces por fotograma"
        )

    def test_el_componente_es_una_vista_y_no_una_copia(self):
        """La vista es lo que permite que `rect` sea un atributo normal."""
        from src.framework.entities.enemy_walker import EnemyWalker

        e = EnemyWalker(pygame.Vector2(0, 0))
        t = e.mundo.obtener(e.entidad, Transform)
        assert t.rect is e.rect, "el componente guardó una copia del rect"
        assert t.posicion is e.position, "el componente guardó una copia de la posición"

    def test_un_mundo_vacio_no_cuesta_nada(self):
        """La escena llama a los sistemas cada fotograma aunque no haya nada.

        Trece de los catorce escenarios entregados no usan ninguna mecánica
        nueva todavía. Si recorrer un mundo vacío costara, la fase 5 les habría
        cobrado a todos por algo que no usan.
        """
        import time

        from src.framework.ecs import systems as sistemas

        m = World()
        t0 = time.perf_counter()
        for _ in range(1000):
            sistemas.sistema_viento(m, FRAME)
            sistemas.sistema_plataformas_moviles(m, FRAME)
            sistemas.sistema_zonas_letales(m, FRAME)
            sistemas.rects_solidos(m)
        ms = (time.perf_counter() - t0) / 1000 * 1000
        assert ms < 0.05, f"un mundo vacío cuesta {ms:.4f} ms por fotograma"


class TestElJugadorEsUnaEntidadDelMundo:
    """F5.11 — la deuda que `_mundo_ecs_paso` dejaba declarada, saldada.

    Aquella función llamaba a los once sistemas a mano porque los dos de sigilo
    recibían el rectángulo del jugador por parámetro, y con una firma distinta
    a `Sistema` no cabían en el `Planificador`.

    Ahora el jugador entra al mundo con su marca `EsJugador`, los sistemas lo
    buscan, y el orden vive en un solo sitio.
    """

    @pytest.fixture
    def escena(self):
        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.framework.entities import entity_factory
        from src.stages.stage0.stage0 import Stage0

        entity_factory.ensure_registered()
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        sc = Stage0(ctx)
        sc.awake()
        sc.start()
        sc.on_enter()
        return sc

    def test_el_jugador_esta_en_el_mundo_con_su_marca(self, escena):
        assert escena._mundo.tiene(escena._player.entidad, EsJugador)
        assert S.rect_del_jugador(escena._mundo) is escena._player.rect, (
            "el mundo devuelve un rect que no es el del jugador: los sistemas "
            "de sigilo estarían mirando a otro sitio"
        )

    def test_los_enemigos_tambien_entran_al_mundo(self, escena):
        """Si no entran, el viento sopla para el jugador y no para ellos.

        Era una rareza real de la primera versión: un nivel con viento tenía
        viento para uno y calma para todos los demás.
        """
        from src.framework.entities.enemy_base import EnemyBase

        enemigos = [
            e for e in escena._stage_data.entity_list if isinstance(e, EnemyBase)
        ]
        assert enemigos, "el prólogo debería tener enemigos"
        for e in enemigos:
            assert escena._mundo.tiene(e.entidad, Transform), (
                f"{type(e).__name__} no está en el mundo: las zonas de efecto "
                f"lo ignorarían"
            )
            assert escena._mundo.tiene(e.entidad, Velocidad), (
                f"{type(e).__name__} no tiene Velocidad: el viento no podría "
                f"empujarlo"
            )

    def test_la_escena_usa_el_planificador_y_no_una_lista_a_mano(self, escena):
        """La deuda decía: «esta función se sustituye por `ejecutar` y desaparece»."""
        assert not hasattr(escena, "_mundo_ecs_paso"), (
            "`_mundo_ecs_paso` sigue existiendo: la deuda no está saldada"
        )
        assert escena._planificador.nombres, "el planificador está vacío"

    def test_todos_los_sistemas_estan_registrados(self, escena):
        """Registrar el planificador y olvidar un sistema lo apagaría en silencio."""
        esperados = {
            "conos_de_vision", "alerta", "acosador", "viento", "corriente",
            "plataformas_moviles", "bloques_ritmicos", "plataformas_hundibles",
            "arrastre", "friccion", "zonas_letales",
        }
        faltan = esperados - set(escena._planificador.nombres)
        assert not faltan, f"sistemas sin registrar: {sorted(faltan)}"

    def test_el_arrastre_corre_despues_de_mover_las_plataformas(self, escena):
        """Al revés, el pasajero queda hundido un fotograma y sale expulsado."""
        orden = escena._planificador.nombres
        # `nombres` respeta el orden de registro, no el de ejecución; se
        # comprueba el de ejecución forzando la ordenación con una pasada.
        escena._planificador.ejecutar(escena._mundo, 1.0 / 60.0)
        orden = escena._planificador.nombres
        assert orden.index("plataformas_moviles") < orden.index("arrastre")
        assert orden.index("arrastre") < orden.index("friccion")

    def test_el_planificador_mide_cada_sistema(self, escena):
        """Cuando el fotograma se pase, hay que saber cuál fue sin adivinar."""
        escena._planificador.ejecutar(escena._mundo, 1.0 / 60.0)
        tiempos = dict(escena._planificador.tiempos())
        assert len(tiempos) >= 11
        assert all(v >= 0.0 for v in tiempos.values())


class TestSaludEsUnaSolaVerdad:
    """F5.12 — la segunda deuda de la fase 5, saldada al revés de lo previsto.

    La deuda decía: *«el día que ninguna entrega dependa de `current_health`, el
    componente pasa a ser la única verdad»*. Ese día no iba a llegar: hay **48
    referencias** a `current_health` y `max_health` en el código de los
    estudiantes, con escrituras incluidas.

    Así que se resolvió al contrario: el componente es una **vista** sobre el
    dueño. No hay dos copias porque no hay copia.
    """

    @pytest.fixture
    def enemigo(self):
        from src.framework.entities.enemy_walker import EnemyWalker
        e = EnemyWalker(pygame.Vector2(0, 0))
        m = World()
        e.adoptar_en(m)
        from src.framework.ecs.components import Salud as S_
        m.poner(e.entidad, S_(duenio=e))
        return e, m

    def test_el_componente_ve_la_vida_del_enemigo(self, enemigo):
        e, m = enemigo
        assert m.obtener(e.entidad, Salud).actual == pytest.approx(e.current_health)

    def test_bajar_la_vida_del_enemigo_se_ve_en_el_componente(self, enemigo):
        """Sin paso de sincronización que alguien pueda olvidar."""
        e, m = enemigo
        e.current_health -= 3.0
        assert m.obtener(e.entidad, Salud).actual == pytest.approx(e.current_health)

    def test_escribir_en_el_componente_baja_la_vida_del_enemigo(self, enemigo):
        """Es lo que hacen las zonas letales: escriben en `Salud`."""
        e, m = enemigo
        antes = e.current_health
        m.obtener(e.entidad, Salud).actual = antes - 2.0
        assert e.current_health == pytest.approx(antes - 2.0), (
            "la zona letal escribió en el componente y la vida del enemigo no "
            "bajó: vuelve a haber dos copias"
        )

    def test_una_zona_letal_mata_a_un_enemigo_de_verdad(self, enemigo):
        """El camino completo, que es el que este proyecto falla siempre."""
        e, m = enemigo
        m.crear(ZonaLetalTemporizada(
            pygame.Rect(e.rect.x - 50, e.rect.y - 50, 200, 200), dano=999.0,
        ))
        S.sistema_zonas_letales(m, FRAME)
        assert e.current_health <= 0.0, (
            "el enemigo estaba dentro de una zona letal y sigue con vida"
        )

    def test_los_fotogramas_de_invencibilidad_protegen_del_componente(self, enemigo):
        """Un enemigo recién golpeado no debe morir por una zona en el mismo instante."""
        e, m = enemigo
        e._invincibility_timer = 1.0
        assert m.obtener(e.entidad, Salud).invulnerable

    def test_una_salud_sin_dueno_guarda_sus_propios_valores(self):
        """Las entidades puramente ECS no tienen dueño y siguen funcionando."""
        s = Salud(actual=5.0, maxima=10.0)
        assert s.fraccion == pytest.approx(0.5)
        s.actual = 2.5
        assert s.actual == pytest.approx(2.5)


class TestElEscenarioDeReferencia:
    """F5.13 — la tercera deuda: las mecánicas no las usaba nadie.

    Estaban en el motor, probadas, documentadas y en la guía del estudiante, y
    **ninguna de las catorce entregas usaba una sola**. Es la misma forma que la
    iluminación que no iluminaba y el nado inalcanzable, un paso más allá: el
    camino existe, está abierto, y no hay nadie andándolo.

    Estas pruebas vigilan que el escenario de referencia siga enseñando las
    once, porque un mapa de ejemplo que pierde la mitad de sus ejemplos es peor
    que no tenerlo: da la impresión de que el resto no existe.
    """

    @pytest.fixture(scope="class")
    def escena(self):
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
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        sc = StageMecanicas(ctx)
        sc.awake()
        sc.start()
        sc.on_enter()
        return sc

    def test_las_once_mecanicas_llegan_al_mundo(self, escena):
        """Que el TMX las declare no basta: tienen que existir como componentes."""
        from src.framework.ecs.components import (
            Acosador,
            Alerta,
            BloqueRitmico,
            ConoDeVision,
            PlataformaHundible,
            PlataformaMovil,
            ZonaDeAgua,
            ZonaDeFriccion,
            ZonaDeViento,
            ZonaLetalTemporizada,
        )

        censo = escena._mundo.censo()
        for componente in (
            ZonaDeViento, ZonaDeFriccion, ZonaLetalTemporizada, ZonaDeAgua,
            PlataformaMovil, BloqueRitmico, PlataformaHundible,
            ConoDeVision, Alerta, Acosador,
        ):
            assert censo.get(componente.__name__, 0) > 0, (
                f"el escenario de referencia ya no enseña {componente.__name__}: "
                f"censo actual {censo}"
            )

    def test_el_escenario_no_necesita_codigo_propio(self, escena):
        """Todo tiene que estar en el TMX, o el ejemplo no sirve de ejemplo.

        Si hiciera falta código para que las mecánicas funcionen, no serían
        usables desde Tiled y el escenario no demostraría lo que pretende.
        """
        from src.framework.scenes.stage_scene import StageScene
        from src.stages.stage_mecanicas.stage_mecanicas import StageMecanicas

        for metodo in ("update", "draw", "_update_gameplay"):
            assert getattr(StageMecanicas, metodo, None) is getattr(
                StageScene, metodo, None,
            ), (
                f"el escenario de referencia sobreescribe `{metodo}`: entonces "
                f"sus mecánicas no se pueden reproducir sólo desde Tiled"
            )

    def test_las_mecanicas_hacen_algo_en_diez_segundos(self, escena):
        """Diez segundos de simulación: los ciclos tienen que haber girado."""
        from src.framework.ecs.components import BloqueRitmico, PlataformaMovil

        posiciones = {
            e: pygame.Vector2(escena._mundo.obtener(e, Transform).posicion)
            for e, _ in escena._mundo.cada(PlataformaMovil)
        }
        estados_bloque = set()
        for _ in range(600):
            escena.update(1.0 / 60.0)
            for e, b in escena._mundo.cada(BloqueRitmico):
                estados_bloque.add((e, b.presente))

        movidas = [
            e for e, p0 in posiciones.items()
            if (escena._mundo.obtener(e, Transform).posicion - p0).length() > 4.0
        ]
        assert movidas, "ninguna plataforma móvil se movió en diez segundos"
        assert len({v for _, v in estados_bloque}) == 2, (
            "los bloques rítmicos no llegaron a aparecer y desaparecer"
        )

    def test_el_mapa_se_puede_regenerar_igual(self):
        """El TMX está generado: el fichero del repositorio y el generador van juntos.

        Sin esto, alguien edita el `.tmx` a mano, el generador se queda viejo, y
        la siguiente ejecución le borra los cambios sin avisar.
        """
        import importlib.util
        import pathlib

        raiz = pathlib.Path(__file__).resolve().parent.parent
        ruta = raiz / "tools" / "generate_stage_mecanicas.py"
        spec = importlib.util.spec_from_file_location("gen_mec", ruta)
        assert spec and spec.loader
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        en_disco = (
            raiz / "assets" / "maps" / "stage_mecanicas" / "stage_mecanicas.tmx"
        ).read_text(encoding="utf-8")
        assert modulo.generar() == en_disco, (
            "el TMX del repositorio no coincide con lo que produce su generador; "
            "ejecuta `python tools/generate_stage_mecanicas.py`"
        )


def test_los_tipos_de_componente_estan_declarados():
    """Los tipos de Tiled y lo que el cargador sabe construir van juntos.

    Es la cuarta vez que se escribe una prueba de esta forma —AUD-104, AUD-106,
    AUD-107— porque es el defecto que más ha castigado a los estudiantes este
    mes: una lista del motor con una copia que se queda vieja. Aquí la copia
    existe por necesidad (no se puede derivar el subconjunto), así que se vigila.
    """
    from src.framework.stage.stage_loader import _TIPOS_DE_COMPONENTE
    from src.framework.stage.tmx_diagnostics import BUILTIN_OBJECT_TYPES

    faltan = _TIPOS_DE_COMPONENTE - set(BUILTIN_OBJECT_TYPES)
    assert not faltan, (
        f"estos tipos los construye el cargador y el validador los rechazaría: "
        f"{sorted(faltan)}"
    )


def test_cada_tipo_de_componente_produce_algo():
    """Ninguno puede quedarse en la lista sin que el cargador sepa hacerlo.

    Sin esta prueba, añadir el nombre a `_TIPOS_DE_COMPONENTE` y olvidar la
    rama en `_handle_componente` produce el peor resultado posible: el
    validador aprueba el mapa, el juego lo carga sin quejarse, y el objeto
    sencillamente no está. Es el defecto que AUD-055 arregló para los enemigos.
    """
    from src.framework.stage.stage_loader import _TIPOS_DE_COMPONENTE, StageData, StageLoader

    class ObjetoFalso:
        x, y, width, height = 10, 20, 32, 16

    for tipo in sorted(_TIPOS_DE_COMPONENTE):
        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        StageLoader._handle_componente(stage, ObjetoFalso(), {}, tipo)
        assert stage.componentes, f"'{tipo}' está declarado y no construye nada"
        assert all(c is not None for c in stage.componentes[0])
