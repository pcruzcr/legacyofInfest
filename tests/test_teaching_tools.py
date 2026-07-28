"""
Module: test_teaching_tools
System: tests
Academic Unit: N/A

Las herramientas del profesor y del estudiante, invocadas como se invocan.

AUD-084 — el fallo que rompía el modelo pedagógico
--------------------------------------------------
`validate_tmx.py` y `grade_stage.py` hacían `ruta.relative_to(_PROJECT_ROOT)`
sólo para imprimir un nombre corto. Eso lanza `ValueError` si una ruta es
relativa y la otra absoluta. Resultado: ambas se caían con un traceback ante
lo único que un ser humano escribe:

    python scripts/validate_tmx.py mi_escenario.tmx

La CI no lo veía porque `--ci` descubre las rutas ya resueltas. Así que la
herramienta que existe para que un estudiante revise su mapa **antes** de
entregarlo fallaba en el primer intento, y el calificador del profesor
también.

Estas pruebas ejecutan los scripts como subprocesos, con rutas relativas,
desde el directorio del proyecto. Importar la función y llamarla no habría
detectado nada: el fallo vivía en `main()`, en la parte que imprime.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
TMX_PLANTILLA = "student_templates/stage_template/stage_template.tmx"
TMX_STAGE0 = "assets/maps/stage0/stage0.tmx"
PY_JEFE = "student_templates/boss_template/boss_template.py"


def _ejecutar(*argumentos: str, entorno: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Lanza un script desde la raíz del proyecto, como haría una persona.

    Se hereda el entorno real y sólo se fuerzan los controladores de SDL. La
    primera versión de este ayudante construía un entorno mínimo desde cero y
    dejaba fuera las rutas de los paquetes, así que los scripts fallaban por
    no encontrar pygame y la prueba culpaba al código equivocado.
    """
    import os

    env = dict(os.environ)
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    if entorno:
        env.update(entorno)
    return subprocess.run(
        [sys.executable, *argumentos],
        cwd=RAIZ, capture_output=True, text=True, timeout=120, env=env,
    )


class TestLasHerramientasAceptanRutasRelativas:
    """Nadie escribe rutas absolutas a mano."""

    @pytest.mark.parametrize(
        ("script", "objetivo"),
        [
            ("scripts/validate_tmx.py", TMX_PLANTILLA),
            ("scripts/validate_tmx.py", TMX_STAGE0),
            ("scripts/grade_stage.py", TMX_STAGE0),
            ("scripts/grade_boss.py", PY_JEFE),
        ],
    )
    def test_no_revienta_con_ruta_relativa(self, script, objetivo):
        r = _ejecutar(script, objetivo)
        assert "Traceback" not in r.stderr, (
            f"{script} se cae con una ruta relativa:\n{r.stderr[-700:]}"
        )
        assert r.returncode in (0, 1), f"código de salida {r.returncode}"

    @pytest.mark.parametrize(
        ("script", "objetivo"),
        [
            ("scripts/validate_tmx.py", TMX_PLANTILLA),
            ("scripts/grade_stage.py", TMX_STAGE0),
        ],
    )
    def test_absoluta_y_relativa_dan_el_mismo_veredicto(self, script, objetivo):
        """Cambiar cómo se escribe la ruta no puede cambiar la nota."""
        rel = _ejecutar(script, objetivo)
        absoluta = _ejecutar(script, str(RAIZ / objetivo))
        assert rel.returncode == absoluta.returncode

    def test_un_archivo_fuera_del_proyecto_no_revienta(self, tmp_path):
        """El profesor guarda las entregas donde quiere, no dentro del repo."""
        copia = tmp_path / "entrega_alumno.tmx"
        copia.write_bytes((RAIZ / TMX_PLANTILLA).read_bytes())
        r = _ejecutar("scripts/validate_tmx.py", str(copia))
        assert "Traceback" not in r.stderr, (
            f"validar una entrega fuera del repositorio revienta:\n{r.stderr[-700:]}"
        )


class TestElAyudanteDeRutasNoLanza:
    """El contrato del módulo, sin subprocesos."""

    @pytest.mark.parametrize(
        "entrada",
        [
            "assets/maps/stage0/stage0.tmx",       # relativa dentro
            "/tmp/fuera/del/proyecto.tmx",         # absoluta fuera
            "../vecino/cosa.tmx",                  # relativa hacia arriba
            "",                                    # vacía
        ],
    )
    def test_nunca_lanza(self, entrada):
        from scripts._cli_paths import display_path

        resultado = display_path(Path(entrada), RAIZ)
        assert isinstance(resultado, str)

    def test_acorta_cuando_puede(self):
        from scripts._cli_paths import display_path

        completa = RAIZ / "assets" / "maps" / "stage0" / "stage0.tmx"
        assert display_path(completa, RAIZ) == str(
            Path("assets/maps/stage0/stage0.tmx"))

    def test_deja_intacto_lo_que_no_puede_acortar(self):
        from scripts._cli_paths import display_path

        fuera = Path("/una/ruta/completamente/ajena.tmx")
        assert display_path(fuera, RAIZ) == str(fuera)


