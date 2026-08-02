"""
mutation_check.py — ¿las pruebas se enterarían si el código cambiara?

AUD-147. Por qué existe, y por qué NO es mutmut
===============================================
La cobertura dice qué líneas se ejecutan. No dice si alguien las está
comprobando. Una prueba que llama a una función y no mira lo que devuelve
suma cobertura y no defiende nada — y este proyecto ya tuvo que corregir tres
de esas **esta misma semana**, escritas por mí:

* la del coyote a 30 vs 144 fps medía cero contra cero;
* la del buffer de salto medía la ausencia de suelo;
* la de la cámara de las cutscenes usaba un doble con un método inventado.

La mutación es la única medida que las habría cazado sola: se estropea el
código a propósito y se mira si alguna prueba se pone roja. Si nadie protesta,
esa línea no está defendida por nadie.

Por qué una herramienta propia y no `mutmut`
---------------------------------------------
1. **No añade una dependencia al curso.** Trece estudiantes instalan este
   repositorio; cada paquete de más es un `pip install` que puede fallar en
   un aula.
2. **Acotado por diseño.** Mutar 25.000 líneas contra 2.300 pruebas son horas.
   Esto muta **los módulos que se le digan** y ejecuta **sólo sus pruebas**,
   así que cabe en un par de minutos y alguien lo leerá. Un informe de una
   hora se ignora, que es exactamente lo que pasó con las seis herramientas
   de calificación que hubo que arreglar este mes.
3. **Se entiende de una lectura.** Es una clase de `ast.NodeTransformer` y un
   bucle. Un estudiante de la asignatura puede leerlo entero.

Uso::

    python scripts/mutation_check.py                 # el conjunto por defecto
    python scripts/mutation_check.py --ci            # falla si baja del umbral
    python scripts/mutation_check.py --objetivo src/engine/audio/mixer_buses.py \\
                                     --pruebas tests/test_buses_de_audio.py

Cómo leer el resultado
-----------------------
* **Mutante muerto**: se estropeó algo y una prueba se puso roja. Bien.
* **Mutante vivo**: se estropeó algo y **nadie se enteró**. Ahí falta una
  prueba, o la que hay no mira lo que debería.

Un 100 % no es el objetivo y perseguirlo produce pruebas que repiten el
código. Lo útil es la **lista de supervivientes**: cada uno es una pregunta
concreta —«¿de verdad da igual que esto sea `>` o `>=`?»— y a veces la
respuesta es que sí.
"""
from __future__ import annotations

import argparse
import ast
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# AUD-177: esta herramienta imprime `→` y la consola de Windows usa cp1252, que
# no lo tiene. Sin esto el proceso muere con UnicodeEncodeError en mitad del
# primer módulo —no al final—, así que la comprobación de mutación no llegaba a
# dar ningún veredicto en la máquina para la que está escrita.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent

#: Módulos que se mutan por defecto, con las pruebas que deberían defenderlos.
#:
#: Se eligen por consecuencia, no por tamaño: son cosas cuyo fallo silencioso
#: se nota jugando y no en una excepción. El reloj y el mezclador van primero
#: porque los dos tuvieron un fallo de este tipo esta semana.
OBJETIVOS: tuple[tuple[str, str], ...] = (
    ("src/engine/audio/mixer_buses.py", "tests/test_buses_de_audio.py"),
    ("src/engine/audio/music_clock.py", "tests/test_reloj_musical.py"),
    ("src/framework/stage/bloques.py", "tests/test_bloques.py"),
)

#: Nota mínima para dar por buena la defensa de un módulo.
#:
#: 70 % y no 100: perseguir el 100 produce pruebas que copian el código línea
#: por línea y no comprueban comportamiento. Por debajo de 70, en cambio, hay
#: partes enteras que nadie está mirando.
UMBRAL: float = 70.0


