"""
Cutscenes: acciones nuevas, guiones desde Tiled y escenas que no bloquean.

AUD-136 (D3)
============
El sistema de escenas estaba escrito y probado, y **nadie lo ejecutaba**. El
único sitio del proyecto que reproducía una cutscene era `Stage0`, a mano, y
su forma de saltarla era apagar el guion desde fuera:

.. code-block:: python

    if im.is_action_just_pressed(Action.CANCEL):
        self._cutscene._active = False
        self._cutscene = None

Eso no es saltar: es tirar la escena a medias. Si el guion movía al jugador
hasta la puerta y abría la puerta, quien pulsaba CANCEL se quedaba donde
estaba, delante de una puerta cerrada. Y era la novena vez este mes que
aparece el mismo patrón —código correcto que no llega al jugador—.

Las tres cosas que estas pruebas defienden
-------------------------------------------
1. **Saltar ejecuta el final.** Es la mitad que casi nadie implementa, y sin
   ella un botón de saltar rompe partidas.
2. **Se puede escribir desde el mapa.** Si hace falta Python, las escenas son
   cosa del profesor y el estudiante no cuenta nada.
3. **No todo bloquea.** Bloquear siempre convierte cada detalle narrativo en
   una interrupción, y a la tercera el jugador se las salta todas sin leer.
"""
from __future__ import annotations

import pygame
import pytest

from src.framework.stage.cutscene_guion import ContextoDeGuion, analizar_guion
from src.framework.stage.cutscene_system import (
    AccionParalela,
    CutsceneScript,
    EventoAction,
    MoverEntidadAction,
    WaitAction,
)


@pytest.fixture(autouse=True)
def _video():
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((320, 240))


class _Bus:
    def __init__(self) -> None:
        self.emitidos: list[str] = []
        self._subs: dict[str, list] = {}

    def emit(self, evento: str, **datos) -> None:
        self.emitidos.append(evento)
        for cb in self._subs.get(evento, []):
            cb(**datos)

    def subscribe(self, evento: str, cb) -> None:
        self._subs.setdefault(evento, []).append(cb)

    def unsubscribe(self, *_a, **_k) -> None:
        pass


class _Actor:
    def __init__(self, x: float = 0.0, y: float = 0.0) -> None:
        self.position = pygame.Vector2(x, y)
        self.rect = pygame.Rect(int(x), int(y), 16, 24)
        self.facing_right = True


class _Camara:
    def __init__(self) -> None:
        self.offset = pygame.Vector2(0, 0)
        self.sacudidas: list[tuple[float, float]] = []

    def shake(self, duracion: float, intensidad: float) -> None:
        self.sacudidas.append((duracion, intensidad))


def _contexto(**kw) -> ContextoDeGuion:
    base = {"camara": _Camara(), "jugador": _Actor(), "bus": _Bus()}
    base.update(kw)
    return ContextoDeGuion(**base)


def _correr(guion: CutsceneScript, segundos: float = 5.0, paso: float = 1 / 60) -> None:
    guion.start()
    t = 0.0
    while guion.active and t < segundos:
        guion.update(paso)
        t += paso


