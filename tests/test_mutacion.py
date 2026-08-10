"""
La herramienta de mutación — AUD-147.

Qué mide la mutación y por qué hacía falta
===========================================
La cobertura dice qué líneas se ejecutan; no dice si alguien las comprueba.
Una prueba que llama a una función y no mira lo que devuelve suma cobertura y
no defiende nada. Este proyecto corrigió **tres** de ésas esta misma semana,
todas mías: la del coyote medía cero contra cero, la del buffer de salto medía
la ausencia de suelo y la de la cámara usaba un doble con un método inventado.

La mutación es la única medida que las habría cazado sola.

Por qué estas pruebas no ejecutan la herramienta entera
--------------------------------------------------------
Cada mutante lanza pytest en un proceso aparte, y arrancar pytest cuesta unos
segundos. Comprobar aquí una pasada completa metería minutos en la suite de
todos los días a cambio de nada: lo que hay que verificar es que **el mutador
muta lo que dice** y que **la recuperación funciona**. Eso se prueba sin
subprocesos y en milisegundos.

La pasada de verdad la corre CI una vez por semana, que es su sitio.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import mutation_check as mut  # noqa: E402


class TestElMutadorMutaLoQueDice:
    def _mutaciones(self, fuente: str) -> list[str]:
        return [mut.aplicar(fuente, i)[0]
                for i in range(mut.contar_mutaciones(fuente))]

    def test_cambia_un_borde_de_comparacion(self) -> None:
        """El cambio que más fallos reales encuentra: casi todos los errores
        de rango del mundo son un `=` de más o de menos."""
        salidas = self._mutaciones("def f(x):\n    return x < 10\n")
        assert any("x <= 10" in s for s in salidas)

    def test_cambia_una_suma_por_una_resta(self) -> None:
        salidas = self._mutaciones("def f(a, b):\n    return a + b\n")
        assert any("a - b" in s for s in salidas)

    def test_cambia_un_and_por_un_or(self) -> None:
        salidas = self._mutaciones("def f(a, b):\n    return a and b\n")
        assert any("a or b" in s for s in salidas)

    def test_cambia_un_booleano(self) -> None:
        salidas = self._mutaciones("def f():\n    return True\n")
        assert any("return False" in s for s in salidas)

    def test_pone_a_cero_una_constante(self) -> None:
        salidas = self._mutaciones("VELOCIDAD = 45.0\n")
        assert any("VELOCIDAD = 0" in s for s in salidas)

    def test_no_toca_los_ceros_ni_los_unos(self) -> None:
        """Cambiar 0 por 0 y 1 por 0 produce mutantes o inertes o triviales;
        los dos ensucian la nota sin decir nada."""
        assert mut.contar_mutaciones("A = 0\nB = 1\n") == 0

    def test_no_toca_las_cadenas(self) -> None:
        """Mutar textos sólo rompe mensajes de registro, y eso no es una
        pregunta interesante sobre las pruebas."""
        assert mut.contar_mutaciones('MENSAJE = "hola"\n') == 0

    def test_cada_indice_produce_una_mutacion_distinta(self) -> None:
        fuente = "def f(a, b):\n    return a + b < 10 and a > 0\n"
        salidas = self._mutaciones(fuente)
        assert len(salidas) == len(set(salidas)), (
            "dos índices dan el mismo mutante: la nota estaría contando dos "
            "veces la misma pregunta"
        )

    def test_el_codigo_mutado_sigue_siendo_python_valido(self) -> None:
        import ast

        fuente = (RAIZ / "src/engine/audio/mixer_buses.py").read_text(
            encoding="utf-8")
        for indice in range(0, mut.contar_mutaciones(fuente), 7):
            ast.parse(mut.aplicar(fuente, indice)[0])

    def test_un_modulo_sin_nada_que_mutar_no_revienta(self) -> None:
        assert mut.contar_mutaciones('"""Sólo un docstring."""\n') == 0


class TestLaRecuperacionTrasUnKill:
    """AUD-147 — la herramienta que comprueba que el código está defendido
    estuvo a un `git checkout` de romperlo.

    La primera versión mutaba en su sitio y restauraba en un `finally`. La
    primera ejecución de prueba se agotó de tiempo, el proceso murió, el
    `finally` no llegó a correr y dejó `mixer_buses.py` con una constante a
    cero y los comentarios borrados por `ast.unparse`.

    El respaldo en disco es la guarda: mientras existe, hay una mutación
    puesta, y cualquier ejecución posterior la deshace antes de nada. Ni un
    `kill -9` puede dejar el árbol roto más allá del siguiente arranque.
    """

    def test_restaura_un_fichero_que_quedo_mutado(self, tmp_path, monkeypatch) -> None:
        # Bajo `src/`, que es donde la herramienta busca de verdad: la
        # recuperación sólo mira ahí y en `scripts/` porque recorrer el árbol
        # entero incluye `assets/` y en un montaje de red eso tarda más que
        # la propia comprobación.
        monkeypatch.setattr(mut, "RAIZ", tmp_path)
        (tmp_path / "src").mkdir()
        modulo = tmp_path / "src" / "cosa.py"
        modulo.write_text("VALOR = 45\n", encoding="utf-8")
        respaldo = Path(str(modulo) + mut.SUFIJO_RESPALDO)
        respaldo.write_text("VALOR = 45\n", encoding="utf-8")
        modulo.write_text("VALOR = 0\n", encoding="utf-8")   # el mutante vivo

        reparados = mut.restaurar_pendientes(verboso=False)
        assert reparados == ["src/cosa.py"]
        assert modulo.read_text(encoding="utf-8") == "VALOR = 45\n"
        assert not respaldo.exists(), "el respaldo se queda y volvería a saltar"

    def test_sin_respaldos_no_hace_nada(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(mut, "RAIZ", tmp_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "cosa.py").write_text("VALOR = 45\n", encoding="utf-8")
        assert mut.restaurar_pendientes(verboso=False) == []

    def test_no_quedan_respaldos_en_el_repositorio(self) -> None:
        """Si esta prueba falla, alguien mató una ejecución y hay un módulo
        mutado ahora mismo en el árbol."""
        sobrantes = [str(p.relative_to(RAIZ))
                     for carpeta in ("src", "scripts")
                     for p in (RAIZ / carpeta).rglob(f"*{mut.SUFIJO_RESPALDO}")]
        assert sobrantes == [], (
            f"quedan respaldos de mutación sin deshacer: {sobrantes}. "
            f"Ejecuta `python scripts/mutation_check.py` para repararlo"
        )


class TestLaNota:
    def test_todo_muerto_es_cien(self) -> None:
        assert mut.Resultado("m", 10, 10, []).nota == 100.0

    def test_ninguno_muerto_es_cero(self) -> None:
        assert mut.Resultado("m", 10, 0, ["a"] * 10).nota == 0.0

    def test_sin_mutantes_no_divide_entre_cero(self) -> None:
        """Un módulo sin nada que mutar no puede sacar cero: no hay pregunta
        que responder, así que la respuesta correcta es «bien»."""
        assert mut.Resultado("m", 0, 0, []).nota == 100.0

    def test_el_umbral_no_es_cien(self) -> None:
        """Perseguir el 100 % produce pruebas que copian el código línea por
        línea y no comprueban comportamiento."""
        assert 50.0 <= mut.UMBRAL < 100.0


class TestLosObjetivosSonReales:
    @pytest.mark.parametrize(("modulo", "pruebas"), mut.OBJETIVOS)
    def test_el_modulo_y_sus_pruebas_existen(self, modulo, pruebas) -> None:
        """Un objetivo que apunta a un fichero borrado convierte la
        herramienta en un adorno que siempre pasa.

        AUD-371 — el campo de pruebas admite **varios** ficheros separados por
        espacios, porque se le pasa a pytest tal cual y pytest acepta varias
        rutas. Hacía falta al medir `resolucion.py`: con su fichero «obvio»
        solo da 52 %, y con las tres suites que de verdad lo ejercitan, 100 %.
        La defensa de un módulo compartido vive repartida, y obligar a un solo
        fichero daba un número falso.

        Esta prueba comprobaba `(RAIZ / pruebas).exists()` sobre la cadena
        entera y se puso roja con el primer objetivo de varios ficheros, que
        es exactamente su trabajo: avisó de que la forma del dato había
        cambiado.
        """
        assert (RAIZ / modulo).exists(), modulo
        for fichero in pruebas.split():
            assert (RAIZ / fichero).exists(), fichero


class TestLaHerramientaNoDejaResiduo:
    """AUD-180: mutar un módulo le cambiaba los finales de línea.

    Tras una pasada, `git status` marcaba `mixer_buses.py`, `music_clock.py` y
    `bloques.py` como modificados, y `git diff` salía **vacío**: el contenido
    era idéntico y sólo habían cambiado los LF por CRLF. Es el diff fantasma
    que `test_toolchain_consistency.py` ya documenta —«guardar CRLF fue lo que
    produjo un diff de 334 archivos sin un solo cambio real»—, y aquí lo
    producía la propia herramienta de calidad sobre los tres módulos que más
    se miran.

    Nota honesta: esta prueba sólo puede ponerse roja en Windows, que es donde
    `os.linesep` es CRLF y donde ocurre el defecto. En Linux pasa con y sin la
    corrección.
    """

    def test_escribir_fuente_conserva_los_finales_de_linea(self, tmp_path) -> None:
        objetivo = tmp_path / "modulo.py"
        objetivo.write_bytes(b"a = 1\nb = 2\n")

        mut.escribir_fuente(objetivo, objetivo.read_text(encoding="utf-8"))

        assert objetivo.read_bytes() == b"a = 1\nb = 2\n", (
            "restaurar el módulo le cambió los finales de línea: el fichero "
            "queda marcado como modificado en git sin un solo cambio real"
        )

    def test_los_modulos_del_repositorio_estan_en_lf(self) -> None:
        """Si alguno llega ya en CRLF, la prueba de arriba mide lo que no es."""
        for modulo, _ in mut.OBJETIVOS:
            assert b"\r\n" not in (RAIZ / modulo).read_bytes(), (
                f"{modulo} está guardado con CRLF; el repositorio usa LF"
            )
