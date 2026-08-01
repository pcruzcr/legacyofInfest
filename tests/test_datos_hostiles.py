"""
Qué hace el juego cuando el fichero de entrada es basura.

AUD-121 — el resultado de la auditoría
=======================================
Se sometió `SaveManager.load` a doce entradas hostiles y **ninguna** lo rompió:
cada una devolvió `None` o un `SaveData` con valores por defecto. El camino de
guardado ya era correcto —escritura a temporal, `fsync`, `os.replace`
atómico— y el de carga captura la familia de excepciones adecuada.

Este fichero **no corrige un defecto**: fija un comportamiento que ya era
bueno, para que siga siéndolo. La distinción importa. Una suite que sólo
contiene pruebas de regresión de defectos pasados deja sin vigilancia
justamente lo que hoy funciona, y ese es el código que alguien optimizará
dentro de seis meses sin saber qué garantizaba.

Lo que sí se verificó y merece quedar escrito
---------------------------------------------
`stage_id` se carga tal cual del fichero, incluido `"../../../etc/passwd"`.
Eso sería una travesía de rutas **si** ese valor construyera alguna ruta. Se
rastreó su uso completo: sólo se compara con `STAGE_ORDER`, se muestra en la
pantalla de carga y se pasa a los logros. El `stage_id` que arma la ruta de un
módulo sale de `STAGE_ORDER`, que es una lista fija en el código, no del
guardado. No hay travesía; la prueba de abajo vigila que siga sin haberla.
"""
from __future__ import annotations

import pytest

from src.engine.core.save_data import MAX_SLOTS, SaveData
from src.engine.core.save_manager import SaveManager


@pytest.fixture
def gestor(tmp_path, monkeypatch) -> SaveManager:
    """Un `SaveManager` que escribe en un directorio desechable."""
    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path / "saves")
    return SaveManager()


#: Cada caso es `(nombre, bytes)`. El nombre sale en el mensaje de fallo, que
#: es lo que alguien va a leer a las tres de la mañana.
ENTRADAS_HOSTILES = [
    ("fichero vacío", b""),
    ("no es JSON", b"{{{ no soy json"),
    ("JSON pero no un objeto", b"[1, 2, 3]"),
    ("sólo la versión", b'{"version": 2}'),
    ("tipos absurdos", b'{"stage_id": 42, "health": "muchisima"}'),
    ("checkpoint negativo", b'{"checkpoint_id": -7}'),
    ("anidamiento de 200", b'{"a":' * 200 + b"1" + b"}" * 200),
    ("infinito", b'{"health": 1e400}'),
    ("NaN", b'{"health": NaN}'),
    ("nulos donde van números", b'{"stage_id": null, "health": null}'),
    ("clave repetida", b'{"health": 1, "health": 99}'),
    ("cadena de 200 000 caracteres", b'{"stage_id": "' + b"x" * 200_000 + b'"}'),
    ("bytes que no son UTF-8", b'{"stage_id": "\xff\xfe\xfd"}'),
]


class TestUnGuardadoCorruptoNoTumbaElJuego:
    @pytest.mark.parametrize(
        ("descripcion", "contenido"), ENTRADAS_HOSTILES,
        ids=[d for d, _ in ENTRADAS_HOSTILES],
    )
    def test_cargar_basura_no_lanza(self, gestor, descripcion, contenido) -> None:
        """El contrato: devolver algo utilizable o `None`, nunca explotar.

        Un `Traceback` al pulsar «Continuar» pierde la partida del jugador y
        además le hace pensar que el juego está roto del todo.
        """
        gestor._slot_path(1).write_bytes(contenido)
        resultado = gestor.load(1)
        assert resultado is None or isinstance(resultado, SaveData), (
            f"«{descripcion}» devolvió {type(resultado).__name__}"
        )

    def test_una_partida_corrupta_no_oculta_las_sanas(self, gestor) -> None:
        """La ranura 2 rota no debe borrar del menú a la 1 y la 3.

        Es el fallo que convierte «he perdido una partida» en «he perdido
        todas», y ocurre cuando el listado propaga la excepción de un elemento.
        """
        buena = SaveData(stage_id="stage0", health=3.0)
        gestor.save(1, buena)
        gestor.save(3, buena)
        gestor._slot_path(2).write_bytes(b"{{{roto")

        ranuras = gestor.list_slots()
        assert {r["slot"] for r in ranuras} == {1, 3}


class TestLosLimitesDeRanura:
    """Partición por equivalencia sobre el número de ranura."""

    @pytest.mark.parametrize("ranura", [0, -1, MAX_SLOTS + 1, 9999])
    def test_guardar_fuera_de_rango_es_un_error_ruidoso(self, gestor, ranura) -> None:
        """Guardar en una ranura que no existe **debe** fallar en voz alta.

        Aquí sí se lanza, y a propósito: quien llama se ha equivocado, y
        tragárselo en silencio significaría que el jugador cree haber guardado.
        """
        with pytest.raises(ValueError):
            gestor.save(ranura, SaveData())

    @pytest.mark.parametrize("ranura", [0, -1, MAX_SLOTS + 1, 9999])
    def test_cargar_fuera_de_rango_devuelve_none(self, gestor, ranura) -> None:
        """Cargar, en cambio, es una consulta: no hay nada, no hay nada."""
        assert gestor.load(ranura) is None

    @pytest.mark.parametrize("ranura", [1, MAX_SLOTS])
    def test_los_extremos_validos_funcionan(self, gestor, ranura) -> None:
        """Sin esto, las dos pruebas de arriba pasarían con `MAX_SLOTS = 0`."""
        gestor.save(ranura, SaveData(stage_id="stage0"))
        assert gestor.load(ranura) is not None

    def test_borrar_una_ranura_inexistente_no_falla(self, gestor) -> None:
        gestor.delete(1)
        gestor.delete(MAX_SLOTS + 5)