class _Mutador(ast.NodeTransformer):
    """Aplica **una** mutación, la número `objetivo` de las que encuentra."""

    #: Comparaciones que se intercambian. Los cambios de borde —`<` por `<=`—
    #: son los que más fallos reales encuentran: casi todos los errores de
    #: rango del mundo son un `=` de más o de menos.
    COMPARACIONES: dict[type, type] = {
        ast.Lt: ast.LtE, ast.LtE: ast.Lt,
        ast.Gt: ast.GtE, ast.GtE: ast.Gt,
        ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
    }
    OPERADORES: dict[type, type] = {
        ast.Add: ast.Sub, ast.Sub: ast.Add,
        ast.Mult: ast.Div, ast.Div: ast.Mult,
    }

    def __init__(self, objetivo: int) -> None:
        self.objetivo = objetivo
        self.encontradas = 0
        self.descripcion = ""

    def _toca(self, texto: str) -> bool:
        """¿Es ésta la mutación que toca aplicar?"""
        actual = self.encontradas
        self.encontradas += 1
        if actual == self.objetivo:
            self.descripcion = texto
            return True
        return False

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        if len(node.ops) == 1 and type(node.ops[0]) in self.COMPARACIONES:
            nuevo = self.COMPARACIONES[type(node.ops[0])]
            if self._toca(f"línea {node.lineno}: "
                          f"{type(node.ops[0]).__name__} → {nuevo.__name__}"):
                node.ops = [nuevo()]
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        if type(node.op) in self.OPERADORES:
            nuevo = self.OPERADORES[type(node.op)]
            if self._toca(f"línea {node.lineno}: "
                          f"{type(node.op).__name__} → {nuevo.__name__}"):
                node.op = nuevo()
        return node

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        nuevo = ast.Or if isinstance(node.op, ast.And) else ast.And
        if self._toca(f"línea {node.lineno}: "
                      f"{type(node.op).__name__} → {nuevo.__name__}"):
            node.op = nuevo()
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        # Sólo números y booleanos: cambiar cadenas produce mutantes que sólo
        # rompen mensajes de registro, y ésos no dicen nada útil.
        if isinstance(node.value, bool):
            if self._toca(f"línea {node.lineno}: {node.value} → {not node.value}"):
                return ast.copy_location(ast.Constant(value=not node.value), node)
        elif isinstance(node.value, (int, float)) and node.value not in (0, 1):
            if self._toca(f"línea {node.lineno}: {node.value} → 0"):
                return ast.copy_location(ast.Constant(value=0), node)
        return node


def contar_mutaciones(fuente: str) -> int:
    contador = _Mutador(objetivo=-1)
    contador.visit(ast.parse(fuente))
    return contador.encontradas


def aplicar(fuente: str, indice: int) -> tuple[str, str]:
    arbol = ast.parse(fuente)
    mutador = _Mutador(indice)
    nuevo = ast.fix_missing_locations(mutador.visit(arbol))
    return ast.unparse(nuevo), mutador.descripcion


@dataclass
class Resultado:
    objetivo: str
    total: int
    muertos: int
    vivos: list[str]

    @property
    def nota(self) -> float:
        return 100.0 * self.muertos / self.total if self.total else 100.0


# AUD-170 — aquí vivía una segunda definición de `_pruebas_pasan`.
#
# Este módulo declaraba la función **dos veces**: ésta, de tres parámetros
# (`pruebas, segundos, raiz`), que corría la suite contra una copia con un
# entorno construido desde cero; y la de más abajo, de dos parámetros, que
# corre contra `RAIZ` heredando `os.environ`. En Python la segunda gana, así
# que ésta llevaba tiempo siendo código inalcanzable — y el único sitio que
# llama a la función lo hace con dos argumentos.
#
# Se retiró la de tres. No es una elección estética:
#
# * la versión viva explica en su propio comentario por qué el entorno tiene
#   que heredarse (sin la ruta de paquetes del usuario, pytest no encuentra
#   pygame y **todos** los mutantes mueren por la razón equivocada, que en una
#   herramienta de mutación significa dar por buena una suite que no lo es);
# * su `PATH` fijo a `/usr/bin:/bin:/usr/local/bin` no existe en Windows, que
#   es donde se desarrolla este repositorio;
# * mientras estaban las dos, `ruff` fallaba con F811 sobre `scripts/`, que
#   está dentro del alcance que el CI lintea.
#
# Lo que la muerta hacía mejor —trabajar sobre una copia en vez de sobre el
# árbol real— no se pierde por descuido: aquí se muta el repositorio a
# propósito, y por eso existen el respaldo en disco y los manejadores de
# señal de `medir`. Si algún día se quiere mutar sobre copia, se cambia esa
# decisión entera, no se deja media implementación muerta esperando.


