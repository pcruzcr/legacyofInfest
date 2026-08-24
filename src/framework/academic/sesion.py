"""
La sesión académica: quién está jugando y qué lleva aprobado.

AUD-095
=======
El progreso por unidad no sirve de nada si no se sabe de quién es. Este
módulo guarda el estudiante activo y su progreso, y da a las escenas un
único punto por el que preguntar.

Es un singleton por proceso, como `Bestiary`. Podría inyectarse por
`GameContext`, pero entonces las diez demos, el menú y la pantalla de
progreso tendrían que ir pasándoselo unas a otras sin usarlo para nada más;
el coste de la indirección no compensa para un dato que es literalmente
«quién está sentado delante».

Sin identificarse también se juega
----------------------------------
Si nadie ha escrito su correo, se usa un progreso anónimo que **no** se
guarda en disco. El juego funciona igual; lo que no hay es nota que entregar.
Un motor que exija registrarse para poder abrir la primera demo es un motor
que nadie prueba.
"""
from __future__ import annotations

from pathlib import Path

#: Dónde se guardan los ficheros de progreso, uno por estudiante.
# AUD-157 — el estado del jugador va al directorio del usuario.
#
# `PROJECT_ROOT` es el árbol de instalación, y una versión empaquetada
# puede estar en un sitio de sólo lectura. Es la misma corrección que
# AUD-032 aplicó a las preferencias y a los logros y que aquí se quedó
# sin aplicar.
from src.engine.core.user_settings import user_data_dir
from src.framework.academic.progress import (
    ProgresoAcademico,
    ResultadoIntento,
    es_correo_valido,
)

DIRECTORIO_PROGRESO: Path = user_data_dir() / "saves" / "academico"


class SesionAcademica:
    """Estudiante activo y su progreso."""

    _instancia: SesionAcademica | None = None

    def __init__(self, directorio: Path | None = None) -> None:
        self._directorio = directorio or DIRECTORIO_PROGRESO
        self._progreso = ProgresoAcademico()

    # -- singleton -------------------------------------------------
    @classmethod
    def instancia(cls) -> SesionAcademica:
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    @classmethod
    def reiniciar(cls, directorio: Path | None = None) -> SesionAcademica:
        """Tira la sesión y empieza otra. Lo usan las pruebas."""
        cls._instancia = cls(directorio)
        return cls._instancia

    # -- estado ----------------------------------------------------
    @property
    def progreso(self) -> ProgresoAcademico:
        return self._progreso

    @property
    def correo(self) -> str:
        return self._progreso.correo

    @property
    def apodo(self) -> str:
        """Cómo llamar a esta persona en pantalla — AUD-291.

        Cae al correo sin dominio si no ha puesto apodo, y a «Estudiante» si
        tampoco hay correo. Nunca devuelve cadena vacía: quien lo consume lo
        mete en una frase, y una frase con un hueco se lee como un fallo del
        juego, no como un dato que falta.
        """
        if self._progreso.apodo:
            return self._progreso.apodo
        correo = self._progreso.correo
        if correo:
            return correo.split("@", 1)[0]
        return "Estudiante"

    def poner_apodo(self, apodo: str) -> None:
        """Cambia el apodo y lo persiste. Sin identificar no hace nada.

        No hace nada a propósito: sin correo no hay fichero donde guardarlo, y
        aceptarlo en memoria daría un apodo que desaparece al cerrar el juego
        sin decir por qué.
        """
        from src.framework.academic.progress import _limpiar_apodo

        if not self.identificado:
            return
        self._progreso.apodo = _limpiar_apodo(apodo)
        self._progreso.guardar(self._directorio)

    @property
    def identificado(self) -> bool:
        return bool(self._progreso.correo)

    @property
    def directorio(self) -> Path:
        return self._directorio

    # -- operaciones -----------------------------------------------
    def entrar(self, correo: str, *, recordar: bool = True) -> bool:
        """Identifica a un estudiante y carga lo que llevara hecho.

        Devuelve `False` si el correo no tiene forma de correo, y en ese caso
        no toca la sesión: es preferible seguir como anónimo a asociar las
        notas de alguien a una cadena escrita a medias.

        Con `recordar`, deja el correo en los ajustes para que el siguiente
        arranque lo reanude solo.
        """
        if not es_correo_valido(correo):
            return False
        self._progreso = ProgresoAcademico.cargar(self._directorio, correo)
        if recordar:
            self._recordar(self._progreso.correo)
        return True

    def reanudar(self) -> bool:
        """Vuelve a entrar con el último estudiante recordado, si lo hay.

        AUD-098 — por qué esto faltaba y por qué importa
        ------------------------------------------------
        El progreso académico se guardaba correctamente y nada volvía a
        leerlo nunca: `entrar()` sólo se llamaba desde las pruebas. Un
        estudiante podía aprobar cinco unidades, cerrar el juego, y al abrirlo
        encontrarse el temario entero bloqueado otra vez, con sus notas
        intactas en el disco pero inalcanzables.

        Es el mismo defecto que la iluminación que no iluminaba y que las
        demos que dibujaban en una esquina: código correcto, probado en
        aislamiento, que no llegaba a la pantalla.
        """
        from src.engine.core import user_settings

        correo = (user_settings.get().student_email or "").strip()
        if not correo:
            return False
        return self.entrar(correo, recordar=False)

    def salir(self) -> None:
        """Vuelve a anónimo y deja de recordar. No borra nada del disco."""
        self._progreso = ProgresoAcademico()
        self._recordar("")

    @staticmethod
    def _recordar(correo: str) -> None:
        """Anota en los ajustes quién es el estudiante activo.

        Sólo el correo. Las notas viven en su propio fichero: mezclarlas con
        los ajustes de volumen las haría viajar cada vez que alguien copia su
        configuración a otra máquina.
        """
        from src.engine.core import user_settings

        ajustes = user_settings.get()
        if ajustes.student_email == correo:
            return
        ajustes.student_email = correo
        ajustes.save()

    def guardar(self) -> Path | None:
        """Escribe el progreso. Devuelve `None` si nadie se ha identificado."""
        if not self.identificado:
            return None
        return self._progreso.guardar(self._directorio)

    def registrar_examen(self, id_unidad: str, aciertos: int) -> ResultadoIntento:
        """Anota un examen y lo guarda en el acto.

        Se guarda inmediatamente y no al salir del juego a propósito: en un
        aula el cierre limpio es la excepción, no la norma.
        """
        resultado = self._progreso.registrar_intento(id_unidad, aciertos)
        self.guardar()
        return resultado


# AUD-200 — los logros siguen a la sesión académica, no al proceso.
#
# El núcleo del motor no puede saber que `framework` existe (regla L1), así
# que `achievements.py` expone un punto de inyección, `bind_ruta_resolver`,
# y la sesión se lo presta aquí: identificado escribe en
# `achievements_<correo>.json`, anónimo conserva la ruta histórica. Sin esta
# pieza, dos estudiantes en la misma máquina compartirían medallas.
def _ruta_de_logros_de_la_sesion() -> Path:
    from src.engine.core.achievements import ACHIEVEMENTS_PATH, _slug_estudiante

    correo = SesionAcademica.instancia().correo
    if not correo:
        return ACHIEVEMENTS_PATH
    return ACHIEVEMENTS_PATH.with_name(f"achievements_{_slug_estudiante(correo)}.json")


def _vincular_logros_a_la_sesion() -> None:
    from src.engine.core.achievements import bind_ruta_resolver

    bind_ruta_resolver(_ruta_de_logros_de_la_sesion)


_vincular_logros_a_la_sesion()
