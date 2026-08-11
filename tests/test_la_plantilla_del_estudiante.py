"""AUD-417 — la plantilla que copian los veintiséis sacaba 64,6 %.

El defecto
==========
`student_templates/stage_template/stage_template.tmx` es el fichero que copia
todo el mundo en la primera clase. Medido con la rúbrica del propio curso
(`scripts/grade_stage.py`), sacaba **84/130 = 64,6 %**: sin enemigos, sin
coleccionables, sin `climate`, sin `author`, con un solo punto de control y sin
un solo salto exigente.

O sea que el punto de partida arrancaba suspendiendo, y encima en silencio:
`validate_tmx.py` la daba por `[OK]` porque ninguna de esas cosas es un error
de formato (eso se arregló en AUD-416).

Qué se hizo
===========
Se regeneró desde cero con `tools/generate_stage_template.py`, con **un
ejemplar de cada cosa** que un nivel puede tener. No es un nivel para jugar: es
un catálogo que se abre en Tiled y se lee. Un estudiante aprende más borrando
un enemigo que le sobra que buscando en la documentación cómo se coloca el
primero.

Por qué se genera en vez de editarse
====================================
Mismo motivo que `stage_mecanicas` desde AUD-153: un defecto en este fichero se
multiplica por veintiséis antes de que nadie lo ejecute, así que conviene que
haya una prueba comprobando que el fichero del repositorio y su generador
siguen de acuerdo. El *porqué* de cada objeto vive en el generador, no perdido
en un XML de 200 líneas.
"""
from __future__ import annotations

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = _RAIZ / "student_templates" / "stage_template" / "stage_template.tmx"
GENERADOR = _RAIZ / "tools" / "generate_stage_template.py"

#: Lo que la plantilla debe demostrar. Cada uno está por un motivo distinto y
#: quitarlo deja al estudiante sin un ejemplo de algo que va a necesitar.
TIPOS_ESPERADOS = {
    "PlayerSpawn", "Checkpoint", "NextTrigger", "Slope",
    "Walker", "Flying", "Shooter",
    "Pickup", "Light", "MessageTrigger", "HazardZone", "Objective",
}


@pytest.fixture(scope="module")
def raiz() -> ET.Element:
    return ET.parse(PLANTILLA).getroot()


def _tipos(raiz: ET.Element, capa: str) -> set[str]:
    salida: set[str] = set()
    for og in raiz.findall("objectgroup"):
        if og.get("name") != capa:
            continue
        for o in og.findall("object"):
            t = o.get("type") or o.get("class") or ""
            if t:
                salida.add(t)
    return salida


def test_el_fichero_coincide_con_su_generador() -> None:
    """El trinquete. Sin esto, alguien edita el TMX a mano, el generador se
    queda viejo y la siguiente ejecución le borra los cambios sin avisar."""
    r = subprocess.run(
        [sys.executable, str(GENERADOR), "--check"],
        capture_output=True, text=True, cwd=str(_RAIZ),
    )
    assert r.returncode == 0, (
        f"la plantilla del repositorio no coincide con lo que produce su "
        f"generador; ejecuta `python tools/generate_stage_template.py`.\n"
        f"{r.stdout}{r.stderr}"
    )


class TestSacaLaNotaQuePide:
    """La medición que motivó el lote."""

    @staticmethod
    @pytest.fixture(scope="class")
    def nota() -> dict:
        """`staticmethod` a propósito: una fixture de clase escrita como método
        de instancia avisa —corre una vez y cada prueba recibe otra instancia—,
        y ese aviso es un ruido que enseña a ignorar los avisos."""
        import json

        r = subprocess.run(
            [sys.executable, "scripts/grade_stage.py", str(PLANTILLA), "--json"],
            capture_output=True, text=True, cwd=str(_RAIZ),
        )
        salida = r.stdout
        return json.loads(salida[salida.find("["):])[0]

    def test_no_baja_de_la_nota_medida(self, nota: dict) -> None:
        """Iba en 64,6 % y quedó en 100 %.

        El umbral se pone en 90 y no en 100 para que añadir una categoría
        nueva a la rúbrica no ponga esto rojo el mismo día — pero si baja de
        90, la plantilla ha vuelto a dejar de enseñar algo.
        """
        pct = 100 * nota["score"] / nota["max_score"]
        assert pct >= 90, (
            f"la plantilla saca {pct:.1f} % en la rúbrica del curso. El "
            f"estudiante que la copia empieza cuesta arriba: "
            f"{ {k: v['msg'] for k, v in nota['categories'].items() if v['score'] < v['max']} }"
        )

    def test_declara_author(self, nota: dict) -> None:
        """La que costaba 3 puntos y ninguna herramienta nombraba (AUD-416)."""
        assert nota["categories"]["metadata"]["score"] == \
            nota["categories"]["metadata"]["max"]

    def test_tiene_un_salto_exigente(self, nota: dict) -> None:
        """Medido: el hueco es de 80 px y el salto llega a 85,5.

        Exigente y cruzable sin salto aéreo, que es lo que enseña a medir un
        salto sin dejar fuera a quien no lo ha desbloqueado.
        """
        assert "no tiene ningún salto exigente" not in \
            nota["categories"]["design_pacing"]["msg"]


class TestEnsenaLoQueTieneQueEnsenar:
    def test_trae_un_ejemplar_de_cada_cosa(self, raiz: ET.Element) -> None:
        faltan = TIPOS_ESPERADOS - _tipos(raiz, "Objects")
        assert not faltan, (
            f"la plantilla ya no demuestra estos tipos: {sorted(faltan)}. "
            "Quien la copie no tendrá un ejemplo de cómo se colocan"
        )

    def test_la_capa_collision_solo_lleva_solid_y_platform(
        self, raiz: ET.Element
    ) -> None:
        """El error que comete todo el mundo, y que un mapa del motor tiene.

        Un `HazardZone` en `Collision` se trata como **suelo sólido**: la
        trampa deja de hacer daño y encima se convierte en plataforma. La
        plantilla tiene que enseñar dónde va cada cosa.
        """
        assert _tipos(raiz, "Collision") <= {"Solid", "Platform"}

    def test_la_zona_de_dano_esta_en_objects(self, raiz: ET.Element) -> None:
        assert "HazardZone" in _tipos(raiz, "Objects")

    def test_tiene_las_ocho_capas(self, raiz: ET.Element) -> None:
        from src.framework.stage.stage_data import REQUIRED_LAYERS

        nombres = {line.get("name") for line in raiz.findall("layer")}
        nombres |= {og.get("name") for og in raiz.findall("objectgroup")}
        assert set(REQUIRED_LAYERS) <= nombres

    def test_el_author_pide_ser_cambiado(self, raiz: ET.Element) -> None:
        """Un campo en blanco se entrega en blanco."""
        props = raiz.find("properties")
        assert props is not None
        autor = [p.get("value") for p in props.findall("property")
                 if p.get("name") == "author"]
        assert autor and autor[0].strip(), "la plantilla no declara 'author'"
        assert autor[0] != "", "el valor vacío se entrega vacío"