class TestNoHayTravesiaDeRutas:
    """El `stage_id` del fichero no debe poder señalar fuera del proyecto."""

    def test_un_stage_id_con_puntos_no_construye_ninguna_ruta(self, gestor) -> None:
        """Se carga tal cual, y eso está bien **mientras** no arme rutas.

        Si algún día alguien escribe `Path(f"assets/maps/{data.stage_id}")`,
        esta prueba no lo cazará —no puede—, pero el comentario de arriba
        explica dónde mirar. Lo que sí se fija aquí es que el valor llega
        intacto y sin ejecutar nada por el camino.
        """
        gestor._slot_path(1).write_bytes(b'{"stage_id": "../../../etc/passwd"}')
        datos = gestor.load(1)
        assert datos is not None
        assert datos.stage_id == "../../../etc/passwd"

    def test_el_registro_de_escenarios_no_lee_del_guardado(self) -> None:
        """La comprobación que de verdad cierra la travesía.

        `discover_stages` construye rutas de módulo con `stage_id`, pero los
        saca de `STAGE_ORDER`, que es una lista fija en el código fuente. Un
        guardado manipulado no puede meter un nombre ahí.
        """
        import inspect

        from src.engine.core import stage_registry

        fuente = inspect.getsource(stage_registry.discover_stages)
        assert "STAGE_ORDER" in fuente
        assert "SaveData" not in fuente and "save" not in fuente.lower(), (
            "el registro de escenarios ha empezado a leer del guardado: "
            "revisa que un `stage_id` manipulado no pueda importar un módulo "
            "arbitrario"
        )


class TestLosLogrosSobrevivenAlCambioDeFormato:
    """AUD-124 — `_stats` estaba declarado `dict[str, int]` y guardaba una lista.

    La anotación mentía. Funcionaba, porque Python no comprueba anotaciones en
    tiempo de ejecución, pero quien leyera `dict[str, int]` podía escribir
    `_stats["explored_stages"] + 1` y romperle la partida a alguien.

    Los escenarios visitados son un **conjunto**, no un contador, y ahora
    viven en su propio atributo. Lo que estas pruebas protegen es que el
    fichero en disco no cambiara de forma: un profesor con logros de medio
    semestre no debe perderlos porque yo haya arreglado una anotación.
    """

    @pytest.fixture
    def sistema(self, tmp_path, monkeypatch):
        import src.engine.core.achievements as modulo

        monkeypatch.setattr(modulo, "ACHIEVEMENTS_PATH", tmp_path / "logros.json")
        return modulo.AchievementSystem()

    def test_los_escenarios_visitados_se_guardan_y_se_recuperan(self, sistema) -> None:
        for stage in ("stage0", "stage1_1", "stage1_2"):
            sistema.mark_explorer(stage)
        sistema.save()

        import src.engine.core.achievements as modulo
        otro = modulo.AchievementSystem()
        otro.load()
        assert otro._explored_stages == ["stage0", "stage1_1", "stage1_2"]

    def test_un_fichero_del_formato_viejo_se_lee_igual(self, sistema, tmp_path) -> None:
        """El caso que de verdad importa: la partida que ya existe en disco."""
        import orjson

        (tmp_path / "logros.json").write_bytes(orjson.dumps({
            "progress": {},
            "stats": {"enemies_killed": 7,
                      "explored_stages": ["stage0", "stage2_2"]},
        }))
        sistema.load()
        assert sistema._explored_stages == ["stage0", "stage2_2"]
        assert sistema._stats["enemies_killed"] == 7
        assert "explored_stages" not in sistema._stats, (
            "la lista volvió a colarse en el diccionario de contadores"
        )

    def test_no_se_cuenta_dos_veces_el_mismo_escenario(self, sistema) -> None:
        for _ in range(5):
            sistema.mark_explorer("stage0")
        assert sistema._explored_stages == ["stage0"]

    def test_un_stage_id_vacio_no_entra(self, sistema) -> None:
        """Un mapa sin `stage_id` no debe contar como escenario explorado."""
        sistema.mark_explorer("")
        assert sistema._explored_stages == []

    def test_los_contadores_no_admiten_basura_del_fichero(self, sistema, tmp_path) -> None:
        """Si el fichero trae texto donde va un contador, se descarta.

        Antes cualquier valor entraba en `_stats` tal cual, y la primera suma
        reventaba en la partida del jugador en vez de al cargar.
        """
        import orjson

        (tmp_path / "logros.json").write_bytes(orjson.dumps({
            "progress": {},
            "stats": {"enemies_killed": "muchisimos", "parries": 3},
        }))
        sistema.load()
        assert "enemies_killed" not in sistema._stats
        assert sistema._stats["parries"] == 3
