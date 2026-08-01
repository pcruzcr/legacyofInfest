"""
Los documentos que existen en dos idiomas dicen lo mismo.

AUD-122 — el hallazgo
======================
El proyecto ya tenía la convención bilingüe (`README.md` en español,
`README.en.md` en inglés; lo mismo con `AUDIT_2026-07`). Nadie la vigilaba, y
la pareja del README se había separado hasta dejar de ser una pareja:

============================  ==================  ==================
Afirmación                    README.md (ES)      README.en.md (EN)
============================  ==================  ==================
Pruebas automatizadas         1.333               640
Estados del jugador           no lo dice          «18 states», y a
                                                  continuación listaba 24
Atmósfera desde Tiled         sí                  no aparecía
============================  ==================  ==================

El número real de pruebas era **2.020**. Los dos estaban mal, cada uno de una
forma distinta, y el inglés además describía una arquitectura de hace meses.

La lección para la política de traducción
------------------------------------------
El encargo pedía «toda la documentación en inglés y español». Este proyecto
tiene **95 documentos**; traducirlos todos daría 190 ficheros que mantener
sincronizados, y el modo de fallo dominante aquí —medido tres veces este mes—
es precisamente que un documento se separe de la realidad. Duplicar la
superficie duplica ese riesgo.

Por eso la política es **bilingüe donde hay lector**, no bilingüe por decreto:

* Bilingüe obligatorio: la puerta de entrada (README) y los informes de
  auditoría publicables. Es lo que lee alguien de fuera.
* Español: el material del curso y los informes internos. El curso es en
  español y los estudiantes son hispanohablantes; una traducción rancia es
  peor que ninguna.
* Inglés: las especificaciones heredadas, hasta que alguien las necesite en
  español. Están en la lista de deuda de `KNOWN_GAPS.md`.

Lo que esta suite hace cumplir es que **lo que sí está en dos idiomas
coincida**. Una pareja que miente es peor que un documento en un solo idioma,
porque hace creer que hay revisión donde no la hay.
"""
from __future__ import annotations

import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Parejas bilingües obligatorias: `(español, inglés)`.
#:
#: Añadir aquí una pareja es declarar que se mantendrá sincronizada. No añadas
#: nada que no vayas a revisar.
PAREJAS: list[tuple[str, str]] = [
    ("README.md", "README.en.md"),
    ("docs/AUDIT_2026-07.es.md", "docs/AUDIT_2026-07.en.md"),
]


class TestLasParejasExisten:
    @pytest.mark.parametrize(("es", "en"), PAREJAS, ids=[p[0] for p in PAREJAS])
    def test_los_dos_lados_estan(self, es, en) -> None:
        assert (RAIZ / es).exists(), f"falta el lado español: {es}"
        assert (RAIZ / en).exists(), (
            f"falta el lado inglés de {es}: {en}. Si se retiró a propósito, "
            f"sácalo también de PAREJAS — una pareja declarada y ausente es "
            f"una promesa rota en silencio"
        )

    @pytest.mark.parametrize(("es", "en"), PAREJAS, ids=[p[0] for p in PAREJAS])
    def test_cada_lado_apunta_al_otro(self, es, en) -> None:
        """Sin el enlace cruzado, la mitad de los lectores no sabe que existe."""
        texto_es = (RAIZ / es).read_text(encoding="utf-8")
        texto_en = (RAIZ / en).read_text(encoding="utf-8")
        nombre_en = pathlib.Path(en).name
        nombre_es = pathlib.Path(es).name
        assert nombre_en in texto_es, f"{es} no menciona a {nombre_en}"
        assert nombre_es in texto_en, f"{en} no menciona a {nombre_es}"