class TestSaltarEjecutaElFinal:
    """La mitad de «saltar» que casi nadie implementa.

    Saltar no es cancelar: es ir al final. Un botón de saltar que deja el
    mundo a medias rompe la partida de quien ya se sabe la escena — que es
    justamente quien lo pulsa.
    """

    def test_saltar_deja_a_la_entidad_en_su_destino(self) -> None:
        actor = _Actor(0, 100)
        guion = CutsceneScript([MoverEntidadAction(actor, 400, None, 3.0)])
        guion.start()
        guion.update(0.1)
        guion.saltar()
        assert actor.position.x == 400, (
            "saltar dejó al personaje a medio camino: si la escena lo llevaba "
            "hasta la puerta, quien salta se queda fuera"
        )

    def test_saltar_emite_los_eventos_que_quedaban(self) -> None:
        bus = _Bus()
        guion = CutsceneScript([
            WaitAction(5.0),
            EventoAction(bus, "ABRIR_COMPUERTA"),
        ])
        guion.start()
        guion.update(0.1)
        guion.saltar()
        assert "ABRIR_COMPUERTA" in bus.emitidos, (
            "saltar se comió el evento que abría la puerta: el nivel se queda "
            "sin salida y el jugador no sabe por qué"
        )

    def test_saltar_termina_el_guion(self) -> None:
        guion = CutsceneScript([WaitAction(10.0)])
        guion.start()
        guion.saltar()
        assert guion.active is False

    def test_saltar_avisa_a_quien_esperaba_el_final(self) -> None:
        """El `callback` es como el escenario recupera el control."""
        llamado = []
        guion = CutsceneScript([WaitAction(10.0)])
        guion.start(lambda: llamado.append(True))
        guion.saltar()
        assert llamado == [True]

    def test_saltar_dos_veces_no_repite_el_final(self) -> None:
        bus = _Bus()
        guion = CutsceneScript([EventoAction(bus, "UNA_VEZ")])
        guion.start()
        guion.saltar()
        guion.saltar()
        assert bus.emitidos.count("UNA_VEZ") <= 1

    def test_un_sonido_saltado_no_suena(self) -> None:
        """Un efecto que se dispara cuando ya no se ve lo que lo causaba es
        ruido. Los eventos de mundo sí; los sonidos no."""
        from src.framework.stage.cutscene_system import SonidoAction

        bus = _Bus()
        guion = CutsceneScript([WaitAction(5.0), SonidoAction(bus, "SFX_TRUENO")])
        guion.start()
        guion.saltar()
        assert "SFX_TRUENO" not in bus.emitidos


class TestLasAccionesNuevas:
    def test_mover_lleva_a_la_entidad_al_destino(self) -> None:
        actor = _Actor(0, 100)
        _correr(CutsceneScript([MoverEntidadAction(actor, 200, 50, 0.5)]))
        assert (actor.position.x, actor.position.y) == (200, 50)

    def test_mover_arrastra_el_rect(self) -> None:
        """Si el `rect` no se mueve, el personaje se dibuja donde estaba y la
        cámara sigue a un fantasma."""
        actor = _Actor(0, 100)
        _correr(CutsceneScript([MoverEntidadAction(actor, 200, 50, 0.5)]))
        assert actor.rect.center == (200, 50)

    def test_mover_gira_a_quien_camina(self) -> None:
        """Cruzar la sala de espaldas se lee como un fallo de animación."""
        actor = _Actor(300, 100)
        actor.facing_right = True
        _correr(CutsceneScript([MoverEntidadAction(actor, 50, None, 0.3)]))
        assert actor.facing_right is False

    def test_mover_con_y_nula_conserva_la_altura(self) -> None:
        actor = _Actor(0, 137)
        _correr(CutsceneScript([MoverEntidadAction(actor, 200, None, 0.3)]))
        assert actor.position.y == 137

    def test_evento_emite_al_empezar(self) -> None:
        bus = _Bus()
        _correr(CutsceneScript([EventoAction(bus, "ALGO")]))
        assert bus.emitidos == ["ALGO"]

    def test_temblor_pide_la_sacudida_a_la_camara(self) -> None:
        from src.framework.stage.cutscene_system import TemblorAction

        cam = _Camara()
        _correr(CutsceneScript([TemblorAction(cam, 0.4, 6.0)]))
        assert cam.sacudidas == [(0.4, 6.0)]

    def test_temblor_sin_camara_no_revienta(self) -> None:
        from src.framework.stage.cutscene_system import TemblorAction

        _correr(CutsceneScript([TemblorAction(None, 0.4, 6.0)]))

    def test_esperar_evento_sigue_cuando_llega(self) -> None:
        from src.framework.stage.cutscene_system import EsperarEventoAction

        bus = _Bus()
        guion = CutsceneScript([EsperarEventoAction(bus, "PUERTA", tope=10.0)])
        guion.start()
        guion.update(0.1)
        assert guion.active
        bus.emit("PUERTA")
        guion.update(0.1)
        assert not guion.active

    def test_esperar_evento_tiene_tope(self) -> None:
        """Una escena que espera para siempre a un evento que no llega deja el
        juego colgado sin control. Eso no es un fallo del guion: es del motor
        por permitirlo."""
        from src.framework.stage.cutscene_system import EsperarEventoAction

        guion = CutsceneScript([EsperarEventoAction(_Bus(), "NUNCA", tope=1.0)])
        _correr(guion, segundos=3.0)
        assert not guion.active