class TestElCalificadorPuntuaAlgoReal:
    """Una nota que sale igual para todo no informa de nada."""

    def test_stage0_saca_mejor_nota_que_la_plantilla_vacia(self):
        """El escenario terminado tiene que puntuar por encima del esqueleto."""
        import json

        from scripts.grade_stage import grade_stage

        completo = grade_stage(RAIZ / TMX_STAGE0)
        plantilla = grade_stage(RAIZ / TMX_PLANTILLA)
        assert completo["percentage"] > plantilla["percentage"], (
            f"stage0 saca {completo['percentage']}% y la plantilla vacía "
            f"{plantilla['percentage']}%: la rúbrica no distingue trabajo hecho "
            "de trabajo sin hacer"
        )
        json.dumps(completo)   # la salida --json tiene que ser serializable

    def test_un_archivo_inexistente_da_cero_sin_reventar(self):
        from scripts.grade_stage import grade_stage

        r = grade_stage(RAIZ / "no_existe_este_archivo.tmx")
        assert r["percentage"] == 0.0
        assert r["errors"]


class TestElEstudianteSinDependenciasRecibeUnaInstruccion:
    """AUD-085 — un traceback en el primer minuto no enseña nada."""

    def test_sin_pygame_dice_que_ejecutar(self):
        """Se simula el estado real de quien acaba de clonar el repositorio."""
        r = _ejecutar(
            "scripts/validate_tmx.py", TMX_STAGE0,
            # Sin las rutas de paquetes, pygame deja de ser importable.
            entorno={"PYTHONNOUSERSITE": "1", "PYTHONPATH": "", "PYTHONHOME": ""},
        )
        salida = r.stdout + r.stderr
        if "pygame" not in salida.lower():
            pytest.skip("pygame sigue disponible en este entorno; nada que simular")
        assert "Traceback" not in r.stderr, (
            f"el validador vuelca la pila en vez de decir qué hacer:\n{r.stderr[-500:]}"
        )
        assert "pip install" in salida, (
            "el mensaje no dice cómo resolverlo"
        )

    def test_el_comprobador_no_lanza_nunca(self):
        from scripts.validate_tmx import _comprobar_dependencias

        resultado = _comprobar_dependencias()
        assert resultado is None or isinstance(resultado, str)


