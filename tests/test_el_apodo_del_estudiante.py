"""AUD-291 — el juego sabía tu correo y no cómo llamarte.

El hueco
--------
`StudentLoginScene` pide el correo desde AUD-098 y con él carga el progreso.
Pero un correo no es un nombre: los diálogos no podían dirigirse a nadie, la
tabla de récords no decía de quién eran los tiempos, y en un aula con un usuario
de sistema compartido eso significa treinta personas mirando marcas que no
saben si son suyas.

Las dos decisiones que hay que defender
---------------------------------------
1. **Dos campos, no uno.** Derivar el apodo del correo dejaría a los diálogos
   llamando «a01234567» a la gente. Un diálogo que te llama por tu matrícula no
   es personalización: es un dato personal proyectado en la pantalla de un aula.
2. **La sustitución ocurre al dibujar, no al cargar el árbol.** El apodo se
   puede cambiar a mitad de partida, y un texto sustituido al cargar seguiría
   diciendo el nombre viejo hasta reiniciar el nivel.
"""
from __future__ import annotations

import pytest

from src.framework.academic.progress import APODO_MAX, ProgresoAcademico
from src.framework.academic.sesion import SesionAcademica


@pytest.fixture
def sesion(tmp_path):
    return SesionAcademica.reiniciar(tmp_path)


class TestElDato:
    def test_se_guarda_y_se_relee(self, sesion, tmp_path) -> None:
        assert sesion.entrar("ana@uni.edu", recordar=False)
        sesion.poner_apodo("Ana")

        otra = SesionAcademica.reiniciar(tmp_path)
        otra.entrar("ana@uni.edu", recordar=False)
        assert otra.apodo == "Ana"

    def test_sin_apodo_cae_al_correo_sin_dominio(self, sesion) -> None:
        sesion.entrar("a01234567@tec.mx", recordar=False)
        assert sesion.apodo == "a01234567"

    def test_sin_identificar_hay_un_nombre_igualmente(self, sesion) -> None:
        """Nunca cadena vacía: quien lo consume lo mete en una frase, y una
        frase con un hueco se lee como un fallo del juego."""
        assert sesion.apodo == "Estudiante"

    def test_sin_identificar_no_se_puede_poner(self, sesion) -> None:
        """Sin correo no hay fichero donde guardarlo, y aceptarlo en memoria
        daría un apodo que desaparece al cerrar sin decir por qué."""
        sesion.poner_apodo("Fantasma")
        assert sesion.apodo == "Estudiante"

    def test_se_recorta_al_maximo(self) -> None:
        largo = ProgresoAcademico("x@y.edu", "A" * 100)
        assert len(largo.apodo) == APODO_MAX

    def test_se_le_quitan_los_saltos_de_linea(self) -> None:
        """Un apodo con un `\\n` parte la frase del diálogo en dos y deja media
        línea colgando — y eso no se diagnostica mirando el diálogo."""
        assert "\n" not in ProgresoAcademico("x@y.edu", "Ana\nMaría").apodo

    def test_admite_tildes_y_espacios(self) -> None:
        """Es un nombre, no un identificador."""
        assert ProgresoAcademico("x@y.edu", "Íñigo M").apodo == "Íñigo M"


class TestEnLosDialogos:
    def test_la_marca_se_sustituye(self, sesion) -> None:
        from src.framework.ui.dialogue_system import personalizar

        sesion.entrar("ana@uni.edu", recordar=False)
        sesion.poner_apodo("Ana")
        assert personalizar("Hola, {apodo}.") == "Hola, Ana."

    def test_un_texto_sin_marca_no_cambia(self, sesion) -> None:
        from src.framework.ui.dialogue_system import personalizar

        assert personalizar("Hola.") == "Hola."

    def test_se_resuelve_al_dibujar_y_no_al_cargar(self, sesion) -> None:
        """Cambiar el apodo a mitad de partida tiene que verse en el diálogo
        siguiente, no en el siguiente arranque."""
        from src.framework.ui.dialogue_system import personalizar

        sesion.entrar("ana@uni.edu", recordar=False)
        sesion.poner_apodo("Ana")
        antes = personalizar("Hola, {apodo}.")
        sesion.poner_apodo("Anita")
        assert personalizar("Hola, {apodo}.") != antes

    def test_sin_identificar_el_dialogo_sigue_teniendo_sentido(self, sesion) -> None:
        from src.framework.ui.dialogue_system import personalizar

        assert personalizar("Hola, {apodo}.") == "Hola, Estudiante."


class TestEnLosRecords:
    def test_la_marca_anota_de_quien_es(self, sesion, tmp_path) -> None:
        import orjson

        from src.framework.stage.speedrun_mode import registrar_marca

        sesion.entrar("ana@uni.edu", recordar=False)
        sesion.poner_apodo("Ana")
        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 42.0, ruta)
        assert orjson.loads(ruta.read_bytes())["apodo"] == "Ana"

    def test_sin_identificar_se_anota_igual(self, sesion, tmp_path) -> None:
        """Perder la marca por no saber el nombre sería cambiar un dato real
        por uno de adorno."""
        import orjson

        from src.framework.stage.speedrun_mode import registrar_marca

        ruta = tmp_path / "speedrun.json"
        registrar_marca("stage0", 42.0, ruta)
        datos = orjson.loads(ruta.read_bytes())
        assert datos["apodo"] == ""
        assert datos["splits"][0]["time"] == 42.0


class TestLaPantallaDeIdentificacion:
    def test_tiene_los_dos_campos(self) -> None:
        import inspect

        from src.engine.scenes import student_login_scene

        fuente = inspect.getsource(student_login_scene)
        assert "self._apodo" in fuente
        assert "K_TAB" in fuente, "sin TAB no hay forma de llegar al segundo campo"

    def test_el_apodo_se_pone_despues_de_entrar(self) -> None:
        """`entrar()` carga el progreso del disco y sobreescribiría un apodo
        puesto antes."""
        import inspect

        from src.engine.scenes.student_login_scene import StudentLoginScene

        fuente = inspect.getsource(StudentLoginScene._confirmar)
        assert fuente.index("entrar(") < fuente.index("poner_apodo(")