class TestVariasCosasALaVez:
    """Todo lo que hace que una escena parezca escrita por alguien pasa a la
    vez: la cámara viaja MIENTRAS el personaje camina."""

    def test_las_dos_acciones_avanzan_juntas(self) -> None:
        uno, dos = _Actor(0, 0), _Actor(0, 100)
        _correr(CutsceneScript([AccionParalela([
            MoverEntidadAction(uno, 100, None, 0.4),
            MoverEntidadAction(dos, 200, None, 0.4),
        ])]))
        assert (uno.position.x, dos.position.x) == (100, 200)

    def test_termina_cuando_acaba_la_mas_larga(self) -> None:
        guion = CutsceneScript([AccionParalela([
            WaitAction(0.1), WaitAction(1.0),
        ])])
        guion.start()
        guion.update(0.2)
        assert guion.active, "terminó al acabar la más corta"

    def test_saltar_un_paralelo_termina_todas(self) -> None:
        uno, dos = _Actor(0, 0), _Actor(0, 100)
        guion = CutsceneScript([AccionParalela([
            MoverEntidadAction(uno, 100, None, 3.0),
            MoverEntidadAction(dos, 200, None, 3.0),
        ])])
        guion.start()
        guion.update(0.1)
        guion.saltar()
        assert (uno.position.x, dos.position.x) == (100, 200)


class TestElGuionEnTexto:
    """Lo que escribe el estudiante en Tiled."""

    def test_una_orden_por_linea(self) -> None:
        guion, errores = analizar_guion(
            "esperar 0.5\nesperar 0.5", _contexto())
        assert errores == []
        assert len(guion._actions) == 2

    def test_los_comentarios_y_las_lineas_vacias_se_ignoran(self) -> None:
        guion, errores = analizar_guion(
            "# la intro\n\nesperar 0.5   # medio segundo\n", _contexto())
        assert errores == []
        assert len(guion._actions) == 1

    def test_el_mas_junta_la_linea_con_la_anterior(self) -> None:
        guion, _e = analizar_guion(
            "camara 100 50 1.0\n+ mover jugador 200 . 1.0", _contexto())
        assert len(guion._actions) == 1
        assert isinstance(guion._actions[0], AccionParalela)

    def test_tres_en_paralelo_siguen_siendo_una_accion(self) -> None:
        guion, _e = analizar_guion(
            "esperar 1\n+ esperar 1\n+ esperar 1", _contexto())
        assert len(guion._actions) == 1

    def test_mover_encuentra_al_jugador_por_su_nombre(self) -> None:
        ctx = _contexto()
        guion, errores = analizar_guion("mover jugador 300 . 1.0", ctx)
        assert errores == []
        _correr(guion)
        assert ctx.jugador.position.x == 300

    def test_mover_encuentra_una_entidad_del_mapa(self) -> None:
        guardia = _Actor(10, 10)
        ctx = _contexto(entidades={"Guardia1": guardia})
        _correr(analizar_guion("mover Guardia1 90 . 0.3", ctx)[0])
        assert guardia.position.x == 90

    def test_el_punto_significa_no_toques_esta_coordenada(self) -> None:
        ctx = _contexto()
        ctx.jugador.position.y = 250
        _correr(analizar_guion("mover jugador 300 . 0.3", ctx)[0])
        assert ctx.jugador.position.y == 250

    def test_texto_con_hablante(self) -> None:
        from src.framework.stage.cutscene_system import DialogueAction

        guion, errores = analizar_guion(
            "texto Eco: Has llegado tarde.", _contexto())
        assert errores == []
        accion = guion._actions[0]
        assert isinstance(accion, DialogueAction)
        assert accion._speaker == "Eco"
        assert accion._text == "Has llegado tarde."

    def test_evento_desde_el_guion_llega_al_bus(self) -> None:
        ctx = _contexto()
        _correr(analizar_guion("evento ABRIR_COMPUERTA", ctx)[0])
        assert "ABRIR_COMPUERTA" in ctx.bus.emitidos

    def test_temblor_admite_valores_por_defecto(self) -> None:
        ctx = _contexto()
        guion, errores = analizar_guion("temblor", ctx)
        assert errores == []
        _correr(guion)
        assert ctx.camara.sacudidas