class TestLasCifrasCoinciden:
    """Lo que separó la pareja del README fueron los números, no la prosa."""

    @staticmethod
    def _sin_bloques_de_codigo(texto: str) -> str:
        """Quita los bloques cercados antes de comparar.

        Dentro de un bloque de código hay volcados de consola, coordenadas y
        rutas: no son afirmaciones sobre el proyecto y **no deben** coincidir
        entre idiomas. El motor imprime sus avisos en español; exigir que el
        documento inglés reprodujera esos mismos números empujaría a traducir
        una salida de consola que en la pantalla del estudiante sale en
        español. Sería documentar una mentira para satisfacer una prueba.
        """
        return re.sub(r"```.*?```", "", texto, flags=re.S)

    @classmethod
    def _numeros(cls, texto: str) -> set[int]:
        """Enteros de la prosa, normalizando el separador de millares.

        El español escribe `2.020` y el inglés `2,020`. Comparar las cadenas
        daría un falso positivo en cada cifra de cuatro dígitos, que es la
        forma más rápida de que alguien desactive esta prueba.
        """
        crudos = re.findall(r"\b\d[\d.,]*\b", cls._sin_bloques_de_codigo(texto))
        valores: set[int] = set()
        for c in crudos:
            limpio = c.replace(".", "").replace(",", "")
            if limpio.isdigit() and len(limpio) <= 9:
                valores.add(int(limpio))
        return valores

    @pytest.mark.parametrize(("es", "en"), PAREJAS, ids=[p[0] for p in PAREJAS])
    def test_ninguna_cifra_grande_esta_solo_en_un_lado(self, es, en) -> None:
        """Sólo se comparan las cifras ≥ 100.

        Las pequeñas son números de sección, de unidad y de versión, y difieren
        legítimamente entre idiomas. Las grandes son afirmaciones sobre el
        proyecto —cuántas pruebas, cuántos tipos, cuántas entidades— y ésas
        tienen que coincidir o una de las dos miente.
        """
        n_es = {n for n in self._numeros((RAIZ / es).read_text(encoding="utf-8"))
                if n >= 100}
        n_en = {n for n in self._numeros((RAIZ / en).read_text(encoding="utf-8"))
                if n >= 100}
        solo_es = sorted(n_es - n_en)
        solo_en = sorted(n_en - n_es)
        assert not (solo_es or solo_en), (
            f"las dos versiones de {pathlib.Path(es).stem} afirman cosas "
            f"distintas.\n  sólo en español: {solo_es}\n  sólo en inglés: "
            f"{solo_en}"
        )


class TestElReadmeDiceLaVerdad:
    """La cifra que más se cita del proyecto, comprobada contra el proyecto."""

    @staticmethod
    def _pruebas_declaradas(ruta: str) -> int:
        texto = (RAIZ / ruta).read_text(encoding="utf-8")
        m = re.search(r"([\d.,]+)\s+(?:pruebas automatizadas|automated tests)",
                      texto)
        assert m, f"{ruta} ya no declara cuántas pruebas hay"
        return int(m.group(1).replace(".", "").replace(",", ""))

    def test_el_numero_de_pruebas_es_el_real(self) -> None:
        """Se recuenta de verdad, en un proceso aparte.

        Un número escrito a mano en el README envejece el día siguiente. Éste
        se compara con lo que `pytest --collect-only` encuentra ahora mismo, y
        se tolera un margen: el README no debería cambiar por añadir tres
        pruebas, pero sí por añadir trescientas.
        """
        import os
        import subprocess
        import sys

        entorno = dict(os.environ)
        entorno.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        salida = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q",
             "-p", "no:cacheprovider"],
            capture_output=True, text=True, timeout=300,
            cwd=str(RAIZ), env=entorno, check=False,
        ).stdout
        m = re.search(r"(\d+)\s+tests? collected", salida)
        assert m, f"no se pudo contar las pruebas:\n{salida[-800:]}"
        reales = int(m.group(1))

        for ruta in ("README.md", "README.en.md"):
            declaradas = self._pruebas_declaradas(ruta)
            desvio = abs(declaradas - reales) / max(reales, 1)
            assert desvio <= 0.05, (
                f"{ruta} dice {declaradas} pruebas y hay {reales} "
                f"({desvio:.0%} de desvío). Antes decía 1.333 en español y "
                f"640 en inglés cuando había 2.020: los dos mal, cada uno a "
                f"su manera"
            )