#: Sufijo del respaldo que se deja en disco mientras se muta.
#:
#: Es la guarda contra `kill -9`. Ver `medir`.
SUFIJO_RESPALDO = ".mutacion_original"


def restaurar_pendientes(verboso: bool = True) -> list[str]:
    """Deshace lo que dejó a medias una ejecución que alguien mató.

    AUD-147 — la herramienta que comprueba que el código está defendido
    estuvo a un `git checkout` de romperlo.

    La primera versión mutaba el fichero en su sitio y lo restauraba en un
    `finally`. Eso funciona hasta que el proceso muere de verdad: la primera
    ejecución de prueba se agotó de tiempo, el `finally` no llegó a correr y
    dejó `mixer_buses.py` con una constante a cero y todos los comentarios
    borrados por `ast.unparse`.

    Lo correcto sería mutar sobre una copia del árbol, y así estaba escrito;
    pero copiar `src` y `tests` en el montaje de este proyecto tarda más de
    cuarenta segundos, y una herramienta que tarda no se usa.

    La solución es un respaldo **en disco** junto al fichero: mientras existe,
    hay una mutación puesta. Cualquier ejecución posterior lo ve y restaura
    antes de hacer nada, así que ni siquiera un `kill -9` deja el árbol roto
    más allá del siguiente arranque. `tests/test_mutacion.py` comprueba que
    esa recuperación funciona.
    """
    reparados = []
    # Sólo donde se muta. Un `rglob` sobre la raíz entera recorre `assets/`,
    # que en un montaje de red tarda más que la propia comprobación.
    candidatos = [r for carpeta in ("src", "scripts")
                  for r in (RAIZ / carpeta).rglob(f"*{SUFIJO_RESPALDO}")]
    for respaldo in candidatos:
        objetivo = respaldo.with_suffix("")
        if objetivo.suffix != ".py":
            objetivo = Path(str(respaldo)[: -len(SUFIJO_RESPALDO)])
        shutil.copy2(respaldo, objetivo)
        respaldo.unlink()
        # Ruta relativa con `/` en cualquier SO: `tests/test_mutacion.py` la
        # compara con `src/cosa.py` y un `os.sep` distinto la rompe en Windows.
        reparados.append(objetivo.relative_to(RAIZ).as_posix())
        if verboso:
            print(f"  restaurado tras una ejecución interrumpida: {reparados[-1]}")
    return reparados


def escribir_fuente(destino: Path, fuente: str) -> None:
    """Escribe un módulo sin traducir los finales de línea.

    AUD-180: `Path.write_text` sin `newline` traduce cada `\\n` al separador del
    sistema, así que en Windows escribía CRLF. Restaurar el original dejaba los
    tres módulos críticos marcados como modificados en git **sin un solo cambio
    real** — el mismo diff fantasma que ya documenta
    `tests/test_toolchain_consistency.py`, sólo que aquí lo producía la propia
    herramienta de calidad, y justo sobre los ficheros que más se miran.
    """
    destino.write_text(fuente, encoding="utf-8", newline="")


def _pruebas_pasan(pruebas: str, segundos: int) -> bool:
    try:
        proceso = subprocess.run(
            [sys.executable, "-m", "pytest", pruebas, "-x", "-q",
             "-p", "no:cacheprovider", "--no-header", "--tb=no"],
            check=False, capture_output=True, cwd=RAIZ, timeout=segundos,
            # El entorno se HEREDA y sólo se añade lo necesario. Construirlo
            # desde cero dejaba fuera la ruta de paquetes del usuario, y
            # pytest no encontraba pygame: cada mutante tardaba lo indecible
            # en fallar por la razón equivocada, que en una herramienta de
            # mutación significa contar como muerto todo lo que se mira.
            env={**os.environ, "SDL_VIDEODRIVER": "dummy",
                 "SDL_AUDIODRIVER": "dummy", "PYTHONPATH": str(RAIZ)},
        )
    except subprocess.TimeoutExpired:
        # Un mutante que cuelga la suite cuenta como muerto: el cambio tuvo
        # consecuencias, que es justo lo que se estaba midiendo.
        return False
    return proceso.returncode == 0