class TestUnGuionMalEscritoNoRompeLaPartida:
    """Un guion es contenido, no código.

    Fallar en caliente por una errata y dejar al jugador sin control es peor
    que ignorar la línea. El estudiante se entera por la lista de errores y
    por el registro, no por una partida rota.
    """

    def test_una_orden_desconocida_se_anota_y_se_sigue(self) -> None:
        guion, errores = analizar_guion(
            "bailar mucho\nesperar 0.5", _contexto())
        assert len(errores) == 1
        assert "bailar" in errores[0]
        assert len(guion._actions) == 1, "la línea buena también se perdió"

    def test_el_error_dice_en_que_linea(self) -> None:
        _g, errores = analizar_guion("esperar 0.5\nbailar", _contexto())
        assert "línea 2" in errores[0]

    def test_faltan_argumentos(self) -> None:
        _g, errores = analizar_guion("camara 100", _contexto())
        assert errores and "camara" in errores[0]

    def test_un_numero_que_no_es_un_numero(self) -> None:
        _g, errores = analizar_guion("esperar pronto", _contexto())
        assert errores

    def test_mover_a_alguien_que_no_existe(self) -> None:
        _g, errores = analizar_guion("mover Fantasma 10 . 1", _contexto())
        assert errores and "Fantasma" in errores[0]

    def test_un_guion_vacio_no_lanza(self) -> None:
        guion, errores = analizar_guion("", _contexto())
        assert errores == []
        assert guion._actions == []

    def test_un_guion_nulo_no_lanza(self) -> None:
        guion, _e = analizar_guion(None, _contexto())  # type: ignore[arg-type]
        assert guion._actions == []


class TestElCutsceneDeTiled:
    """Lo que el estudiante pone en el mapa tiene que llegar al motor.

    Es la comprobación que faltó en AUD-127: el sistema de diálogo estaba
    entero y era inalcanzable porque el campo que lo nombraba no existía en el
    cargador. Aquí se mira el camino, no la clase.
    """

    def _cargar(self, props: dict, ancho: int = 64, alto: int = 64):
        from src.framework.stage.stage_loader import StageData, StageLoader

        stage = StageData(map_layer=None)  # type: ignore[arg-type]
        obj = type("Obj", (), {"x": 100, "y": 200, "width": ancho, "height": alto})()
        StageLoader._handle_cutscene(stage, obj, props)
        return stage.escenas

    def test_el_guion_llega_desde_el_tmx(self) -> None:
        escenas = self._cargar({"guion": "esperar 1"})
        assert escenas and escenas[0].guion == "esperar 1"

    def test_una_escena_sin_guion_se_descarta(self) -> None:
        """Una escena vacía quitaría el mando un instante para no hacer nada."""
        assert self._cargar({"guion": "   "}) == []

    def test_bloquea_por_defecto(self) -> None:
        assert self._cargar({"guion": "esperar 1"})[0].bloquea is True

    def test_se_puede_pedir_que_no_bloquee(self) -> None:
        escena = self._cargar({"guion": "esperar 1", "bloquea": "false"})[0]
        assert escena.bloquea is False

    def test_un_punto_en_tiled_se_dispara_al_empezar(self) -> None:
        escena = self._cargar({"guion": "esperar 1"}, ancho=0, alto=0)[0]
        assert escena.al_empezar is True

    def test_un_rectangulo_se_dispara_al_entrar(self) -> None:
        assert self._cargar({"guion": "esperar 1"})[0].al_empezar is False

    def test_cutscene_es_un_tipo_conocido_del_validador(self) -> None:
        """Si no está en la lista, el validador le dice al estudiante que su
        objeto es de un tipo desconocido — y el objeto funciona."""
        from src.framework.stage.tmx_diagnostics import known_object_types

        assert "Cutscene" in known_object_types(())


