"""
El temario está separado por unidades, se desbloquea al aprobar, y se guarda.

AUD-095
=======
Lo que se pidió, literalmente: «que apareciera información técnica matemática
y fuera separado unidad por unidad, que se activaran cuando cada una se
completara». Antes de este cambio no existía ninguna de las tres cosas:

- Las diez demos estaban abiertas desde el primer minuto.
- No había explicación matemática en ninguna parte.
- El cuestionario existía pero no registraba nada: se contestaba y se
  olvidaba al salir de la escena.

Estas pruebas miran las tres.
"""
from __future__ import annotations

import json

import pytest

from src.framework.academic.curriculum import (
    PLAN,
    ids_de_unidades,
    siguiente_unidad,
    unidad,
    unidad_de_escena,
)
from src.framework.academic.progress import (
    ACIERTOS_PARA_APROBAR,
    PREGUNTAS_POR_UNIDAD,
    ProgresoAcademico,
    es_correo_valido,
    nombre_de_fichero,
)
from src.framework.academic.sesion import SesionAcademica


class TestElTemarioEstaCompleto:
    """El contenido, no el mecanismo: que haya de verdad teoría y preguntas."""

    def test_hay_unidades(self):
        assert len(PLAN) >= 10

    @pytest.mark.parametrize("u", PLAN, ids=[u.id for u in PLAN])
    def test_cada_unidad_tiene_cinco_preguntas(self, u):
        assert len(u.preguntas) == PREGUNTAS_POR_UNIDAD, (
            f"{u.id} tiene {len(u.preguntas)} preguntas; el examen es de "
            f"{PREGUNTAS_POR_UNIDAD}, y con menos el umbral de aprobado "
            f"({ACIERTOS_PARA_APROBAR}) deja de significar lo que dice."
        )

    @pytest.mark.parametrize("u", PLAN, ids=[u.id for u in PLAN])
    def test_cada_unidad_explica_sus_matematicas(self, u):
        assert len(u.teoria) >= 3, f"{u.id} tiene {len(u.teoria)} bloques de teoría"
        for bloque in u.teoria:
            assert bloque.formula.strip(), f"{u.id}/{bloque.titulo}: sin fórmula"
            assert len(bloque.explicacion) > 80, (
                f"{u.id}/{bloque.titulo}: la explicación son "
                f"{len(bloque.explicacion)} caracteres. Una fórmula sin "
                f"explicación no enseña nada."
            )

    @pytest.mark.parametrize("u", PLAN, ids=[u.id for u in PLAN])
    def test_la_teoria_apunta_a_codigo_que_existe(self, u):
        """La distancia entre la fórmula y su implementación es de un clic.

        Si el fichero se renombra y nadie actualiza la teoría, la referencia
        pasa a ser ruido. Esto lo impide.
        """
        from pathlib import Path

        raiz = Path(__file__).resolve().parent.parent
        for bloque in u.teoria:
            destino = raiz / bloque.codigo
            assert destino.is_file(), (
                f"{u.id}/{bloque.titulo} apunta a {bloque.codigo}, que no existe"
            )

    @pytest.mark.parametrize("u", PLAN, ids=[u.id for u in PLAN])
    def test_cada_unidad_tiene_su_demo_registrada(self, u):
        """El temario y el registro de escenas no pueden divergir.

        Si alguien renombra la clave de una demo, la unidad se queda con un
        botón que no abre nada. Esto lo detecta antes que el estudiante.
        """
        from src.engine.scenes.scene_registry import get_registry, register_demo_scenes

        register_demo_scenes()
        assert u.escena in get_registry().keys, (
            f"{u.id} declara la escena '{u.escena}', que no está en el registro"
        )

    def test_los_identificadores_no_se_repiten(self):
        ids = ids_de_unidades()
        assert len(ids) == len(set(ids))

    def test_las_respuestas_correctas_caen_dentro_de_las_opciones(self):
        """Lo garantiza `Pregunta.__post_init__`; esto comprueba que salta."""
        from src.framework.academic.curriculum import Pregunta

        with pytest.raises(ValueError, match="fuera de las"):
            Pregunta(enunciado="¿?", opciones=("a", "b"), correcta=5, porque="")