def medir(ruta_modulo: str, ruta_pruebas: str, *, maximo: int = 25,
          segundos: int = 120, verboso: bool = True) -> Resultado:
    """Muta el módulo, corre sus pruebas y cuenta quién se entera.

    El respaldo se escribe **antes** de la primera mutación y se borra al
    final; mientras exista, cualquier otra ejecución sabe que hay algo que
    deshacer. Ver `restaurar_pendientes`.
    """
    modulo = RAIZ / ruta_modulo
    respaldo = Path(str(modulo) + SUFIJO_RESPALDO)
    original = modulo.read_text(encoding="utf-8")
    total_posibles = contar_mutaciones(original)
    # Muestreo repartido: con un módulo grande, coger las 25 primeras
    # mutaciones sólo mide la cabecera del fichero.
    paso = max(1, total_posibles // maximo)
    indices = list(range(0, total_posibles, paso))[:maximo]

    def _deshacer(*_a: object) -> None:
        escribir_fuente(modulo, original)
        respaldo.unlink(missing_ok=True)

    shutil.copy2(modulo, respaldo)
    anteriores = [
        (s, signal.signal(s, lambda *a: (_deshacer(), sys.exit(130))))
        for s in (signal.SIGINT, signal.SIGTERM)
    ]
    muertos, vivos = 0, []
    try:
        for indice in indices:
            mutado, descripcion = aplicar(original, indice)
            escribir_fuente(modulo, mutado)
            if _pruebas_pasan(ruta_pruebas, segundos):
                vivos.append(descripcion)
                if verboso:
                    print(f"    VIVE  {descripcion}", flush=True)
            else:
                muertos += 1
                if verboso:
                    print(f"    muere {descripcion}", flush=True)
    finally:
        _deshacer()
        for s, anterior in anteriores:
            signal.signal(s, anterior)

    return Resultado(ruta_modulo, len(indices), muertos, vivos)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objetivo", help="módulo a mutar")
    parser.add_argument("--pruebas", help="pruebas que deberían defenderlo")
    parser.add_argument("--maximo", type=int, default=25,
                        help="mutantes por módulo (25 por defecto)")
    parser.add_argument("--umbral", type=float, default=UMBRAL)
    parser.add_argument("--ci", action="store_true",
                        help="devuelve 1 si algún módulo baja del umbral")
    args = parser.parse_args()

    if args.objetivo and args.pruebas:
        objetivos = ((args.objetivo, args.pruebas),)
    elif args.objetivo or args.pruebas:
        print("--objetivo y --pruebas van juntos", file=sys.stderr)
        return 2
    else:
        objetivos = OBJETIVOS

    print("Comprobación de mutación — ¿se enterarían las pruebas?\n")
    restaurar_pendientes()
    resultados = []
    empezado = time.perf_counter()
    for modulo, pruebas in objetivos:
        print(f"  {modulo}  ({pruebas})")
        resultado = medir(modulo, pruebas, maximo=args.maximo)
        resultados.append(resultado)
        print(f"    → {resultado.muertos}/{resultado.total} "
              f"= {resultado.nota:.0f} %\n")

    print(f"{'=' * 56}")
    fallidos = [r for r in resultados if r.nota < args.umbral]
    for resultado in resultados:
        marca = "OK " if resultado.nota >= args.umbral else "BAJO"
        print(f"  [{marca}] {resultado.nota:5.1f} %  {resultado.objetivo}")
    if fallidos:
        print("\nMutantes vivos — cada uno es una pregunta sin responder:")
        for resultado in fallidos:
            for vivo in resultado.vivos:
                print(f"  · {resultado.objetivo}: {vivo}")
    print(f"\n{time.perf_counter() - empezado:.0f} s")

    if args.ci and fallidos:
        print("\nAlgún módulo está por debajo del umbral.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