class TestElDirector:
    """Quien las reproduce. Antes no existía: sólo stage 0 lo hacía a mano."""

    def _escena(self, guion: str = "esperar 1", **kw):
        from src.framework.stage.stage_loader import EscenaGuionizada

        base = {"rect": pygame.Rect(300, 0, 32, 240), "guion": guion}
        base.update(kw)
        return EscenaGuionizada(**base)

    def _director(self, escenas, ctx=None, vistas=None):
        from src.framework.stage.cutscene_director import CutsceneDirector

        ctx = ctx or _contexto()
        return CutsceneDirector(ctx, escenas, bus=ctx.bus, vistas=vistas), ctx

    def test_una_escena_de_punto_arranca_al_cargar(self) -> None:
        escena = self._escena(rect=pygame.Rect(50, 50, 0, 0))
        director, _ctx = self._director([escena])
        assert director.bloquea is True

    def test_una_escena_de_zona_espera_al_jugador(self) -> None:
        director, _ctx = self._director([self._escena()])
        director.update(0.1, pygame.Rect(0, 0, 16, 24))
        assert director.bloquea is False
        director.update(0.1, pygame.Rect(300, 0, 16, 24))
        assert director.bloquea is True

    def test_una_escena_que_no_bloquea_deja_jugar(self) -> None:
        """El detalle narrativo que no interrumpe: un compañero que grita
        desde una cornisa mientras se sigue corriendo."""
        director, _ctx = self._director([self._escena(bloquea=False)])
        director.update(0.1, pygame.Rect(300, 0, 16, 24))
        assert director.bloquea is False

    def test_no_se_repite_al_volver_a_pisar_la_zona(self) -> None:
        escena = self._escena("esperar 0.05")
        director, _ctx = self._director([escena])
        dentro = pygame.Rect(300, 0, 16, 24)
        for _ in range(20):
            director.update(0.02, dentro)
        assert director.bloquea is False
        director.update(0.02, dentro)
        assert director.bloquea is False, "la escena se repite en bucle"

    def test_la_memoria_sobrevive_a_la_muerte(self) -> None:
        """Morir recarga el TMX y crea objetos nuevos. Si la memoria viviera
        en ellos, la intro se repetiría en cada intento."""
        vistas: set[str] = set()
        primera = self._escena(rect=pygame.Rect(50, 50, 0, 0))
        director, _ctx = self._director([primera], vistas=vistas)
        assert director.bloquea is True

        # El mapa se recarga: mismo sitio, mismo guion, objeto nuevo.
        segunda = self._escena(rect=pygame.Rect(50, 50, 0, 0))
        director2, _ctx2 = self._director([segunda], vistas=vistas)
        assert director2.bloquea is False, (
            "la introducción se reproduce otra vez tras morir"
        )

    def test_un_evento_del_mapa_arranca_la_escena(self) -> None:
        escena = self._escena(arranca_con="LLEGA_EL_JEFE")
        director, ctx = self._director([escena])
        jugador = pygame.Rect(0, 0, 16, 24)
        director.update(0.1, jugador)
        assert director.bloquea is False
        ctx.bus.emit("INTERACT_TRIGGER_FIRED", nombre="LLEGA_EL_JEFE")
        director.update(0.1, jugador)
        assert director.bloquea is True

    def test_saltar_termina_lo_que_esta_en_curso(self) -> None:
        escena = self._escena("esperar 30", rect=pygame.Rect(50, 50, 0, 0))
        director, _ctx = self._director([escena])
        director.update(0.1, pygame.Rect(0, 0, 16, 24), saltar=True)
        assert director.bloquea is False

    def test_una_escena_no_saltable_no_se_salta(self) -> None:
        escena = self._escena("esperar 30", rect=pygame.Rect(50, 50, 0, 0),
                              saltable=False)
        director, _ctx = self._director([escena])
        director.update(0.1, pygame.Rect(0, 0, 16, 24), saltar=True)
        assert director.bloquea is True

    def test_los_errores_de_guion_quedan_registrados(self) -> None:
        escena = self._escena("bailar mucho", rect=pygame.Rect(50, 50, 0, 0))
        director, _ctx = self._director([escena])
        assert director.errores

    def test_dibujar_sin_escenas_no_lanza(self) -> None:
        director, _ctx = self._director([])
        director.draw(pygame.Surface((320, 240)))