class TestElDesbloqueoEncadenado:
    """«que se activaran cuando cada una se completara»."""

    def test_al_empezar_solo_esta_abierta_la_primera(self):
        p = ProgresoAcademico("nuevo@uni.edu")
        assert p.unidades_desbloqueadas() == (ids_de_unidades()[0],)

    def test_aprobar_abre_la_siguiente(self):
        p = ProgresoAcademico("a@uni.edu")
        primera, segunda = ids_de_unidades()[:2]
        assert not p.esta_desbloqueada(segunda)
        r = p.registrar_intento(primera, ACIERTOS_PARA_APROBAR)
        assert r.aprobado
        assert r.recien_aprobada
        assert r.desbloqueada == segunda
        assert p.esta_desbloqueada(segunda)

    def test_suspender_no_abre_nada(self):
        p = ProgresoAcademico("a@uni.edu")
        primera, segunda = ids_de_unidades()[:2]
        r = p.registrar_intento(primera, ACIERTOS_PARA_APROBAR - 1)
        assert not r.aprobado
        assert r.desbloqueada is None
        assert not p.esta_desbloqueada(segunda)

    def test_no_se_puede_saltar_una_unidad(self):
        """Aprobar la tercera no abre la quinta."""
        p = ProgresoAcademico("a@uni.edu")
        ids = ids_de_unidades()
        p.registrar_intento(ids[2], PREGUNTAS_POR_UNIDAD)
        assert not p.esta_desbloqueada(ids[4])

    def test_repasar_y_fallar_no_quita_el_aprobado(self):
        """Se guarda el mejor intento, no el último.

        Si se guardara el último, volver a una unidad aprobada para repasar y
        contestar deprisa cerraría la unidad siguiente, que el estudiante ya
        podría tener a medias.
        """
        p = ProgresoAcademico("a@uni.edu")
        primera, segunda = ids_de_unidades()[:2]
        p.registrar_intento(primera, PREGUNTAS_POR_UNIDAD)
        p.registrar_intento(primera, 0)
        assert p.esta_aprobada(primera)
        assert p.esta_desbloqueada(segunda)
        assert p.aciertos(primera) == PREGUNTAS_POR_UNIDAD
        assert p.intentos(primera) == 2

    def test_lo_que_no_es_del_temario_nunca_se_bloquea(self):
        p = ProgresoAcademico("a@uni.edu")
        assert p.esta_desbloqueada("sandbox")
        assert p.esta_desbloqueada("leaderboard")

    def test_una_unidad_inventada_no_se_puede_registrar(self):
        p = ProgresoAcademico("a@uni.edu")
        with pytest.raises(ValueError, match="no existe la unidad"):
            p.registrar_intento("gravedad_cuantica", 5)

    def test_unidad_actual_es_la_primera_sin_aprobar(self):
        p = ProgresoAcademico("a@uni.edu")
        ids = ids_de_unidades()
        assert p.unidad_actual() == ids[0]
        p.registrar_intento(ids[0], PREGUNTAS_POR_UNIDAD)
        assert p.unidad_actual() == ids[1]

    def test_la_ultima_unidad_no_desbloquea_nada(self):
        p = ProgresoAcademico("a@uni.edu")
        r = p.registrar_intento(ids_de_unidades()[-1], PREGUNTAS_POR_UNIDAD)
        assert r.desbloqueada is None
        assert siguiente_unidad(ids_de_unidades()[-1]) is None


class TestLaIdentidadDelEstudiante:
    """El progreso va asociado al correo de la universidad."""

    def test_el_correo_se_normaliza(self):
        p = ProgresoAcademico("  Juan.Perez@UNI.EDU  ")
        assert p.correo == "juan.perez@uni.edu"

    def test_correos_validos_e_invalidos(self):
        assert es_correo_valido("a.b@uni.edu.co")
        assert not es_correo_valido("sin arroba")
        assert not es_correo_valido("dos@@uni.edu")
        assert not es_correo_valido("sin@dominio")

    def test_el_nombre_de_fichero_es_seguro(self):
        """Nada de lo que escriba el estudiante puede salir del directorio."""
        nombre = nombre_de_fichero("../../etc/passwd@uni.edu")
        assert "/" not in nombre
        assert ".." not in nombre.replace(".json", "")
        assert nombre.endswith(".json")

    def test_dos_formas_del_mismo_correo_dan_el_mismo_fichero(self):
        assert nombre_de_fichero("A@Uni.Edu") == nombre_de_fichero("a@uni.edu")


