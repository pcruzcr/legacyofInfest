"""
La inundación que sube — AUD-135.

Por qué esta mecánica y no otra
================================
Es la más barata del catálogo pendiente —una `HazardZone` con el borde
superior móvil— y la que más cambia el ritmo de un escenario: convierte una
sala de plataformas en una persecución **sin añadir un solo enemigo**. El agua
no persigue: sube a velocidad constante. Por eso es justa —la amenaza es
predecible, el error es del jugador— y por eso funciona en un curso: el
estudiante la coloca con tres propiedades en Tiled y obtiene una escena que
parece diseñada por alguien con experiencia.

Lo que estas pruebas vigilan de verdad
---------------------------------------
Tres cosas, y las tres son fallos que se cometen al implementarla:

1. **El fondo no se mueve.** Si el rectángulo se desplaza en vez de crecer,
   deja el suelo limpio detrás y el jugador puede volver a bajar. La amenaza
   deja de serlo.
2. **El redondeo no se come la subida.** El borde va en `float` y el `rect` en
   `int`: si se redondea en cada fotograma, a 30 px/s y 60 fps el agua sube
   0,5 px por fotograma, se redondea a 0 y **no sube nunca**. Es un fallo que
   no aparece en una prueba con `dt` grande y arruina el juego real.
3. **Se reinicia al morir.** Sin `reiniciar()`, morir ahogado deja el agua
   arriba y el reintento es imposible. Es el fallo clásico de las mecánicas
   con estado: nadie las prueba en la segunda vida.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.stage_loader import HazardZone


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


def _zona(**kw) -> HazardZone:
    base = {"rect": pygame.Rect(0, 400, 200, 40), "sube": 60.0}
    base.update(kw)
    return HazardZone(**base)


class TestElAguaSube:
    def test_el_borde_superior_sube(self) -> None:
        hz = _zona()
        antes = hz.rect.top
        hz.avanzar(1.0)
        assert hz.rect.top == antes - 60

    def test_el_fondo_no_se_mueve(self) -> None:
        """Si se desplazara, dejaría el suelo limpio detrás."""
        hz = _zona()
        fondo = hz.rect.bottom
        for _ in range(30):
            hz.avanzar(1 / 60)
        assert hz.rect.bottom == fondo

    def test_la_zona_crece_en_vez_de_desplazarse(self) -> None:
        hz = _zona()
        alto = hz.rect.height
        hz.avanzar(0.5)
        assert hz.rect.height > alto

    def test_una_zona_fija_no_se_mueve(self) -> None:
        """`sube = 0` es el caso de siempre: pinchos, lava, un rectángulo."""
        hz = _zona(sube=0.0)
        copia = hz.rect.copy()
        hz.avanzar(5.0)
        assert hz.rect == copia

    def test_el_redondeo_no_se_come_la_subida(self) -> None:
        """30 px/s a 60 fps son 0,5 px por fotograma.

        Redondeando fotograma a fotograma, 0,5 se pierde y el agua no sube
        NUNCA. El borde se lleva en float justo por esto.
        """
        hz = _zona(sube=30.0)
        for _ in range(60):
            hz.avanzar(1 / 60)
        assert hz.rect.top == pytest.approx(400 - 30, abs=1), (
            "un segundo a 30 px/s tiene que subir 30 px; si sale 0, el borde "
            "se está redondeando en cada fotograma"
        )

    def test_un_dt_de_cero_no_hace_nada(self) -> None:
        hz = _zona()
        copia = hz.rect.copy()
        hz.avanzar(0.0)
        assert hz.rect == copia


class TestElTope:
    def test_el_agua_se_para_en_sube_hasta(self) -> None:
        hz = _zona(sube_hasta=380.0)
        hz.avanzar(10.0)
        assert hz.rect.top == 380

    def test_no_lo_pasa_ni_con_un_salto_de_tiempo_enorme(self) -> None:
        """Un `dt` grande —una pausa, un punto de interrupción— no debe
        mandar el agua fuera del mapa."""
        hz = _zona(sube_hasta=380.0)
        hz.avanzar(600.0)
        assert hz.rect.top == 380
        assert hz.rect.height > 0

    def test_sin_tope_sigue_subiendo(self) -> None:
        hz = _zona(sube_hasta=None)
        hz.avanzar(10.0)
        assert hz.rect.top == 400 - 600


class TestElArranquePorEvento:
    def test_sin_arranca_con_empieza_ya(self) -> None:
        assert _zona().activa is True

    def test_con_arranca_con_espera(self) -> None:
        hz = _zona(arranca_con="ABRIR_COMPUERTA")
        assert hz.activa is False
        hz.avanzar(5.0)
        assert hz.rect.top == 400, "el agua subió antes de que nadie la llamara"

    def test_arrancar_la_pone_en_marcha(self) -> None:
        hz = _zona(arranca_con="ABRIR_COMPUERTA")
        hz.arrancar()
        hz.avanzar(1.0)
        assert hz.rect.top == 340


class TestElReinicioAlMorir:
    def test_reiniciar_devuelve_el_agua_a_su_altura(self) -> None:
        hz = _zona()
        hz.avanzar(3.0)
        hz.reiniciar()
        assert hz.rect.top == 400
        assert hz.rect.height == 40
        assert hz.rect.bottom == 440

    def test_reiniciar_dos_veces_no_encoge_la_zona(self) -> None:
        """El fallo de contabilidad más fácil: recortar la altura cada vez."""
        hz = _zona()
        for _ in range(3):
            hz.avanzar(2.0)
            hz.reiniciar()
        assert hz.rect.height == 40

    def test_reiniciar_vuelve_a_dejarla_esperando_su_evento(self) -> None:
        hz = _zona(arranca_con="ABRIR")
        hz.arrancar()
        hz.avanzar(1.0)
        hz.reiniciar()
        assert hz.activa is False, (
            "tras morir, el agua arrancaría sola y el jugador no entendería "
            "por qué la segunda vida es más difícil que la primera"
        )


class TestLoQueLlegaDesdeTiled:
    """El estudiante escribe propiedades, no Python. Si el cargador no las
    lee, la mecánica existe y nadie puede usarla — que es la familia de fallos
    más cara de este proyecto (AUD-127, AUD-132)."""

    def _cargar(self, props: dict) -> HazardZone:
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("Obj", (), {"x": 0, "y": 400, "width": 200, "height": 40})()
        StageLoader._handle_hazard_zone(stage, obj, props)
        assert stage.hazard_zones, "el cargador descartó la zona"
        return stage.hazard_zones[0]

    def test_sube_llega_desde_el_tmx(self) -> None:
        assert self._cargar({"sube": 45.0}).sube == 45.0

    def test_sube_hasta_llega_desde_el_tmx(self) -> None:
        assert self._cargar({"sube": 45.0, "sube_hasta": 120.0}).sube_hasta == 120.0

    def test_arranca_con_llega_desde_el_tmx(self) -> None:
        hz = self._cargar({"sube": 45.0, "arranca_con": "COMPUERTA"})
        assert hz.arranca_con == "COMPUERTA"
        assert hz.activa is False

    def test_una_zona_de_siempre_sigue_funcionando(self) -> None:
        """Compatibilidad: los 15 escenarios entregados no declaran nada de
        esto y tienen que seguir comportándose igual."""
        hz = self._cargar({"damage": 1.0})
        assert hz.damage == 1.0
        assert hz.sube == 0.0
        assert hz.sube_de_verdad is False

    def test_un_sube_negativo_no_hunde_el_agua(self) -> None:
        """Dato hostil: `sube = -50` en Tiled haría bajar el rectángulo hasta
        salirse del mapa. Se recorta a 0 en la puerta de entrada."""
        assert self._cargar({"sube": -50.0}).sube == 0.0

    def test_un_sube_con_basura_no_rompe_la_carga(self) -> None:
        hz = self._cargar({"sube": "muy rápido"})
        assert hz.sube == 0.0

    def test_sube_hasta_vacio_significa_sin_tope(self) -> None:
        """Tiled guarda las propiedades vacías como cadena vacía, no como
        ausentes. Confundirlas pondría el tope en y=0."""
        assert self._cargar({"sube": 30.0, "sube_hasta": ""}).sube_hasta is None


class TestElSistemaLaSubeYAhoga:
    """La cadena real: `HazardSystem.update` sube el agua y hace daño.

    Que `avanzar()` funcione aislado no significa que nadie lo llame — es el
    fallo de este proyecto que más veces ha costado tiempo (AUD-127, AUD-132).
    """

    @pytest.fixture
    def montaje(self):
        from src.engine.core.event_bus import EventBus
        from src.framework.stage.hazard_system import HazardSystem

        class _Contexto:
            def __init__(self) -> None:
                self.event_bus = EventBus()
                self.scene_manager = None

        class _Jugador:
            def __init__(self) -> None:
                self.rect = pygame.Rect(100, 300, 20, 30)
                self.danos: list[float] = []

            def apply_damage(self, cantidad, origen=None) -> None:
                self.danos.append(cantidad)

        class _Escenario:
            def __init__(self) -> None:
                self.message_triggers: list = []
                self.hazard_zones: list = []
                self.death_pits: list = []

        ctx = _Contexto()
        return HazardSystem(ctx), _Jugador(), _Escenario(), ctx

    def test_el_sistema_sube_el_agua(self, montaje) -> None:
        sistema, jugador, escenario, _ctx = montaje
        hz = HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=60.0)
        escenario.hazard_zones.append(hz)
        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 340, (
            "el agua sólo sube si alguien llama a avanzar(); aislada funciona "
            "y en el juego no pasa nada"
        )

    def test_el_agua_alcanza_al_jugador_y_le_hace_dano(self, montaje) -> None:
        """La prueba que de verdad importa: subir hasta tocarlo y doler."""
        sistema, jugador, escenario, _ctx = montaje
        jugador.rect.topleft = (100, 300)          # pies en y=330
        escenario.hazard_zones.append(
            HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=100.0),
        )
        for _ in range(60):                        # un segundo a 60 fps
            sistema.update(1 / 60, jugador, escenario)
        assert jugador.danos, "el agua pasó por encima del jugador sin tocarlo"

    def test_antes_de_llegar_no_duele(self, montaje) -> None:
        sistema, jugador, escenario, _ctx = montaje
        jugador.rect.topleft = (100, 100)
        escenario.hazard_zones.append(
            HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=10.0),
        )
        for _ in range(30):
            sistema.update(1 / 60, jugador, escenario)
        assert jugador.danos == [], "hizo daño desde lejos"

    def test_un_disparador_del_mapa_la_pone_en_marcha(self, montaje) -> None:
        """El circuito completo: interruptor en Tiled → bus → agua.

        Es el mismo receptor que faltaba en AUD-132 con las puertas.
        """
        from src.framework.stage.interactable_system import EVENTO_DISPARADOR

        sistema, jugador, escenario, ctx = montaje
        hz = HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=60.0,
                        arranca_con="ROMPER_LA_PRESA")
        escenario.hazard_zones.append(hz)

        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 400, "subió sin que nadie rompiera la presa"

        ctx.event_bus.emit(EVENTO_DISPARADOR, nombre="ROMPER_LA_PRESA")
        ctx.event_bus.dispatch()
        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 340

    def test_un_evento_que_suena_antes_de_tiempo_no_se_pierde(self, montaje) -> None:
        """El interruptor puede sonar antes de que el escenario mire la zona.

        Sin memoria de eventos, el agua no arrancaría nunca y el interruptor
        parecería roto — y el estudiante buscaría el fallo en su mapa.
        """
        from src.framework.stage.interactable_system import EVENTO_DISPARADOR

        sistema, jugador, escenario, ctx = montaje
        ctx.event_bus.emit(EVENTO_DISPARADOR, nombre="ROMPER_LA_PRESA")
        ctx.event_bus.dispatch()
        hz = HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=60.0,
                        arranca_con="ROMPER_LA_PRESA")
        escenario.hazard_zones.append(hz)
        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 340

    def test_otro_evento_no_la_arranca(self, montaje) -> None:
        from src.framework.stage.interactable_system import EVENTO_DISPARADOR

        sistema, jugador, escenario, ctx = montaje
        hz = HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=60.0,
                        arranca_con="ROMPER_LA_PRESA")
        escenario.hazard_zones.append(hz)
        ctx.event_bus.emit(EVENTO_DISPARADOR, nombre="ABRIR_LA_PUERTA")
        ctx.event_bus.dispatch()
        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 400

    def test_reset_devuelve_el_agua_y_olvida_los_eventos(self, montaje) -> None:
        from src.framework.stage.interactable_system import EVENTO_DISPARADOR

        sistema, jugador, escenario, ctx = montaje
        hz = HazardZone(rect=pygame.Rect(0, 400, 400, 40), sube=60.0,
                        arranca_con="ROMPER_LA_PRESA")
        escenario.hazard_zones.append(hz)
        ctx.event_bus.emit(EVENTO_DISPARADOR, nombre="ROMPER_LA_PRESA")
        ctx.event_bus.dispatch()
        sistema.update(2.0, jugador, escenario)

        sistema.reset(escenario)
        assert hz.rect.top == 400
        sistema.update(1.0, jugador, escenario)
        assert hz.rect.top == 400, (
            "tras reiniciar, el agua arranca sola: la segunda vida sería más "
            "difícil que la primera sin que el jugador entienda por qué"
        )

    def test_reset_sin_escenario_sigue_valiendo(self, montaje) -> None:
        """Compatibilidad: había código llamando `reset()` sin argumentos."""
        sistema, _jugador, _escenario, _ctx = montaje
        sistema.reset()          # no debe lanzar


class TestElAguaSeVe:
    """Una zona de daño que no se ve es una trampa.

    Las fijas se dibujan con tiles —el diseñador pinta pinchos o lava—, pero
    los tiles no suben. Si el motor no dibuja la inundación, el jugador recibe
    daño de la nada y lee un fallo donde hay una mecánica.
    """

    @pytest.fixture
    def sistema(self):
        from src.framework.stage.drawing_system import DrawingSystem

        return DrawingSystem()

    def _escenario(self, *zonas):
        return type("E", (), {"hazard_zones": list(zonas)})()

    def test_la_inundacion_se_dibuja(self, sistema) -> None:
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), sube=30.0),
        )
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 0))
        assert lienzo.get_at((100, 150))[:3] != (0, 0, 0), (
            "el agua no se ve: el jugador recibiría daño de un rectángulo "
            "invisible que además se mueve"
        )

    def test_una_zona_fija_no_la_dibuja_este_metodo(self, sistema) -> None:
        """`_draw_inundaciones` es sólo del agua: las fijas las pinta
        `_draw_zonas_de_dano`, con otro color y otro pulso.

        AUD-228: aquí ponía que «los 15 escenarios entregados tienen zonas fijas
        pintadas con tiles, dibujarlas encima las taparía». Se comprobó y era
        falso: en todo el proyecto hay **dos** `HazardZone` fijas —`stage0` y
        `stage3_3_el_patio`— y ninguna de las dos tiene arte de peligro debajo.
        La suposición nunca se midió, y mientras tanto el nivel que copian los
        estudiantes hacía daño desde un rectángulo invisible.
        """
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(HazardZone(rect=pygame.Rect(0, 100, 200, 100)))
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 0))
        assert lienzo.get_at((100, 150))[:3] == (0, 0, 0)

    def test_se_sigue_viendo_el_nivel_debajo(self, sistema) -> None:
        """El agua es translúcida a propósito: el jugador tiene que ver las
        plataformas sumergidas para planear la subida."""
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((200, 30, 30))          # una plataforma roja bien visible
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), sube=30.0),
        )
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 0))
        r, g, b = lienzo.get_at((100, 150))[:3]
        assert r > g and r > b, "el agua es opaca y tapa el nivel"

    def test_fuera_de_camara_no_dibuja_nada(self, sistema) -> None:
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), sube=30.0),
        )
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 5000))
        assert lienzo.get_at((100, 150))[:3] == (0, 0, 0)

    def test_dibujar_no_asigna_una_superficie_por_fotograma(self, sistema) -> None:
        """AUD-023: el lienzo del agua se cachea. Repintarlo cada fotograma
        sería una asignación por fotograma, justo lo que se quitó entonces."""
        lienzo = pygame.Surface((200, 200))
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), sube=30.0),
        )
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 0))
        primero = sistema._agua_cache
        sistema._draw_inundaciones(lienzo, escenario, pygame.Vector2(0, 0))
        assert sistema._agua_cache is primero


class TestLasZonasFijasTambienSeVen:
    """AUD-228 — «una zona de daño que no se ve es una trampa», y esa regla el
    motor sólo se la aplicaba al agua.

    Las fijas no se pintaban nunca. El contrato implícito era que el diseñador
    dibujara pinchos en las baldosas, pero no estaba escrito en ningún sitio y
    no se cumplía: los dos únicos mapas del proyecto con una `HazardZone` fija
    son `stage0` —el que los estudiantes copian— y `stage3_3_el_patio`, y
    ninguno tenía arte debajo.
    """

    @pytest.fixture
    def sistema(self):
        from src.framework.stage.drawing_system import DrawingSystem

        return DrawingSystem()

    def _escenario(self, *zonas):
        return type("E", (), {"hazard_zones": list(zonas)})()

    def test_una_zona_fija_se_ve(self, sistema) -> None:
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(HazardZone(rect=pygame.Rect(0, 100, 200, 100)))
        sistema._draw_zonas_de_dano(lienzo, escenario, pygame.Vector2(0, 0))
        assert lienzo.get_at((100, 150))[:3] != (0, 0, 0), (
            "la zona de daño sigue siendo invisible: el jugador pierde salud "
            "sin nada en pantalla que lo explique"
        )

    def test_avisa_en_rojo_y_no_en_el_azul_del_agua(self, sistema) -> None:
        """Son dos mecánicas distintas y tienen que separarse de un vistazo."""
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(HazardZone(rect=pygame.Rect(0, 100, 200, 100)))
        sistema._draw_zonas_de_dano(lienzo, escenario, pygame.Vector2(0, 0))
        r, g, b = lienzo.get_at((100, 150))[:3]
        assert r > b, f"el aviso de daño sale azulado ({r},{g},{b})"

    def test_se_sigue_viendo_el_nivel_debajo(self, sistema) -> None:
        """Es un aviso, no una capa de pintura: el suelo tiene que leerse."""
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((30, 200, 40))          # una plataforma verde bien visible
        escenario = self._escenario(HazardZone(rect=pygame.Rect(0, 100, 200, 100)))
        sistema._draw_zonas_de_dano(lienzo, escenario, pygame.Vector2(0, 0))
        _r, g, _b = lienzo.get_at((100, 150))[:3]
        assert g > 90, "el aviso es opaco y tapa el nivel"

    def test_el_agua_no_la_pinta_este_metodo(self, sistema) -> None:
        """La que sube ya la dibuja `_draw_inundaciones`. Pintarla dos veces la
        dejaría del color equivocado."""
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), sube=30.0),
        )
        sistema._draw_zonas_de_dano(lienzo, escenario, pygame.Vector2(0, 0))
        assert lienzo.get_at((100, 150))[:3] == (0, 0, 0)

    def test_un_mapa_con_su_propio_arte_puede_apagarlo(self, sistema) -> None:
        """`visible=false` en el TMX, para el que sí pintó sus pinchos."""
        lienzo = pygame.Surface((200, 200))
        lienzo.fill((0, 0, 0))
        escenario = self._escenario(
            HazardZone(rect=pygame.Rect(0, 100, 200, 100), visible=False),
        )
        sistema._draw_zonas_de_dano(lienzo, escenario, pygame.Vector2(0, 0))
        assert lienzo.get_at((100, 150))[:3] == (0, 0, 0)

    def test_tiled_escribe_los_booleanos_como_texto(self) -> None:
        """`"false"` es una cadena, y una cadena no vacía es verdadera en
        Python: leerla sin convertir dejaría `visible=false` sin efecto."""
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("O", (), {"x": 0, "y": 0, "width": 32, "height": 16})()
        StageLoader._handle_hazard_zone(stage, obj, {"visible": "false"})
        assert stage.hazard_zones[0].visible is False

        stage2 = StageData(map_layer=None)  # type: ignore[arg-type]
        StageLoader._handle_hazard_zone(stage2, obj, {})
        assert stage2.hazard_zones[0].visible is True, (
            "sin la propiedad, una zona de daño se ve: es el valor por defecto "
            "que evita el daño invisible"
        )