class TestElCalificadorPuntuaDisenoYNoSoloEstructura:
    """F2.4 — la rúbrica medía que los objetos estuvieran, no que se jugara.

    Todo lo que había antes se puede satisfacer sin diseñar nada: colocar las
    capas obligatorias, un spawn, cuatro checkpoints y algunos enemigos en un
    rectángulo vacío daba más del 90 %. `framework.stage.level_metrics` ya
    sabía responder a las preguntas que importan —¿se llega a la salida?, ¿hay
    saltos imposibles?, ¿hay plataformas huérfanas?— y llevaba desde su
    creación sin conectarse a nada que calificara.
    """

    @staticmethod
    def _calificar(ruta_relativa: str) -> dict:
        from scripts.grade_stage import grade_stage

        return grade_stage(RAIZ / ruta_relativa)

    def test_la_rubrica_incluye_las_tres_categorias_de_diseno(self):
        from scripts.grade_stage import RUBRIC

        for cat in ("design_completable", "design_geometry", "design_pacing"):
            assert cat in RUBRIC, f"falta la categoría {cat}"
        diseno = sum(RUBRIC[c] for c in
                     ("design_completable", "design_geometry", "design_pacing"))
        assert diseno / sum(RUBRIC.values()) > 0.15, (
            f"el diseño pesa sólo el {diseno / sum(RUBRIC.values()):.0%} de la "
            "nota: no cambia el resultado de nadie"
        )

    def test_stage0_se_puede_completar(self):
        r = self._calificar(TMX_STAGE0)
        assert r["categories"]["design_completable"]["score"] > 0, (
            "el escenario de referencia del juego no se puede terminar según "
            "el calificador"
        )
        assert r["design"]["exit_reachable"] is True

    def test_el_informe_expone_las_metricas_crudas(self):
        """El profesor tiene que poder ver el dato, no sólo la nota."""
        r = self._calificar(TMX_STAGE0)
        for clave in ("exit_reachable", "orphan_platforms", "impossible_ledges",
                      "demanding_gaps", "worst_checkpoint_gap"):
            assert clave in r["design"], f"falta la métrica {clave}"

    def test_un_nivel_que_no_carga_no_tumba_el_calificador(self, tmp_path):
        """Un calificador que revienta con una entrega mala es inútil."""
        from scripts.grade_stage import grade_stage

        roto = tmp_path / "roto.tmx"
        roto.write_text(
            '<?xml version="1.0"?><map version="1.10" width="10" height="10" '
            'tilewidth="16" tileheight="16"><layer name="Terrain" width="10" '
            'height="10"><data encoding="csv">0</data></layer></map>',
            encoding="utf-8",
        )
        r = grade_stage(roto)
        assert r["categories"]["design_completable"]["score"] == 0
        assert "no se pudo analizar" in \
               r["categories"]["design_completable"]["msg"]
        assert isinstance(r["percentage"], float)

    def test_avisa_de_que_una_arena_de_jefe_usa_otra_rubrica(self):
        """La arena del juego puntúa 0 en alcanzabilidad, y no es un fallo suyo.

        `exit_is_reachable` recorre plataformas; en una arena la salida se abre
        al derrotar al jefe. Sin este aviso, un profesor suspendería una
        entrega correcta.
        """
        r = self._calificar("assets/maps/boss_venado/boss_venado.tmx")
        if r["categories"]["design_completable"]["score"] > 0:
            pytest.skip("la arena ahora sí es alcanzable andando")
        assert any("grade_boss" in w for w in r["warnings"]), (
            "no se avisa de que a una arena le corresponde otra rúbrica"
        )

    def test_los_tipos_validos_salen_del_motor_y_no_de_una_copia(self):
        """F2.4 — la lista escrita a mano marcaba `Light` como tipo inexistente.

        Un calificador que da error sobre lo que el motor acepta enseña a
        desconfiar de él.
        """
        from scripts.grade_stage import _tipos_no_enemigos

        tipos = _tipos_no_enemigos()
        for esperado in ("Light", "MessageTrigger_Once", "CameraLock"):
            assert esperado in tipos, f"el calificador no conoce '{esperado}'"

    def test_stage0_no_produce_avisos_de_tipos_desconocidos(self):
        r = self._calificar(TMX_STAGE0)
        desconocidos = [w for w in r["warnings"] if "Unknown enemy types" in w]
        assert not desconocidos, (
            f"el calificador marca tipos válidos como desconocidos: {desconocidos}"
        )