class TestLaPersistencia:
    """«el progreso no se guardaba»: ahora sí, y sobrevive al cierre."""

    def test_ida_y_vuelta_por_disco(self, tmp_path):
        p = ProgresoAcademico("est@uni.edu")
        ids = ids_de_unidades()
        p.registrar_intento(ids[0], PREGUNTAS_POR_UNIDAD)
        p.registrar_intento(ids[1], 2)
        p.guardar(tmp_path)

        vuelta = ProgresoAcademico.cargar(tmp_path, "est@uni.edu")
        assert vuelta.correo == "est@uni.edu"
        assert vuelta.aciertos(ids[0]) == PREGUNTAS_POR_UNIDAD
        assert vuelta.aciertos(ids[1]) == 2
        assert vuelta.esta_desbloqueada(ids[1])
        assert not vuelta.esta_desbloqueada(ids[2])

    def test_un_estudiante_nuevo_empieza_de_cero(self, tmp_path):
        p = ProgresoAcademico.cargar(tmp_path, "nadie@uni.edu")
        assert p.unidades_aprobadas() == ()

    def test_un_fichero_corrupto_no_tumba_el_juego(self, tmp_path):
        """Peor que perder unas notas es que treinta portátiles no arranquen."""
        ruta = tmp_path / nombre_de_fichero("roto@uni.edu")
        ruta.write_text("{esto no es json", encoding="utf-8")
        p = ProgresoAcademico.cargar(tmp_path, "roto@uni.edu")
        assert p.correo == "roto@uni.edu"
        assert p.unidades_aprobadas() == ()

    def test_se_ignora_una_unidad_que_ya_no_existe(self, tmp_path):
        """Si se retira una unidad, su nota deja de contar para el porcentaje."""
        ruta = tmp_path / nombre_de_fichero("viejo@uni.edu")
        ruta.write_text(json.dumps({
            "version": 1, "correo": "viejo@uni.edu",
            "mejor": {"unidad_retirada": 5}, "intentos": {"unidad_retirada": 1},
        }), encoding="utf-8")
        p = ProgresoAcademico.cargar(tmp_path, "viejo@uni.edu")
        assert p.porcentaje() == 0.0

    def test_no_se_usa_pickle(self, tmp_path):
        """AUD-035 sacó pickle del proyecto; estos ficheros se intercambian."""
        p = ProgresoAcademico("est@uni.edu")
        destino = p.guardar(tmp_path)
        assert destino.suffix == ".json"
        json.loads(destino.read_text(encoding="utf-8"))


class TestLaSesion:
    def test_sin_identificarse_se_juega_pero_no_se_guarda(self, tmp_path):
        s = SesionAcademica.reiniciar(tmp_path)
        assert not s.identificado
        assert s.guardar() is None
        assert list(tmp_path.iterdir()) == []

    def test_entrar_con_un_correo_malo_no_toca_la_sesion(self, tmp_path):
        s = SesionAcademica.reiniciar(tmp_path)
        assert not s.entrar("esto no es un correo")
        assert not s.identificado

    def test_registrar_un_examen_lo_guarda_en_el_acto(self, tmp_path):
        """En un aula el cierre limpio es la excepción, no la norma."""
        s = SesionAcademica.reiniciar(tmp_path)
        s.entrar("est@uni.edu")
        s.registrar_examen(ids_de_unidades()[0], PREGUNTAS_POR_UNIDAD)
        assert (tmp_path / nombre_de_fichero("est@uni.edu")).is_file()

    def test_dos_estudiantes_no_se_pisan(self, tmp_path):
        s = SesionAcademica.reiniciar(tmp_path)
        ids = ids_de_unidades()
        s.entrar("uno@uni.edu")
        s.registrar_examen(ids[0], PREGUNTAS_POR_UNIDAD)
        s.entrar("dos@uni.edu")
        assert not s.progreso.esta_aprobada(ids[0])
        s.entrar("uno@uni.edu")
        assert s.progreso.esta_aprobada(ids[0])


