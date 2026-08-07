"""
Module: test_seguridad_del_motor
System: tests
Academic Unit: N/A

AUD-189 — las propiedades de seguridad del motor, fijadas por prueba.

Por qué existe
-------------
Este motor **ejecuta código de 26 estudiantes** y carga ficheros TMX que ellos
escriben. Es superficie de ataque real, no hipotética, y hasta esta auditoría
nadie la había mirado nunca.

La revisión encontró el motor en mejor forma de lo esperado, y eso no fue
suerte: hay decisiones correctas tomadas a conciencia —`orjson` en vez de
`pickle` para persistir, `register_eval=False` al crear el intérprete de Lua,
cero dependencias de red—. El problema de las decisiones correctas no escritas
es que se deshacen sin querer: alguien mete `pickle` porque «es más rápido para
guardar un dataclass» y nadie se entera.

Esta prueba convierte «está bien hoy» en «el CI falla el día que deje de
estarlo». No busca vulnerabilidades: fija invariantes.

Qué se comprobó a mano, y sale bien
-----------------------------------
* Una bomba de entidades XML (*billion laughs*) en un `.tmx`: no se expande.
* Un tileset externo con travesía de rutas (`../../../Windows/win.ini`): se
  rechaza sin leer el fichero.

Los dos casos quedan abajo como prueba, porque son exactamente lo que un
estudiante curioso intentará.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pygame
import pytest

RAIZ = Path(__file__).resolve().parent.parent
MOTOR = (RAIZ / "src" / "engine", RAIZ / "src" / "framework")


def _modulos_del_motor() -> list[Path]:
    """Sólo motor y framework: `src/stages/` es de estudiantes (invariante 1)."""
    return [p for base in MOTOR for p in base.rglob("*.py")]


class TestNadaQueEjecuteCodigoAjeno:
    #: `pickle` y compañía ejecutan código al deserializar. Una partida guardada
    #: en pickle es ejecución arbitraria disfrazada de fichero de guardado, y el
    #: fichero lo puede editar cualquiera.
    PROHIBIDOS = {"pickle", "cPickle", "marshal", "shelve", "dill"}

    def test_el_motor_no_deserializa_con_pickle(self) -> None:
        culpables = []
        for ruta in _modulos_del_motor():
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    nombres = {a.name.split(".")[0] for a in nodo.names}
                elif isinstance(nodo, ast.ImportFrom):
                    nombres = {(nodo.module or "").split(".")[0]}
                else:
                    continue
                if nombres & self.PROHIBIDOS:
                    culpables.append(f"{ruta.relative_to(RAIZ)}:{nodo.lineno}")
        assert not culpables, (
            "el motor persiste con orjson justamente para no ejecutar código al "
            f"cargar; esto lo rompe: {culpables}"
        )

    def test_el_motor_no_usa_eval_ni_exec_ni_shell(self) -> None:
        """Sólo el `compile` **suelto** cuenta.

        La primera versión de esta prueba miraba el nombre de la función sin
        mirar de qué módulo colgaba, y señaló `re.compile` en
        `academic/progress.py` como ejecución dinámica. Es una expresión
        regular compilada, lo más inocente que hay. Una prueba de seguridad que
        grita por `re.compile` se desactiva a la semana, y entonces deja de
        avisar del día que aparezca un `exec` de verdad.
        """
        sueltas = {"eval", "exec", "compile"}
        con_modulo = {("os", "system"), ("os", "popen"),
                      ("subprocess", "call"), ("subprocess", "run"),
                      ("subprocess", "Popen"), ("subprocess", "check_output")}
        culpables = []
        for ruta in _modulos_del_motor():
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), str(ruta))
            for nodo in ast.walk(arbol):
                if not isinstance(nodo, ast.Call):
                    continue
                f = nodo.func
                if isinstance(f, ast.Name) and f.id in sueltas:
                    culpables.append(
                        f"{ruta.relative_to(RAIZ)}:{nodo.lineno} → {f.id}()",
                    )
                elif (isinstance(f, ast.Attribute)
                        and isinstance(f.value, ast.Name)
                        and (f.value.id, f.attr) in con_modulo):
                    culpables.append(
                        f"{ruta.relative_to(RAIZ)}:{nodo.lineno} "
                        f"→ {f.value.id}.{f.attr}()",
                    )
        assert not culpables, f"ejecución dinámica en el motor: {culpables}"

    def test_el_motor_no_abre_conexiones_de_red(self) -> None:
        """Sin red no hay exfiltración posible, y eso es lo que hace que el
        resto de riesgos de este proyecto sean locales y menores. Es la
        propiedad más valiosa de las tres y la más fácil de perder."""
        red = {"socket", "requests", "urllib", "http", "ftplib", "smtplib",
               "telnetlib", "asyncio"}
        culpables = []
        for ruta in _modulos_del_motor():
            arbol = ast.parse(ruta.read_text(encoding="utf-8"), str(ruta))
            for nodo in ast.walk(arbol):
                if isinstance(nodo, ast.Import):
                    nombres = {a.name.split(".")[0] for a in nodo.names}
                elif isinstance(nodo, ast.ImportFrom):
                    nombres = {(nodo.module or "").split(".")[0]}
                else:
                    continue
                if nombres & red:
                    culpables.append(f"{ruta.relative_to(RAIZ)}:{nodo.lineno}")
        assert not culpables, (
            f"el motor ha ganado una dependencia de red: {culpables}. "
            f"Si es deliberada, hay que revisar qué datos de alumnos salen"
        )


class TestElInterpreteDeLua:
    def test_se_crea_sin_eval(self) -> None:
        """`register_eval=False` desactiva `eval` dentro de Lua. El scripting
        es un extra opcional, pero si se instala pasa a ejecutar guiones que
        alguien más escribió."""
        fuente = (RAIZ / "src" / "framework" / "ai" / "lua_script.py").read_text(
            encoding="utf-8",
        )
        assert "register_eval=False" in fuente, (
            "LuaRuntime se está creando sin desactivar eval"
        )


class TestUnTmxHostilNoRompeElCargador:
    @pytest.fixture(autouse=True)
    def _video(self):
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 240))

    def test_una_bomba_de_entidades_no_se_expande(self, tmp_path) -> None:
        """*Billion laughs*: 5 niveles de entidades anidadas son ~10^5 caracteres
        desde un fichero de 400 bytes. Con expansión, la carga se come la RAM."""
        from src.framework.stage.stage_loader import StageLoader

        bomba = tmp_path / "bomba.tmx"
        bomba.write_text(
            '<?xml version="1.0"?>\n'
            "<!DOCTYPE map [\n"
            ' <!ENTITY a "aaaaaaaaaa">\n'
            ' <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">\n'
            ' <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">\n'
            ' <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">\n'
            ' <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;&d;&d;">\n'
            "]>\n"
            '<map version="1.10" orientation="orthogonal" width="10" '
            'height="10" tilewidth="16" tileheight="16">\n'
            ' <properties><property name="nombre" value="&e;"/></properties>\n'
            "</map>",
            encoding="utf-8",
        )
        StageLoader.clear_tmx_cache()

        # AUD-317 — la guarda tiene que cortar la bomba **antes** de expandir:
        # si el rechazo llega tarde y por otro motivo, la prueba no demuestra
        # que la expansión esté acotada, sólo que el cargador no reventó.
        with pytest.raises(Exception) as fallo:
            StageLoader.load(bomba)
        assert "entidad" in str(fallo.value).lower(), (
            "el mapa bomba debe rechazarse por la guarda de entidades XML, no "
            "por un fallo tardío del parser: ese es el único rechazo que "
            "prueba que nada se expandió"
        )

    def test_una_travesia_real_se_rechaza_por_geometria(self, tmp_path, monkeypatch) -> None:
        """AUD-317 — el test de arriba se libraba porque `win.ini` no es un
        tileset; una travesía hacia un fichero que sí lo parece se leería. La
        guarda tiene que cortarla por geometría: ninguna `source=` puede
        resolver fuera del árbol del juego."""
        from src.engine.core import settings as cfg
        from src.framework.stage.stage_loader import StageLoader

        arbol = tmp_path / "arbol"
        (arbol / "assets" / "maps").mkdir(parents=True)
        objetivo = tmp_path / "fuera.txt"
        objetivo.write_text("secreto", encoding="utf-8")
        monkeypatch.setattr(cfg, "PROJECT_ROOT", arbol)

        mapa = arbol / "assets" / "maps" / "travesia.tmx"
        mapa.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<map version="1.10" orientation="orthogonal" width="4" height="4" '
            'tilewidth="16" tileheight="16">\n'
            ' <tileset firstgid="1" source="../../../fuera.txt"/>\n'
            ' <layer id="1" name="Terrain" width="4" height="4">'
            '<data encoding="csv">0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0</data></layer>\n'
            "</map>",
            encoding="utf-8",
        )
        StageLoader.clear_tmx_cache()

        with pytest.raises(Exception) as fallo:
            StageLoader.load(mapa)
        assert "hostil" in str(fallo.value).lower(), (
            "una source= que escapa del árbol debe rechazarse por la guarda, "
            "no por lo que le pase a pytmx con el fichero"
        )

    def test_un_tileset_con_travesia_de_rutas_se_rechaza(self, tmp_path) -> None:
        """`source="../../../Windows/win.ini"` — el intento evidente de que el
        motor lea un fichero de fuera del árbol del juego."""
        from src.framework.stage.stage_loader import StageLoader

        mapa = tmp_path / "traversal.tmx"
        mapa.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<map version="1.10" orientation="orthogonal" renderorder="right-down"'
            ' width="4" height="4" tilewidth="16" tileheight="16" infinite="0">\n'
            ' <tileset firstgid="1" source="../../../../../../Windows/win.ini"/>\n'
            ' <layer id="1" name="Terrain" width="4" height="4">'
            '<data encoding="csv">0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0</data></layer>\n'
            "</map>",
            encoding="utf-8",
        )
        StageLoader.clear_tmx_cache()

        with pytest.raises(Exception) as fallo:
            StageLoader.load(mapa)
        # Se rechaza por no ser un tileset, sin llegar a interpretar el fichero.
        assert "tileset" in str(fallo.value).lower()
