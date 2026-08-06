"""AUD-296 — extender el motor sin tocar el núcleo.

Qué añade sobre el bus de eventos, que es la pregunta justa
-----------------------------------------------------------
El bus ya sirve para enterarse de que algo pasó. Lo que no da es **descubrimiento**
—un manejador del bus hay que suscribirlo desde código del motor, así que
«extender sin tocar el núcleo» era falso— ni los puntos que el bus no publica,
como dibujar: nadie emite un evento por fotograma con la superficie dentro.

Lo que este fichero defiende
----------------------------
1. Que un `.py` dejado en `plugins/` se cargue solo.
2. Que un plugin roto **no se lleve la clase por delante** — misma decisión que
   AUD-289 para las entidades.
3. Que uno que falla repetidamente se desenganche, porque esto corre por
   fotograma y sesenta trazas por segundo entierran la causa.
4. Que una errata en el nombre del gancho **se diga**, en vez de dejar un
   plugin que se carga y no hace nada.
"""
from __future__ import annotations

import pytest

from src.engine.core.plugins import (
    FALLOS_TOLERADOS,
    GANCHOS,
    GestorDePlugins,
    get_gestor,
)


@pytest.fixture
def gestor() -> GestorDePlugins:
    return GestorDePlugins()


class TestEnganchar:
    def test_un_gancho_conocido_se_engancha(self, gestor) -> None:
        assert gestor.enganchar("escenario_dibujado", lambda **_: None)
        assert gestor.enganchados("escenario_dibujado") == 1

    def test_una_errata_se_dice(self, gestor) -> None:
        """El error más probable de un plugin recién escrito. Sin el aviso, se
        carga, no hace nada y no dice por qué."""
        assert not gestor.enganchar("escenario_dibujao", lambda **_: None)

    def test_se_dispara_con_sus_datos(self, gestor) -> None:
        recibido = {}
        gestor.enganchar("escenario_actualizado",
                         lambda **datos: recibido.update(datos))
        gestor.disparar("escenario_actualizado", escena="x", dt=0.016)
        assert recibido == {"escena": "x", "dt": 0.016}

    def test_disparar_un_gancho_vacio_no_hace_nada(self, gestor) -> None:
        gestor.disparar("juego_arrancado", app=None)

    def test_los_ganchos_documentados_son_los_que_hay(self) -> None:
        """Cada gancho es una promesa de estabilidad hacia veintiséis personas.
        La lista corta es la decisión."""
        assert set(GANCHOS) == {
            "juego_arrancado", "escenario_cargado",
            "escenario_actualizado", "escenario_dibujado",
        }


class TestUnPluginRoto:
    def test_no_tumba_el_fotograma(self, gestor) -> None:
        def _revienta(**_):
            raise RuntimeError("me olvidé de un import")

        gestor.enganchar("escenario_dibujado", _revienta)
        gestor.disparar("escenario_dibujado", superficie=None, escena=None)

    def test_los_demas_siguen_corriendo(self, gestor) -> None:
        """Un plugin roto no puede silenciar al de al lado."""
        visto = []

        def _revienta(**_):
            raise RuntimeError("boom")

        gestor.enganchar("escenario_dibujado", _revienta)
        gestor.enganchar("escenario_dibujado", lambda **_: visto.append(1))
        gestor.disparar("escenario_dibujado", superficie=None, escena=None)
        assert visto == [1]

    def test_al_segundo_fallo_se_desengancha(self, gestor) -> None:
        """Esto corre por fotograma: sesenta trazas por segundo del mismo error
        entierran el registro donde estaría la causa."""
        def _revienta(**_):
            raise RuntimeError("boom")

        gestor.enganchar("escenario_dibujado", _revienta)
        for _ in range(FALLOS_TOLERADOS):
            gestor.disparar("escenario_dibujado", superficie=None, escena=None)
        assert gestor.enganchados("escenario_dibujado") == 0


class TestDescubrir:
    def test_carga_un_plugin_del_directorio(self, gestor, tmp_path) -> None:
        (tmp_path / "saludo.py").write_text(
            "def registrar(gestor):\n"
            "    gestor.enganchar('juego_arrancado', lambda **_: None)\n",
            encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 1
        assert gestor.cargados == ["saludo"]
        assert gestor.enganchados("juego_arrancado") == 1

    def test_un_directorio_que_no_existe_no_es_un_error(self, gestor, tmp_path) -> None:
        """Lo normal es no tener plugins. Avisar en cada arranque enseñaría a
        ignorar los avisos."""
        assert gestor.descubrir(tmp_path / "no_existe") == 0

    def test_los_que_empiezan_por_guion_bajo_se_saltan(self, gestor, tmp_path) -> None:
        """Para que un plugin pueda tener módulos auxiliares."""
        (tmp_path / "_ayuda.py").write_text("x = 1\n", encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 0

    def test_uno_sin_registrar_se_ignora_con_aviso(self, gestor, tmp_path) -> None:
        (tmp_path / "vacio.py").write_text("x = 1\n", encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 0

    def test_uno_que_no_importa_no_tumba_el_arranque(self, gestor, tmp_path) -> None:
        (tmp_path / "roto.py").write_text("import modulo_que_no_existe\n",
                                          encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 0

    def test_uno_cuyo_registrar_falla_tampoco(self, gestor, tmp_path) -> None:
        (tmp_path / "malo.py").write_text(
            "def registrar(gestor):\n    raise RuntimeError('boom')\n",
            encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 0

    def test_carga_varios_en_orden(self, gestor, tmp_path) -> None:
        for nombre in ("b", "a"):
            (tmp_path / f"{nombre}.py").write_text(
                "def registrar(gestor):\n    pass\n", encoding="utf-8")
        assert gestor.descubrir(tmp_path) == 2
        assert gestor.cargados == ["a", "b"]


class TestElCableado:
    def test_app_descubre_y_dispara(self) -> None:
        import inspect

        from src.engine.core import app

        fuente = inspect.getsource(app)
        assert "self.plugins.descubrir()" in fuente
        assert 'disparar("juego_arrancado"' in fuente

    def test_el_escenario_dispara_los_tres_suyos(self) -> None:
        import inspect

        from src.framework.scenes import stage_scene

        fuente = inspect.getsource(stage_scene)
        for gancho in ("escenario_cargado", "escenario_actualizado",
                       "escenario_dibujado"):
            assert f'"{gancho}"' in fuente, f"{gancho} no se dispara desde ninguna parte"

    def test_el_gestor_global_es_uno_solo(self) -> None:
        assert get_gestor() is get_gestor()

    def test_el_directorio_esta_documentado(self) -> None:
        from pathlib import Path

        from src.engine.core import settings

        readme = Path(settings.PROJECT_ROOT) / "plugins" / "README.md"
        assert readme.is_file(), "un punto de extensión sin documentar no existe"
        texto = readme.read_text(encoding="utf-8")
        for gancho in GANCHOS:
            assert gancho in texto, f"{gancho} no está en el README de plugins"
