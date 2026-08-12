"""AUD-450 — el bestiario y los récords se compartían entre partidas.

Los dos guardan en `user_data_dir()/saves/`, un fichero por **instalación**:
`bestiary.json` y `speedrun.json`. Es el mismo defecto que AUD-438 quitó de
los logros, y con la misma consecuencia: empiezas una partida nueva y el
bestiario ya está descubierto, y los récords son los de otro perfil.

Por qué por ruta y no dentro de `SaveData`
------------------------------------------
Los logros se metieron dentro de la partida porque son pocos datos y encajan
en el fichero. El bestiario crece con cada enemigo del juego y los récords con
cada escenario, y los dos ya saben serializarse solos y aceptan una ruta.
Meterlos dentro obligaría a duplicar esa serialización y a subir la versión
otra vez; derivar la ruta del perfil activo consigue el aislamiento sin
tocar cómo se guardan.

Sigue habiendo **un** sistema de guardado: el `SaveManager` es quien dice qué
partida está activa, y de ahí sale la carpeta.
"""
from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from src.engine.core.save_manager import SaveManager, ruta_del_perfil


@pytest.fixture
def gestor(tmp_path, monkeypatch):
    monkeypatch.setattr(SaveManager, "SAVES_DIR", tmp_path)
    return SaveManager()


class TestLaRutaDependeDelPerfil:
    def test_dos_ranuras_dan_dos_rutas(self, gestor) -> None:
        gestor.ranura_activa = 1
        uno = ruta_del_perfil("bestiary.json")
        gestor.ranura_activa = 2
        dos = ruta_del_perfil("bestiary.json")
        assert uno != dos, (
            f"las dos partidas escriben en el mismo fichero: {uno}"
        )

    def test_la_misma_ranura_da_la_misma_ruta(self, gestor) -> None:
        gestor.ranura_activa = 3
        assert ruta_del_perfil("speedrun.json") == ruta_del_perfil("speedrun.json")

    def test_sin_ranura_activa_se_conserva_la_ruta_de_siempre(self, gestor) -> None:
        """El respaldo: un escenario lanzado con --stage no declara ranura, y
        quedarse sin sitio donde escribir sería peor que compartirlo."""
        gestor.ranura_activa = None
        ruta = ruta_del_perfil("bestiary.json")
        assert ruta.name == "bestiary.json"
        assert "slot" not in ruta.parent.name

    def test_la_ranura_va_en_la_carpeta_y_no_en_el_nombre(self, gestor) -> None:
        """Para que borrar una partida sea borrar una carpeta.

        Con el número en el nombre —`bestiary_1.json`— borrar un perfil obliga
        a recordar la lista de ficheros que le pertenecen, y el día que se
        añada uno nuevo se quedará huérfano.
        """
        gestor.ranura_activa = 2
        ruta = ruta_del_perfil("bestiary.json")
        assert ruta.name == "bestiary.json"
        assert "2" in ruta.parent.name


class TestElBestiarioNoSeContamina:
    def test_lo_visto_en_una_partida_no_aparece_en_otra(self, gestor) -> None:
        from src.framework.entities.bestiary import Bestiary

        gestor.ranura_activa = 1
        uno = Bestiary()
        uno.record_kill("walker")
        uno.save()

        gestor.ranura_activa = 2
        dos = Bestiary()
        dos.load()

        assert dos.get_entry("walker") is None or dos.get_entry("walker").kills == 0, (
            "la ranura 2 empieza con el bestiario de la 1 ya descubierto"
        )

    def test_y_al_volver_sigue_estando(self, gestor) -> None:
        """Aislar no puede convertirse en perder el progreso."""
        from src.framework.entities.bestiary import Bestiary

        gestor.ranura_activa = 1
        uno = Bestiary()
        uno.record_kill("walker")
        uno.save()

        gestor.ranura_activa = 2
        Bestiary().save()

        gestor.ranura_activa = 1
        vuelta = Bestiary()
        vuelta.load()
        entrada = vuelta.get_entry("walker")
        assert entrada is not None and entrada.kills == 1