class TestElMenuRespetaElProgreso:
    """La comprobación que importa: que el menú no deje entrar donde no debe."""

    @pytest.fixture
    def menu(self, tmp_path):
        import pygame

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core import settings
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.demo_menu_scene import DemoMenuScene

        pygame.init()
        pygame.font.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        SesionAcademica.reiniciar(tmp_path)
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        escena = DemoMenuScene(ctx)
        escena.awake()
        escena.start()
        escena.on_enter()
        return escena

    def _fila(self, menu, id_unidad):
        for e in menu._entradas:
            if e.unidad_id == id_unidad:
                return e
        msg = f"no hay fila para {id_unidad}"
        raise AssertionError(msg)

    def test_el_menu_lista_todas_las_unidades(self, menu):
        listadas = {e.unidad_id for e in menu._entradas if e.unidad_id}
        assert listadas == set(ids_de_unidades())

    def test_al_empezar_solo_la_primera_unidad_esta_abierta(self, menu):
        ids = ids_de_unidades()
        assert not menu.esta_bloqueada(self._fila(menu, ids[0]))
        for i in ids[1:]:
            assert menu.esta_bloqueada(self._fila(menu, i)), f"{i} debería estar bloqueada"

    def test_pulsar_enter_en_una_bloqueada_no_abre_nada(self, menu):
        ids = ids_de_unidades()
        antes = len(menu.context.scene_manager._stack)
        menu._abrir(self._fila(menu, ids[3]))
        assert len(menu.context.scene_manager._stack) == antes
        assert "Bloqueada" in menu._error_msg

    def test_aprobar_abre_la_fila_siguiente(self, menu):
        ids = ids_de_unidades()
        SesionAcademica.instancia().entrar("est@uni.edu")
        SesionAcademica.instancia().registrar_examen(ids[0], PREGUNTAS_POR_UNIDAD)
        menu.on_enter()
        assert not menu.esta_bloqueada(self._fila(menu, ids[1]))
        assert menu.esta_bloqueada(self._fila(menu, ids[2]))

    def test_las_herramientas_sueltas_estan_siempre_abiertas(self, menu):
        sueltas = [e for e in menu._entradas if not e.unidad_id]
        assert sueltas
        for e in sueltas:
            assert not menu.esta_bloqueada(e)

    def test_la_teoria_se_puede_abrir_aunque_la_unidad_este_bloqueada(self, menu):
        """Es la única forma de aprobarla, y aprobarla es lo que la abre."""
        from src.engine.scenes.unit_theory_scene import UnitTheoryScene

        ids = ids_de_unidades()
        menu._abrir_teoria(self._fila(menu, ids[5]))
        cima = menu.context.scene_manager._stack[-1]
        assert isinstance(cima, UnitTheoryScene)

    def test_el_cursor_arranca_en_la_unidad_pendiente(self, menu):
        ids = ids_de_unidades()
        SesionAcademica.instancia().entrar("est@uni.edu")
        for i in ids[:3]:
            SesionAcademica.instancia().registrar_examen(i, PREGUNTAS_POR_UNIDAD)
        menu.on_enter()
        assert menu._entradas[menu._selected].unidad_id == ids[3]


class TestElExamenRegistraElResultado:
    """«el quiz está pero no cuenta para nada»: ahora sí cuenta."""

    @pytest.fixture
    def escena(self, tmp_path):
        import pygame

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core import settings
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.unit_theory_scene import UnitTheoryScene

        pygame.init()
        pygame.font.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        s = SesionAcademica.reiniciar(tmp_path)
        s.entrar("est@uni.edu")
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        e = UnitTheoryScene(ctx, ids_de_unidades()[0])
        e.awake()
        e.start()
        e.on_enter()
        return e

    def _contestar(self, escena, *, bien: bool) -> None:
        """Recorre el examen entero contestando todo bien o todo mal."""
        from src.engine.scenes.unit_theory_scene import EXAMEN

        escena._modo = EXAMEN
        for pregunta in escena._unidad.preguntas:
            correcta = pregunta.correcta
            escena._opcion = correcta if bien else (correcta + 1) % len(pregunta.opciones)
            escena._respondida = True
            if escena._opcion == correcta:
                escena._aciertos += 1
            escena._avanzar_pregunta()

    def test_acertar_todo_aprueba_y_desbloquea(self, escena):
        from src.engine.scenes.unit_theory_scene import RESULTADO

        self._contestar(escena, bien=True)
        assert escena._modo == RESULTADO
        assert escena._resultado.aprobado
        assert escena._resultado.desbloqueada == ids_de_unidades()[1]
        assert SesionAcademica.instancia().progreso.esta_aprobada(ids_de_unidades()[0])

    def test_fallar_todo_no_aprueba(self, escena):
        self._contestar(escena, bien=False)
        assert not escena._resultado.aprobado
        assert escena._resultado.desbloqueada is None
        assert not SesionAcademica.instancia().progreso.esta_aprobada(ids_de_unidades()[0])

    def test_el_resultado_queda_en_disco(self, escena, tmp_path):
        self._contestar(escena, bien=True)
        assert (tmp_path / nombre_de_fichero("est@uni.edu")).is_file()

    def test_dejar_el_examen_a_medias_no_cuenta_como_intento(self, escena):
        """Abrir por error y salir no puede gastar un intento."""
        from src.engine.scenes.unit_theory_scene import EXAMEN, TEORIA

        escena._modo = EXAMEN
        escena._pregunta = 2
        escena._aciertos = 1
        # Es lo que hace ESC dentro del examen.
        escena._modo = TEORIA
        escena._reiniciar_examen()
        assert SesionAcademica.instancia().progreso.intentos(ids_de_unidades()[0]) == 0