class TestStage0YaNoLoHaceAMano:
    """El escenario de referencia del curso es el ejemplo que copian todos.

    Mientras stage 0 apagase un guion tocando `_active` desde fuera, cada
    estudiante que mirase cómo se hace una escena copiaría ese defecto.
    """

    def _fuente(self) -> str:
        import inspect

        from src.stages.stage0.stage0 import Stage0

        import src.stages.stage0.stage0 as modulo
        return inspect.getsource(modulo) + inspect.getsource(Stage0)

    def test_no_toca_el_atributo_privado_del_guion(self) -> None:
        assert "_cutscene._active" not in self._fuente(), (
            "stage 0 vuelve a apagar la escena a medias en vez de saltarla"
        )

    def test_su_intro_es_un_guion_de_texto(self) -> None:
        from src.stages.stage0.stage0 import Stage0

        assert "camara" in Stage0.GUION_DE_INTRO

    def test_la_intro_de_stage0_se_entiende(self) -> None:
        """Que el guion exista no basta: tiene que analizarse sin errores."""
        from src.stages.stage0.stage0 import Stage0

        _guion, errores = analizar_guion(Stage0.GUION_DE_INTRO, _contexto())
        assert errores == []


class TestLasBandas:
    """Las bandas negras son la señal de «esto no lo controlas tú».

    Sólo tienen sentido en una escena que bloquea; en una que no bloquea
    serían un marco que estorba mientras se juega.
    """

    def test_una_escena_que_bloquea_pinta_bandas(self) -> None:
        guion = CutsceneScript([WaitAction(1.0)], bloquea=True, bandas=True)
        guion.start()
        for _ in range(20):
            guion.update(1 / 60)
        lienzo = pygame.Surface((320, 240))
        lienzo.fill((90, 90, 90))
        guion.draw(lienzo)
        assert lienzo.get_at((160, 2))[:3] == (0, 0, 0)
        assert lienzo.get_at((160, 238))[:3] == (0, 0, 0)

    def test_sin_bandas_no_se_pinta_nada(self) -> None:
        guion = CutsceneScript([WaitAction(1.0)], bandas=False)
        guion.start()
        guion.update(0.1)
        lienzo = pygame.Surface((320, 240))
        lienzo.fill((90, 90, 90))
        guion.draw(lienzo)
        assert lienzo.get_at((160, 2))[:3] == (90, 90, 90)

    def test_las_bandas_se_recogen_al_acabar(self) -> None:
        """Si se quedaran puestas, el juego seguiría con el marco de una
        escena que ya terminó."""
        guion = CutsceneScript([WaitAction(0.1)], bandas=True)
        guion.start()
        for _ in range(120):
            guion.update(1 / 60)
        assert guion.terminada is True
        assert guion._alto_banda == 0.0
