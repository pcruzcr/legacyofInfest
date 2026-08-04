"""AUD-245 — cuatro accesores públicos con su lógica duplicada al lado.

El patrón, cuatro veces
=======================
Una clase publicaba un accesor y, a pocas líneas, otro método suyo hacía **la
misma consulta a mano** en vez de llamarlo. El resultado son dos copias de una
regla: la pública sin llamadores —así aparecían en el barrido de AUD-233— y la
privada llevándose todo el uso.

======================  =============================================
símbolo                 quién repetía su trabajo
======================  =============================================
`ajustar_bus`           `set_music_volume` y `set_sfx_volume`
`Bestiary.get_entry`    `_asegurar`
`GhostData.get_frame`   `posicion_en`
`SpeedrunTimer.get_splits`  `save`
======================  =============================================

No son sólo estética. Dos copias de una regla son una que se queda atrás, y en
`get_splits` la diferencia ya era un defecto real: `save` volcaba `self._splits`
—la lista **viva**— dentro del diccionario que se serializa, mientras que el
accesor devuelve una copia. Quien tocara los parciales después de guardar estaba
editando lo que se acababa de escribir.

Estas pruebas fijan que la delegación exista, no sólo que el resultado coincida:
comprobar el resultado pasaría igual con las dos copias, que es exactamente la
situación de la que se viene.
"""
from __future__ import annotations

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _llama_a(fichero: str, funcion: str, objetivo: str) -> bool:
    """¿El cuerpo de `funcion` contiene una llamada a `objetivo`?"""
    arbol = ast.parse((RAIZ / fichero).read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if nodo.name != funcion:
            continue
        for hijo in ast.walk(nodo):
            if isinstance(hijo, ast.Call):
                f = hijo.func
                nombre = getattr(f, "attr", None) or getattr(f, "id", None)
                if nombre == objetivo:
                    return True
    return False


class TestLosVolumenesPasanPorElBus:
    RUTA = "src/engine/audio/audio_manager.py"

    def test_la_musica_delega_en_ajustar_bus(self) -> None:
        assert _llama_a(self.RUTA, "set_music_volume", "ajustar_bus")

    def test_los_efectos_delegan_en_ajustar_bus(self) -> None:
        assert _llama_a(self.RUTA, "set_sfx_volume", "ajustar_bus")

    def test_y_el_volumen_sigue_llegando(self, _pygame_init) -> None:
        """La delegación no puede cambiar lo que oye el jugador."""
        from src.engine.audio.audio_manager import AudioManager

        audio = AudioManager()
        audio.set_music_volume(0.25)
        assert audio.music_volume == 0.25
        audio.set_sfx_volume(0.5)
        assert audio.sfx_volume == 0.5

    def test_los_valores_absurdos_se_siguen_acotando(self, _pygame_init) -> None:
        from src.engine.audio.audio_manager import AudioManager

        audio = AudioManager()
        audio.set_music_volume(9.0)
        assert audio.music_volume == 1.0
        audio.set_sfx_volume(-3.0)
        assert audio.sfx_volume == 0.0


class TestElBestiarioConsultaPorSuAccesor:
    def test_asegurar_delega_en_get_entry(self) -> None:
        assert _llama_a("src/framework/entities/bestiary.py",
                        "_asegurar", "get_entry")


class TestElFantasmaLeeSusFotogramasPorElAccesor:
    def test_posicion_en_delega_en_get_frame(self) -> None:
        assert _llama_a("src/framework/stage/speedrun_mode.py",
                        "posicion_en", "get_frame")

    def test_el_indice_fuera_de_rango_sigue_devolviendo_none(self) -> None:
        """La señal de «vas por detrás de tu récord» no puede perderse."""
        from src.framework.stage.speedrun_mode import GhostData

        fantasma = GhostData()
        assert fantasma.posicion_en(0.0) is None
        fantasma.record(10.0, 20.0, "idle")
        assert fantasma.posicion_en(0.0) == (10.0, 20.0)
        assert fantasma.posicion_en(9999.0) is None


class TestElCronometroGuardaUnaCopia:
    def test_save_delega_en_get_splits(self) -> None:
        assert _llama_a("src/framework/stage/speedrun_mode.py",
                        "save", "get_splits")

    def test_tocar_los_parciales_despues_no_altera_lo_guardado(
        self, tmp_path,
    ) -> None:
        """El defecto real que escondía la duplicación.

        `save` volcaba la lista viva. Con `get_splits` se guarda una copia, así
        que seguir cronometrando después de guardar ya no reescribe el fichero
        que se acaba de escribir.
        """
        import json

        from src.framework.stage.speedrun_mode import SpeedrunTimer

        ruta = tmp_path / "speedrun.json"
        reloj = SpeedrunTimer()
        reloj.start()
        reloj.update(5.0)
        reloj.split("stage0")
        reloj.save(ruta)

        reloj.update(60.0)
        reloj.split("stage1_1")

        guardado = json.loads(ruta.read_text(encoding="utf-8"))
        assert [s["stage_id"] for s in guardado["splits"]] == ["stage0"], (
            "lo escrito en disco cambió al seguir jugando: `save` volvió a "
            "volcar la lista viva en vez de una copia"
        )