class TestElPuenteEntreDemoYUnidad:
    def test_cada_demo_del_temario_sabe_a_qué_unidad_pertenece(self):
        for u in PLAN:
            assert unidad_de_escena(u.escena) is u

    def test_una_escena_de_fuera_del_temario_no_tiene_unidad(self):
        assert unidad_de_escena("sandbox") is None

    def test_buscar_una_unidad_inexistente_devuelve_none(self):
        assert unidad("no_existe") is None


class TestElProgresoSobreviveAlCierreDelJuego:
    """AUD-098 — el eslabón que faltaba entre guardar y volver a usarlo.

    AUD-095 dejó el progreso guardándose bien y **nadie volvía a leerlo
    nunca**: `entrar()` sólo se llamaba desde las pruebas, no había pantalla
    que pidiera el correo y `App` no reanudaba nada al arrancar. Un estudiante
    podía aprobar cinco unidades, cerrar el juego, y encontrarse el temario
    entero bloqueado otra vez con sus notas intactas en el disco.

    Esta clase recorre el ciclo entero: identificarse, aprobar, «cerrar el
    juego» —tirando la sesión— y reanudar.
    """

    @pytest.fixture
    def ajustes_aislados(self, tmp_path, monkeypatch):
        """Ajustes en un fichero temporal: no tocar los del desarrollador."""
        from src.engine.core import user_settings

        destino = tmp_path / "config.json"
        monkeypatch.setattr(user_settings, "_default_config_path", lambda: destino)
        user_settings.reset()
        user_settings.set_settings(user_settings.UserSettings.load(destino))
        yield destino
        user_settings.reset()

    def test_ciclo_completo_identificar_aprobar_cerrar_reanudar(
        self, tmp_path, ajustes_aislados,
    ):
        ids = ids_de_unidades()

        sesion = SesionAcademica.reiniciar(tmp_path)
        assert sesion.entrar("alumno@uni.edu")
        sesion.registrar_examen(ids[0], PREGUNTAS_POR_UNIDAD)
        sesion.registrar_examen(ids[1], PREGUNTAS_POR_UNIDAD)
        assert len(sesion.progreso.unidades_aprobadas()) == 2

        # Se cierra el juego: sesión nueva, en blanco.
        reabierta = SesionAcademica.reiniciar(tmp_path)
        assert not reabierta.identificado
        assert reabierta.progreso.unidades_aprobadas() == ()

        # Al arrancar, App llama a esto.
        assert reabierta.reanudar(), "no se reanudó al último estudiante"
        assert reabierta.correo == "alumno@uni.edu"
        assert len(reabierta.progreso.unidades_aprobadas()) == 2, (
            "las notas estaban en el disco y no volvieron: es exactamente el "
            "defecto que AUD-098 corrige"
        )
        assert reabierta.progreso.esta_desbloqueada(ids[2])

    def test_sin_nadie_recordado_no_hay_nada_que_reanudar(self, tmp_path, ajustes_aislados):
        sesion = SesionAcademica.reiniciar(tmp_path)
        assert not sesion.reanudar()
        assert not sesion.identificado

    def test_cerrar_sesion_deja_de_recordar_pero_no_borra(self, tmp_path, ajustes_aislados):
        ids = ids_de_unidades()
        sesion = SesionAcademica.reiniciar(tmp_path)
        sesion.entrar("alumno@uni.edu")
        sesion.registrar_examen(ids[0], PREGUNTAS_POR_UNIDAD)
        sesion.salir()

        otra = SesionAcademica.reiniciar(tmp_path)
        assert not otra.reanudar(), "seguía recordando a un estudiante que salió"
        # Pero sus notas siguen ahí para cuando vuelva.
        assert otra.entrar("alumno@uni.edu")
        assert otra.progreso.esta_aprobada(ids[0])

    def test_un_correo_invalido_no_se_recuerda(self, tmp_path, ajustes_aislados):
        from src.engine.core import user_settings

        sesion = SesionAcademica.reiniciar(tmp_path)
        assert not sesion.entrar("no es un correo")
        assert user_settings.get().student_email == ""


