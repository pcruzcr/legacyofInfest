"""AUD-814 — Contrato del Stage 4.1 reconstruido.

El TMX, los activos, el audio y los datos del nivel nuevo. Todo lo que
aquí se afirma sale del fichero real en disco, no del diseño: si el
generador y el mapa se desincronizan, estas pruebas lo dicen.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
TMX = RAIZ / "assets" / "maps" / "stage4_1" / "stage4_1.tmx"

MW, MH, TS = 960, 40, 16
ANCHO = 160


def _raiz() -> ET.Element:
    return ET.parse(TMX).getroot()


def _props(elemento: ET.Element) -> dict:
    grupo = elemento.find("properties")
    if grupo is None:
        return {}
    return {p.get("name"): p.get("value") for p in list(grupo)}


def _objetos(nombre_grupo: str) -> list:
    raiz = _raiz()
    for grupo in raiz.findall("objectgroup"):
        if grupo.get("name") == nombre_grupo:
            return list(grupo.findall("object"))
    return []


class TestTMXNuevo:
    def test_existe(self) -> None:
        assert TMX.is_file()

    def test_dimensiones_960x40(self) -> None:
        raiz = _raiz()
        assert int(raiz.get("width")) == MW
        assert int(raiz.get("height")) == MH
        assert int(raiz.get("tilewidth")) == TS

    def test_las_8_capas(self) -> None:
        nombres = {c.get("name") for c in _raiz().findall("layer")}
        assert {"BG_Far", "BG_Mid", "BG_Near", "Terrain", "Terrain_Detail",
                "FG_Overlay"} <= nombres
        grupos = {g.get("name") for g in _raiz().findall("objectgroup")}
        assert {"Collision", "Objects"} <= grupos

    def test_seis_tilesets_con_png(self) -> None:
        sets = _raiz().findall("tileset")
        assert len(sets) == 6
        for i, ts in enumerate(sets, start=1):
            assert int(ts.get("firstgid")) == (i - 1) * 256 + 1
            png = (RAIZ / "assets" / "tilesets"
                   / f"tileset_stage41_f{i}.png")
            assert png.is_file(), png

    def test_terreno_lleno_en_las_seis_fases(self) -> None:
        for capa in _raiz().findall("layer"):
            if capa.get("name") != "Terrain":
                continue
            vals = [int(x) for x in capa.find("data").text.strip().split(",")]
            assert len(vals) == MW * MH
            for fase in range(6):
                a, b = fase * ANCHO, (fase + 1) * ANCHO
                nz = sum(1 for y in range(MH) for x in range(a, b)
                         if vals[y * MW + x] != 0)
                # 8 filas de suelo x 160 columnas = 1280, más las lomas.
                assert nz >= 1280, (fase + 1, nz)

    def test_fondos_con_arte(self) -> None:
        # AUD-816: siluetas por grupos, nunca sábana. Cada plano trae
        # cientos de baldosas en grupos con huecos, no miles en línea.
        minimos = {"BG_Far": 150, "BG_Mid": 150, "BG_Near": 150,
                   "FG_Overlay": 150}
        for capa in _raiz().findall("layer"):
            nombre = capa.get("name")
            if nombre not in minimos:
                continue
            vals = [int(x) for x in capa.find("data").text.strip().split(",")]
            nz = sum(1 for v in vals if v != 0)
            assert minimos[nombre] <= nz <= 1500, (nombre, nz)

    def test_propiedades(self) -> None:
        props = _props(_raiz())
        assert props["stage_id"] == "stage4_1"
        assert props["zone"] == "4"
        assert props["climate"] == "clear"
        assert int(props["start_hour"]) == 10
        # Sin cielo=true el motor lo trata como interior y anula el clima.
        assert props.get("cielo") == "true"

    def test_bgm_resuelve(self) -> None:
        from src.framework.audio.dynamic_music import resolver_pista_de_musica
        props = _props(_raiz())
        assert resolver_pista_de_musica(props["bgm_track"]) is not None

    def test_siete_checkpoints(self) -> None:
        cps = [o for o in _objetos("Objects") if o.get("type") == "Checkpoint"]
        assert len(cps) == 7
        ids = sorted(int(_props(o)["checkpoint_id"]) for o in cps)
        assert ids == [1, 2, 3, 4, 5, 6, 7]

    def test_seis_slopes_en_elevaciones(self) -> None:
        slopes = [o for o in _objetos("Objects") if o.get("type") == "Slope"]
        # Seis rampas + tres cimas llanas (patrón AUD-477: la cima plana
        # evita que la cara de la bajada clave al jugador en el vértice).
        assert len(slopes) == 9
        for s in slopes:
            assert _props(s).get("sube") in ("derecha", "izquierda")
        llanas = [s for s in slopes
                  if (s.get("name") or "").startswith("cima_llana_")]
        assert len(llanas) == 3

    def test_bases_de_seguridad_bajo_rampas(self) -> None:
        """Sin suelo bajo el vano de cada elevación, saltar fuera de la
        rampa es caer al vacío. Tres bases a nivel del suelo llano."""
        bases = [o for o in _objetos("Collision")
                 if (o.get("type") == "Solid"
                     and (o.get("name") or "").startswith("base_"))]
        assert len(bases) == 3
        for base in bases:
            assert float(base.get("y")) == 32 * 16

    def test_friccion_musgo_lodo_sendero(self) -> None:
        zonas = [o for o in _objetos("Objects") if o.get("type") == "FrictionZone"]
        mats = {_props(z)["material"] for z in zonas}
        assert {"musgo", "lodo", "sendero", "polvo"} <= mats
        for z in zonas:
            props = _props(z)
            if props["material"] == "musgo":
                assert float(props["inercia"]) > 0.0
            if props["material"] == "lodo":
                assert float(props["multiplicador"]) < 1.0

    def test_viento_fase3(self) -> None:
        vientos = [o for o in _objetos("Objects") if o.get("type") == "WindZone"]
        assert len(vientos) == 1
        props = _props(vientos[0])
        assert float(props["fuerza_x"]) < 0.0

    def test_luces_verdes_fase6(self) -> None:
        luces = [o for o in _objetos("Objects") if o.get("type") == "Light"]
        assert len(luces) == 13
        for luz in luces:
            props = _props(luz)
            assert float(props["radius"]) >= 60.0
            assert float(props["intensity"]) == 0.0
            assert 800 * TS <= float(luz.get("x")) <= 950 * TS

    def test_cutscene_intro_nombra_paburu(self) -> None:
        escenas = [o for o in _objetos("Objects") if o.get("type") == "Cutscene"]
        assert len(escenas) == 2
        guiones = " ".join(_props(e).get("guion", "") for e in escenas)
        assert "Paburu" in guiones

    def test_dialogos_tres_espiritus_y_easter_egg(self) -> None:
        msgs = [o for o in _objetos("Objects")
                if o.get("type") == "MessageTrigger_Once"]
        arboles = {_props(m).get("dialogue", "") for m in msgs}
        assert {"venado", "serpiente", "halcon",
                "campanero", "maestra", "paburu"} <= arboles

    def test_altares_no_automaticos(self) -> None:
        altares = [o for o in _objetos("Objects")
                   if o.get("type") == "EventTrigger"]
        assert {o.get("name") for o in altares} == {
            "altar_venado", "altar_serpiente", "altar_halcon"}
        for altar in altares:
            props = _props(altar)
            assert props.get("automatico") == "false"
            assert props.get("evento") == altar.get("name")

    def test_portal_con_llave_a_paburu(self) -> None:
        warps = [o for o in _objetos("Objects") if o.get("type") == "WarpZone"]
        assert len(warps) == 1
        props = _props(warps[0])
        assert props["destino_stage_id"] == "boss_paburu"
        assert props["key_id"] == "paburu_despertado"


class TestTrazadoNuevo:
    def test_dimensiones(self) -> None:
        from src.stages.stage4_1 import trazado
        assert (trazado.MW, trazado.MH) == (960, 40)
        assert trazado.ANCHO_SECCION == 160
        assert trazado.FILA_SUELO == 32

    def test_altares_en_llano(self) -> None:
        from src.stages.stage4_1 import trazado
        for col in (trazado.COLUMNA_ALTAR_VENADO,
                    trazado.COLUMNA_ALTAR_SERPIENTE,
                    trazado.COLUMNA_ALTAR_HALCON):
            assert trazado.altura_del_suelo(col) == trazado.FILA_SUELO, col

    def test_luces_en_fase6(self) -> None:
        from src.stages.stage4_1 import trazado
        assert len(trazado.COLUMNAS_DE_LUZ) == 13
        assert all(800 <= c <= 950 for c in trazado.COLUMNAS_DE_LUZ)

    def test_fases_en_columnas(self) -> None:
        from src.stages.stage4_1 import trazado
        from src.stages.stage4_1.fases import FASES
        assert [f.desde_columna for f in FASES] == [i * 160 for i in range(6)]
        assert trazado.fase_de_la_columna(880) == 6


class TestAudioNuevo:
    @pytest.mark.parametrize("fase", [1, 2, 3, 4, 5, 6])
    def test_musica_existe_y_resuelve(self, fase: int) -> None:
        from src.framework.audio.dynamic_music import resolver_pista_de_musica
        nombre = f"mus_stage41_f{fase}"
        ruta = RAIZ / "assets" / "music" / (nombre + ".wav")
        assert ruta.is_file()
        assert resolver_pista_de_musica(nombre) is not None

    @pytest.mark.parametrize("fase", [1, 2, 3, 4, 5, 6])
    def test_ambiente_existe(self, fase: int) -> None:
        from src.stages.stage4_1.fases import FASES
        ruta = RAIZ / "assets" / FASES[fase - 1].sonido_ambiente
        assert ruta.is_file(), ruta

    @pytest.mark.parametrize("nombre", ["s41_trueno", "s41_despertar",
                                        "s41_liberacion", "s41_paso_luz",
                                        "s41_golpe_silencio",
                                        "s41_grito_halcon"])
    def test_efectos_existen(self, nombre: str) -> None:
        ruta = (RAIZ / "assets" / "sfx" / "environment" / (nombre + ".wav"))
        assert ruta.is_file(), ruta

    def test_cama_de_fuego_existe(self) -> None:
        ruta = (RAIZ / "assets" / "sfx" / "environment"
                / "amb_stage41_fuego.wav")
        assert ruta.is_file(), ruta

    def test_fases_sin_resolver_none(self) -> None:
        """S41-AUD: ningún resolver()->None para música requerida."""
        from src.framework.audio.dynamic_music import resolver_pista_de_musica
        from src.stages.stage4_1.fases import FASES
        for fase in FASES:
            assert fase.musica is not None
            assert resolver_pista_de_musica(fase.musica) is not None, fase.numero


class TestDialogosNuevos:
    def test_cinco_arboles(self) -> None:
        datos = json.loads((RAIZ / "data" / "dialogues" / "stage4_1.json")
                           .read_text(encoding="utf-8"))
        ids = {d["id"] for d in datos}
        assert {"venado", "serpiente", "halcon",
                "campanero", "maestra", "paburu"} == ids

    def test_hablan_jhon_y_jin(self) -> None:
        datos = json.loads((RAIZ / "data" / "dialogues" / "stage4_1.json")
                           .read_text(encoding="utf-8"))
        voces = {n.get("speaker", "")
                 for d in datos for n in d["nodes"].values()}
        assert "Jhon" in voces and "Jin" in voces

    def test_liberacion_cierra_cada_espiritu(self) -> None:
        datos = json.loads((RAIZ / "data" / "dialogues" / "stage4_1.json")
                           .read_text(encoding="utf-8"))
        for d in datos:
            if d["id"] not in ("venado", "serpiente", "halcon"):
                continue
            textos = " ".join(n.get("text", "") for n in d["nodes"].values())
            assert len(textos) > 40, d["id"]

    def test_retratos_y_voces_con_archivo(self) -> None:
        """S41 audiovisual: cada nodo con retrato/voz apunta a un fichero
        que existe. Jin no tiene retrato en el repo (hueco documentado,
        no placeholder): sus nodos van sin retrato pero con hablante."""
        datos = json.loads((RAIZ / "data" / "dialogues" / "stage4_1.json")
                           .read_text(encoding="utf-8"))
        for d in datos:
            for nid, n in d["nodes"].items():
                assert n.get("speaker"), (d["id"], nid)
                retrato = n.get("portrait")
                if retrato:
                    assert (RAIZ / "assets" / "sprites" / "portraits"
                            / retrato).is_file(), retrato
                voz = n.get("voice")
                if voz:
                    candidatos = list((RAIZ / "assets" / "sfx" / "voz").glob(
                        voz + ".*"))
                    assert candidatos, voz
        jin = [n for d in datos for n in d["nodes"].values()
               if n.get("speaker") == "Jin"]
        assert jin, "Jin debe hablar en el nivel"
        assert all(not n.get("portrait") for n in jin)

    def test_piras_y_antorchas_en_trazado(self) -> None:
        from src.stages.stage4_1 import trazado
        assert len(trazado.PIRAS_FASE4) == 3
        assert all(480 <= c < 560 for c in trazado.PIRAS_FASE4)
        assert len(trazado.ANTORCHAS_FASE6) == 4
        assert all(800 <= c <= 940 for c in trazado.ANTORCHAS_FASE6)