class TestElPrevisualizadorCierraElCicloDelEstudiante:
    """F3.2 — hoy el estudiante coloca objetos en Tiled y no ve nada.

    Los focos son el caso peor: en Tiled un `Light` es un rectángulo de 16x16
    idéntico a cualquier otro objeto, así que ajustar `radius` o `intensity`
    significaba lanzar el juego, cargar la partida y caminar hasta la zona.
    Una partida entera por cada intento.
    """

    def test_dibuja_el_mapa_entero_y_no_una_ventana(self, tmp_path):
        """El objetivo es ver la composición del nivel de un vistazo."""
        import xml.etree.ElementTree as ET

        r = _ejecutar("scripts/preview_tmx.py", TMX_STAGE0,
                      "--salida", str(tmp_path / "vista.png"))
        assert "Traceback" not in r.stderr, r.stderr[-600:]
        salida = tmp_path / "vista.png"
        assert salida.exists(), "no se generó la imagen"

        raiz = ET.parse(RAIZ / TMX_STAGE0).getroot()
        esperado = (int(raiz.get("width")) * int(raiz.get("tilewidth")),
                    int(raiz.get("height")) * int(raiz.get("tileheight")))
        import pygame
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 180))
        assert pygame.image.load(str(salida)).get_size() == esperado, (
            "la vista no cubre el mapa completo"
        )

    def test_la_imagen_no_sale_en_blanco(self, tmp_path):
        """Una vista previa vacía es peor que ninguna: engaña."""
        import pygame

        destino = tmp_path / "vista.png"
        _ejecutar("scripts/preview_tmx.py", TMX_STAGE0, "--salida", str(destino))
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 180))
        pix = pygame.surfarray.array3d(
            pygame.image.load(str(destino))).astype(float)
        assert pix.std() > 10.0, (
            f"la imagen es casi uniforme (desviación {pix.std():.1f}): no se "
            "está dibujando el mapa"
        )

    def test_los_focos_se_dibujan_con_su_radio(self, tmp_path):
        """La razón de ser de la herramienta.

        Se compara la vista con y sin el calco de objetos: los círculos de
        alcance tienen que aportar píxeles nuevos.
        """
        import numpy as np
        import pygame

        con = tmp_path / "con.png"
        sin = tmp_path / "sin.png"
        _ejecutar("scripts/preview_tmx.py", TMX_STAGE0, "--salida", str(con))
        _ejecutar("scripts/preview_tmx.py", TMX_STAGE0, "--salida", str(sin),
                  "--sin-luz")
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 180))
        a = pygame.surfarray.array3d(pygame.image.load(str(con))).astype(float)
        b = pygame.surfarray.array3d(pygame.image.load(str(sin))).astype(float)
        assert not np.array_equal(a, b), (
            "--sin-luz da la misma imagen que con luz"
        )

    def test_la_hora_cambia_la_vista(self, tmp_path):
        """Permite comprobar que un nivel se ve de noche antes de jugarlo."""
        import pygame

        dia, noche = tmp_path / "dia.png", tmp_path / "noche.png"
        _ejecutar("scripts/preview_tmx.py", TMX_STAGE0, "--salida", str(dia),
                  "--hora", "12")
        _ejecutar("scripts/preview_tmx.py", TMX_STAGE0, "--salida", str(noche),
                  "--hora", "23")
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((320, 180))
        d = pygame.surfarray.array3d(pygame.image.load(str(dia))).astype(float)
        n = pygame.surfarray.array3d(pygame.image.load(str(noche))).astype(float)
        assert n.mean() < d.mean(), (
            f"la noche ({n.mean():.1f}) no sale más oscura que el día "
            f"({d.mean():.1f})"
        )

    def test_informa_de_lo_que_encontro(self, tmp_path):
        """El resumen es la mitad del valor: dice si falta algo."""
        r = _ejecutar("scripts/preview_tmx.py", TMX_STAGE0,
                      "--salida", str(tmp_path / "v.png"))
        for etiqueta in ("focos", "entidades", "puntos de control",
                         "clima", "estación"):
            assert etiqueta in r.stdout, f"el resumen no menciona '{etiqueta}'"

    def test_un_mapa_roto_explica_qué_hacer_en_vez_de_reventar(self, tmp_path):
        roto = tmp_path / "roto.tmx"
        roto.write_text('<?xml version="1.0"?><map></map>', encoding="utf-8")
        r = _ejecutar("scripts/preview_tmx.py", str(roto),
                      "--salida", str(tmp_path / "v.png"))
        assert "Traceback" not in r.stderr, (
            f"vuelca la pila con un mapa roto:\n{r.stderr[-400:]}"
        )
        assert "validate_tmx" in r.stdout, (
            "no remite al validador, que es la herramienta que diagnostica"
        )


class TestElEmpaquetadoEstaBienDeclarado:
    """F3.3 — no se construye el .exe en la suite, pero sí se vigila la receta.

    Compilar con PyInstaller tarda minutos y necesita la herramienta instalada,
    así que no cabe en una suite que corre en cada cambio. Lo que sí cabe —y es
    donde falla este tipo de guion— es comprobar que la lista de datos y de
    importaciones ocultas siga coincidiendo con el proyecto real. Un ejecutable
    al que le falta `locale/` arranca y muestra la interfaz sin traducir.
    """

    def test_empaqueta_todas_las_carpetas_de_datos_que_existen(self):
        from scripts.build_executable import DATOS

        for carpeta in DATOS:
            assert (RAIZ / carpeta).is_dir(), (
                f"el empaquetado declara '{carpeta}', que no existe"
            )

    def test_no_olvida_ninguna_carpeta_de_datos_necesaria(self):
        """Las tres que el juego lee en tiempo de ejecución."""
        from scripts.build_executable import DATOS

        for imprescindible in ("assets", "locale"):
            assert imprescindible in DATOS, (
                f"sin '{imprescindible}' el ejecutable arranca roto"
            )

    def test_las_importaciones_ocultas_existen_de_verdad(self):
        """Un nombre mal escrito aquí no falla al construir: falla al ejecutar."""
        import importlib.util

        from scripts.build_executable import OCULTOS

        for modulo in OCULTOS:
            raiz = modulo.split(".")[0]
            if importlib.util.find_spec(raiz) is None:
                continue          # dependencia opcional no instalada
            assert importlib.util.find_spec(modulo) is not None, (
                f"el empaquetado declara '{modulo}', que no se puede importar"
            )

    def test_avisa_si_falta_pyinstaller_en_vez_de_reventar(self):
        r = _ejecutar("scripts/build_executable.py")
        assert "Traceback" not in r.stderr, r.stderr[-400:]