class TestLaPantallaDeIdentificacion:
    """Que exista la puerta, y que haga lo que dice."""

    @pytest.fixture
    def escena(self, tmp_path, monkeypatch):
        import pygame

        from src.engine.audio.audio_manager import AudioManager
        from src.engine.core import settings, user_settings
        from src.engine.core.event_bus import EventBus
        from src.engine.core.game_context import GameContext
        from src.engine.core.save_manager import SaveManager
        from src.engine.input.input_manager import InputManager
        from src.engine.scene.scene_manager import SceneManager
        from src.engine.scenes.student_login_scene import StudentLoginScene

        monkeypatch.setattr(
            user_settings, "_default_config_path", lambda: tmp_path / "config.json",
        )
        user_settings.reset()
        pygame.init()
        pygame.font.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        SesionAcademica.reiniciar(tmp_path)
        ctx = GameContext(
            input_manager=InputManager(), audio_manager=AudioManager(),
            scene_manager=None, event_bus=EventBus(), clock=None,
            save_manager=SaveManager(),
        )
        ctx.scene_manager = SceneManager(ctx)
        e = StudentLoginScene(ctx)
        e.awake()
        e.start()
        e.on_enter()
        yield e
        user_settings.reset()

    @staticmethod
    def _teclear(escena, texto: str) -> None:
        import pygame

        escena.process_events([
            pygame.event.Event(pygame.KEYDOWN, key=ord(c), mod=0, unicode=c)
            for c in texto
        ])

    def test_teclear_llena_el_campo(self, escena):
        self._teclear(escena, "ana@uni.edu")
        assert escena._buffer == "ana@uni.edu"

    def test_los_caracteres_raros_no_entran(self, escena):
        """Un espacio o una comilla acabarían en un nombre de fichero."""
        self._teclear(escena, "a n'a@uni.edu")
        assert escena._buffer == "ana@uni.edu"

    def test_el_borrado_funciona(self, escena):
        import pygame

        self._teclear(escena, "abc")
        escena.process_events([
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, mod=0, unicode=""),
        ])
        assert escena._buffer == "ab"

    def test_confirmar_un_correo_valido_identifica(self, escena):
        self._teclear(escena, "ana@uni.edu")
        escena._confirmar()
        assert SesionAcademica.instancia().correo == "ana@uni.edu"

    def test_confirmar_uno_invalido_avisa_y_no_identifica(self, escena):
        self._teclear(escena, "ana-arroba-uni")
        escena._confirmar()
        assert not SesionAcademica.instancia().identificado
        assert escena._mensaje, "no se dijo al estudiante qué estaba mal"

    def test_no_se_pasa_del_limite_de_longitud(self, escena):
        from src.engine.scenes.student_login_scene import MAX_LONGITUD

        self._teclear(escena, "a" * (MAX_LONGITUD + 40))
        assert len(escena._buffer) == MAX_LONGITUD

    def test_dibuja_sin_caerse(self, escena):
        import pygame

        from src.engine.core import settings

        superficie = pygame.Surface((settings.INTERNAL_WIDTH, settings.INTERNAL_HEIGHT))
        self._teclear(escena, "ana@uni.edu")
        for _ in range(4):
            escena.update(1.0 / 60.0)
            escena.draw(superficie)
