"""
AUD-107 — las herramientas del profesor frente a lo que el motor sabe de verdad.

Tres defectos, un mismo patrón
==============================
Es la tercera vez esta semana que un calificador guarda su propia copia de algo
que el motor ya sabe, y la copia se queda vieja (AUD-104 en los ataques del
jefe, AUD-106 en los tipos del validador de TMX). Aquí:

1. `grade_stage` tenía una lista de doce enemigos escrita a mano. Cuatro de
   esos nombres no existen en el motor y faltaban veintidós de los treinta
   reales, así que el informe decía «2 enemy(ies) placed» sobre un mapa con
   siete.
2. `grade_stage` sólo reconocía tilesets incrustados en el `.tmx`, no los
   `.tsx` externos —la forma que recomienda Tiled—, y restaba 5 puntos a un
   mapa cuyo tileset estaba en su sitio.
3. `grade_boss`, recorriendo un directorio, calificaba **todos** los `.py` como
   si cada uno debiera ser un jefe: sprites, arena, escena e introducción
   sacaban 0/100 y hundían la media que se imprime al final.

Cada prueba de aquí fija la conducta corregida contra el caso real que la
destapó, no contra un ejemplo inventado: si alguien vuelve a escribir la lista
a mano, estas pruebas se ponen rojas.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def _cargar(nombre: str):
    """Importa un script de `scripts/`, que no es un paquete."""
    ruta = RAIZ / "scripts" / f"{nombre}.py"
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    assert spec and spec.loader
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def gs():
    return _cargar("grade_stage")


@pytest.fixture(scope="module")
def gb():
    return _cargar("grade_boss")


# ---------------------------------------------------------------- enemigos
#: Los cuatro que la lista escrita a mano nombraba y el motor no tiene. Son de
#: un bestiario anterior; llevaban ahí desde entonces.
FANTASMAS = ("MushMom", "Bat", "Skitter", "Mantis")

#: Cuatro del bestiario oficial de la Zona 2 que la lista no incluía, y que son
#: exactamente los que el mapa de stage2_2 coloca.
REALES_QUE_FALTABAN = (
    "WalkerGuardia", "FlyingBoa", "ShooterSerpienteArbol", "WalkerSerpientePequena",
)


def test_los_tipos_de_enemigo_salen_del_registro_del_motor(gs):
    tipos = gs._tipos_de_enemigo()
    from src.framework.entities import entity_factory
    from src.framework.stage.stage_loader import StageLoader
    entity_factory.ensure_registered()
    assert tipos == set(StageLoader._entity_registry), (
        "la lista de enemigos debe ser el registro del motor, no una copia"
    )


@pytest.mark.parametrize("nombre", REALES_QUE_FALTABAN)
def test_reconoce_los_enemigos_que_la_lista_a_mano_olvidaba(gs, nombre):
    assert nombre in gs._tipos_de_enemigo()


@pytest.mark.parametrize("nombre", FANTASMAS)
def test_no_reconoce_enemigos_que_el_motor_no_tiene(gs, nombre):
    assert nombre not in gs._tipos_de_enemigo(), (
        f"«{nombre}» no existe en el motor: aceptarlo haría pasar una errata"
    )


def test_cuenta_los_enemigos_que_el_estudiante_registro_el_mismo(gs):
    """La Soda coloca dos enemigos y **los dos** son suyos.

    `LaSodaWalkerRaton` y `LaSodaFlyingCucaracha` no están en el motor: los
    registra su propio paquete. Sin leerlo, el informe diría «0 enemigos» sobre
    un nivel poblado, que es justo lo que castiga hacer las cosas bien.
    """
    paquete = RAIZ / "src" / "stages" / "stage1_2_la_soda"
    if not paquete.is_dir():
        pytest.skip("la entrega de La Soda no está instalada")
    tipos = gs._tipos_de_enemigo(paquete)
    assert {"LaSodaWalkerRaton", "LaSodaFlyingCucaracha"} <= tipos


def test_el_mapa_de_stage2_2_declara_sus_siete_enemigos(gs):
    """El caso que destapó el fallo: se contaban 2 de 7."""
    tmx = RAIZ / "assets" / "maps" / "stage2_2" / "stage2_2.tmx"
    if not tmx.exists():
        pytest.skip("la entrega de stage2_2 no está instalada")
    informe = gs.grade_stage(tmx)
    assert informe["categories"]["enemies_placed"]["msg"] == "7 enemy(ies) placed"


# ---------------------------------------------------------------- tilesets
def _tmx_con_tileset_externo(carpeta: Path) -> Path:
    """Mapa mínimo que apunta a un `.tsx`, como hace Tiled por defecto."""
    (carpeta / "cuadros.png").write_bytes(
        # PNG de 1x1 válido; sólo hace falta que el fichero exista.
        bytes.fromhex(
            "89504e470d0a1a0a0000000d494844520000000100000001080600000"
            "01f15c4890000000a49444154789c6300010000050001"
            "0d0a2db40000000049454e44ae426082",
        ),
    )
    (carpeta / "cuadros.tsx").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<tileset version="1.10" name="cuadros" tilewidth="16" tileheight="16"'
        ' tilecount="1" columns="1">\n'
        ' <image source="cuadros.png" width="16" height="16"/>\n'
        "</tileset>\n",
        encoding="utf-8",
    )
    tmx = carpeta / "mapa.tmx"
    tmx.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<map version="1.10" orientation="orthogonal" renderorder="right-down"'
        ' width="4" height="4" tilewidth="16" tileheight="16">\n'
        ' <tileset firstgid="1" source="cuadros.tsx"/>\n'
        ' <layer id="1" name="Terrain" width="4" height="4">\n'
        '  <data encoding="csv">0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0</data>\n'
        " </layer>\n"
        "</map>\n",
        encoding="utf-8",
    )
    return tmx


def test_un_tileset_externo_tsx_cuenta_como_valido(gs, tmp_path):
    tmx = _tmx_con_tileset_externo(tmp_path)
    informe = gs.grade_stage(tmx)
    assert informe["categories"]["tileset_valid"]["score"] == gs.RUBRIC["tileset_valid"]


def test_un_tsx_que_apunta_a_una_imagen_que_no_existe_sigue_fallando(gs, tmp_path):
    """El arreglo no debe convertirse en un aprobado general."""
    tmx = _tmx_con_tileset_externo(tmp_path)
    (tmp_path / "cuadros.png").unlink()
    informe = gs.grade_stage(tmx)
    assert informe["categories"]["tileset_valid"]["score"] == 0


# ------------------------------------------------------------------- jefes
def test_solo_son_jefes_los_ficheros_con_una_subclase_de_bossbase(gb, tmp_path):
    jefe = tmp_path / "mi_jefe.py"
    jefe.write_text(
        "from src.framework.entities.boss_base import BossBase\n"
        "class MiJefe(BossBase):\n    pass\n",
        encoding="utf-8",
    )
    sprites = tmp_path / "sprites.py"
    sprites.write_text("HOJA = 'sprites/jefe.png'\n", encoding="utf-8")

    assert gb._define_un_jefe(jefe)
    assert not gb._define_un_jefe(sprites), (
        "un módulo de sprites no es un jefe mal hecho: no es un jefe"
    )


def test_un_fichero_ilegible_se_califica_en_vez_de_descartarse(gb, tmp_path):
    """Si no compila, el informe debe decirlo, no callarse."""
    roto = tmp_path / "roto.py"
    roto.write_text("class MiJefe(BossBase:\n", encoding="utf-8")
    assert gb._define_un_jefe(roto)


def test_el_paquete_de_un_jefe_real_se_califica_por_su_jefe(gb):
    """boss_paburu trae siete módulos; sólo uno es el jefe.

    Antes se calificaban los siete y la media impresa era 14,3 % sobre un jefe
    que saca 100.
    """
    paquete = RAIZ / "src" / "stages" / "boss_paburu"
    if not paquete.is_dir():
        pytest.skip("la entrega de Paburu no está instalada")
    ficheros = [
        f for f in paquete.rglob("*.py")
        if f.name != "__init__.py" and "__pycache__" not in f.parts
    ]
    jefes = [f for f in ficheros if gb._define_un_jefe(f)]
    assert len(ficheros) > 1, "el paquete debería tener varios módulos"
    assert len(jefes) == 1, f"se esperaba un solo jefe, hay {len(jefes)}: {jefes}"
    assert gb.grade_boss(jefes[0])["percentage"] == 100.0
